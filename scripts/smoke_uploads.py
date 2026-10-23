"""Exercise real local Upload/Analyze widgets in a disposable database.

Uses prepared research pixels and actual local polyp inference; no scripted model,
no LLM call, no image/safety/report approval, and no application database changes.
The local research kit and installed companion are prerequisites, not downloads.
"""

import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from streamlit.testing.v1 import AppTest

from medical_assistant.auth import LocalAuth
from medical_assistant.database import seed
from medical_assistant.research_examples import PATIENT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parents[1]
    parser.add_argument("--kit", type=Path, default=root / "data/research-demo")
    args = parser.parse_args()
    kit = args.kit.resolve()
    outcomes = []
    with tempfile.TemporaryDirectory(prefix="lovisa-upload-smoke-") as temp:
        path = Path(temp) / "history.sqlite3"
        seed(path)
        auth = LocalAuth(path)
        auth.create_clinician("upload.smoke", "temporary-upload-smoke-password")
        # Only persistence is redirected. File uploads, validators and CV run for real.
        with (
            patch("medical_assistant.runtime.get_services", return_value=(path, auth)),
            patch.dict(os.environ, {"LOVISA_RESEARCH_DEMO_DIR": str(kit)}),
        ):
            app = AppTest.from_file(str(root / "app.py"), default_timeout=30).run()
            app.text_input(key="login_user").input("upload.smoke")
            app.text_input(key="login_password").input(
                "temporary-upload-smoke-password"
            )
            app.button(key="login").click().run()
            app.selectbox(key="patient").set_value(PATIENT).run()
            job = None
            try:
                for view, prefix, filename in (
                    ("CT review", "ct", "ct-real.mhcra.zip"),
                    ("Endoscopy review", "endo", "endoscopy-03.endo.zip"),
                    ("Endoscopy review", "endo", "endoscopy-03.jpg"),
                ):
                    app.radio(key="workspace").set_value(view).run(timeout=30)
                    app.get("file_uploader")[0].set_value(
                        (
                            filename,
                            (kit / filename).read_bytes(),
                            "application/zip"
                            if filename.endswith("zip")
                            else "image/jpeg",
                        )
                    ).run()
                    started = time.monotonic()
                    app.button(key=prefix + "_generate").click().run(timeout=30)
                    if prefix + "_job" in app.session_state:
                        job = app.session_state[prefix + "_job"]
                        while (
                            job.status() == "running"
                            and time.monotonic() - started < 115
                        ):
                            time.sleep(0.2)
                        if job.status() != "complete":
                            raise RuntimeError(job.error)
                        app.run(timeout=30)
                    if app.exception or app.error:
                        raise RuntimeError(
                            str([e.value for e in app.error]) or str(app.exception)
                        )
                    _, proposal = app.session_state.imaging_proposal
                    assert len(app.image) >= 2
                    assert not app.session_state.imaging_store.snapshots(PATIENT)
                    assert "case_id" not in app.session_state
                    outcomes.append(
                        {
                            "file": filename,
                            "operation": "existing-results validation"
                            if filename.endswith("zip")
                            else "actual installed-model inference",
                            "seconds_to_visible_results": round(
                                time.monotonic() - started, 2
                            ),
                            "candidates": len(
                                proposal["manifest"]["study"]["candidates"]
                            ),
                            "review": "pending; no approval issued",
                        }
                    )
                    app.button(
                        key="imaging_discard" if prefix == "ct" else "endo_discard"
                    ).click().run()
            finally:
                if job and job.status() == "running":
                    job.cancel()
    print(json.dumps({"passed": True, "actual_uploads": outcomes}, indent=2))


if __name__ == "__main__":
    main()

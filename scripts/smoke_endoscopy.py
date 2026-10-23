"""Actual bounded synthetic producer/receiver smoke; no imaging or final approvals."""

import argparse
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from medical_assistant.endo_worker import LocalEndoscopyJob
from medical_assistant.imaging_contract import validate_bundle


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--endo-root", required=True)
    p.add_argument("--mode", choices=["fixture", "installed"], default="fixture")
    p.add_argument("--model-dir")
    p.add_argument("--backend", default="onnx-cpu")
    args = p.parse_args()
    with tempfile.TemporaryDirectory() as temp:
        job = LocalEndoscopyJob(
            "synthetic-checklist",
            root=args.endo_root,
            jobs=Path(temp),
            mode=args.mode,
            model_dir=args.model_dir,
            backend=args.backend,
        )
        while job.status() == "running":
            time.sleep(0.05)
        if job.status() != "complete":
            raise ValueError(job.error + "\n" + job.log_path.read_text())
        bundle, _, artifacts = validate_bundle(
            job.bundle_path.read_bytes(), job.patient_id
        )
        if bundle.study_id != job.study_id:
            raise ValueError("Requested study mismatch")
        print(
            f"PASS: actual {args.mode} producer -> LOVISA validator; {len(bundle.study.candidates)} candidate(s), {len(artifacts)} artifacts, {job.elapsed:.2f}s; approvals remain pending."
        )


if __name__ == "__main__":
    main()

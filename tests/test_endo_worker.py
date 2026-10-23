"""Actual artificial producer tests are separate from scripted worker lifecycle checks."""

import os
import sys
import time

import pytest

from medical_assistant.endo_worker import LocalEndoscopyJob


def test_explicit_mode_and_patient_validation(tmp_path):
    for kwargs in ({"mode": "cloud"}, {"mode": "fixture", "backend": "openvino-npu"}):
        with pytest.raises(ValueError):
            LocalEndoscopyJob("synthetic-test", root=tmp_path, **kwargs)
    with pytest.raises(ValueError):
        LocalEndoscopyJob("../other", root=tmp_path)
    with pytest.raises(ValueError, match="Install"):
        LocalEndoscopyJob("synthetic-test", root=tmp_path)


def test_endo_command_identity_uses_local_companion_only(tmp_path):
    root = tmp_path / "companion"
    (root / "src/endo").mkdir(parents=True)
    (root / "src/endo/cli.py").write_text("")
    (root / "endo").mkdir()
    (root / "endo/cli.py").write_text(
        "import sys\nfrom pathlib import Path\np=Path(sys.argv[sys.argv.index('--output')+1]);p.mkdir();(p/'bundle.endo.zip').write_bytes(b'scripted worker, not inference')\n"
    )
    python = (
        root / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    )
    python.parent.mkdir(parents=True)
    python.symlink_to(sys.executable)
    job = LocalEndoscopyJob(
        "synthetic-test",
        root=root,
        jobs=tmp_path / "jobs",
        mode="installed",
        model_dir=tmp_path / "model with spaces",
    )
    limit = time.monotonic() + 5
    while job.status() == "running" and time.monotonic() < limit:
        time.sleep(0.02)
    assert job.status() == "complete"
    assert job.process.args[1:4] == ["-m", "endo.cli", "bridge"]
    assert job.process.args[job.process.args.index("--study-id") + 1] == job.study_id
    assert job.patient_id == "synthetic-test"

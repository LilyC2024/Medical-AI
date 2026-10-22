"""Actual stdlib subprocess tests; these dummy workers do not run CT inference."""
import os
import sys
import time
from pathlib import Path

import pytest

from medical_assistant.ct_worker import LocalCTJob


def worker_root(tmp_path, body):
    root = tmp_path / "ct"
    (root / "deploy").mkdir(parents=True)
    (root / "deploy/__init__.py").write_text("")
    (root / "deploy/mhcra_bridge.py").write_text(body)
    executable = root / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    executable.parent.mkdir(parents=True)
    executable.symlink_to(sys.executable)
    return root


def wait(job):
    until = time.monotonic() + 10
    while job.status() == "running" and time.monotonic() < until:
        time.sleep(0.02)
    assert job.status() != "running"


def test_worker_completes_without_shell_and_uses_unique_identity(tmp_path):
    root = worker_root(tmp_path, """import sys
from pathlib import Path
p=Path(sys.argv[sys.argv.index('--output-dir')+1])/'exchange'
p.mkdir(parents=True)
(p/'bundle.mhcra.zip').write_bytes(b'dummy test artifact, not a CT result')
""")
    job = LocalCTJob("synthetic-checklist", root=root, jobs=tmp_path / "jobs")
    wait(job)
    assert job.status() == "complete"
    assert job.bundle_path.is_file()
    assert job.patient_id == "synthetic-checklist"
    assert job.study_id.startswith("synthetic-")
    assert job.process.args[1:3] == ["-m", "deploy.mhcra_bridge"]


@pytest.mark.parametrize("mode", ["cancel", "timeout"])
def test_worker_cancellation_and_watchdog_stop_process(tmp_path, mode):
    root = worker_root(tmp_path, "import time\ntime.sleep(60)\n")
    job = LocalCTJob("synthetic-checklist", root=root, jobs=tmp_path / "jobs", timeout=0.1 if mode == "timeout" else 10)
    if mode == "cancel":
        job.cancel()
    wait(job)
    job.process.wait(timeout=5)
    assert job.status() == ("cancelled" if mode == "cancel" else "timed_out")
    assert not job.bundle_path.exists()


def test_missing_companion_and_invalid_identity_are_actionable(tmp_path):
    with pytest.raises(ValueError, match="Install the CT companion"):
        LocalCTJob("synthetic-checklist", root=tmp_path)
    with pytest.raises(ValueError, match="Invalid synthetic"):
        LocalCTJob("../escape", root=tmp_path)

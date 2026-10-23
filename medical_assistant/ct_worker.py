"""Bounded local CT subprocesses. No shell, uploads, downloads or model tools."""

import os
import signal
import subprocess
import threading
from pathlib import Path
from uuid import uuid4

from medical_assistant.storage import ROOT


def configured_ct_root():
    return (
        Path(os.environ.get("MHCRA_CT_ROOT", str(ROOT.parent / "ai-medimg-2.5D-CT")))
        .expanduser()
        .resolve()
    )


def configured_ct_model(root=None):
    root = Path(root or configured_ct_root())
    default = (
        root / "models/luna16-full"
        if (root / "models/luna16-full/registration.json").is_file()
        else root / "models/luna16"
    )
    return (
        Path(os.environ.get("MHCRA_CT_MODEL_DIR", str(default))).expanduser().resolve()
    )


class LocalCTJob:
    def __init__(
        self,
        patient_id,
        *,
        root=None,
        jobs=None,
        timeout=180,
        mode="legacy",
        model_dir=None,
        device="cpu",
    ):
        import re

        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", patient_id):
            raise ValueError("Invalid synthetic patient ID")
        self.patient_id = patient_id
        if (
            mode not in ("legacy", "lung-fixture", "lung-pretrained")
            or device not in ("cpu", "cuda")
            or (mode != "lung-pretrained" and device != "cpu")
        ):
            raise ValueError("Unsupported CT job mode/device")
        self.mode = mode
        self.study_id = "synthetic-" + uuid4().hex[:16]
        self.root = Path(root or configured_ct_root()).resolve()
        python = (
            self.root
            / ".venv"
            / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        )
        module = (
            "deploy.mhcra_bridge" if mode == "legacy" else "deploy.mhcra_lung_bridge"
        )
        if (
            not python.is_file()
            or not (self.root / (module.replace(".", "/") + ".py")).is_file()
        ):
            raise ValueError(
                "Install the CT companion and its .venv; see docs/IMAGING.md"
            )
        self.directory = Path(jobs or ROOT / "data/imaging/jobs") / uuid4().hex
        self.directory.mkdir(parents=True)
        self.output = self.directory / "demo"
        self.log_path = self.directory / "worker.log"
        self.state = "running"
        self.error = ""
        self._lock = threading.Lock()
        self._log = self.log_path.open("wb")
        command = [
            str(python),
            "-m",
            module,
            "--patient-id",
            patient_id,
            "--study-id",
            self.study_id,
            "--output-dir",
            str(self.output),
        ]
        if mode == "legacy":
            command.append("--demo")
        else:
            command += [
                "--mode",
                "fixture" if mode == "lung-fixture" else "pretrained",
                "--device",
                device,
            ]
            if mode == "lung-pretrained":
                command += [
                    "--model-dir",
                    str(
                        Path(model_dir or configured_ct_model(self.root))
                        .expanduser()
                        .resolve()
                    ),
                ]
        env = {
            **os.environ,
            "LANGCHAIN_TRACING_V2": "false",
            "LANGSMITH_TRACING": "false",
            "OLLAMA_NO_CLOUD": "1",
            "MPLBACKEND": "Agg",
        }
        try:
            self.process = subprocess.Popen(
                command,
                cwd=self.root,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=self._log,
                stderr=subprocess.STDOUT,
                start_new_session=os.name != "nt",
            )
        except Exception:
            self._log.close()
            raise
        threading.Thread(target=self._watch, args=(timeout,), daemon=True).start()

    @property
    def bundle_path(self):
        return self.output / "exchange/bundle.mhcra.zip"

    def _watch(self, timeout):
        try:
            code = self.process.wait(timeout=timeout)
            with self._lock:
                if self.state == "running":
                    self.state = (
                        "complete"
                        if code == 0 and self.bundle_path.is_file()
                        else "failed"
                    )
                    if self.state == "failed":
                        self.error = "CT worker failed. See its local log; no imaging was accepted."
        except subprocess.TimeoutExpired:
            self.cancel(timed_out=True)
        finally:
            self._log.close()

    def cancel(self, *, timed_out=False):
        with self._lock:
            if self.state != "running":
                return
            self.state = "timed_out" if timed_out else "cancelled"
            self.error = (
                "CT worker timed out; no imaging was accepted."
                if timed_out
                else "CT job cancelled."
            )
            try:
                if os.name == "nt":
                    subprocess.run(
                        ["taskkill", "/PID", str(self.process.pid), "/T", "/F"],
                        capture_output=True,
                        timeout=10,
                        check=False,
                    )
                else:
                    os.killpg(self.process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

    def status(self):
        with self._lock:
            return self.state

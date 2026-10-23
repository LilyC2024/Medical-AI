"""Bounded local subprocess lifecycle shared by the endoscopy interfaces."""

import math
import os
import signal
import subprocess
import threading
import time
from pathlib import Path


class LocalJob:
    def __init__(
        self, command, *, cwd, directory, output, timeout=110, input_files=None
    ):
        """Initialise the explicit local model or bounded worker without remote fallback."""
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("Positive finite timeout required")
        self.timeout = min(timeout, 110)
        self.started = time.monotonic()
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=False)
        for name, payload in (input_files or {}).items():
            if (
                Path(name).name != name
                or "\\" in name
                or ":" in name
                or name in ("worker.log", ".", "..")
                or len(payload) > 16 * 1024**2
            ):
                raise ValueError("Invalid local worker input file")
            (self.directory / name).write_bytes(payload)
        self.bundle_path = Path(output)
        self.log_path = self.directory / "worker.log"
        self._log = self.log_path.open("wb")
        self._lock = threading.Lock()
        self.state = "running"
        self.error = ""
        try:
            self.process = subprocess.Popen(
                command,
                cwd=cwd,
                env={
                    **os.environ,
                    "LANGCHAIN_TRACING": "false",
                    "LANGCHAIN_TRACING_V2": "false",
                    "LANGSMITH_TRACING": "false",
                    "OLLAMA_NO_CLOUD": "1",
                },
                stdin=subprocess.DEVNULL,
                stdout=self._log,
                stderr=subprocess.STDOUT,
                start_new_session=os.name != "nt",
            )
        except Exception:
            self._log.close()
            raise
        threading.Thread(target=self._watch, daemon=True).start()

    def _watch(self):
        """Publish completion only after successful process exit within the deadline."""
        try:
            code = self.process.wait(timeout=max(0.01, self.timeout - self.elapsed))
            if self.elapsed >= self.timeout:
                self.cancel(timed_out=True)
                return
            with self._lock:
                if self.state == "running":
                    self.state = (
                        "complete"
                        if code == 0 and self.bundle_path.is_file()
                        else "failed"
                    )
                    if self.state == "failed":
                        self.error = "Local image analysis stopped. Check the installed model and local worker log; no review was approved."
        except subprocess.TimeoutExpired:
            self.cancel(timed_out=True)
        finally:
            if self.state in ("timed_out", "cancelled"):
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    pass
            self._log.close()

    def cancel(self, *, timed_out=False):
        """Stop the worker process tree and prevent late result publication."""
        with self._lock:
            if self.state != "running":
                return
            self.state = "timed_out" if timed_out else "cancelled"
            self.error = (
                "Image analysis reached its response limit; no result was accepted."
                if timed_out
                else "Image analysis cancelled."
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

    @property
    def elapsed(self):
        """Return local monotonic time since the job began."""
        return time.monotonic() - self.started

    def status(self):
        """Read worker lifecycle state under its lock."""
        with self._lock:
            return self.state

    def progress(self):
        """Read only allowlisted stage markers from the bounded log tail."""
        stages = {
            "source": "Preparing the source image",
            "model": "Loading the installed image model",
            "detect": "Finding candidate regions",
            "export": "Checking source images and annotations",
        }
        try:
            with self.log_path.open("rb") as handle:
                handle.seek(max(0, self.log_path.stat().st_size - 4096))
                lines = handle.read(4096).decode(errors="replace").splitlines()
            for line in reversed(lines):
                if line.startswith("LOVISA_STAGE="):
                    return stages.get(line.split("=", 1)[1], "Processing image")
        except OSError:
            pass
        return "Starting local image analysis"

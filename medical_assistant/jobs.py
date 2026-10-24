"""Session-owned background work with a hard publication deadline; no UI in workers."""

import math
import threading
import time
from uuid import uuid4

MAX_JOB_SECONDS = 110.0  # Leave room for the browser's next one-second refresh.
_SLOTS = threading.BoundedSemaphore(2)


class WorkStopped(RuntimeError):
    pass


class Budget:
    def __init__(self, seconds=MAX_JOB_SECONDS):
        if not math.isfinite(seconds) or seconds <= 0:
            raise ValueError("A positive finite work budget is required")
        self.seconds = min(seconds, MAX_JOB_SECONDS)
        self.started = time.monotonic()
        self.stopped = threading.Event()

    @property
    def elapsed(self):
        return time.monotonic() - self.started

    def check(self):
        if self.stopped.is_set() or self.elapsed >= self.seconds:
            raise WorkStopped(
                "Work stopped before the two-minute response limit. No final report was approved."
            )


class WorkTask:
    """Run a callable(progress, budget) once; ignore cancelled/late results.

    Threads never write Streamlit state. A timed-out Python/native operation may
    finish unwinding in its daemon thread; its result cannot be published. Slots
    are held until it exits so repeated retries cannot grow unbounded workers.
    """

    def __init__(
        self, target, *, seconds=MAX_JOB_SECONDS, title="Preparing your workspace"
    ):
        self.budget = Budget(seconds)
        if not _SLOTS.acquire(blocking=False):
            raise WorkStopped(
                "Local processing is busy. Wait for the current task to finish before retrying."
            )
        self.id = uuid4().hex
        self._lock = threading.RLock()
        self._state = "running"
        self._step = title
        self._result = None
        self._error = ""
        self._finished = None
        self._timer = threading.Timer(self.budget.seconds, self._timeout)
        self._timer.daemon = True
        self._thread = threading.Thread(target=self._run, args=(target,), daemon=True)
        self._timer.start()
        self._thread.start()

    def _timeout(self):
        with self._lock:
            if self._state == "running":
                self._state = "timed_out"
                self._finished = time.monotonic()
                self._error = "This run reached the response limit. Try again with fewer records or the CT fixture. No final report was approved."
                self.budget.stopped.set()

    def progress(self, message):
        self.budget.check()
        with self._lock:
            if self._state == "running":
                self._step = message

    def _run(self, target):
        try:
            result = target(self.progress, self.budget)
            self.budget.check()
            with self._lock:
                if self._state == "running":
                    self._result = result
                    self._state = "complete"
                    self._finished = time.monotonic()
        except Exception as error:
            if (
                isinstance(error, WorkStopped)
                and self.budget.elapsed >= self.budget.seconds
            ):
                self._timeout()
            with self._lock:
                if self._state == "running":
                    self._state = "failed"
                    self._finished = time.monotonic()
                    self._error = str(error)
        finally:
            self._timer.cancel()
            _SLOTS.release()

    def cancel(self):
        with self._lock:
            if self._state == "running":
                self._state = "cancelled"
                self._finished = time.monotonic()
                self._error = "Processing cancelled. No final report was approved."
                self.budget.stopped.set()
                self._timer.cancel()

    def snapshot(self):
        if self.budget.elapsed >= self.budget.seconds:
            self._timeout()
        with self._lock:
            return {
                "state": self._state,
                "step": self._step,
                "elapsed": (self._finished or time.monotonic()) - self.budget.started,
                "limit": self.budget.seconds,
                "error": self._error,
            }

    def result(self):
        if self.snapshot()["state"] != "complete":
            raise WorkStopped("Processing has no completed result")
        return self._result


class BudgetInference:
    """Check cancellation/deadline before and after the local model call."""

    def __init__(self, inference, budget):
        self.inference, self.budget = inference, budget
        self.model = inference.model

    @property
    def model_digest(self):
        return getattr(self.inference, "model_digest", None)

    def assess(self, *args, **kwargs):
        self.budget.check()
        result = self.inference.assess(*args, **kwargs)
        self.budget.check()
        return result

    def close(self):
        self.inference.close()

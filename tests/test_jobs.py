"""Scripted work, not live inference; verify timeout/cancellation races."""

import threading
import time
import pytest
from medical_assistant.jobs import (
    WorkTask,
    Budget,
    BudgetInference,
    WorkStopped,
    MAX_JOB_SECONDS,
)


def finish(task):
    task._thread.join(timeout=2)
    assert not task._thread.is_alive()


def test_fast_work_reports_actual_stage_and_result():
    def work(progress, budget):
        progress("Checking sources")
        return {"draft": "unreviewed"}

    task = WorkTask(work)
    finish(task)
    assert task.snapshot()["step"] == "Checking sources"
    assert task.result() == {"draft": "unreviewed"}


@pytest.mark.parametrize("action", ["cancel", "timeout"])
def test_late_results_never_publish_and_slots_are_bounded(action):
    entered, release = threading.Event(), threading.Event()

    def slow(progress, budget):
        entered.set()
        release.wait(1)
        return "late clinical draft"

    task = WorkTask(slow, seconds=0.03 if action == "timeout" else 1)
    assert entered.wait(1)
    if action == "cancel":
        task.cancel()
    else:
        time.sleep(0.05)
    assert task.snapshot()["state"] == (
        "cancelled" if action == "cancel" else "timed_out"
    )
    release.set()
    finish(task)
    with pytest.raises(WorkStopped):
        task.result()
    assert task._result is None


def test_model_result_after_cancellation_is_rejected():
    budget = Budget()

    class Model:
        model = "scripted"

        def assess(self, *a, **k):
            budget.stopped.set()
            return "unsupported late output"

    with pytest.raises(WorkStopped):
        BudgetInference(Model(), budget).assess("system", "user")


@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf")])
def test_invalid_budget(value):
    with pytest.raises(ValueError):
        Budget(value)


def test_budget_cannot_exceed_response_limit():
    assert Budget(10000).seconds == MAX_JOB_SECONDS < 120

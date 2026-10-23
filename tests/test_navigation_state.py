"""No inference: fixed navigation and isolation of abandoned patient work."""

import pytest

from medical_assistant.ui.navigation import (
    clear_patient,
    destination,
    ensure_patient,
    go_to,
)


class Task:
    cancelled = False

    def cancel(self):
        self.cancelled = True

    def snapshot(self):
        return {"state": "cancelled"}


class Job(Task):
    patient_id = "old"

    def status(self):
        return "running"


class Store:
    discarded = None

    def discard(self, key):
        self.discarded = key


def test_patient_cleanup_cancels_work_discards_pending_and_keeps_only_identity():
    task, job, store = Task(), Job(), Store()
    state = {
        "patient": "new",
        "auth_token": "login",
        "analysis_task": task,
        "ct_job": job,
        "imaging_store": store,
        "imaging_proposal": ("proposal", {"manifest": {"patient_id": "old"}}),
        "safety_notes": "old private notes",
        "review_notes": "old report",
        "symptoms": "old symptoms",
        "proposal": "old import",
        "pending_ct_slice_old": 9,
        "workspace": "Clinical report",
    }
    clear_patient(state)
    assert task.cancelled and job.cancelled and store.discarded == "proposal"
    assert state == {
        "patient": "new",
        "auth_token": "login",
        "workspace": "Patient overview",
        "focus_target": "choose-patient",
    }


def test_scope_guard_rejects_mismatched_report_before_rendering():
    class Client:
        closed = False

        def close(self):
            self.closed = True

    class Workflow:
        inference = Client()

        def state(self, case):
            return {"record": {"patient_id": "old"}}

    w = Workflow()
    state = {
        "patient": "new",
        "auth_token": "login",
        "workflow": w,
        "case_id": "old-case",
    }
    assert not ensure_patient(state, "new")
    assert "workflow" not in state and w.inference.closed
    assert ensure_patient(state, "new")


@pytest.mark.parametrize(
    "target",
    [
        "safety-check",
        "ct-review",
        "clinical-report",
        "source-records",
        "choose-patient",
        "patient-overview",
    ],
)
def test_navigation_only_selects_view_and_anchor_without_running_or_approving(target):
    state = {}
    go_to(target, state=state)
    assert state == {"workspace": destination(target), "focus_target": target}


@pytest.mark.parametrize(
    "target", ["<script>bad()</script>", "https://example.invalid", "other-patient"]
)
def test_untrusted_navigation_targets_are_rejected(target):
    with pytest.raises(ValueError):
        go_to(target, state={})


def test_scope_guard_clears_a_different_patients_pending_import():
    state = {
        "patient": "new",
        "auth_token": "login",
        "proposal": ("p", {"record": {"patient_id": "old"}}),
    }
    assert not ensure_patient(state, "new")
    assert "proposal" not in state


def test_cleanup_closes_a_completed_but_uncollected_client():
    class Client:
        closed = False

        def close(self):
            self.closed = True

    class Workflow:
        inference = Client()

    workflow = Workflow()

    class Completed(Task):
        def snapshot(self):
            return {"state": "complete"}

        def result(self):
            return workflow, "case"

    clear_patient({"analysis_task": Completed()})
    assert workflow.inference.closed

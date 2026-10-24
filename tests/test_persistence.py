"""Restart-safe pending reviews: durable receipt key and SQLite checkpoints."""

import pytest
from test_ui import login, open_safety, ui, wait_analysis  # noqa: F401
from test_workflow import review_for

from medical_assistant.auth import LocalAuth
from medical_assistant.persistence import resolve_receipt_key
from medical_assistant.workflow import MedicalHistoryOrchestrator

KEY = "ab" * 32


def restart(path, inference):
    """A fresh process: new auth (sessions lost) and a new orchestrator."""
    auth = LocalAuth(path)
    return auth, auth.login("dr.example", "synthetic-test-password"), MedicalHistoryOrchestrator(inference, auth=auth)


def pending(record, inference, path):
    auth = LocalAuth(path)
    auth.create_clinician("dr.example", "synthetic-test-password")
    token = auth.login("dr.example", "synthetic-test-password")
    flow = MedicalHistoryOrchestrator(inference, auth=auth)
    case, events = flow.start(record, "fictional_patient.json")
    list(events)
    flow.acknowledge_safety(case, review_for(flow.state(case), safety=True), token)
    return case


def test_receipt_key_sources_and_validation(monkeypatch):
    assert resolve_receipt_key()[1] == "ephemeral"
    monkeypatch.setenv("LOVISA_RECEIPT_KEY", KEY)
    assert resolve_receipt_key() == (bytes.fromhex(KEY), "env")
    for bad in ("ab" * 8, "not-hex"):
        monkeypatch.setenv("LOVISA_RECEIPT_KEY", bad)
        with pytest.raises(ValueError):
            resolve_receipt_key()


def test_durable_key_resumes_and_approves_a_pending_review_after_restart(
    record, inference, tmp_path, monkeypatch
):
    monkeypatch.setenv("LOVISA_RECEIPT_KEY", KEY)
    path = tmp_path / "durable.sqlite3"
    case = pending(record, inference, path)
    auth, token, flow = restart(path, inference)
    assert auth.durable_receipts
    assert [c["case_id"] for c in flow.resumable_cases(record.patient_id)] == [case]
    assert flow.resumable_cases("another-patient") == []
    state = flow.state(case)
    assert state["status"] == "awaiting_clinician_review"
    flow.review(case, review_for(state), token)
    assert flow.export(case)["reviewed"] is True
    assert flow.resumable_cases(record.patient_id) == []


def test_changed_key_cannot_approve_persisted_review(
    record, inference, tmp_path, monkeypatch
):
    monkeypatch.setenv("LOVISA_RECEIPT_KEY", KEY)
    path = tmp_path / "rotated.sqlite3"
    case = pending(record, inference, path)
    monkeypatch.setenv("LOVISA_RECEIPT_KEY", "cd" * 32)
    _, token, flow = restart(path, inference)
    with pytest.raises((PermissionError, ValueError)):
        flow.review(case, review_for(flow.state(case)), token)
    assert not flow.state(case).get("reviewed")
    assert flow.state(case)["status"] == "awaiting_clinician_review"
    monkeypatch.setenv("LOVISA_RECEIPT_KEY", KEY)
    _, restored_token, restored = restart(path, inference)
    restored.review(case, review_for(restored.state(case)), restored_token)
    assert restored.export(case)["reviewed"] is True


def test_ephemeral_key_keeps_workflows_in_memory(record, inference, tmp_path):
    path = tmp_path / "memory.sqlite3"
    case = pending(record, inference, path)
    auth, _, flow = restart(path, inference)
    assert not auth.durable_receipts
    assert flow.resumable_cases(record.patient_id) == []
    assert not flow.state(case)
    assert not (tmp_path / "workflow_checkpoints.sqlite3").exists()


@pytest.fixture
def durable(monkeypatch):
    monkeypatch.setenv("LOVISA_RECEIPT_KEY", KEY)


def test_ui_offers_saved_review_after_session_loss(durable, ui):  # noqa: F811
    app, _, auth, _ = ui
    assert auth.durable_receipts
    login(app)
    open_safety(app)
    assert not app.get("button") or not any(
        b.key == "resume_saved" for b in app.button
    )
    app.radio(key="safety_action").set_value(
        "Allow draft generation after my safety assessment"
    )
    wait_analysis(app.button(key="submit_safety").click().run())
    wait_analysis(app.button(key="generate").click().run())
    case = app.session_state.case_id
    for key in ("workflow", "case_id"):  # a browser session lost on restart
        del app.session_state[key]
    open_safety(app.run())
    app.button(key="resume_saved").click().run()
    assert not app.exception and app.session_state.case_id == case
    state = app.session_state.workflow.state(case)
    assert state["status"] == "awaiting_clinician_review" and not state["reviewed"]

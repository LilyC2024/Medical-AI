"""Adversarial regressions for the reviewed cross-branch integration."""
import json

import pytest
from langgraph.errors import GraphInterrupt
from langgraph.types import Interrupt
from test_workflow import pending_draft, review_for

from medical_assistant.audit import audit_events
from medical_assistant.auth import LocalAuth
from medical_assistant.database import connect
from medical_assistant.persistence import workflow_checkpointer
from medical_assistant.tracing import traced
from medical_assistant.workflow import MedicalHistoryOrchestrator


def test_database_receipts_and_checkpoints_are_isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("LOVISA_RECEIPT_KEY", "ab" * 32)
    a, b = LocalAuth(tmp_path / "a.sqlite3"), LocalAuth(tmp_path / "b.sqlite3")
    for auth in (a, b):
        auth.create_clinician("dr.example", "synthetic-test-password")
    token = a.login("dr.example", "synthetic-test-password")
    receipt = a.receipt(token, "same-action", "a" * 64)
    with pytest.raises(PermissionError):
        b.verify_receipt(receipt, "same-action", "a" * 64)
    assert workflow_checkpointer(a.path, True) is not workflow_checkpointer(b.path, True)


def test_saved_case_cannot_be_read_from_another_database(record, inference, tmp_path, monkeypatch):
    monkeypatch.setenv("LOVISA_RECEIPT_KEY", "ab" * 32)
    a, b = LocalAuth(tmp_path / "a.sqlite3"), LocalAuth(tmp_path / "b.sqlite3")
    flow = MedicalHistoryOrchestrator(inference, auth=a)
    case, events = flow.start(record, "fictional_patient.json")
    list(events)
    other = MedicalHistoryOrchestrator(inference, auth=b)
    assert not other.state(case)
    assert other.resumable_cases(record.patient_id) == []
    # Even an explicitly misconfigured shared checkpointer fails the identity check.
    other = MedicalHistoryOrchestrator(inference, auth=b, checkpointer=flow.graph.checkpointer)
    with pytest.raises(PermissionError, match="different database"):
        other.state(case)


@pytest.mark.parametrize("kind", ["exception", "interrupt"])
def test_trace_errors_never_serialize_exception_or_interrupt_text(tmp_path, monkeypatch, kind):
    trace = tmp_path / (kind + ".jsonl")
    monkeypatch.setenv("LOVISA_TRACE_FILE", str(trace))
    secret = "PRIVATE-RECORD-TEXT-DO-NOT-LOG"

    def bad_node(state):
        if kind == "interrupt":
            raise GraphInterrupt((Interrupt(value={"draft": secret}),))
        raise ValueError(secret)

    with pytest.raises((ValueError, GraphInterrupt)):
        traced("safe_step", bad_node)({"case_id": "synthetic-case"})
    text = trace.read_text()
    assert secret not in text
    span = json.loads(text)
    assert span["events"] == []
    assert "description" not in span["status"]
    assert span["resource"]["attributes"] == {"service.name": "lovisa"}


def test_audit_detects_modified_displayed_decision(record, inference, auth_session):
    flow, case, token = pending_draft(record, inference, auth_session)
    flow.review(case, review_for(flow.state(case)), token)
    auth = auth_session[0]
    with connect(auth.path) as db:
        row = db.execute("SELECT id,payload FROM audit WHERE action=?", ("clinical-review:" + case,)).fetchone()
        body = json.loads(row[1])
        body["decision"]["approved"] = False
        db.execute("UPDATE audit SET payload=? WHERE id=?", (json.dumps(body), row[0]))
    event = next(e for e in audit_events(auth.path, record.patient_id, auth) if e["kind"] == "clinical-review")
    assert event["receipt"] == "mismatch with recorded decision"

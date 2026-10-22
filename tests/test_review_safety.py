"""Independent adversarial review checks; scripted inference, never a live model."""
import json
from datetime import date

import pytest
from langgraph.types import Command

from medical_assistant.database import attach_original
from medical_assistant.models import PatientRecord, Review
from medical_assistant.report import digest
from medical_assistant.safety import SafetyAgent
from medical_assistant.storage import save_report
from medical_assistant.workflow import MedicalHistoryOrchestrator


def review_for(state, *, safety=False, approved=True):
    return Review(approved=approved, reviewer="dr.example", clinician_attestation=True,
        draft_sha256=state["safety_decision"]["decision_sha256"] if safety else digest(state["draft"]),
        notes="Independent synthetic review; original sources inspected.")


def warning_record(record, warning="present", *, dated=None):
    data = record.model_dump(mode="json", exclude={"sources"})
    entry = data["entries"][0]
    entry["warning_screen"] = warning
    entry["date"] = dated
    raw = json.dumps(data)
    return attach_original(PatientRecord.model_validate_json(raw), "warning-fixture.json", raw)


def test_urgent_hold_cannot_be_approved_by_authenticated_clinician(record, inference, auth_session):
    auth, token = auth_session
    workflow = MedicalHistoryOrchestrator(inference, auth=auth)
    case, events = workflow.start(warning_record(record), "warning-fixture.json")
    list(events)
    state = workflow.state(case)
    assert state["safety_decision"]["state"] == "urgent"
    with pytest.raises(ValueError, match="Urgent"):
        workflow.acknowledge_safety(case, review_for(state, safety=True), token)
    assert inference.calls == []
    assert "draft" not in workflow.state(case)
    stopped = workflow.acknowledge_safety(case, review_for(state, safety=True, approved=False), token)
    assert stopped["status"] == "stopped_for_human_review"
    assert inference.calls == []


def test_raw_graph_resume_requires_authentic_signed_receipt(record, inference, auth_session):
    auth, _ = auth_session
    workflow = MedicalHistoryOrchestrator(inference, auth=auth)
    case, events = workflow.start(record, "fixture.json")
    list(events)
    review = review_for(workflow.state(case), safety=True)
    forged = {"review": review.model_dump(), "receipt": {
        "actor": review.reviewer, "action": "safety-review:" + case,
        "content_sha256": digest(review.model_dump_json()), "signature": "f" * 64}}
    with pytest.raises(PermissionError, match="Invalid approval receipt"):
        workflow.graph.invoke(Command(resume=forged), workflow.config(case))
    assert inference.calls == []
    assert "draft" not in workflow.state(case)


def test_safety_missing_date_does_not_become_current_absence(record):
    decision = SafetyAgent().evaluate(warning_record(record, "absent"), as_of=date(2026, 10, 22))
    assert decision["state"] == "uncertain"
    assert "Current warning-sign screening" in " ".join(decision["assessment"]["missing_information"])


def test_save_rejects_fabricated_approval_receipt(tmp_path):
    report = "# Fabricated final report\nNo clinician ever reviewed this."
    review = Review(approved=True, reviewer="dr.example", clinician_attestation=True,
        draft_sha256=digest(report), notes="Fabricated, not authenticated.")
    with pytest.raises((PermissionError, ValueError)):
        save_report({"status": "complete", "reviewed": True, "final_report": report,
            "review": review.model_dump(), "approval_receipt": {"signature": "forged"}}, tmp_path)
    assert list(tmp_path.iterdir()) == []

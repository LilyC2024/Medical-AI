import json
import sqlite3

import pytest
from pydantic import ValidationError

from medical_assistant.models import Assessment, PatientRecord, Review
from medical_assistant.report import digest
from medical_assistant.storage import load_record, save_report
from medical_assistant.workflow import MedicalHistoryOrchestrator


def review_for(state, approved=True, *, safety=False):
    return Review(
        approved=approved,
        reviewer="dr.example",
        clinician_attestation=True,
        draft_sha256=state["safety_decision"]["decision_sha256"]
        if safety
        else digest(state["draft"]),
        notes="Checked sources, uncertainty and limitations for this synthetic case.",
    )


def pending_draft(record, inference, auth_session):
    auth, token = auth_session
    orchestrator = MedicalHistoryOrchestrator(inference, auth=auth)
    case_id, events = orchestrator.start(record, "fictional_patient.json")
    list(events)
    orchestrator.acknowledge_safety(
        case_id, review_for(orchestrator.state(case_id), safety=True), token
    )
    return orchestrator, case_id, token


def test_safety_first_stream_cannot_silently_continue(record, inference, auth_session):
    auth, token = auth_session
    orchestrator = MedicalHistoryOrchestrator(inference, auth=auth)
    case_id, events = orchestrator.start(record, "fictional_patient.json")
    assert list(next(events)) == ["safety"]
    assert inference.calls == []
    assert any("__interrupt__" in event for event in events)
    state = orchestrator.state(case_id)
    assert state["status"] == "awaiting_safety_review"
    assert state["reviewed"] is False
    assert "draft" not in state
    with pytest.raises(ValueError, match="clinician approval"):
        orchestrator.export(case_id)
    with pytest.raises(PermissionError):
        orchestrator.acknowledge_safety(case_id, review_for(state, safety=True))
    orchestrator.acknowledge_safety(case_id, review_for(state, safety=True), token)
    assert [role for role, _ in inference.calls] == ["reasoning"]
    state = orchestrator.state(case_id)
    assert state["status"] == "awaiting_clinician_review" and state["reviewed"] is False
    assert state["final_safety_decision"]["state"] == "uncertain"


def test_authenticated_approval_required_before_reviewed_and_audited(
    record, inference, auth_session, tmp_path
):
    orchestrator, case_id, token = pending_draft(record, inference, auth_session)
    state = orchestrator.state(case_id)
    with pytest.raises(PermissionError):
        orchestrator.review(case_id, review_for(state))
    assert not orchestrator.state(case_id)["reviewed"]
    orchestrator.review(case_id, review_for(state), token)
    payload = orchestrator.export(case_id)
    assert payload["status"] == "complete" and payload["reviewed"] is True
    assert payload["final_report"].count("# ") == 1
    assert any(
        e["filename"] == "fictional_patient.json"
        and e["date"] == "2025-03-10"
        and e["entry_id"] == "report-2025-03-10"
        for e in payload["report_evidence"]["record_entries"]
    )
    assert payload["review"]["reviewer"] == "dr.example" and payload["reviewed_at"]
    assert len(payload["review_history"]) == 1
    assert save_report(
        payload, tmp_path, auth=orchestrator.auth, safety=orchestrator.safety
    ).exists()
    assert len(inference.calls) == 1
    with sqlite3.connect(auth_session[0].path) as db:
        rows = db.execute(
            "SELECT action,actor,payload FROM audit ORDER BY id"
        ).fetchall()
    assert [row[1] for row in rows] == ["dr.example", "dr.example"]
    assert json.loads(rows[-1][2])["decision"]["approved"] is True
    assert "clinical-review:" in rows[-1][0]
    with pytest.raises(ValueError):
        orchestrator.review(case_id, review_for(state), token)


def test_rejection_edits_stale_approval_and_fresh_approval(
    record, inference, auth_session
):
    orchestrator, case_id, token = pending_draft(record, inference, auth_session)
    original = orchestrator.state(case_id)
    rejected = orchestrator.review(case_id, review_for(original, approved=False), token)
    assert (
        rejected["status"] == "awaiting_clinician_review" and not rejected["reviewed"]
    )
    with pytest.raises(ValueError):
        orchestrator.export(case_id)
    edited = (
        original["draft"]
        + "\nClinician correction: current medication use remains unverified.\n"
    )
    with pytest.raises(ValueError, match="source-bound"):
        orchestrator.revise(case_id, edited, token)
    stale_review = review_for(original)
    stale_review.draft_sha256 = "0" * 64
    with pytest.raises(ValueError, match="Stale"):
        orchestrator.review(case_id, stale_review, token)
    orchestrator.review(case_id, review_for(orchestrator.state(case_id)), token)
    payload = orchestrator.export(case_id)
    assert payload["final_report"] == original["draft"]
    assert payload["generated_draft"] == original["draft"]
    assert len(payload["review_history"]) == 2


@pytest.mark.parametrize(
    "changes",
    [{"reviewer": " "}, {"clinician_attestation": False}, {"approved": "yes"}],
)
def test_review_requires_identity_attestation_and_bool(changes):
    payload = dict(
        approved=True,
        reviewer="dr.example",
        clinician_attestation=True,
        draft_sha256="a" * 64,
        notes="Verified synthetic record",
    )
    payload.update(changes)
    with pytest.raises(ValidationError):
        Review(**payload)


def test_reject_unknown_sources_and_misattribution(record):
    for claim in [
        {"kind": "documented", "text": "Invented result", "evidence_ids": ["unknown"]},
        {
            "kind": "documented",
            "text": record.entries[-1].text,
            "evidence_ids": [record.entries[-1].id],
        },
    ]:
        with pytest.raises(ValueError):
            Assessment(findings=[claim]).validate_sources(record)


def test_record_validation(record, tmp_path):
    data = record.model_dump(mode="json")
    data["fictional"] = False
    with pytest.raises(ValidationError):
        PatientRecord.model_validate(data)
    data["fictional"] = True
    data["entries"].append(data["entries"][0])
    with pytest.raises(ValueError, match="unique"):
        PatientRecord.model_validate(data)
    large = tmp_path / "large.json"
    large.write_text(" " * 100_001)
    with pytest.raises(ValueError, match="100 KB"):
        load_record(large)


def test_no_saving_unapproved_report(tmp_path):
    with pytest.raises(ValueError):
        save_report({"status": "awaiting_clinician_review"}, tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_saving_detects_tampered_reviewed_report(
    record, inference, auth_session, tmp_path
):
    orchestrator, case_id, token = pending_draft(record, inference, auth_session)
    orchestrator.review(case_id, review_for(orchestrator.state(case_id)), token)
    payload = orchestrator.export(case_id)
    payload["final_report"] += "Unreviewed addition."
    with pytest.raises(ValueError, match="does not match"):
        save_report(
            payload, tmp_path, auth=orchestrator.auth, safety=orchestrator.safety
        )


def test_model_failure_stops_before_draft_and_final(record, inference, auth_session):
    def fail(*args, **kwargs):
        raise ValueError("Malformed local output")

    inference.assess = fail
    auth, token = auth_session
    orchestrator = MedicalHistoryOrchestrator(inference, auth=auth)
    case_id, events = orchestrator.start(record, "fictional_patient.json")
    list(events)
    with pytest.raises(ValueError, match="Malformed"):
        orchestrator.acknowledge_safety(
            case_id, review_for(orchestrator.state(case_id), safety=True), token
        )
    assert "draft" not in orchestrator.state(case_id)
    with pytest.raises(ValueError):
        orchestrator.export(case_id)


def test_cases_and_authenticated_receipts_are_isolated(record, inference, auth_session):
    orchestrator, first, token = pending_draft(record, inference, auth_session)
    second, events = orchestrator.start(record, "two.json")
    list(events)
    orchestrator.review(first, review_for(orchestrator.state(first)), token)
    assert orchestrator.state(second)["status"] == "awaiting_safety_review"
    receipt = orchestrator.state(first)["approval_receipt"]
    with pytest.raises(PermissionError):
        auth_session[0].verify_receipt(
            receipt, "clinical-review:" + second, receipt["content_sha256"]
        )

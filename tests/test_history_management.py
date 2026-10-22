import json

import pytest

from medical_assistant.database import get_history, initialize, seed
from medical_assistant.history import MedicalHistoryAgent, MedicationAgent
from medical_assistant.history_import import HistoryManagement
from medical_assistant.models import Review
from medical_assistant.storage import PATIENT_DIR
from conftest import create_auth


def test_medication_agent_extracts_documented_dose_change_and_source_dates(tmp_path):
    path = tmp_path / "history.sqlite3"
    seed(path)
    record = get_history("synthetic-checklist", path)
    result = MedicationAgent().run(record)
    assert [(item.name, item.dose) for item in result.medications] == [("amlodipine", "5 mg"), ("amlodipine", "10 mg")]
    assert len(result.dose_changes) == 1
    change = result.dose_changes[0]
    assert (change.previous_dose, change.documented_dose) == ("5 mg", "10 mg")
    assert change.evidence_ids == ["dose-1", "dose-2"]
    assert change.date.isoformat() == "2025-02-10"


def test_history_agent_never_invents_missing_dates(tmp_path):
    path = tmp_path / "history.sqlite3"
    seed(path)
    result = MedicalHistoryAgent().run(get_history("synthetic-checklist", path))
    assert result.missing_dates == ["symptom-undated"]
    assert "symptom-undated" not in result.known_dates
    assert len(result.known_dates) == 4
    assert "Date unavailable" in result.missing_information[0]


def test_possible_duplicate_encounters_are_flagged_without_losing_originals():
    from medical_assistant.models import PatientRecord
    data = json.loads((PATIENT_DIR / "checklist_patient.json").read_text())
    data["entries"].append({**data["entries"][0], "id": "possible-duplicate-visit"})
    record = PatientRecord.model_validate(data)
    result = MedicalHistoryAgent().run(record)
    assert len(result.findings) == len(record.entries)
    assert any("Possible duplicate" in item and "possible-duplicate-visit" in item for item in result.missing_information)


def test_import_is_pending_until_approved_and_preserves_original_source(tmp_path):
    path = tmp_path / "history.sqlite3"
    initialize(path)
    auth, token = create_auth(path)
    workflow = HistoryManagement(path, auth=auth)
    raw = (PATIENT_DIR / "checklist_patient.json").read_text()
    proposal_id, proposal = workflow.prepare(raw, "checklist_patient.json")
    with pytest.raises(LookupError):
        get_history("synthetic-checklist", path)
    review = Review(approved=False, reviewer="dr.example", clinician_attestation=True,
                    draft_sha256=proposal["sha256"], notes="Reviewed synthetic source")
    with pytest.raises(ValueError, match="approval"):
        workflow.approve(proposal_id, review, token)
    review.approved = True
    saved = workflow.approve(proposal_id, review, token)
    assert saved.sources[0].content == raw
    assert all(entry.verification_status == "verified" for entry in saved.entries)
    retry_id, retry = workflow.prepare(raw, "checklist_patient.json")
    assert len(retry["duplicate_ids"]) == 5
    review.draft_sha256 = retry["sha256"]
    assert len(workflow.approve(retry_id, review, token).entries) == 5


def test_import_rejects_conflicting_dates_and_unsupported_assertions(tmp_path):
    path = tmp_path / "history.sqlite3"
    seed(path)
    workflow = HistoryManagement(path)
    data = json.loads((PATIENT_DIR / "checklist_patient.json").read_text())
    data["entries"][0]["date"] = "2024-01-01"
    with pytest.raises(ValueError, match="Conflicting"):
        workflow.prepare(json.dumps(data), "conflict.json")
    stored = get_history("synthetic-checklist", path).model_dump(mode="json")
    stored["entries"][0]["medication"]["dose"] = "999 mg"
    with pytest.raises(ValueError, match="unsupported"):
        workflow.prepare(json.dumps(stored), "unsupported.json")

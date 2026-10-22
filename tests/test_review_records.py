"""Adversarial persistence and provenance regression checks from publication review."""
import json
import sqlite3

import pytest

from medical_assistant.database import attach_original, get_history, initialize, write_synthetic
from medical_assistant.history import MedicationAgent
from medical_assistant.models import Assessment, PatientRecord
from medical_assistant.storage import PATIENT_DIR


def checklist_record():
    path = PATIENT_DIR / "checklist_patient.json"
    return attach_original(PatientRecord.model_validate_json(path.read_text()), path.name, path.read_text())


def test_medication_values_must_match_the_cited_order():
    record = checklist_record()
    with pytest.raises(ValueError, match="[Mm]edication|[Uu]nsupported"):
        Assessment(medications=[{
            "name": "invented medicine", "dose": "999 mg", "frequency": "every minute",
            "source_type": "documented", "evidence_ids": ["dose-1"],
            "reconciliation_question": "Verify historical use.",
        }]).validate_sources(record)


def test_dose_change_values_must_match_cited_orders():
    record = checklist_record()
    with pytest.raises(ValueError, match="[Dd]ose|[Uu]nsupported"):
        Assessment(dose_changes=[{
            "name": "amlodipine", "previous_dose": "500 mg", "documented_dose": "1000 mg",
            "date": "2099-01-01", "evidence_ids": ["dose-1", "dose-2"],
        }]).validate_sources(record)


def test_append_cannot_leave_history_unreadable_after_crossing_bundle_limit(tmp_path):
    path = tmp_path / "records.sqlite3"
    initialize(path)
    data = json.loads((PATIENT_DIR / "checklist_patient.json").read_text())
    template = data["entries"][0]
    data["entries"] = [{**template, "id": f"fact-{index}"} for index in range(100)]
    raw = json.dumps(data)
    write_synthetic(attach_original(PatientRecord.model_validate(data), "first.json", raw), path, actor="fixture", action="test")
    data["entries"] = [{**template, "id": "fact-100"}]
    raw = json.dumps(data)
    try:
        write_synthetic(attach_original(PatientRecord.model_validate(data), "second.json", raw), path, actor="fixture", action="test")
    except ValueError:
        # Enforcing a bounded patient history is valid if the append rolls back.
        pass
    record = get_history(data["patient_id"], path)
    assert len(record.entries) in (100, 101)
    assert len({entry.id for entry in record.entries}) == len(record.entries)
    if len(record.entries) == 100:
        with sqlite3.connect(path) as connection:
            assert connection.execute("SELECT COUNT(*) FROM sources").fetchone()[0] == 1
            assert connection.execute("SELECT COUNT(*) FROM audit").fetchone()[0] == 1


def test_deterministic_medication_extraction_preserves_dose_sources():
    record = checklist_record()
    result = MedicationAgent().run(record)
    change = result.dose_changes[0]
    assert change.previous_dose == "5 mg"
    assert change.documented_dose == "10 mg"
    assert change.evidence_ids == ["dose-1", "dose-2"]


def test_original_source_metadata_is_immutable_and_rolls_back(tmp_path):
    from medical_assistant.database import seed
    path = tmp_path / "records.sqlite3"
    seed(path)
    original = get_history("synthetic-checklist", path)
    data = original.model_dump(mode="json")
    data["sources"][0]["filename"] = "forged-citation.json"
    with pytest.raises(ValueError, match="immutable"):
        write_synthetic(PatientRecord.model_validate(data), path, actor="fixture", action="test")
    assert get_history(original.patient_id, path) == original


@pytest.mark.parametrize("content", ["[]", "{}", '{"entries": null}'])
def test_malformed_original_source_fails_with_validation_error(content):
    from medical_assistant.grounding import validate_record_grounding
    from medical_assistant.report import digest
    data = checklist_record().model_dump(mode="json")
    data["sources"][0]["content"] = content
    data["sources"][0]["sha256"] = digest(content)
    with pytest.raises(ValueError, match="JSON record"):
        validate_record_grounding(PatientRecord.model_validate(data))


def test_original_source_patient_display_name_must_match():
    from medical_assistant.grounding import validate_record_grounding
    data = checklist_record().model_dump(mode="json")
    data["display_name"] = "Another synthetic person"
    with pytest.raises(ValueError, match="display name"):
        validate_record_grounding(PatientRecord.model_validate(data))


def test_history_import_context_limit_rejected_before_approval(tmp_path):
    from medical_assistant.history_import import HistoryManagement
    data = json.loads((PATIENT_DIR / "checklist_patient.json").read_text())
    template = data["entries"][0]
    data["entries"] = [{**template, "id": f"fact-{index}", "text": "x" * 7000} for index in range(4)]
    workflow = HistoryManagement(tmp_path / "records.sqlite3")
    with pytest.raises(ValueError, match="prototype limit"):
        workflow.prepare(json.dumps(data), "too-large.json")
    assert not workflow.pending

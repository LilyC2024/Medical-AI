import json
import sqlite3

import pytest
from pydantic import ValidationError

from medical_assistant.database import attach_original, get_history, initialize, list_patients, seed, write_synthetic
from medical_assistant.models import PatientRecord
from medical_assistant.storage import PATIENT_DIR, load_record


def test_sqlite_retrieval_has_exact_encounters_and_no_duplicates(tmp_path):
    path = tmp_path / "history.sqlite3"
    seed(path)
    seed(path)
    record = get_history("synthetic-checklist", path)
    assert [e.id for e in record.entries] == ["dose-1", "visit-1", "dose-2", "visit-2", "symptom-undated"]
    assert len(record.entries) == 5
    assert [e.id for e in record.entries if e.kind == "encounter"] == ["visit-1", "visit-2"]
    assert len(list_patients(path)) == 7
    assert record.entries[-1].date is None
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT COUNT(*) FROM audit").fetchone()[0] == 7
        assert db.execute("SELECT COUNT(*) FROM sources WHERE patient_id='synthetic-checklist'").fetchone()[0] == 1
    assert record.sources[0].filename == "checklist_patient.json"


def test_missing_patient_and_invalid_data_fail_closed(tmp_path):
    path = tmp_path / "history.sqlite3"
    initialize(path)
    with pytest.raises(LookupError):
        get_history("missing", path)
    data = json.loads((PATIENT_DIR / "checklist_patient.json").read_text())
    data["entries"][0]["date"] = "2025-02-30"
    with pytest.raises(ValidationError):
        PatientRecord.model_validate(data)
    data["entries"][0]["date"] = None
    data["fictional"] = False
    with pytest.raises(ValidationError):
        PatientRecord.model_validate(data)


def test_conflicting_dates_rollback_whole_transaction(tmp_path):
    path = tmp_path / "history.sqlite3"
    seed(path)
    original = get_history("synthetic-checklist", path)
    changed = original.model_dump(mode="json")
    changed["entries"][0]["date"] = "2024-01-01"
    with pytest.raises(ValueError, match="unsupported"):
        write_synthetic(PatientRecord.model_validate(changed), path, actor="test", action="test")
    assert get_history("synthetic-checklist", path) == original

    # A new, internally consistent source still cannot overwrite a stored ID.
    data = json.loads((PATIENT_DIR / "checklist_patient.json").read_text())
    data["entries"][0]["date"] = "2024-01-01"
    raw = json.dumps(data)
    changed_record = attach_original(PatientRecord.model_validate(data), "conflict.json", raw)
    with pytest.raises(ValueError, match="Conflicting encounter"):
        write_synthetic(changed_record, path, actor="test", action="test")
    assert get_history("synthetic-checklist", path) == original


def test_original_source_hash_and_references_are_validated(record, tmp_path):
    source_path = PATIENT_DIR / "fictional_patient.json"
    source_record = attach_original(record, source_path.name, source_path.read_text())
    changed = source_record.model_dump(mode="json")
    changed["sources"][0]["content"] += "tampered"
    with pytest.raises(ValueError, match="digest"):
        PatientRecord.model_validate(changed)
    changed = source_record.model_dump(mode="json")
    changed["entries"][0]["source_id"] = "invented-source"
    with pytest.raises(ValueError, match="original source"):
        PatientRecord.model_validate(changed)

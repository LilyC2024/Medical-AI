"""Five authored artificial examples, staged reasoning, concise evidence and scoped demo credentials."""

from datetime import date, datetime
from zoneinfo import ZoneInfo
import pytest
from conftest import FakeInference, create_auth
from medical_assistant.database import seed, get_history
from medical_assistant.history import MedicalHistoryAgent, MedicationAgent
from medical_assistant.models import Review
from medical_assistant.safety import SafetyAgent
from medical_assistant.workflow import MedicalHistoryOrchestrator
from medical_assistant.report import inline_text


def test_demo_password_exception_is_explicit_and_only_for_demo(tmp_path):
    auth, _ = create_auth(tmp_path / "accounts.sqlite3")
    with pytest.raises(ValueError):
        auth.create_clinician("demo", "toy")
    with pytest.raises(ValueError):
        auth.create_clinician("other", "toy", local_demo=True)
    auth.create_clinician("demo", "toy", local_demo=True)
    assert auth.require(auth.login("demo", "toy")) == "demo"
    with pytest.raises(PermissionError):
        auth.login("demo", "wrong")


@pytest.mark.parametrize("patient", [f"demo-0{i}" for i in range(1, 6)])
def test_complex_demos_keep_exact_sources_and_safe_staged_reports(tmp_path, patient):
    path = tmp_path / "demo.sqlite3"
    seed(path)
    seed(path)
    auth, token = create_auth(path)
    inference = FakeInference()
    record = get_history(patient, path)
    assert len(record.entries) >= 6 and len({e.id for e in record.entries}) == len(
        record.entries
    )
    history = MedicalHistoryAgent().run(record)
    assert history.missing_dates
    assert all(e.source_id == record.sources[0].id for e in record.entries)
    assert SafetyAgent().evaluate(record, as_of=date(2026, 10, 23))["state"] == (
        "urgent" if patient == "demo-04" else "uncertain"
    )
    flow = MedicalHistoryOrchestrator(inference, auth=auth)
    case, events = flow.start_patient(patient, path, safety_only=True)
    list(events)
    assert not inference.calls
    with pytest.raises((ValueError, PermissionError)):
        flow.continue_analysis(case, token)
    state = flow.state(case)
    review = Review(
        approved=patient != "demo-04",
        reviewer="dr.example",
        clinician_attestation=True,
        notes="Scripted assessment of fictional missing data only.",
        draft_sha256=state["safety_decision"]["decision_sha256"],
    )
    flow.acknowledge_safety(case, review, token, safety_only=True)
    assert not inference.calls
    if patient == "demo-04":
        assert flow.state(case)["status"] == "stopped_for_human_review"
        with pytest.raises(ValueError):
            flow.continue_analysis(case, token)
        return
    assert flow.ready_for_analysis(case, token)
    flow.continue_analysis(case, token)
    state = flow.state(case)
    assert len(inference.calls) == 1 and state["status"] == "awaiting_clinician_review"
    report = state["draft"]
    assert report.count("\n## ") == 7
    # Source text occurs once; hypotheses use the evidence key, not repeated quotations.
    for e in record.entries:
        assert report.count(inline_text(e.text)) == sum(
            other.text == e.text for other in record.entries
        )
        assert f"| {e.id}]" in report
    assert len(report.split()) < 1250
    with pytest.raises(ValueError):
        flow.export(case)
    if patient in ("demo-01", "demo-02", "demo-05"):
        assert MedicationAgent().run(record).dose_changes


def test_normal_checks_still_require_explicit_generate_and_signin(record, tmp_path):
    from medical_assistant.database import attach_original
    from medical_assistant.models import PatientRecord
    import json

    raw = json.dumps(
        {
            "fictional": True,
            "patient_id": "ready",
            "display_name": "Ready fictional",
            "entries": [
                {
                    "id": "today",
                    "date": datetime.now(ZoneInfo("Europe/Amsterdam"))
                    .date()
                    .isoformat(),
                    "source_type": "documented",
                    "kind": "encounter",
                    "text": "Fictional observation: blood pressure 120/80 mmHg and structured warning screening absent.",
                    "blood_pressure": {"systolic": 120, "diastolic": 80},
                    "warning_screen": "absent",
                }
            ],
        }
    )
    ready = attach_original(PatientRecord.model_validate_json(raw), "ready.json", raw)
    auth, token = create_auth(tmp_path / "ready.sqlite3")
    inference = FakeInference()
    f = MedicalHistoryOrchestrator(inference, auth=auth)
    case, events = f.start(ready, "ready.json", safety_only=True)
    list(events)
    assert not inference.calls and f.ready_for_analysis(case, token)
    with pytest.raises(PermissionError):
        f.continue_analysis(case, None)

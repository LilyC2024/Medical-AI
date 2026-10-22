import json
from datetime import date

import pytest

from medical_assistant.database import attach_original
from medical_assistant.models import PatientRecord
from medical_assistant.safety import POLICY_PATH, SafetyAgent
from medical_assistant.workflow import MedicalHistoryOrchestrator
from test_workflow import review_for


def screen_record(record, *, warning="absent", measured=True, day="2026-10-22"):
    data = record.model_dump(mode="json", exclude={"sources"})
    for entry in data["entries"]:
        entry["source_id"] = None
    data["entries"].append({"id": "current-screen", "date": day, "source_type": "documented", "kind": "encounter",
        "text": "Synthetic screening observation; see structured fields. No clinical safety classification is asserted.",
        "warning_screen": warning, "blood_pressure": {"systolic": 125, "diastolic": 80} if measured else None})
    raw = json.dumps(data)
    return attach_original(PatientRecord.model_validate(data), "screen.json", raw)


def test_policy_distinguishes_known_missing_stale_and_explicit_warning(record):
    agent = SafetyAgent()
    assert agent.evaluate(screen_record(record), as_of=date(2026,10,22))["state"] == "ordinary_eligible"
    assert agent.evaluate(screen_record(record, measured=False), as_of=date(2026,10,22))["state"] == "uncertain"
    assert agent.evaluate(screen_record(record, warning="unknown"), as_of=date(2026,10,22))["state"] == "uncertain"
    assert agent.evaluate(screen_record(record, day="2025-01-01"), as_of=date(2026,10,22))["state"] == "uncertain"
    assert agent.evaluate(screen_record(record, warning="present"), as_of=date(2026,10,22))["state"] == "urgent"


def test_missing_or_model_override_policy_fails_closed(record, inference, auth_session, tmp_path):
    path = tmp_path / "policy.json"
    with pytest.raises(OSError):
        SafetyAgent(path).evaluate(record)
    policy = json.loads(POLICY_PATH.read_text())
    policy["model_may_override"] = True
    path.write_text(json.dumps(policy))
    orchestrator = MedicalHistoryOrchestrator(inference, auth=auth_session[0], safety=SafetyAgent(path))
    case_id, events = orchestrator.start(record, "fixture.json")
    with pytest.raises(ValueError):
        list(events)
    assert not inference.calls
    assert not orchestrator.state(case_id)["reviewed"]


def test_policy_change_during_inference_prevents_report(record, inference, auth_session, tmp_path):
    path = tmp_path / "policy.json"
    path.write_text(POLICY_PATH.read_text())
    original = inference.assess
    def mutate_policy(*args, **kwargs):
        result = original(*args, **kwargs)
        policy = json.loads(path.read_text())
        policy["version"] = "changed-during-inference"
        path.write_text(json.dumps(policy))
        return result
    inference.assess = mutate_policy
    auth, token = auth_session
    orchestrator = MedicalHistoryOrchestrator(inference, auth=auth, safety=SafetyAgent(path))
    case_id, events = orchestrator.start(record, "fixture.json")
    list(events)
    with pytest.raises(ValueError, match="changed"):
        orchestrator.acknowledge_safety(case_id, review_for(orchestrator.state(case_id), safety=True), token)
    assert "draft" not in orchestrator.state(case_id)
    assert not orchestrator.state(case_id)["reviewed"]


def test_authentication_wrong_password_identity_and_expired_session(auth_session):
    import time
    auth, token = auth_session
    with pytest.raises(PermissionError):
        auth.login("dr.example", "wrong-password")
    with pytest.raises(PermissionError):
        auth.require("forged-session")
    auth.sessions[token] = ("dr.example", time.monotonic() - 1)
    with pytest.raises(PermissionError):
        auth.require(token)

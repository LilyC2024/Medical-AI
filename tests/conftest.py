import json

import pytest

from medical_assistant.models import Assessment
from medical_assistant.storage import PATIENT_DIR, load_record
from medical_assistant.database import attach_original
from medical_assistant.auth import LocalAuth
from medical_assistant.reasoning_constraints import MEDICATION_HYPOTHESIS, SLEEP_HYPOTHESIS, UNCERTAINTY, CONSIDERATIONS


@pytest.fixture
def record():
    path = PATIENT_DIR / "fictional_patient.json"
    return attach_original(load_record(path), path.name, path.read_text())


def create_auth(path):
    auth = LocalAuth(path)
    auth.create_clinician("dr.example", "synthetic-test-password")
    return auth, auth.login("dr.example", "synthetic-test-password")


@pytest.fixture
def auth_session(tmp_path):
    return create_auth(tmp_path / "authenticated.sqlite3")


class FakeInference:
    """Scripted test responses only; never used by the application."""
    model = "test-local-model"

    def __init__(self):
        self.calls = []

    def close(self):
        pass

    def assess(self, system, user, *, schema=None):
        payload = json.loads(user)
        if "Safety Specialist:" in system:
            role = "safety"
            result = {"safety_flags": [{"urgency": "unknown", "text": "Current emergency-symptom screening is not supplied.",
                      "evidence_ids": ["report-2025-03-10"], "escalation": "A clinician must establish current safety status."}]}
        elif "Medical History Specialist:" in system:
            role = "history"
            result = {"findings": [{"kind": "patient_reported", "text": "Intermittent tiredness and irregular sleep are reported.",
                                  "evidence_ids": ["report-2025-03-10"]}]}
        elif "Medication Specialist:" in system:
            role = "medications"
            result = {"medications": [{"name": "cetirizine", "dose": "10 mg", "frequency": "once daily (historical)",
                       "source_type": "documented", "evidence_ids": ["medication-2025-02-14"],
                       "reconciliation_question": "Which allergy tablet is currently taken, and at what dose and frequency?"}]}
        else:
            role = "reasoning"
            symptom = next(entry for entry in payload["record"]["entries"] if entry["source_type"] == "patient_reported")
            label = SLEEP_HYPOTHESIS if "sleep" in symptom["text"].casefold() else MEDICATION_HYPOTHESIS
            result = {"explanations": [{"possibility": label, "supporting": [
                {"kind": "patient_reported", "text": symptom["text"], "evidence_ids": [symptom["id"]]}],
                "conflicting": [], "uncertainty": UNCERTAINTY,
                "clinician_may_consider": [CONSIDERATIONS[0]]}]}
        self.calls.append((role, payload))
        return Assessment.model_validate(result)


@pytest.fixture
def inference():
    return FakeInference()


@pytest.fixture(autouse=True)
def ephemeral_receipt_key(monkeypatch):
    """Tests default to the in-memory key unless a test sets LOVISA_RECEIPT_KEY."""
    from medical_assistant import persistence

    monkeypatch.delenv("LOVISA_RECEIPT_KEY", raising=False)
    monkeypatch.setattr(persistence, "_keyring_value", lambda: None)

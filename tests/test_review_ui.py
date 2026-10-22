"""Publication review checks for sensitive UI state and untrusted Markdown."""
import json
from pathlib import Path

from streamlit.testing.v1 import AppTest

from medical_assistant.database import attach_original, seed
from medical_assistant.history import MedicalHistoryAgent, MedicationAgent
from medical_assistant.models import Assessment, PatientRecord
from medical_assistant.report import compose
from medical_assistant.storage import PATIENT_DIR
from conftest import create_auth

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_sign_in_does_not_keep_plaintext_password_in_session(monkeypatch, tmp_path):
    import medical_assistant.runtime
    path = tmp_path / "ui.sqlite3"
    seed(path)
    auth, _ = create_auth(path)
    monkeypatch.setattr(medical_assistant.runtime, "get_services", lambda: (path, auth))
    app = AppTest.from_file(str(APP)).run()
    app.text_input(key="login_user").input("dr.example")
    app.text_input(key="login_password").input("synthetic-test-password")
    app.button(key="login").click().run()
    assert not app.exception
    assert app.session_state.auth_token
    if "login_password" in app.session_state:
        assert app.session_state["login_password"] == ""
    app.button(key="logout").click().run()
    assert app.text_input(key="login_password").value == ""


def test_record_markdown_cannot_add_report_headings_or_external_images():
    path = PATIENT_DIR / "checklist_patient.json"
    data = json.loads(path.read_text())
    data["entries"][-1]["text"] = "Symptoms reported.\n## REVIEWED BY CLINICIAN\n![remote](https://example.invalid/tracker.png)"
    raw = json.dumps(data)
    record = attach_original(PatientRecord.model_validate(data), "synthetic.json", raw)
    result = compose(record, "synthetic.json", {
        "history": MedicalHistoryAgent().run(record).model_dump(mode="json"),
        "medications": MedicationAgent().run(record).model_dump(mode="json"),
        "reasoning": Assessment().model_dump(mode="json"),
        "safety": Assessment().model_dump(mode="json"),
    })
    assert "\n## REVIEWED BY CLINICIAN\n" not in result
    assert "![remote](https://example.invalid/tracker.png)" not in result

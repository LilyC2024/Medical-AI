import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from conftest import FakeInference, create_auth
from medical_assistant.database import get_history, seed

APP = Path(__file__).resolve().parents[1] / "app.py"


@pytest.fixture
def ui(monkeypatch, tmp_path):
    import medical_assistant.runtime
    import medical_assistant.ollama_client
    import medical_assistant.storage
    path = tmp_path / "history.sqlite3"
    seed(path)
    auth, _ = create_auth(path)
    inference = FakeInference()
    real_save = medical_assistant.storage.save_report
    monkeypatch.setattr(medical_assistant.runtime, "get_services", lambda: (path, auth))
    monkeypatch.setattr(medical_assistant.ollama_client, "OllamaClient", lambda model: inference)
    monkeypatch.setattr(medical_assistant.storage, "save_report", lambda payload, **kwargs: real_save(payload, tmp_path / "reports", **kwargs))
    return AppTest.from_file(str(APP)).run(), path, auth, inference


def login(app):
    app.text_input(key="login_user").input("dr.example")
    app.text_input(key="login_password").input("synthetic-test-password")
    return app.button(key="login").click().run()


def test_ui_loads_sqlite_and_blocks_unauthenticated_safety_continuation(ui):
    app, _, _, inference = ui
    assert not app.exception
    assert app.title[0].value == "LOVISA — Medical History & Clinical Reasoning Assistant"
    assert app.selectbox(key="patient").value == "fictional-001"
    assert not app.get("download_button")
    app.button(key="generate").click().run()
    assert not app.exception
    assert app.button(key="submit_safety").disabled
    assert inference.calls == []
    assert app.session_state.workflow.state(app.session_state.case_id)["status"] == "awaiting_safety_review"


def test_ui_safety_review_rejection_approval_and_export(ui, tmp_path):
    app, _, _, inference = ui
    login(app)
    app.button(key="generate").click().run()
    app.text_area(key="safety_notes").input("Synthetic test: assessed the missing-data limitations.")
    app.checkbox(key="safety_attest").check()
    app.radio(key="safety_action").set_value("Continue after clinician assessment of uncertainty")
    app.button(key="submit_safety").click().run(timeout=20)
    assert not app.exception
    assert len(inference.calls) == 1
    assert not app.get("download_button")
    app.button(key="submit_review").click().run()
    assert app.error  # Empty notes/no attestation cannot approve.
    app.text_area(key="review_notes").input("Verified synthetic source excerpts and unresolved uncertainty.")
    app.checkbox(key="attested").check()
    app.button(key="submit_review").click().run()
    assert not app.exception
    assert not app.get("download_button")
    app.radio(key="decision").set_value("Approve report")
    app.button(key="submit_review").click().run()
    assert not app.exception
    assert len(app.get("download_button")) == 2
    reports = list((tmp_path / "reports").glob("*.json"))
    assert len(reports) == 1
    assert json.loads(reports[0].read_text())["reviewed"] is True


def test_ui_observation_proposal_requires_approval_and_preserves_unknown_date(ui):
    app, path, _, _ = ui
    login(app)
    app.selectbox(key="patient").set_value("synthetic-checklist").run()
    before = len(get_history("synthetic-checklist", path).entries)
    app.text_area(key="symptoms").input("Synthetic observation: symptom timing remains unavailable.")
    app.button(key="prepare_symptom").click().run()
    assert not app.exception
    assert len(get_history("synthetic-checklist", path).entries) == before
    assert app.button(key="generate").disabled
    app.text_area(key="import_notes").input("Verified synthetic observation text; date and measurements were not supplied.")
    app.checkbox(key="import_attest").check()
    app.button(key="approve_import").click().run()
    assert not app.exception
    record = get_history("synthetic-checklist", path)
    assert len(record.entries) == before + 1
    observation = next(entry for entry in record.entries if entry.id.startswith("observation-"))
    assert observation.date is None and observation.blood_pressure is None
    assert observation.verification_status == "verified"


def test_ui_urgent_case_stops_without_calling_model(ui):
    app, _, _, inference = ui
    login(app)
    app.text_area(key="symptoms").input("Synthetic fixture explicitly reports a warning sign for workflow testing.")
    app.selectbox(key="warning_screen").set_value("present")
    app.button(key="prepare_symptom").click().run()
    app.text_area(key="import_notes").input("Verified explicit synthetic warning flag.")
    app.checkbox(key="import_attest").check()
    app.button(key="approve_import").click().run()
    app.button(key="generate").click().run()
    assert not app.exception
    assert app.radio(key="safety_action").disabled
    app.text_area(key="safety_notes").input("Stop automated analysis for human assessment of the synthetic flag.")
    app.checkbox(key="safety_attest").check()
    app.button(key="submit_safety").click().run()
    assert not app.exception
    assert inference.calls == []
    assert app.session_state.workflow.state(app.session_state.case_id)["status"] == "stopped_for_human_review"
    assert not app.get("download_button")

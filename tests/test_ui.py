import json
import time
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
    monkeypatch.setattr(
        medical_assistant.ollama_client, "OllamaClient", lambda model: inference
    )
    monkeypatch.setattr(
        medical_assistant.storage,
        "save_report",
        lambda payload, **kwargs: real_save(payload, tmp_path / "reports", **kwargs),
    )
    app = AppTest.from_file(str(APP)).run()
    yield app, path, auth, inference
    task = (
        app.session_state["analysis_task"]
        if "analysis_task" in app.session_state
        else None
    )
    if task is not None:
        task.cancel()
        task._thread.join(timeout=2)


def login(app, *, choose=True):
    app.text_input(key="login_user").input("dr.example")
    app.text_input(key="login_password").input("synthetic-test-password")
    app.button(key="login").click().run()
    if choose:
        app.selectbox(key="patient").set_value("fictional-001").run()
    return app


def wait_analysis(app):
    """Wait only for scripted test workers; no live timing/accuracy claim."""
    until = time.monotonic() + 5
    while "analysis_task" in app.session_state and time.monotonic() < until:
        app.session_state.analysis_task._thread.join(timeout=0.03)
        app.run(timeout=20)
    assert "analysis_task" not in app.session_state
    assert not app.exception
    return app


def open_imaging(app):
    return app.radio(key="workspace").set_value("CT review").run()


def open_safety(app):
    return app.button(key="guide_safety-check").click().run()


def open_sources(app):
    return app.button(key="guide_sources").click().run()


def prepare_safety(app):
    open_safety(app)
    assert app.button(key="generate").disabled
    app.text_area(key="safety_notes").input(
        "Scripted assessment of fictional missing data."
    )
    app.checkbox(key="safety_attest").check()
    app.radio(key="safety_action").set_value(
        "Allow draft generation after my safety assessment"
    )
    wait_analysis(app.button(key="submit_safety").click().run())
    assert not app.button(key="generate").disabled
    return app


def test_ui_hides_all_patient_examples_until_signin(ui):
    app, _, _, inference = ui
    assert not app.exception and app.title[0].value == "LOVISA"
    assert not app.selectbox and not app.radio and not app.get("download_button")
    assert not any(b.key == "generate" for b in app.button)
    login(app)
    assert app.selectbox(key="patient").value == "fictional-001"
    assert len(app.selectbox(key="patient").options) == 7
    assert not any(b.key == "generate" for b in app.button) and not inference.calls
    open_safety(app)
    assert app.button(key="generate").disabled
    # Generation is the last clinical action in the Safety check column.
    assert app.button(key="generate").label == "Generate draft for clinician review"
    app.button(key="logout").click().run()
    assert not app.selectbox and not app.radio and not app.get("download_button")


def test_ui_safety_review_rejection_approval_and_export(ui, tmp_path):
    app, _, _, inference = ui
    login(app)
    open_safety(app)
    assert app.button(key="generate").disabled
    app.text_area(key="safety_notes").input(
        "Synthetic test: assessed the missing-data limitations."
    )
    app.checkbox(key="safety_attest").check()
    app.radio(key="safety_action").set_value(
        "Allow draft generation after my safety assessment"
    )
    wait_analysis(app.button(key="submit_safety").click().run(timeout=20))
    assert not app.exception
    assert len(inference.calls) == 0
    assert not app.button(key="generate").disabled
    wait_analysis(app.button(key="generate").click().run())
    assert len(inference.calls) == 1
    assert not app.get("download_button")
    app.button(key="submit_review").click().run()
    assert app.error  # Empty notes/no attestation cannot approve.
    app.text_area(key="review_notes").input(
        "Verified synthetic source excerpts and unresolved uncertainty."
    )
    app.checkbox(key="attested").check()
    app.button(key="submit_review").click().run()
    assert not app.exception
    assert not app.get("download_button")
    app.button(key="preview_report_note").click().run()
    assert not app.checkbox(key="attested").value
    app.checkbox(key="attested").check()
    app.radio(key="decision").set_value("Approve report")
    app.button(key="submit_review").click().run()
    assert not app.exception
    assert len(app.get("download_button")) == 3
    reports = list((tmp_path / "reports").glob("*.json"))
    assert len(reports) == 1
    assert json.loads(reports[0].read_text())["reviewed"] is True


def test_ui_observation_proposal_requires_approval_and_preserves_unknown_date(ui):
    app, path, _, _ = ui
    login(app)
    app.selectbox(key="patient").set_value("synthetic-checklist").run()
    open_sources(app)
    before = len(get_history("synthetic-checklist", path).entries)
    app.text_area(key="symptoms").input(
        "Synthetic observation: symptom timing remains unavailable."
    )
    app.button(key="prepare_symptom").click().run()
    assert not app.exception
    assert len(get_history("synthetic-checklist", path).entries) == before
    assert not any(b.key == "generate" for b in app.button)
    app.text_area(key="import_notes").input(
        "Verified synthetic observation text; date and measurements were not supplied."
    )
    app.checkbox(key="import_attest").check()
    app.button(key="approve_import").click().run()
    assert not app.exception
    record = get_history("synthetic-checklist", path)
    assert len(record.entries) == before + 1
    observation = next(
        entry for entry in record.entries if entry.id.startswith("observation-")
    )
    assert observation.date is None and observation.blood_pressure is None
    assert observation.verification_status == "verified"


def test_ui_urgent_case_stops_without_calling_model(ui):
    app, _, _, inference = ui
    login(app)
    open_sources(app)
    app.text_area(key="symptoms").input(
        "Synthetic fixture explicitly reports a warning sign for workflow testing."
    )
    app.selectbox(key="warning_screen").set_value("present")
    app.button(key="prepare_symptom").click().run()
    app.text_area(key="import_notes").input("Verified explicit synthetic warning flag.")
    app.checkbox(key="import_attest").check()
    app.button(key="approve_import").click().run()
    open_safety(app)
    assert not app.exception
    assert app.button(key="generate").disabled
    assert not any(b.key == "submit_safety" for b in app.button)
    assert inference.calls == [] and not app.get("download_button")

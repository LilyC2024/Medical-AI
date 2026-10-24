"""Scripted failure paths: recoverable capacity errors and literal error rendering."""

# Imported pytest fixtures are reused as test parameters.
# ruff: noqa: F811
import json
from datetime import datetime
from zoneinfo import ZoneInfo

from test_ui import login, open_safety, open_sources, prepare_safety, ui, wait_analysis  # noqa: F401

from medical_assistant.database import attach_original, write_synthetic
from medical_assistant.jobs import WorkStopped
from medical_assistant.models import PatientRecord


BUSY = "Local processing is busy. Wait for the current task to finish before retrying."
UNTRUSTED = "![remote](https://example.invalid/tracker.png)"


def busy_worker(*args, **kwargs):
    raise WorkStopped(BUSY)


def test_busy_safety_submission_keeps_controls_available_and_can_retry(ui, monkeypatch):
    import medical_assistant.ui.clinical as clinical

    app, _, _, inference = ui
    login(app)
    open_safety(app)
    app.checkbox(key="safety_attest").check()
    app.radio(key="safety_action").set_value(
        "Allow draft generation after my safety assessment"
    )
    with monkeypatch.context() as patch:
        patch.setattr(clinical, "WorkTask", busy_worker)
        app.button(key="submit_safety").click().run()
    assert not app.exception
    assert any("Local processing is busy" in item.value for item in app.error)
    assert "analysis_task" not in app.session_state and not inference.calls
    assert app.button(key="generate").disabled
    wait_analysis(app.button(key="submit_safety").click().run())
    assert not app.button(key="generate").disabled and not inference.calls


def test_busy_draft_generation_preserves_safety_and_can_retry(ui, monkeypatch):
    import medical_assistant.ui.clinical as clinical

    app, _, _, inference = ui
    login(app)
    prepare_safety(app)
    case = app.session_state.case_id
    with monkeypatch.context() as patch:
        patch.setattr(clinical, "WorkTask", busy_worker)
        app.button(key="generate").click().run()
    assert not app.exception
    assert any("Local processing is busy" in item.value for item in app.error)
    assert app.session_state.case_id == case and not inference.calls
    assert "analysis_task" not in app.session_state
    assert not app.button(key="generate").disabled
    wait_analysis(app.button(key="generate").click().run())
    assert len(inference.calls) == 1 and not app.get("download_button")


def test_busy_ordinary_preflight_returns_error_without_starting_analysis(ui, monkeypatch):
    import medical_assistant.ui.clinical as clinical

    app, path, _, inference = ui
    raw = json.dumps(
        {
            "fictional": True,
            "patient_id": "ready",
            "display_name": "Ready fictional",
            "entries": [
                {
                    "id": "today",
                    "date": datetime.now(ZoneInfo("Europe/Amsterdam")).date().isoformat(),
                    "source_type": "documented",
                    "kind": "encounter",
                    "text": "Artificial fixture: supplied blood pressure and warning screening.",
                    "blood_pressure": {"systolic": 120, "diastolic": 80},
                    "warning_screen": "absent",
                }
            ],
        }
    )
    record = attach_original(PatientRecord.model_validate_json(raw), "ready.json", raw)
    write_synthetic(record, path, actor="scripted-fixture", action="test-seed")
    login(app, choose=False)
    app.selectbox(key="patient").set_value("ready").run()
    open_safety(app)
    with monkeypatch.context() as patch:
        patch.setattr(clinical, "WorkTask", busy_worker)
        app.button(key="preflight").click().run()
    assert not app.exception
    assert any("Local processing is busy" in item.value for item in app.error)
    assert app.button(key="generate").disabled and not inference.calls
    assert "analysis_task" not in app.session_state
    wait_analysis(app.button(key="preflight").click().run())
    assert not app.button(key="generate").disabled and not inference.calls


def test_worker_failure_shows_bounded_literal_reason_without_remote_markup(ui, monkeypatch):
    app, _, _, inference = ui
    login(app)
    prepare_safety(app)

    def failed(*args, **kwargs):
        raise ValueError("Missing local model weights " + UNTRUSTED + "x" * 2000)

    monkeypatch.setattr(inference, "assess", failed)
    wait_analysis(app.button(key="generate").click().run())
    reason = next(c.value for c in app.caption if "Missing local model weights" in c.value)
    assert len(reason) < 900 and UNTRUSTED not in reason
    assert "\\!\\[remote\\]" in reason
    assert not app.get("download_button") and not app.image


def test_invalid_import_error_cannot_render_record_supplied_image_markup(ui):
    app, _, _, _ = ui
    login(app)
    open_sources(app)
    raw = json.dumps(
        {"fictional": UNTRUSTED, "patient_id": "fictional-001", "display_name": "Test", "entries": []}
    )
    app.get("file_uploader")[0].set_value(("bad.json", raw.encode(), "application/json")).run()
    app.button(key="preview_import").click().run()
    assert not app.exception and app.error
    error = app.error[0].value
    assert UNTRUSTED not in error and "fictional" in error and "Input should be True" in error
    assert len(error) < 1400 and not app.image
    assert "proposal" not in app.session_state


def test_error_formatter_handles_nested_validation_without_echoing_source_values():
    from pydantic import ValidationError

    from medical_assistant.ui.errors import error_message

    try:
        PatientRecord.model_validate({"fictional": UNTRUSTED, "entries": []})
    except ValidationError as error:
        displayed = error_message(error)
    assert "fictional" in displayed and "patient_id" in displayed
    assert "additional validation issues" in displayed
    assert UNTRUSTED not in displayed and "errors.pydantic.dev" not in displayed

"""Patient-scoped navigation and discoverable safety controls, with scripted inference only."""

# Imported pytest fixture is intentionally reused as a test parameter.
# ruff: noqa: F811
import threading

from test_nodule_imaging import nodule_bytes
from test_ui import login, open_imaging, open_safety, prepare_safety, ui  # noqa: F401


def test_login_requires_explicit_selection_before_showing_any_patient(ui):
    app, _, _, inference = ui
    login(app, choose=False)
    assert not app.exception and app.selectbox(key="patient").value is None
    assert not app.radio and not app.text_area and not app.get("download_button")
    body = "\n".join(m.value for m in app.markdown)
    assert "Alex Example" not in body and "Morgan Synthetic" not in body
    assert not inference.calls


def test_clickable_guide_reaches_safety_without_starting_inference(ui):
    app, _, _, inference = ui
    login(app)
    app.button(key="next_action").click().run()
    assert app.radio(key="workspace").value == "Safety check"
    assert app.text_area(key="safety_notes")
    assert app.button(key="generate").disabled
    app.button(key="guide_patient-overview").click().run()
    assert app.radio(key="workspace").value == "Patient overview"
    assert not any(b.key == "generate" for b in app.button)
    app.button(key="guide_sources").click().run()
    assert app.radio(key="workspace").value == "Source records"
    assert app.get(
        "download_button"
    )  # Input originals, never a reviewed-report export.
    assert not app.json and not app.code and not inference.calls


def test_patient_switch_discards_pending_ct_and_unsubmitted_notes(ui):
    app, _, _, inference = ui
    login(app)
    open_imaging(app)
    store = app.session_state.imaging_store
    proposal = store.prepare(nodule_bytes(patient="fictional-001"), "fictional-001")
    app.session_state.imaging_proposal = proposal
    app.run()
    app.text_area(key="imaging_notes").input("Only the previous patient's notes.")
    app.selectbox(key="patient").set_value("demo-01").run()
    assert not app.exception and "imaging_proposal" not in app.session_state
    assert not store.pending
    body = "\n".join(m.value for m in app.markdown)
    assert "Morgan Synthetic" in body and "Alex Example" not in body
    assert "Five complex" not in body and "SHA-256" not in body
    open_imaging(app)
    assert not any(a.key == "imaging_notes" for a in app.text_area)
    assert not app.metric and not app.json and not app.code and not inference.calls


def test_pending_ct_has_direct_resolution_action_in_safety_view(ui):
    app, _, _, inference = ui
    login(app)
    open_imaging(app)
    store = app.session_state.imaging_store
    app.session_state.imaging_proposal = store.prepare(
        nodule_bytes(patient="fictional-001"), "fictional-001"
    )
    open_safety(app)
    assert app.button(key="generate").disabled
    assert not any(b.key == "submit_safety" for b in app.button)
    app.button(key="open_pending").click().run()
    assert app.radio(key="workspace").value == "CT review"
    app.button(key="imaging_discard").click().run()
    open_safety(app)
    assert app.text_area(key="safety_notes") and not inference.calls


def test_switch_during_analysis_cancels_and_rejects_old_patient_result(ui, monkeypatch):
    app, _, _, inference = ui
    login(app)
    prepare_safety(app)
    entered, release = threading.Event(), threading.Event()
    original = inference.assess

    def slow(*args, **kwargs):
        entered.set()
        release.wait(4)
        return original(*args, **kwargs)

    monkeypatch.setattr(inference, "assess", slow)
    app.button(key="generate").click().run()
    assert entered.wait(1)
    task = app.session_state.analysis_task
    app.selectbox(key="patient").set_value("demo-03").run()
    release.set()
    task._thread.join(timeout=2)
    app.run()
    assert not app.exception and "workflow" not in app.session_state
    assert (
        "analysis_task" not in app.session_state and "case_id" not in app.session_state
    )
    assert task._result is None
    assert not app.get("download_button")
    assert "Sam Synthetic" in "\n".join(m.value for m in app.markdown)

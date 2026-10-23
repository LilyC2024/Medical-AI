"""Real Streamlit controls, artificial pixels and scripted clinical inference/review."""

# ruff: noqa: F811
from test_endoscopy import endo_bytes
from test_ui import login, open_safety, prepare_safety, ui, wait_analysis  # noqa: F401


def test_pending_endoscopy_guide_blocks_safety_until_explicit_candidate_review(ui):
    app, _, _, inference = ui
    login(app)
    app.button(key="guide_endoscopy-review").click().run()
    assert app.button(key="endo_generate") and not app.exception
    store = app.session_state.imaging_store
    app.session_state.imaging_proposal = store.prepare(
        endo_bytes(patient="fictional-001"), "fictional-001"
    )
    app.run()
    assert len(app.image) == 2
    app.text_area(key="endo_notes").input("Scripted artificial region inspection.")
    app.checkbox(key="endo_attest").check()
    app.button(key="endo_accept").click().run()
    assert app.error and not store.snapshots("fictional-001")
    open_safety(app)
    assert app.button(key="generate").disabled
    app.button(key="open_pending").click().run()
    assert app.radio(key="workspace").value == "Endoscopy review"
    key = next(s.key for s in app.radio if str(s.key).startswith("endo_decision_"))
    app.radio(key=key).set_value("accept")
    app.text_area(key="endo_notes").input("Scripted artificial region inspection.")
    app.checkbox(key="endo_attest").check()
    app.button(key="endo_accept").click().run()
    assert not app.exception and len(store.snapshots("fictional-001")) == 1
    assert not inference.calls
    prepare_safety(app)
    wait_analysis(app.button(key="generate").click().run())
    assert (
        len(app.image) == 2
        and "Endoscopy inspection"
        in app.session_state.workflow.state(app.session_state.case_id)["draft"]
    )
    assert not app.get("download_button")


def test_switching_patient_discards_private_endoscopy_proposal(ui):
    app, _, _, _ = ui
    login(app)
    app.button(key="guide_endoscopy-review").click().run()
    store = app.session_state.imaging_store
    app.session_state.imaging_proposal = store.prepare(
        endo_bytes(patient="fictional-001"), "fictional-001"
    )
    app.run()
    app.selectbox(key="patient").set_value("demo-01").run()
    assert (
        not app.exception
        and "imaging_proposal" not in app.session_state
        and not store.pending
    )
    app.button(key="guide_endoscopy-review").click().run()
    assert not app.image and not app.metric


def test_urgent_case_blocks_endoscopy_controls_before_imaging(ui):
    app, _, _, inference = ui
    login(app)
    app.selectbox(key="patient").set_value("demo-04").run()
    app.button(key="guide_endoscopy-review").click().run()
    assert not any(b.key == "endo_generate" for b in app.button)
    assert app.warning and not inference.calls

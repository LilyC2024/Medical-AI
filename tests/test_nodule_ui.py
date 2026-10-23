# ruff: noqa: F811
from test_nodule_imaging import nodule_bytes
from test_ui import login, open_imaging, ui  # noqa: F401


def test_nodule_ui_requires_decisions_and_authentication(ui):
    app, path, auth, inference = ui
    login(app)
    app.selectbox(key="patient").set_value("synthetic-checklist").run()
    open_imaging(app)
    store = app.session_state.imaging_store
    key, proposal = store.prepare(nodule_bytes(), "synthetic-checklist")
    app.session_state.imaging_proposal = (key, proposal)
    app.run()
    assert not app.exception and not any(b.key == "generate" for b in app.button)
    app.text_area(key="imaging_notes").input(
        "Inspected synthetic source and candidates."
    )
    app.checkbox(key="imaging_attest").check()
    app.button(key="imaging_accept").click().run()
    assert app.error and not store.snapshots("synthetic-checklist")
    app.radio(key=key + "_decision_N001").set_value("accept")
    app.button(key="imaging_accept").click().run()
    assert not app.exception and len(store.snapshots("synthetic-checklist")) == 1
    assert not any(b.key == "generate" for b in app.button) and not inference.calls
    assert not app.get("download_button")


def test_nodule_ui_previews_and_preserves_caliper(ui):
    app, path, auth, inference = ui
    login(app)
    app.selectbox(key="patient").set_value("synthetic-checklist").run()
    open_imaging(app)
    store = app.session_state.imaging_store
    key, proposal = store.prepare(nodule_bytes(), "synthetic-checklist")
    app.session_state.imaging_proposal = (key, proposal)
    app.run()
    app.radio(key=key + "_decision_N001").set_value("accept")
    app.checkbox(key=key + "_caliper_N001").check()
    app.button(key="nodule_measurement_preview").click().run()
    assert not app.exception
    app.number_input(key=key + "_z_N001").set_value(0)
    app.number_input(key=key + "_y0_N001").set_value(3.0)
    app.number_input(key=key + "_x0_N001").set_value(3.0)
    app.number_input(key=key + "_y1_N001").set_value(3.0)
    app.number_input(key=key + "_x1_N001").set_value(8.0)
    app.button(key="nodule_measurement_preview").click().run()
    assert not app.exception and not store.snapshots("synthetic-checklist")
    app.text_area(key="imaging_notes").input(
        "Reviewed source plane and previewed five-millimeter synthetic caliper."
    )
    app.checkbox(key="imaging_attest").check()
    app.button(key="imaging_accept").click().run()
    assert not app.exception
    snapshot = store.snapshots("synthetic-checklist")[0]
    assert snapshot["nodule_review"]["decisions"][0]["caliper"]["end_zyx"] == [
        0.0,
        3.0,
        8.0,
    ]
    store.verify([snapshot])
    assert not inference.calls

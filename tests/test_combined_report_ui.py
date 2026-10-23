"""UI regressions using artificial CT and scripted models/reviewers only."""

# ruff: noqa: F811
from test_nodule_imaging import approve_nodule
from test_ui import login, open_imaging, prepare_safety, ui, wait_analysis  # noqa: F401

from medical_assistant.imaging import ImagingStore


def test_ct_report_shows_inspection_images_and_requires_previewed_note(ui):
    app, path, auth, inference = ui
    login(app)
    store = ImagingStore(path, auth)
    approve_nodule(store, app.session_state.auth_token, patient="fictional-001")
    prepare_safety(app)
    wait_analysis(app.button(key="generate").click().run())
    assert not app.exception
    assert len(app.image) == 2
    assert [caption for image in app.image for caption in image.captions] == [
        "Source CT",
        "Reviewed CT annotation",
    ]
    draft = app.session_state.workflow.state(app.session_state.case_id)["draft"]
    assert "CT inspection" in draft and "5.00 mm" in draft
    assert not app.get("download_button")
    app.text_area(key="review_notes").input(
        "Scripted inspection: check the artificial caliper and reconcile current medicines."
    )
    app.checkbox(key="attested").check()
    app.radio(key="decision").set_value("Approve report")
    app.button(key="submit_review").click().run()
    assert app.error and not app.get("download_button")
    app.button(key="preview_report_note").click().run()
    assert not app.exception and not app.checkbox(key="attested").value
    updated = app.session_state.workflow.state(app.session_state.case_id)
    assert "Scripted inspection" in updated["draft"] and not updated["reviewed"]
    app.checkbox(key="attested").check()
    app.button(key="submit_review").click().run()
    assert not app.exception and len(app.get("download_button")) == 3
    assert any(
        "with CT images" in button.label for button in app.get("download_button")
    )
    assert len(inference.calls) == 1


def test_no_ct_report_has_clear_route_to_start_with_imaging(ui):
    app, _, _, _ = ui
    login(app)
    prepare_safety(app)
    wait_analysis(app.button(key="generate").click().run())
    assert app.button(key="new_report_ct")
    app.button(key="new_report_ct").click().run()
    assert not app.exception and "case_id" not in app.session_state
    assert app.selectbox(key="patient").value == "fictional-001"
    assert app.radio(key="workspace").value == "CT review"
    assert not app.button(key="ct_generate").disabled

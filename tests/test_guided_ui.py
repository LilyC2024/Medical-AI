"""Scripted synthetic UI regressions: login, result retention and safety-before-generation."""

# Ruff sees imported pytest fixtures as redefinitions at test parameters.
# ruff: noqa: F811
from test_nodule_imaging import nodule_bytes
from test_ui import login, open_imaging, open_safety, prepare_safety, ui, wait_analysis  # noqa: F401


def test_completed_ct_automatically_shows_results_and_keeps_them_after_analysis(
    ui, tmp_path
):
    app, _, _, inference = ui
    login(app)
    open_imaging(app)
    path = tmp_path / "result.zip"
    path.write_bytes(nodule_bytes(patient="fictional-001"))

    class Completed:
        patient_id = "fictional-001"
        study_id = "lung-study"
        bundle_path = path

        def status(self):
            return "complete"

    app.session_state.ct_job = Completed()
    app.run()
    assert not app.exception
    assert any(h.value == "CT analysis results" for h in app.subheader)
    assert not any("No CT result yet" in item.value for item in app.info)
    assert app.metric[0].label == "Candidates proposed" and app.metric[0].value == "1"
    assert not any(b.key == "generate" for b in app.button)
    app.radio(key="workspace").set_value("Patient overview").run()
    open_imaging(app)
    assert app.metric[0].value == "1"
    key, proposal = app.session_state.imaging_proposal
    app.radio(key=key + "_decision_N001").set_value("accept")
    app.text_area(key="imaging_notes").input("Scripted fixture inspection only.")
    app.checkbox(key="imaging_attest").check()
    app.button(key="imaging_accept").click().run()
    prepare_safety(app)
    assert not inference.calls
    wait_analysis(app.button(key="generate").click().run())
    open_imaging(app)
    assert not app.button(key="ct_generate").disabled
    assert any("fresh, unreviewed report" in item.value for item in app.info)
    assert any(h.value == "CT analysis results" for h in app.subheader)
    assert app.metric[0].value == "1" and app.metric[1].value == "1"
    assert len(inference.calls) == 1 and not app.get("download_button")


def test_patient_change_clears_unsubmitted_safety_decision(ui):
    app, _, _, _ = ui
    login(app)
    open_safety(app)
    app.text_area(key="safety_notes").input("Unsubmitted notes for previous patient.")
    app.checkbox(key="safety_attest").uncheck()
    app.radio(key="safety_action").set_value(
        "Allow draft generation after my safety assessment"
    )
    app.selectbox(key="patient").set_value("demo-01").run()
    open_safety(app)
    assert app.text_area(key="safety_notes").value == ""
    assert app.checkbox(key="safety_attest").value
    assert app.radio(key="safety_action").value == "Keep analysis paused"
    assert app.button(key="generate").disabled


def test_expired_login_hides_case_data_and_controls(ui):
    app, _, auth, _ = ui
    login(app)
    token = app.session_state.auth_token
    auth.sessions[token] = ("dr.example", 0)
    app.run()
    assert not app.exception and not app.selectbox and not app.radio
    assert not any(b.key == "generate" for b in app.button)
    assert not app.get("download_button")

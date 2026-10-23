"""Explicit submit remains required with selected confirmations and optional notes."""

# ruff: noqa: F811
import pytest
from pydantic import ValidationError
from test_endoscopy import endo_bytes
from test_nodule_imaging import nodule_bytes
from test_ui import login, open_imaging, open_safety, ui, wait_analysis  # noqa: F401

from medical_assistant.models import Review


def test_blank_notes_are_valid_but_missing_confirmation_is_not():
    values = dict(
        approved=True,
        reviewer="scripted reviewer",
        clinician_attestation=True,
        draft_sha256="a" * 64,
        notes="",
    )
    assert Review(**values).notes == ""
    with pytest.raises(ValidationError):
        Review(**dict(values, clinician_attestation=False))


def test_safety_and_final_review_accept_blank_notes_only_after_submit(ui):
    app, _, _, inference = ui
    login(app)
    open_safety(app)
    assert (
        app.checkbox(key="safety_attest").value
        and app.text_area(key="safety_notes").value == ""
    )
    assert app.button(key="generate").disabled and not inference.calls
    assert app.radio(key="safety_action").value == "Keep analysis paused"
    app.radio(key="safety_action").set_value(
        "Allow draft generation after my safety assessment"
    )
    wait_analysis(app.button(key="submit_safety").click().run())
    assert (
        not app.exception
        and not app.button(key="generate").disabled
        and not inference.calls
    )
    wait_analysis(app.button(key="generate").click().run())
    flow, case = app.session_state.workflow, app.session_state.case_id
    assert not flow.state(case)["reviewed"]
    assert (
        app.checkbox(key="attested").value
        and app.text_area(key="review_notes").value == ""
    )
    app.radio(key="decision").set_value("Approve report")
    assert not flow.state(case)["reviewed"]
    app.button(key="submit_review").click().run()
    assert not app.exception and flow.state(case)["reviewed"]
    assert flow.state(case)["review_history"][-1]["notes"] == ""


@pytest.mark.parametrize("modality", ["ct", "endoscopy"])
def test_image_acceptance_optional_note_and_no_automatic_candidate_decision(
    ui, modality
):
    app, path, auth, inference = ui
    login(app)
    app.button(
        key="guide_" + ("ct-review" if modality == "ct" else "endoscopy-review")
    ).click().run()
    store = app.session_state.imaging_store
    key, proposal = store.prepare(
        (nodule_bytes if modality == "ct" else endo_bytes)("fictional-001"),
        "fictional-001",
    )
    app.session_state.imaging_proposal = (key, proposal)
    app.run()
    attest = "imaging_attest" if modality == "ct" else "endo_attest"
    action = "imaging_accept" if modality == "ct" else "endo_accept"
    assert app.checkbox(key=attest).value
    app.button(key=action).click().run()
    assert app.error and not store.snapshots("fictional-001")
    choice = next(r.key for r in app.radio if "_decision_" in str(r.key))
    app.radio(key=choice).set_value("accept")
    app.button(key=action).click().run()
    assert not app.exception and len(store.snapshots("fictional-001")) == 1
    assert (
        store.snapshots("fictional-001")[0]["review"]["notes"] == ""
        and not inference.calls
    )

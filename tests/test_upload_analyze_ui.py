"""Actual Streamlit file uploads; artificial pixels, scripted models/reviewers."""

# ruff: noqa: F811
from types import SimpleNamespace

import pytest
from test_endoscopy import endo_bytes
from test_nodule_imaging import nodule_bytes
from test_ui import login, prepare_safety, ui, wait_analysis  # noqa: F401


def upload(app, name, raw, mime="application/zip"):
    app.get("file_uploader")[0].set_value((name, raw, mime)).run()


@pytest.mark.parametrize(
    "view,prefix,make",
    [("CT review", "ct", nodule_bytes), ("Endoscopy review", "endo", endo_bytes)],
)
def test_upload_after_draft_is_enabled_and_reopens_safety(ui, view, prefix, make):
    app, _, _, inference = ui
    login(app)
    prepare_safety(app)
    wait_analysis(app.button(key="generate").click().run())
    old = app.session_state.workflow
    case = app.session_state.case_id
    before = old.state(case)
    app.radio(key="workspace").set_value(view).run()
    assert app.button(key=prefix + "_generate").label == "Analyze"
    assert not app.button(key=prefix + "_generate").disabled
    assert any(p.proto.popover.label == "Upload" for p in app.get("popover"))
    upload(app, "test.zip", make(patient="fictional-001"))
    app.button(key=prefix + "_generate").click().run()
    assert not app.exception and len(app.image) == 2
    assert "case_id" not in app.session_state
    assert old.state(case) == before  # Frozen report was not edited or approved.
    assert not app.session_state.imaging_store.snapshots("fictional-001")
    app.button(key="guide_safety-check").click().run()
    assert app.button(key="generate").disabled and len(inference.calls) == 1
    assert not app.get("download_button")


@pytest.mark.parametrize(
    "view,prefix,make",
    [("CT review", "ct", nodule_bytes), ("Endoscopy review", "endo", endo_bytes)],
)
def test_invalid_upload_shows_specific_error_and_retry_succeeds(ui, view, prefix, make):
    app, _, _, _ = ui
    login(app)
    app.radio(key="workspace").set_value(view).run()
    app.button(key=prefix + "_generate").click().run()
    assert any("Choose a file with Upload" in e.value for e in app.error)
    upload(app, "broken.zip", b"not an archive")
    app.button(key=prefix + "_generate").click().run()
    assert any("Analysis could not start" in e.value for e in app.error)
    assert not app.exception and not app.session_state.imaging_store.pending
    assert not app.button(key=prefix + "_generate").disabled
    upload(app, "valid.zip", make(patient="fictional-001"))
    app.button(key=prefix + "_generate").click().run()
    assert not app.exception and not app.error and len(app.image) == 2
    assert app.success and app.session_state.imaging_proposal


def test_cross_modality_pending_has_visible_blocker_and_navigation(ui):
    app, _, _, _ = ui
    login(app)
    app.button(key="guide_ct-review").click().run()
    upload(app, "ct.zip", nodule_bytes(patient="fictional-001"))
    app.button(key="ct_generate").click().run()
    original = app.session_state.imaging_proposal
    app.button(key="guide_endoscopy-review").click().run()
    assert any(
        "CT review" in e.value and "pending study" in e.value for e in app.warning
    )
    app.button(key="endo_generate").click().run()
    assert app.error and app.session_state.imaging_proposal == original
    app.button(key="endo_open_ct").click().run()
    assert app.radio(key="workspace").value == "CT review" and len(app.image) == 2


def test_failed_and_completed_other_jobs_do_not_disable_upload(ui):
    app, _, _, _ = ui
    login(app)
    app.button(key="guide_endoscopy-review").click().run()
    for status in ("failed", "complete", "cancelled", "timed_out"):
        app.session_state.ct_job = SimpleNamespace(
            patient_id="fictional-001", status=lambda s=status: s, error="test"
        )
        app.run()
        assert not app.button(key="endo_generate").disabled
    upload(app, "endo.zip", endo_bytes(patient="fictional-001"))
    app.button(key="endo_generate").click().run()
    assert not app.exception and len(app.image) == 2


def test_unknown_raw_endoscopy_source_error_is_actionable(ui):
    app, _, _, _ = ui
    login(app)
    app.button(key="guide_endoscopy-review").click().run()
    upload(app, "unknown.jpg", b"not a permitted research image", "image/jpeg")
    app.button(key="endo_generate").click().run()
    assert any("research composite" in e.value for e in app.error)
    assert not app.exception and "endo_job" not in app.session_state


def test_wrong_section_file_reports_error_without_candidate_or_source_leak(ui):
    app, _, _, _ = ui
    login(app)
    app.button(key="guide_ct-review").click().run()
    upload(app, "endo.zip", endo_bytes(patient="fictional-001"))
    app.button(key="ct_generate").click().run()
    assert any("other imaging section" in e.value for e in app.error)
    assert not app.image and not app.session_state.imaging_store.pending

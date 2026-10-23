# ruff: noqa: F811
from test_imaging import bundle_bytes
from test_ui import login, open_imaging, prepare_safety, ui, wait_analysis  # noqa: F401


def test_imaging_workbench_requires_review_and_keeps_facts_separate(ui):
    app, path, auth, inference = ui
    assert not app.exception
    assert not app.radio
    login(app)
    app.selectbox(key="patient").set_value("synthetic-checklist").run()
    open_imaging(app)
    store = app.session_state.imaging_store
    proposal = store.prepare(bundle_bytes(), "synthetic-checklist")
    app.session_state.imaging_proposal = proposal
    app.run()
    assert not app.exception
    assert not any(b.key == "generate" for b in app.button)
    app.checkbox(key="imaging_attest").uncheck()
    app.button(key="imaging_accept").click().run()
    assert app.error
    assert store.snapshots("synthetic-checklist") == []
    app.text_area(key="imaging_notes").input(
        "Verified synthetic association, overlays and limitations."
    )
    app.checkbox(key="imaging_attest").check()
    app.button(key="imaging_accept").click().run()
    assert not app.exception
    assert len(store.snapshots("synthetic-checklist")) == 1
    assert not any(b.key == "generate" for b in app.button)
    assert inference.calls == []
    assert not app.get("download_button")


def test_pending_imaging_can_be_discarded_without_acceptance(ui):
    app, _, _, _ = ui
    login(app)
    open_imaging(app)
    store = app.session_state.imaging_store
    app.session_state.imaging_proposal = store.prepare(
        bundle_bytes(patient="fictional-001"), "fictional-001"
    )
    app.run()
    assert not store.snapshots("fictional-001")
    app.button(key="imaging_discard").click().run()
    assert not app.exception
    assert not store.pending
    assert not store.snapshots("fictional-001")


def test_urgent_ui_routing_skips_optional_artifact_inspection(ui, monkeypatch):
    import json

    from test_imaging import acceptance

    from medical_assistant.database import get_history
    from medical_assistant.history_import import HistoryManagement
    from medical_assistant.imaging import ImagingStore

    app, path, auth, inference = ui
    login(app)
    manager = HistoryManagement(path, auth=auth)
    key, proposal = manager.prepare(
        json.dumps(
            {
                "fictional": True,
                "patient_id": "fictional-001",
                "display_name": get_history("fictional-001", path).display_name,
                "entries": [
                    {
                        "id": "urgent-image-test",
                        "date": None,
                        "source_type": "documented",
                        "kind": "symptom",
                        "text": "Synthetic structured warning.",
                        "warning_screen": "present",
                    }
                ],
            }
        ),
        "warning.json",
    )
    manager.approve(key, acceptance(proposal), app.session_state.auth_token)

    def fail(*args):
        raise AssertionError("Optional image checks delayed urgent routing")

    monkeypatch.setattr(ImagingStore, "snapshots", fail)
    app.run()
    assert not app.exception
    assert any("structured warning-sign report" in error.value for error in app.error)
    assert not any(b.key == "generate" for b in app.button)
    assert not inference.calls


def test_new_warning_blocks_review_of_an_older_case_snapshot(ui):
    import json

    from test_imaging import acceptance

    from medical_assistant.database import get_history
    from medical_assistant.history_import import HistoryManagement

    app, path, auth, _ = ui
    login(app)
    prepare_safety(app)
    wait_analysis(app.button(key="generate").click().run())
    assert app.button(key="submit_review")
    manager = HistoryManagement(path, auth=auth)
    key, proposal = manager.prepare(
        json.dumps(
            {
                "fictional": True,
                "patient_id": "fictional-001",
                "display_name": get_history("fictional-001", path).display_name,
                "entries": [
                    {
                        "id": "late-warning-test",
                        "date": None,
                        "source_type": "documented",
                        "kind": "symptom",
                        "text": "New synthetic warning in another session.",
                        "warning_screen": "present",
                    }
                ],
            }
        ),
        "warning.json",
    )
    manager.approve(key, acceptance(proposal), app.session_state.auth_token)
    app.run()
    assert not app.exception
    assert any("outside this case snapshot" in item.value for item in app.error)
    assert not any(button.key == "submit_review" for button in app.button)
    assert not app.get("download_button")

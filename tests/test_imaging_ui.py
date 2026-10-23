from test_ui import ui, login, wait_analysis, open_imaging  # noqa: F401
from test_imaging import bundle_bytes


def test_imaging_workbench_requires_review_and_keeps_facts_separate(ui):
    app, path, auth, inference = ui
    assert not app.exception
    open_imaging(app)
    assert app.button(key="ct_generate").disabled
    login(app)
    app.selectbox(key="patient").set_value("synthetic-checklist").run()
    open_imaging(app)
    store = app.session_state.imaging_store
    proposal = store.prepare(bundle_bytes(), "synthetic-checklist")
    app.session_state.imaging_proposal = proposal
    app.run()
    assert not app.exception
    assert app.button(key="generate").disabled
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
    assert not app.button(key="generate").disabled
    assert inference.calls == []
    assert not app.get("download_button")


def test_pending_imaging_can_be_discarded_without_acceptance(ui):
    app, _, _, _ = ui
    open_imaging(app)
    store = app.session_state.imaging_store
    app.session_state.imaging_proposal = store.prepare(
        bundle_bytes(patient="fictional-001"), "fictional-001"
    )
    app.run()
    assert app.button(key="imaging_accept").disabled
    app.button(key="imaging_discard").click().run()
    assert not app.exception
    assert not store.pending
    assert not store.snapshots("fictional-001")


def test_urgent_ui_routing_skips_optional_artifact_inspection(ui, monkeypatch):
    import json
    from medical_assistant.database import get_history
    from medical_assistant.history_import import HistoryManagement
    from medical_assistant.imaging import ImagingStore
    from test_imaging import acceptance

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
    wait_analysis(app.button(key="generate").click().run())
    assert not app.exception
    assert (
        app.session_state.workflow.state(app.session_state.case_id)["safety_decision"][
            "state"
        ]
        == "urgent"
    )
    assert not inference.calls


def test_new_warning_blocks_review_of_an_older_case_snapshot(ui):
    import json
    from medical_assistant.database import get_history
    from medical_assistant.history_import import HistoryManagement
    from test_imaging import acceptance

    app, path, auth, _ = ui
    login(app)
    wait_analysis(app.button(key="generate").click().run())
    app.text_area(key="safety_notes").input("Assessed synthetic uncertainty.")
    app.checkbox(key="safety_attest").check()
    app.radio(key="safety_action").set_value(
        "Continue after clinician assessment of uncertainty"
    )
    wait_analysis(app.button(key="submit_safety").click().run(timeout=20))
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

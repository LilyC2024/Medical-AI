"""Action routing uses artificial pixels and scripted workers; no clinical approval."""

from types import SimpleNamespace

import pytest
from conftest import create_auth
from test_endoscopy import endo_bytes
from test_nodule_imaging import nodule_bytes

from medical_assistant.database import seed
from medical_assistant.imaging import ImagingStore
from medical_assistant.imaging_actions import (
    analyze,
    blocker,
    collect,
    job_pending,
    failure_detail,
)


@pytest.fixture
def context(tmp_path):
    path = tmp_path / "history.sqlite3"
    seed(path)
    auth, token = create_auth(path)
    return {}, ImagingStore(path, auth), auth, token


@pytest.mark.parametrize(
    "modality,make", [("ct", nodule_bytes), ("endoscopy", endo_bytes)]
)
def test_upload_after_active_report_starts_fresh_unreviewed_context(
    context, modality, make
):
    state, store, auth, token = context
    closed = []
    old = {"reviewed": True, "draft": "unchanged approved report"}
    state.update(
        case_id="old",
        workflow=SimpleNamespace(
            inference=SimpleNamespace(close=lambda: closed.append(True)), snapshot=old
        ),
        safety_action="allow",
        saved_path="keep-on-disk.html",
        patient="fictional-001",
        auth_token=token,
    )
    analyze(
        state,
        store,
        auth,
        token,
        "fictional-001",
        modality,
        upload=("result.zip", make(patient="fictional-001")),
    )
    assert closed and "case_id" not in state and "safety_action" not in state
    assert state["patient"] == "fictional-001" and state["auth_token"] == token
    assert state["imaging_proposal"][1]["manifest"]["patient_id"] == "fictional-001"
    assert old == {"reviewed": True, "draft": "unchanged approved report"}
    assert store.snapshots("fictional-001") == []


@pytest.mark.parametrize(
    "upload", [("bad.zip", b"broken"), ("preview.png", b"pixels"), ("empty.zip", b"")]
)
def test_invalid_upload_keeps_existing_context_and_allows_retry(context, upload):
    state, store, auth, token = context
    state["case_id"] = "unchanged"
    with pytest.raises(ValueError):
        analyze(state, store, auth, token, "fictional-001", "ct", upload=upload)
    assert state == {"case_id": "unchanged"} and not store.pending
    analyze(
        state,
        store,
        auth,
        token,
        "fictional-001",
        "ct",
        upload=("good.zip", nodule_bytes(patient="fictional-001")),
    )
    assert "case_id" not in state and len(store.pending) == 1


def test_wrong_modality_and_patient_fail_without_pending_leak(context):
    state, store, auth, token = context
    for modality, raw in [
        ("ct", endo_bytes(patient="fictional-001")),
        ("endoscopy", nodule_bytes(patient="fictional-001")),
        ("ct", nodule_bytes(patient="demo-01")),
    ]:
        with pytest.raises(ValueError):
            analyze(
                state,
                store,
                auth,
                token,
                "fictional-001",
                modality,
                upload=("bad.zip", raw),
            )
        assert not store.pending and "imaging_proposal" not in state


def test_pending_study_is_never_silently_replaced(context):
    state, store, auth, token = context
    original = store.prepare(endo_bytes(patient="fictional-001"), "fictional-001")
    state["imaging_proposal"] = original
    assert "Endoscopy review" in blocker(state)
    with pytest.raises(ValueError, match="pending"):
        analyze(
            state,
            store,
            auth,
            token,
            "fictional-001",
            "ct",
            upload=("new.zip", nodule_bytes(patient="fictional-001")),
        )
    assert state["imaging_proposal"] == original and len(store.pending) == 1


def test_stale_completed_job_does_not_block_other_upload_or_replace_it(
    context, tmp_path
):
    state, store, auth, token = context
    path = tmp_path / "completed.zip"
    path.write_bytes(endo_bytes(patient="fictional-001"))
    job = SimpleNamespace(
        status=lambda: "complete",
        patient_id="fictional-001",
        study_id="endo-test",
        bundle_path=path,
    )
    state["endo_job"] = job
    assert blocker(state) is None
    analyze(
        state,
        store,
        auth,
        token,
        "fictional-001",
        "ct",
        upload=("new.zip", nodule_bytes(patient="fictional-001")),
    )
    before = state["imaging_proposal"]
    collect(state, store, "endoscopy", "fictional-001")
    assert state["imaging_proposal"] == before and not getattr(
        job, "inspection_ready", False
    )


def test_running_worker_record_import_and_missing_input_have_explanations(context):
    state, store, auth, token = context
    for update, message in [
        ({"proposal": "import"}, "Source records"),
        (
            {"ct_job": SimpleNamespace(status=lambda: "running")},
            "CT analysis is running",
        ),
        ({}, "Upload"),
    ]:
        state.clear()
        state.update(update)
        with pytest.raises(ValueError, match=message):
            analyze(state, store, auth, token, "fictional-001", "ct")


def test_expired_auth_cannot_upload_or_reset_context(context):
    state, store, auth, token = context
    state["case_id"] = "keep"
    auth.logout(token)
    with pytest.raises(PermissionError):
        analyze(
            state,
            store,
            auth,
            token,
            "fictional-001",
            "ct",
            upload=("new.zip", nodule_bytes(patient="fictional-001")),
        )
    assert state == {"case_id": "keep"} and not store.pending


def test_raw_image_runs_on_uploaded_bytes_not_a_generated_phantom(context, monkeypatch):
    import medical_assistant.imaging_actions as actions

    state, store, auth, token = context
    calls = []
    raw = b"exact permitted test image"
    monkeypatch.setattr(
        actions, "matching_endoscopy", lambda payload, patient: {"original": payload}
    )
    monkeypatch.setattr(
        actions,
        "LocalEndoscopyJob",
        lambda *args, **kwargs: calls.append(kwargs) or SimpleNamespace(),
    )
    analyze(
        state,
        store,
        auth,
        token,
        "research-composite-demo",
        "endoscopy",
        upload=("image.jpg", raw),
    )
    assert calls[0]["image_bytes"] == raw and calls[0]["mode"] == "installed"
    assert calls[0]["research"] == {"original": raw} and "endo_job" in state
    assert not store.pending


def test_uploaded_zip_takes_priority_over_example_model(context, monkeypatch):
    import medical_assistant.imaging_actions as actions

    state, store, auth, token = context
    monkeypatch.setattr(
        actions,
        "LocalCTJob",
        lambda *a, **kw: pytest.fail("Uploaded source was replaced with a phantom"),
    )
    analyze(
        state,
        store,
        auth,
        token,
        "fictional-001",
        "ct",
        upload=("new.zip", nodule_bytes(patient="fictional-001")),
        mode="lung-pretrained",
    )
    assert state["imaging_proposal"] and "ct_job" not in state


def test_failed_collection_is_retryable_and_does_not_hold_safety(context, tmp_path):
    state, store, _, _ = context
    path = tmp_path / "bad.zip"
    path.write_bytes(b"broken")
    job = SimpleNamespace(
        status=lambda: "complete",
        patient_id="fictional-001",
        study_id="lung-study",
        bundle_path=path,
    )
    state["ct_job"] = job
    collect(state, store, "ct", "fictional-001")
    assert "could not be verified" in state["ct_action_error"]
    assert not job_pending(job) and not store.pending


def test_collect_waits_for_explicit_analyze_when_report_is_frozen(context, tmp_path):
    state, store, auth, token = context
    path = tmp_path / "result.zip"
    path.write_bytes(nodule_bytes(patient="fictional-001"))
    job = SimpleNamespace(
        status=lambda: "complete",
        patient_id="fictional-001",
        study_id="lung-study",
        bundle_path=path,
    )
    state.update(ct_job=job, case_id="old")
    collect(state, store, "ct", "fictional-001")
    assert "imaging_proposal" not in state and job_pending(job)
    analyze(state, store, auth, token, "fictional-001", "ct")
    assert (
        state["imaging_proposal"] and "case_id" not in state and "ct_job" not in state
    )


def test_new_upload_retires_stale_terminal_job(context):
    state, store, auth, token = context
    state["ct_job"] = SimpleNamespace(status=lambda: "complete")
    analyze(
        state,
        store,
        auth,
        token,
        "fictional-001",
        "ct",
        upload=("new.zip", nodule_bytes(patient="fictional-001")),
    )
    assert "ct_job" not in state


def test_worker_failure_displays_actual_exception_without_traceback(tmp_path):
    path = tmp_path / "worker.log"
    path.write_text(
        'Traceback (most recent call last):\n  File "model.py", line 1\nValueError: Missing local registered weights\n'
    )
    job = SimpleNamespace(error="Local analysis failed.", log_path=path)
    assert (
        failure_detail(job)
        == "Local analysis failed. ValueError: Missing local registered weights"
    )

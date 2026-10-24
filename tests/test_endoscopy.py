"""Artificial image fixtures and scripted reviewers/inference; no clinical approval."""

import copy
import io
import zipfile
from datetime import datetime, timezone

import numpy as np
import pytest
from conftest import create_auth
from test_workflow import review_for

from medical_assistant.database import seed
from medical_assistant.endo_contracts import (
    Artifact,
    Bundle,
    ModelInfo,
    Study,
    array_bytes,
    digest,
    overlay_pixels,
    png,
    regions,
    sha,
)
from medical_assistant.endo_contracts import Review as EndoReview
from medical_assistant.endo_support import verify_endo_snapshot
from medical_assistant.imaging import ImagingStore
from medical_assistant.models import Review
from medical_assistant.nodule_support import imaging_acceptance_digest
from medical_assistant.report_assets import inspection_figures, portable_html
from medical_assistant.storage import save_report
from medical_assistant.workflow import MedicalHistoryOrchestrator


def endo_bytes(patient="synthetic-checklist", study_id="endo-test", *, negative=False):
    source = np.full((32, 32, 3), [110, 50, 50], np.uint8)
    probability = np.zeros((32, 32), np.float32)
    if not negative:
        probability[10:20, 8:18] = 0.9
    mask, candidates = regions(probability, 0.5, 8)
    study = Study(
        study_id=study_id,
        patient_alias=patient,
        input_kind="generated-synthetic",
        source_sha256=sha(source.tobytes()),
        width=32,
        height=32,
        model=ModelInfo(
            name="synthetic-fixture",
            backend="fixture",
            checkpoint_sha256="a" * 64,
            recipe_sha256="b" * 64,
            threshold=0.5,
            min_area_px=8,
            evaluation_scope="software-fixture",
        ),
        candidates=candidates,
    )
    files = {
        "source.png": ("source_preview", png(source)),
        "mask.png": ("mask", png(mask)),
        "probability.npy": ("probability", array_bytes(probability)),
        "overlay.png": (
            "overlay_preview",
            png(overlay_pixels(source, mask, candidates)),
        ),
    }
    bundle = Bundle(
        synthetic=True,
        patient_id=patient,
        study_id=study_id,
        job_id="f" * 32,
        processed_at=datetime.now(timezone.utc),
        study=study,
        artifacts=[
            Artifact(path=p, role=r, sha256=sha(data), size_bytes=len(data))
            for p, (r, data) in files.items()
        ],
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        z.writestr("bundle.json", bundle.model_dump_json())
        for name, (_, data) in files.items():
            z.writestr(name, data)
    return buffer.getvalue()


def approve_endo(store, token, patient="synthetic-checklist", study_id="endo-test"):
    key, proposal = store.prepare(endo_bytes(patient, study_id), patient)
    review = EndoReview(
        study_digest=digest(proposal["manifest"]["study"]),
        reviewer="dr.example",
        attested=True,
        decisions=[{"candidate_id": "polyp-1", "decision": "accept"}],
    )
    acceptance = Review(
        approved=True,
        reviewer="dr.example",
        clinician_attestation=True,
        notes="Scripted artificial image inspection.",
        draft_sha256=imaging_acceptance_digest(proposal, endo_review=review),
    )
    return store.approve(key, acceptance, token, endo_review=review)


@pytest.fixture
def endo_store(tmp_path):
    path = tmp_path / "history.sqlite3"
    seed(path)
    auth, token = create_auth(path)
    return ImagingStore(path, auth), token


def test_candidate_decisions_authentication_and_immutability(endo_store):
    store, token = endo_store
    key, p = store.prepare(endo_bytes(), "synthetic-checklist")
    r = EndoReview(
        study_digest=digest(p["manifest"]["study"]),
        reviewer="dr.example",
        attested=True,
        decisions=[{"candidate_id": "polyp-1", "decision": "uncertain"}],
    )
    with pytest.raises(ValueError):
        imaging_acceptance_digest(p, endo_review=r)
    r.decisions[0].decision = "accept"
    acceptance = Review(
        approved=True,
        reviewer="dr.example",
        clinician_attestation=True,
        notes="Scripted review.",
        draft_sha256=imaging_acceptance_digest(p, endo_review=r),
    )
    with pytest.raises(PermissionError):
        store.approve(key, acceptance, endo_review=r)
    accepted = store.approve(key, acceptance, token, endo_review=r)
    verify_endo_snapshot(accepted)
    assert store.snapshots("synthetic-checklist") == [accepted]
    bad = copy.deepcopy(accepted)
    bad["endo_review"]["decisions"][0]["decision"] = "reject"
    with pytest.raises(ValueError):
        store.verify([bad])
    with pytest.raises(ValueError):
        approve_endo(store, token)


def test_mismatched_patient_and_cross_modality_decisions_rejected(endo_store):
    store, _ = endo_store
    with pytest.raises(ValueError):
        store.prepare(endo_bytes(), "fictional-001")
    _, p = store.prepare(endo_bytes(), "synthetic-checklist")
    with pytest.raises(ValueError):
        imaging_acceptance_digest(p, nodule_review={"forged": "CT"})
    with pytest.raises(ValueError):
        imaging_acceptance_digest(p)


def test_combined_history_ct_and_endo_report_is_approval_bound(
    endo_store, inference, tmp_path
):
    from test_nodule_imaging import approve_nodule

    store, token = endo_store
    approve_endo(store, token)
    approve_nodule(store, token)
    flow = MedicalHistoryOrchestrator(inference, auth=store.auth)
    case, events = flow.start_patient("synthetic-checklist", store.path)
    list(events)
    flow.acknowledge_safety(case, review_for(flow.state(case), safety=True), token)
    state = flow.state(case)
    assert (
        "Endoscopy inspection" in state["draft"]
        and "1 accepted on inspection" in state["draft"]
    )
    assert any(
        s["manifest"].get("study", {}).get("candidates", [{}])[0].get("area_px") == 100
        for s in state["imaging"]
    )
    assert "5.00 mm" in state["draft"] and state["draft"].count("# ") == 1
    assert (
        len(state["report_evidence"]["ct_studies"]) == 1
        and len(state["report_evidence"]["endoscopy_studies"]) == 1
    )
    assert "imaging" not in inference.calls[0][1]
    assert len(inspection_figures(state, store)) == 2
    with pytest.raises(ValueError):
        flow.export(case)
    flow.prepare_report_note(case, "", token)  # preview is required
    flow.review(case, review_for(state), token)
    payload = flow.export(case)
    html = portable_html(payload, auth=store.auth, safety=flow.safety)
    assert "Source endoscopy" in html and html.count("data:image/png;base64,") == 4
    assert save_report(
        payload, tmp_path / "reports", auth=store.auth, safety=flow.safety
    ).exists()
    changed = copy.deepcopy(payload)
    changed["imaging"][0]["endo_review"]["decisions"][0]["decision"] = "reject"
    with pytest.raises((ValueError, PermissionError)):
        save_report(changed, tmp_path / "forged", auth=store.auth, safety=flow.safety)


def test_source_image_changes_block_report_export(endo_store, inference):
    store, token = endo_store
    accepted = approve_endo(store, token)
    flow = MedicalHistoryOrchestrator(inference, auth=store.auth)
    case, events = flow.start_patient("synthetic-checklist", store.path)
    list(events)
    flow.acknowledge_safety(case, review_for(flow.state(case), safety=True), token)
    flow.prepare_report_note(case, "", token)  # preview is required
    flow.review(case, review_for(flow.state(case)), token)
    path = store.preview_path(accepted, "source_preview", 0)
    path.write_bytes(b"changed")
    with pytest.raises(ValueError):
        flow.export(case)


def test_patient_isolation_cancels_endoscopy_job():
    from medical_assistant.ui.navigation import ensure_patient

    class Job:
        patient_id = "old"
        cancelled = False

        def status(self):
            return "running"

        def cancel(self):
            self.cancelled = True

    job = Job()
    state = {"patient": "new", "auth_token": "session", "endo_job": job}
    assert (
        not ensure_patient(state, "new") and job.cancelled and "endo_job" not in state
    )


def test_zero_candidates_never_becomes_normal_exam(endo_store):
    from medical_assistant.report import endoscopy_summary

    store, token = endo_store
    key, p = store.prepare(endo_bytes(negative=True), "synthetic-checklist")
    r = EndoReview(
        study_digest=digest(p["manifest"]["study"]),
        reviewer="dr.example",
        attested=True,
        decisions=[],
    )
    approval = Review(
        approved=True,
        reviewer="dr.example",
        clinician_attestation=True,
        notes="Scripted negative-image review; not normality.",
        draft_sha256=imaging_acceptance_digest(p, endo_review=r),
    )
    accepted = store.approve(key, approval, token, endo_review=r)
    text = endoscopy_summary([accepted])
    assert "0 candidate" in text and "exclude missed polyps" in text

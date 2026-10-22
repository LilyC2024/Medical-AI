"""Synthetic exchange fixtures; scripted model tests are not live CT/LLM tests."""
import io
import json
import zipfile

import numpy as np
import pytest
from PIL import Image

from medical_assistant.database import get_history, seed
from medical_assistant.imaging import ImagingStore
from medical_assistant.imaging_contract import CLASSES, COLORS, file_digest, validate_bundle
from medical_assistant.models import Review
from medical_assistant.report import digest
from medical_assistant.storage import save_report
from medical_assistant.workflow import MedicalHistoryOrchestrator


def bundle_bytes(patient="synthetic-checklist", study="synthetic-study-001", mutate=None):
    labels = np.array([[[0, 1], [2, 3]], [[1, 1], [0, 3]]], dtype=np.uint8)
    mask = io.BytesIO()
    np.savez_compressed(mask, predicted_labels=labels, spacing_zyx=np.array([5., 1., 1.]),
                        origin_lps=np.array([10., 20., 30.]), direction_lps=np.eye(3).ravel())
    files = {"runtime/prediction_mask.npz": mask.getvalue()}
    artifacts = [{"path": "runtime/prediction_mask.npz", "role": "mask", "slice_index": None}]
    for i in range(2):
        source = np.full((2, 2, 3), 128, dtype=np.uint8)
        overlay = source.copy()
        selected = labels[i] != 0
        overlay[selected] = (0.55 * source[selected] + 0.45 * COLORS[labels[i][selected]]).astype(np.uint8)
        for role, pixels in [("source_preview", source), ("overlay_preview", overlay)]:
            buffer = io.BytesIO()
            Image.fromarray(pixels).save(buffer, format="PNG")
            name = f"previews/{i}-{role}.png"
            files[name] = buffer.getvalue()
            artifacts.append({"path": name, "role": role, "slice_index": i})
    for a in artifacts:
        a.update(sha256=file_digest(files[a["path"]]), size_bytes=len(files[a["path"]]))
    counts = [int((labels == i).sum()) for i in range(4)]
    manifest = dict(schema_version="mhcra-imaging-v1", synthetic=True, patient_id=patient,
                    study_id=study, job_id="a" * 32, acquisition_date=None,
                    processed_at="2026-01-01T12:00:00+00:00", source_series_sha256="b" * 64,
                    checkpoint_sha256="c" * 64, onnx_sha256="d" * 64, model_name="UNetSmall",
                    classes=CLASSES, geometry=dict(shape_zyx=[2, 2, 2], spacing_zyx_mm=[5, 1, 1],
                    origin_lps=[10, 20, 30], direction_lps=np.eye(3).ravel().tolist()),
                    voxel_counts=counts, candidate_volumes_mm3=[c * 5 for c in counts],
                    postprocessing_enabled=False, onnx_parity_passed=True, uncertainty_mean=0.8,
                    artifacts=artifacts, limitations="Explicit synthetic unit fixture; no clinical findings.")
    if mutate:
        mutate(manifest, files)
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("bundle.json", json.dumps(manifest))
        for name, value in files.items():
            z.writestr(name, value)
    return output.getvalue()


def acceptance(proposal, *, approved=True):
    return Review(approved=approved, reviewer="dr.example", clinician_attestation=True,
                  notes="Checked synthetic association and all research limitations.", draft_sha256=proposal["sha256"])


@pytest.fixture
def imaging_store(auth_session):
    auth, token = auth_session
    seed(auth.path)
    return ImagingStore(auth.path, auth), token


def accepted_imaging(store, token, study="synthetic-study-001"):
    key, proposal = store.prepare(bundle_bytes(study=study), "synthetic-checklist")
    return store.approve(key, acceptance(proposal), token)


def test_valid_bundle_and_authenticated_immutable_acceptance(imaging_store):
    store, token = imaging_store
    before = len(get_history("synthetic-checklist", store.path).entries)
    key, proposal = store.prepare(bundle_bytes(), "synthetic-checklist")
    assert store.snapshots("synthetic-checklist") == []
    with pytest.raises(PermissionError):
        store.approve(key, acceptance(proposal))
    review = acceptance(proposal)
    review.draft_sha256 = "0" * 64
    with pytest.raises(ValueError):
        store.approve(key, review, token)
    item = store.approve(key, acceptance(proposal), token)
    assert store.snapshots("synthetic-checklist") == [item]
    assert item["manifest"]["acquisition_date"] is None
    assert len(get_history("synthetic-checklist", store.path).entries) == before
    key, proposal = store.prepare(bundle_bytes(), "synthetic-checklist")
    with pytest.raises(ValueError, match="immutable"):
        store.approve(key, acceptance(proposal), token)
    store.discard(key)


@pytest.mark.parametrize("mutate", [
    lambda m, f: m.update(synthetic=False),
    lambda m, f: m.update(onnx_parity_passed=False),
    lambda m, f: m.update(postprocessing_enabled=True),
    lambda m, f: m.update(acquisition_date="2025-01-01"),
    lambda m, f: m["artifacts"][0].update(path="../../escape.npz"),
    lambda m, f: m["geometry"].update(spacing_zyx_mm=[0, 1, 1]),
    lambda m, f: m.update(voxel_counts=[8, 0, 0, 0], candidate_volumes_mm3=[40, 0, 0, 0]),
    lambda m, f: f.update({"runtime/prediction_mask.npz": b"tampered"}),
    lambda m, f: f.update({"unexpected.txt": b"unlisted"}),
    lambda m, f: m["artifacts"].pop(),
    lambda m, f: m["geometry"].update(origin_lps=[100, 20, 30]),
])
def test_invalid_contracts_and_artifacts_fail_closed(mutate):
    with pytest.raises(ValueError):
        validate_bundle(bundle_bytes(mutate=mutate), "synthetic-checklist")


def test_wrong_patient_and_duplicate_zip_entries_fail():
    with pytest.raises(ValueError, match="different synthetic patient"):
        validate_bundle(bundle_bytes(), "fictional-001")
    raw = io.BytesIO(bundle_bytes())
    with zipfile.ZipFile(raw, "a") as z:
        with pytest.warns(UserWarning):
            z.writestr("bundle.json", "{}")
    with pytest.raises(ValueError, match="Duplicate"):
        validate_bundle(raw.getvalue(), "synthetic-checklist")


def test_overlay_integrity_is_checked_even_when_hash_matches():
    def mutate(m, files):
        overlay = next(a for a in m["artifacts"] if a["role"] == "overlay_preview")
        source = next(a for a in m["artifacts"] if a["role"] == "source_preview")
        files[overlay["path"]] = files[source["path"]]
        overlay.update(sha256=file_digest(files[overlay["path"]]), size_bytes=len(files[overlay["path"]]))
    with pytest.raises(ValueError, match="Overlay"):
        validate_bundle(bundle_bytes(mutate=mutate), "synthetic-checklist")


def test_string_mask_metadata_is_rejected_as_validation_error():
    def mutate(m, files):
        a = m["artifacts"][0]
        with np.load(io.BytesIO(files[a["path"]]), allow_pickle=False) as original:
            arrays = {key: original[key] for key in original.files}
        arrays["spacing_zyx"] = np.array(["5", "1", "1"])
        output = io.BytesIO()
        np.savez_compressed(output, **arrays)
        files[a["path"]] = output.getvalue()
        a.update(sha256=file_digest(files[a["path"]]), size_bytes=len(files[a["path"]]))
    with pytest.raises(ValueError, match="geometry mismatch"):
        validate_bundle(bundle_bytes(mutate=mutate), "synthetic-checklist")


@pytest.mark.parametrize("member", ["predicted_labels.npy", "spacing_zyx.npy"])
def test_array_header_allocation_bombs_are_rejected_before_numpy_load(member, monkeypatch):
    def mutate(m, files):
        artifact = m["artifacts"][0]
        raw = io.BytesIO()
        np.lib.format.write_array_header_1_0(raw, {"descr": "|u1", "fortran_order": False, "shape": (10**12,)})
        original = io.BytesIO(files[artifact["path"]])
        output = io.BytesIO()
        with zipfile.ZipFile(original) as source, zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as target:
            for name in source.namelist():
                target.writestr(name, raw.getvalue() if name == member else source.read(name))
        files[artifact["path"]] = output.getvalue()
        artifact.update(sha256=file_digest(output.getvalue()), size_bytes=len(output.getvalue()))
    payload = bundle_bytes(mutate=mutate)
    monkeypatch.setattr(np, "load", lambda *a, **k: pytest.fail("Untrusted header reached allocating array loader"))
    with pytest.raises(ValueError, match="header shape"):
        validate_bundle(payload, "synthetic-checklist")


def test_completed_job_study_identity_is_bound(imaging_store):
    store, _ = imaging_store
    with pytest.raises(ValueError, match="requested study"):
        store.prepare(bundle_bytes(), "synthetic-checklist", study_id="another-study")
    assert not store.pending


def test_commit_failure_restores_pending_files(imaging_store, monkeypatch):
    from contextlib import contextmanager
    import medical_assistant.imaging as imaging_module
    store, token = imaging_store
    key, proposal = store.prepare(bundle_bytes(), "synthetic-checklist")
    original = imaging_module.connect

    @contextmanager
    def failed_commit(path):
        with original(path) as db:
            yield db
            raise OSError("Simulated disk failure at commit")

    with monkeypatch.context() as patch:
        patch.setattr(imaging_module, "connect", failed_commit)
        with pytest.raises(OSError, match="disk failure"):
            store.approve(key, acceptance(proposal), token)
    assert (store.root / "pending" / key / "bundle.json").exists()
    assert not store._directory("synthetic-checklist", "synthetic-study-001").exists()
    assert not store.snapshots("synthetic-checklist")


def test_same_bundle_can_recover_orphaned_promotion_after_process_crash(imaging_store):
    store, token = imaging_store
    key, proposal = store.prepare(bundle_bytes(), "synthetic-checklist")
    target = store._directory("synthetic-checklist", "synthetic-study-001")
    target.parent.mkdir(parents=True)
    (store.root / "pending" / key).rename(target)  # simulated crash before DB insertion
    store.pending.clear()
    key, proposal = store.prepare(bundle_bytes(), "synthetic-checklist")
    snapshot = store.approve(key, acceptance(proposal), token)
    assert store.snapshots("synthetic-checklist") == [snapshot]
    assert not (store.root / "pending" / key).exists()


def test_case_database_must_match_authenticated_imaging_store(imaging_store, inference, tmp_path):
    store, _ = imaging_store
    other = tmp_path / "other.sqlite3"
    seed(other)
    workflow = MedicalHistoryOrchestrator(inference, auth=store.auth)
    with pytest.raises(ValueError, match="database must match"):
        workflow.start_patient("synthetic-checklist", other)


def test_tampered_pending_and_accepted_artifacts_are_blocked(imaging_store):
    store, token = imaging_store
    key, proposal = store.prepare(bundle_bytes(), "synthetic-checklist")
    path = store.root / "pending" / key / proposal["manifest"]["artifacts"][1]["path"]
    original = path.read_bytes()
    path.write_bytes(b"changed")
    with pytest.raises(ValueError, match="changed"):
        store.approve(key, acceptance(proposal), token)
    path.write_bytes(original)
    snapshot = store.approve(key, acceptance(proposal), token)
    path = store.preview_path(snapshot, "source_preview", 0)
    path.write_bytes(b"changed")
    with pytest.raises(ValueError, match="changed"):
        store.snapshots("synthetic-checklist")


def test_appendix_is_review_bound_and_excluded_from_llm(imaging_store, inference, tmp_path):
    store, token = imaging_store
    accepted_imaging(store, token)
    workflow = MedicalHistoryOrchestrator(inference, auth=store.auth)
    case, events = workflow.start_patient("synthetic-checklist", store.path)
    list(events)
    assert workflow.state(case)["status"] == "awaiting_safety_review" and not inference.calls
    state = workflow.state(case)
    workflow.acknowledge_safety(case, Review(approved=True, reviewer="dr.example", clinician_attestation=True,
        notes="Assessed synthetic uncertainty.", draft_sha256=state["safety_decision"]["decision_sha256"]), token)
    state = workflow.state(case)
    assert state["draft"].count("\n## ") == 7
    assert "Research imaging appendix" in state["draft"]
    assert "acquisition date unavailable" in state["draft"]
    assert "confirmed clinical findings" in state["draft"]
    assert len(inference.calls) == 1
    assert "UNetSmall" not in json.dumps(inference.calls[0][1])
    with pytest.raises(ValueError):
        workflow.export(case)
    workflow.review(case, Review(approved=True, reviewer="dr.example", clinician_attestation=True,
        notes="Verified synthetic report and imaging appendix.", draft_sha256=digest(state["draft"])), token)
    payload = workflow.export(case)
    assert save_report(payload, tmp_path / "reports", auth=store.auth, safety=workflow.safety).exists()
    image = store.preview_path(payload["imaging"][0], "source_preview", 0)
    image.write_bytes(b"changed")
    with pytest.raises(ValueError, match="changed"):
        workflow.export(case)
    with pytest.raises(ValueError, match="changed"):
        save_report(payload, tmp_path / "reports", auth=store.auth, safety=workflow.safety)


def test_urgent_safety_is_not_delayed_by_corrupt_optional_imaging(imaging_store, inference):
    from medical_assistant.history_import import HistoryManagement
    store, token = imaging_store
    snapshot = accepted_imaging(store, token)
    manager = HistoryManagement(store.path, auth=store.auth)
    key, proposal = manager.prepare(json.dumps({"fictional": True, "patient_id": "synthetic-checklist",
        "display_name": get_history("synthetic-checklist", store.path).display_name,
        "entries": [{"id": "urgent-test", "date": None, "kind": "symptom", "source_type": "documented",
        "text": "Explicit synthetic warning fixture.", "warning_screen": "present"}]}), "synthetic-warning.json")
    manager.approve(key, acceptance(proposal), token)
    store.preview_path(snapshot, "source_preview", 0).write_bytes(b"changed")
    workflow = MedicalHistoryOrchestrator(inference, auth=store.auth)
    case, events = workflow.start_patient("synthetic-checklist", store.path)
    list(events)
    assert workflow.state(case)["safety_decision"]["state"] == "urgent"
    assert not inference.calls


def test_active_case_uses_fixed_imaging_snapshot(imaging_store, inference):
    store, token = imaging_store
    accepted_imaging(store, token)
    workflow = MedicalHistoryOrchestrator(inference, auth=store.auth)
    case, events = workflow.start_patient("synthetic-checklist", store.path)
    list(events)
    accepted_imaging(store, token, study="synthetic-study-002")
    assert len(workflow.state(case)["imaging"]) == 1
    assert len(store.snapshots("synthetic-checklist")) == 2

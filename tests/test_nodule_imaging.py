"""Scripted synthetic exchange tests; neither live detection nor clinician approval."""

import io
import json
import zipfile

import numpy as np
from PIL import Image
import pytest

from medical_assistant.nodule_models import (
    Geometry,
    SourceSlice,
    ModelProvenance,
    Candidate,
    Study,
    Decision,
    Caliper,
    Review as NoduleReview,
    digest as ndigest,
)
from medical_assistant.nodule_exchange import (
    PENDING_REPORT,
    wire_pixels,
    byte_digest,
    read_exchange,
)
from medical_assistant.imaging_contract import validate_bundle
from medical_assistant.imaging import ImagingStore
from medical_assistant.nodule_support import imaging_acceptance_digest
from medical_assistant.models import Review
from medical_assistant.database import seed, get_history
from medical_assistant.workflow import MedicalHistoryOrchestrator
from medical_assistant.report import digest
from medical_assistant.storage import save_report


def nodule_bytes(patient="synthetic-checklist", study_id="lung-study", mutate=None, *, no_candidates=False):
    g = Geometry(
        shape_zyx=(2, 12, 12),
        spacing_zyx_mm=(2, 1, 1),
        origin_lps_mm=(10, 20, 30),
        direction_lps=tuple(np.eye(3).ravel()),
    )
    sources = [
        SourceSlice(index=i, sha256=str(i + 1) * 64, sop_uid_sha256=str(i + 3) * 64)
        for i in range(2)
    ]
    study = Study(
        study_id=study_id,
        patient_alias=patient,
        input_kind="generated-synthetic",
        protocol_attestation="synthetic-phantom",
        source_sha256=ndigest(
            {
                "geometry": g.model_dump(mode="json"),
                "sources": [s.model_dump(mode="json") for s in sources],
            }
        ),
        geometry=g,
        sources=sources,
        model=ModelProvenance(
            name="Scripted synthetic unit fixture",
            checkpoint_sha256="a" * 64,
            config_sha256="b" * 64,
            execution_device="cpu",
            software_versions={"test": "scripted"},
            synthetic_fixture=True,
            score_threshold=0.5,
        ),
        candidates=[] if no_candidates else [
            Candidate(candidate_id="N001", box_zyx=(0, 2, 3, 1, 7, 8), score=0.8)
        ],
    )
    hu = np.full(g.shape_zyx, -800, dtype=np.float32)
    hu[:, 3:6, 4:7] = 50
    array = io.BytesIO()
    np.save(array, hu, allow_pickle=False)
    files = {
        "source.npy": array.getvalue(),
        "producer/report.md": PENDING_REPORT.encode(),
    }
    items = [
        {"path": "source.npy", "role": "source_volume", "slice_index": None},
        {"path": "producer/report.md", "role": "producer_report", "slice_index": None},
    ]
    for index in range(2):
        source, overlay = wire_pixels(study, hu, index)
        for role, pixels in (("source_preview", source), ("overlay_preview", overlay)):
            path = f"previews/{index}-{role}.png"
            out = io.BytesIO()
            Image.fromarray(pixels).save(out, format="PNG")
            files[path] = out.getvalue()
            items.append({"path": path, "role": role, "slice_index": index})
    for a in items:
        a.update(sha256=byte_digest(files[a["path"]]), size_bytes=len(files[a["path"]]))
    manifest = {
        "schema_version": "mhcra-lung-nodules-v2",
        "synthetic": True,
        "patient_id": patient,
        "study_id": study_id,
        "job_id": "f" * 32,
        "acquisition_date": None,
        "processed_at": "2026-10-22T12:00:00+00:00",
        "status": "pending_review",
        "study": study.model_dump(mode="json"),
        "producer_review": None,
        "artifacts": items,
    }
    if mutate:
        mutate(manifest, files)
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("bundle.json", json.dumps(manifest))
        for path, data in files.items():
            z.writestr(path, data)
    return out.getvalue()


def candidate_review(proposal, **changes):
    bundle = read_exchange_bytes_manifest(proposal)
    values = dict(
        study_digest=ndigest(bundle.study),
        reviewer="dr.example",
        qualified_reviewer_attestation=True,
        approved=True,
        decisions=[
            Decision(
                candidate_id="N001",
                decision="accept",
                caliper=Caliper(start_zyx=(0, 3, 3), end_zyx=(0, 3, 8)),
            )
        ],
    )
    return NoduleReview(**(values | changes))


def read_exchange_bytes_manifest(proposal):
    from medical_assistant.nodule_exchange import NoduleBundle

    return NoduleBundle.model_validate(proposal["manifest"])


def approve_nodule(store, token, patient="synthetic-checklist"):
    key, proposal = store.prepare(nodule_bytes(patient), patient)
    nr = candidate_review(proposal)
    review = Review(
        approved=True,
        reviewer="dr.example",
        clinician_attestation=True,
        notes="Scripted synthetic review only.",
        draft_sha256=imaging_acceptance_digest(proposal, nr),
    )
    return store.approve(key, review, token, nodule_review=nr)


@pytest.fixture
def nodule_store(auth_session):
    auth, token = auth_session
    seed(auth.path)
    return ImagingStore(auth.path, auth), token


def test_current_nodule_bundle_dispatch_and_authenticated_acceptance(nodule_store):
    store, token = nodule_store
    bundle, _, _ = validate_bundle(nodule_bytes(), "synthetic-checklist")
    assert bundle.status == "pending_review" and bundle.producer_review is None
    count = len(get_history("synthetic-checklist", store.path).entries)
    item = approve_nodule(store, token)
    assert store.snapshots("synthetic-checklist") == [item]
    assert item["nodule_review"]["decisions"][0]["caliper"]["end_zyx"] == [
        0.0,
        3.0,
        8.0,
    ]
    assert len(get_history("synthetic-checklist", store.path).entries) == count


@pytest.mark.parametrize(
    "issue",
    [
        "missing",
        "uncertain",
        "wrong_actor",
        "stale",
        "missing_attestation",
        "changed_measurement",
    ],
)
def test_candidate_review_cannot_be_bypassed(nodule_store, issue):
    store, token = nodule_store
    key, p = store.prepare(nodule_bytes(), "synthetic-checklist")
    nr = candidate_review(p)
    review = Review(
        approved=True,
        reviewer="dr.example",
        clinician_attestation=True,
        notes="Checked synthetic fixture.",
        draft_sha256=imaging_acceptance_digest(p, nr),
    )
    with pytest.raises((ValueError, PermissionError)):
        if issue == "missing":
            nr = None
        if issue == "uncertain":
            nr = candidate_review(
                p, decisions=[Decision(candidate_id="N001", decision="uncertain")]
            )
        if issue == "wrong_actor":
            nr = candidate_review(p, reviewer="other")
        if issue == "stale":
            nr = candidate_review(p, study_digest="0" * 64)
        if issue == "missing_attestation":
            nr = candidate_review(p, qualified_reviewer_attestation=False)
        if issue == "changed_measurement":
            nr = candidate_review(
                p,
                decisions=[
                    Decision(
                        candidate_id="N001",
                        decision="accept",
                        caliper=Caliper(start_zyx=(0, 3, 3), end_zyx=(0, 3, 7)),
                    )
                ],
            )
        store.approve(key, review, token, nodule_review=nr)
    assert not store.snapshots("synthetic-checklist")


@pytest.mark.parametrize(
    "issue",
    [
        "public",
        "wrong_patient",
        "bad_header",
        "bad_report",
        "unlisted",
        "bad_overlay",
        "bad_source",
    ],
)
def test_unsafe_nodule_archives_rejected(issue):
    def mutate(m, f):
        if issue == "public":
            m["study"]["input_kind"] = "approved-public-research"
        if issue == "wrong_patient":
            m["patient_id"] = "other"
        role = {
            "bad_header": "source_volume",
            "bad_report": "producer_report",
            "bad_overlay": "overlay_preview",
            "bad_source": "source_preview",
        }.get(issue)
        if role:
            a = next(a for a in m["artifacts"] if a["role"] == role)
            if issue == "bad_header":
                out = io.BytesIO()
                np.lib.format.write_array_header_1_0(
                    out,
                    {"descr": "<f4", "fortran_order": False, "shape": (10**9, 12, 12)},
                )
                data = out.getvalue()
            elif issue == "bad_report":
                data = b"Cancer confirmed"
            else:
                out = io.BytesIO()
                Image.fromarray(np.full((12, 12, 3), 73, dtype=np.uint8)).save(
                    out, format="PNG"
                )
                data = out.getvalue()
            f[a["path"]] = data
            a.update(sha256=byte_digest(data), size_bytes=len(data))
        if issue == "unlisted":
            f["surprise.txt"] = b"unlisted"

    with pytest.raises(ValueError):
        validate_bundle(nodule_bytes(mutate=mutate), "synthetic-checklist")


def test_nodule_appendix_is_grounded_separate_from_llm_and_final_review(
    nodule_store, inference, tmp_path
):
    store, token = nodule_store
    approve_nodule(store, token)
    workflow = MedicalHistoryOrchestrator(inference, auth=store.auth)
    case, events = workflow.start_patient("synthetic-checklist", store.path)
    list(events)
    assert not inference.calls
    state = workflow.state(case)
    workflow.acknowledge_safety(
        case,
        Review(
            approved=True,
            reviewer="dr.example",
            clinician_attestation=True,
            notes="Assessed synthetic uncertainty.",
            draft_sha256=state["safety_decision"]["decision_sha256"],
        ),
        token,
    )
    state = workflow.state(case)
    assert "5.00 mm" in state["draft"] and "do not establish malignancy" in state["draft"]
    assert "1" * 64 not in state["draft"]
    assert state["report_evidence"]["ct_studies"][0]["study_id"] == "lung-study"
    assert state["imaging"][0]["manifest"]["study"]["sources"][0]["sha256"] == "1" * 64
    assert state["draft"].count("# ") == 1
    assert "Scripted synthetic unit fixture" not in json.dumps(inference.calls)
    with pytest.raises(ValueError):
        workflow.export(case)
    workflow.review(
        case,
        Review(
            approved=True,
            reviewer="dr.example",
            clinician_attestation=True,
            notes="Checked synthetic combined draft.",
            draft_sha256=digest(state["draft"]),
        ),
        token,
    )
    payload = workflow.export(case)
    assert save_report(
        payload, tmp_path / "reports", auth=store.auth, safety=workflow.safety
    ).exists()
    source = store.preview_path(payload["imaging"][0], "source_volume", None)
    source.write_bytes(b"changed")
    with pytest.raises(ValueError):
        workflow.export(case)
    with pytest.raises(ValueError):
        save_report(
            payload, tmp_path / "reports", auth=store.auth, safety=workflow.safety
        )


def test_old_incomplete_nodule_v1_requires_reexport():
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        z.writestr("nodules.json", "{}")
    with pytest.raises(ValueError, match="re-export"):
        validate_bundle(out.getvalue(), "synthetic-checklist")


def test_urgent_routing_precedes_corrupt_nodule_optional_artifacts(
    nodule_store, inference
):
    from medical_assistant.history_import import HistoryManagement
    from test_imaging import acceptance

    store, token = nodule_store
    snapshot = approve_nodule(store, token)
    manager = HistoryManagement(store.path, auth=store.auth)
    key, proposal = manager.prepare(
        json.dumps(
            {
                "fictional": True,
                "patient_id": "synthetic-checklist",
                "display_name": get_history(
                    "synthetic-checklist", store.path
                ).display_name,
                "entries": [
                    {
                        "id": "nodule-urgent-test",
                        "date": None,
                        "kind": "symptom",
                        "source_type": "documented",
                        "text": "Explicit synthetic warning fixture.",
                        "warning_screen": "present",
                    }
                ],
            }
        ),
        "synthetic-warning.json",
    )
    manager.approve(key, acceptance(proposal), token)
    store.preview_path(snapshot, "source_volume", None).write_bytes(b"changed")
    workflow = MedicalHistoryOrchestrator(inference, auth=store.auth)
    case, events = workflow.start_patient("synthetic-checklist", store.path)
    list(events)
    assert workflow.state(case)["safety_decision"]["state"] == "urgent"
    assert not inference.calls


def test_viewer_verifies_archive_once_and_checks_each_displayed_artifact(
    nodule_store, monkeypatch
):
    store, token = nodule_store
    snapshot = approve_nodule(store, token)
    original = store._verify_directory
    calls = []

    def checked(*args):
        calls.append(True)
        return original(*args)

    monkeypatch.setattr(store, "_verify_directory", checked)
    resolve = store.preview_resolver(snapshot)
    source = resolve("source_preview", 0)
    resolve("overlay_preview", 0)
    resolve("source_volume", None)
    assert len(calls) == 1
    source.write_bytes(b"changed after verification")
    with pytest.raises(ValueError, match="Displayed imaging artifact changed"):
        resolve("source_preview", 0)

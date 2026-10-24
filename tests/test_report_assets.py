"""Verified images/portable reports; all inference and clinician actions here are scripted."""

# Imported pytest fixtures are intentionally reused as test parameters.
# ruff: noqa: F811
import copy
import re

import pytest
from test_nodule_imaging import approve_nodule, nodule_store  # noqa: F401
from test_workflow import pending_draft, review_for

from medical_assistant.models import PatientRecord
from medical_assistant.report_assets import inspection_figures, portable_html
from medical_assistant.workflow import MedicalHistoryOrchestrator


def report_with_ct(store, token, inference):
    approve_nodule(store, token)
    flow = MedicalHistoryOrchestrator(inference, auth=store.auth)
    case, events = flow.start_patient("synthetic-checklist", store.path)
    list(events)
    flow.acknowledge_safety(case, review_for(flow.state(case), safety=True), token)
    return flow, case


def test_portable_report_requires_approval_and_contains_verified_ct_and_note(
    nodule_store, inference
):
    store, token = nodule_store
    flow, case = report_with_ct(store, token, inference)
    state = flow.prepare_report_note(
        case,
        "Scripted reviewer inspected the artificial CT and remaining uncertainty.",
        token,
    )
    with pytest.raises(ValueError, match="approved"):
        portable_html(state, auth=flow.auth, safety=flow.safety)
    figures = inspection_figures(state, store)
    assert len(figures) == 1 and figures[0].source_png.startswith(b"\x89PNG")
    assert figures[0].overlay_png != figures[0].source_png
    assert "non-ML" in figures[0].caption
    flow.review(case, review_for(state), token)
    rendered = portable_html(flow.export(case), auth=flow.auth, safety=flow.safety)
    assert rendered.count("<h1>") == 1 and "<h2>" not in rendered
    assert rendered.count('src="data:image/png;base64,') == 2
    assert "5.00 mm" in rendered and "Scripted reviewer inspected" in rendered
    assert "<script" not in rendered and not re.search(
        r'(src|href)="https?://', rendered
    )
    assert "SHA-256" not in rendered and "Source key" not in rendered
    source = store.preview_path(state["imaging"][0], "source_preview", 0)
    source.write_bytes(b"changed")
    with pytest.raises(ValueError, match="changed"):
        portable_html(flow.state(case), auth=flow.auth, safety=flow.safety)


def test_portable_report_escapes_notes_and_reports_absent_ct(
    record, inference, auth_session
):
    flow, case, token = pending_draft(record, inference, auth_session)
    state = flow.prepare_report_note(
        case, '<script>alert(1)</script><img src="https://example.invalid">', token
    )
    flow.review(case, review_for(state), token)
    page = portable_html(flow.export(case), auth=flow.auth, safety=flow.safety)
    assert "<script>" not in page and "&lt;script&gt;" in page
    assert "No accepted CT study is included" in page
    assert "data:image/png" not in page
    tampered = copy.deepcopy(flow.export(case))
    tampered["report_evidence"]["record_entries"][0]["excerpt"] = "Invented"
    with pytest.raises((ValueError, PermissionError)):
        portable_html(tampered, auth=flow.auth, safety=flow.safety)


def test_zero_candidates_remain_an_inspected_study_without_reassurance(nodule_store):
    from test_nodule_imaging import candidate_review, nodule_bytes

    from medical_assistant.models import Review
    from medical_assistant.nodule_support import imaging_acceptance_digest
    from medical_assistant.report import ct_summary

    store, token = nodule_store
    key, proposal = store.prepare(
        nodule_bytes(no_candidates=True), "synthetic-checklist"
    )
    choices = candidate_review(proposal, decisions=[])
    snapshot = store.approve(
        key,
        Review(
            approved=True,
            reviewer="dr.example",
            clinician_attestation=True,
            notes="Scripted zero-candidate software fixture; no normality conclusion.",
            draft_sha256=imaging_acceptance_digest(proposal, choices),
        ),
        token,
        nodule_review=choices,
    )
    text = ct_summary([snapshot])
    assert "0 candidates proposed" in text and "do not establish a normal CT" in text
    assert "No accepted CT study" not in text and "No reviewer caliper" in text
    figures = inspection_figures(
        {"record": {"patient_id": "synthetic-checklist"}, "imaging": [snapshot]}, store
    )
    assert len(figures) == 1


def test_ct_accepted_later_requires_a_new_report_snapshot(nodule_store, inference):
    store, token = nodule_store
    flow = MedicalHistoryOrchestrator(inference, auth=store.auth)
    old, events = flow.start_patient(
        "synthetic-checklist", store.path, safety_only=True
    )
    list(events)
    approve_nodule(store, token)
    flow.acknowledge_safety(old, review_for(flow.state(old), safety=True), token)
    assert "No accepted CT study is included" in flow.state(old)["draft"]
    fresh, events = flow.start_patient("synthetic-checklist", store.path)
    list(events)
    flow.acknowledge_safety(fresh, review_for(flow.state(fresh), safety=True), token)
    assert "5.00 mm" in flow.state(fresh)["draft"]


def test_legacy_mask_stays_distinct_in_the_portable_report(nodule_store, inference):
    from test_imaging import accepted_imaging

    store, token = nodule_store
    accepted_imaging(store, token)
    flow = MedicalHistoryOrchestrator(inference, auth=store.auth)
    case, events = flow.start_patient("synthetic-checklist", store.path)
    list(events)
    flow.acknowledge_safety(case, review_for(flow.state(case), safety=True), token)
    state = flow.state(case)
    flow.prepare_report_note(case, "", token)  # preview is required
    flow.review(case, review_for(state), token)
    page = portable_html(flow.export(case), auth=flow.auth, safety=flow.safety)
    assert "legacy tissue-mask" in page and "not nodule detections" in page
    assert page.count('src="data:image/png;base64,') == 2
    assert "Reviewed calipers" not in page


def test_same_text_cannot_substitute_another_accepted_ct_after_approval(
    nodule_store, inference, tmp_path
):
    from test_nodule_imaging import candidate_review, nodule_bytes

    from medical_assistant.models import Review
    from medical_assistant.nodule_support import imaging_acceptance_digest
    from medical_assistant.report import compose, evidence_index
    from medical_assistant.storage import save_report

    store, token = nodule_store
    flow, case = report_with_ct(store, token, inference)
    flow.prepare_report_note(case, "", token)  # preview is required
    flow.review(case, review_for(flow.state(case)), token)
    original = flow.export(case)
    key, proposal = store.prepare(
        nodule_bytes(study_id="different-study"), "synthetic-checklist"
    )
    choices = candidate_review(proposal)
    other = store.approve(
        key,
        Review(
            approved=True,
            reviewer="dr.example",
            clinician_attestation=True,
            notes="Scripted second study, never part of the first report approval.",
            draft_sha256=imaging_acceptance_digest(proposal, choices),
        ),
        token,
        nodule_review=choices,
    )
    forged = copy.deepcopy(original)
    forged["imaging"] = [other]
    forged["report_evidence"] = evidence_index(
        PatientRecord.model_validate(forged["record"]), forged["assessments"], [other]
    )
    # Patient/candidate counts/calipers match, so brief visible prose alone cannot distinguish them.
    assert (
        compose(
            PatientRecord.model_validate(forged["record"]),
            forged["source_file"],
            forged["assessments"],
            forged["evidence"],
            [other],
        )
        == original["final_report"]
    )
    with pytest.raises(PermissionError):
        portable_html(forged, auth=flow.auth, safety=flow.safety)
    with pytest.raises(PermissionError):
        save_report(forged, tmp_path / "forged", auth=flow.auth, safety=flow.safety)

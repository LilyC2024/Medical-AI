"""Concise combined reports and signed note previews, with scripted inference/reviewers."""

# Imported pytest fixtures are intentionally reused as test parameters.
# ruff: noqa: F811
import copy

import pytest
from test_nodule_imaging import approve_nodule, nodule_store  # noqa: F401
from test_workflow import pending_draft, review_for

from medical_assistant.report import inline_text
from medical_assistant.storage import save_report
from medical_assistant.workflow import MedicalHistoryOrchestrator


def test_note_is_previewed_before_approval_and_survives_export(
    record, inference, auth_session, tmp_path
):
    flow, case, token = pending_draft(record, inference, auth_session)
    old = flow.state(case)
    before = old["record"]
    note = "Fictional reviewer: reconcile current medicine use before considering these hypotheses."
    with pytest.raises(PermissionError):
        flow.prepare_report_note(case, note)
    updated = flow.prepare_report_note(case, note, token)
    assert inline_text(note) in updated["draft"] and not updated["reviewed"]
    assert updated["record"] == before and len(inference.calls) == 1
    with pytest.raises(ValueError, match="Stale"):
        flow.review(case, review_for(old), token)
    with pytest.raises(ValueError):
        flow.export(case)
    flow.review(case, review_for(updated), token)
    payload = flow.export(case)
    assert inline_text(note) in payload["final_report"]
    assert save_report(
        payload, tmp_path / "reports", auth=flow.auth, safety=flow.safety
    ).exists()
    with pytest.raises(ValueError):
        flow.prepare_report_note(case, "Unapproved later note", token)


@pytest.mark.parametrize("field", ["clinician_note", "note_receipt", "report_evidence"])
def test_tampered_note_or_evidence_cannot_be_saved(
    record, inference, auth_session, tmp_path, field
):
    flow, case, token = pending_draft(record, inference, auth_session)
    state = flow.prepare_report_note(
        case, "Scripted review of fictional uncertainty.", token
    )
    flow.review(case, review_for(state), token)
    payload = copy.deepcopy(flow.export(case))
    if field == "clinician_note":
        payload[field]["text"] = "Forged clinical opinion"
    elif field == "note_receipt":
        payload[field]["signature"] = "f" * 64
    else:
        payload[field]["record_entries"][0]["excerpt"] = "Invented finding"
    with pytest.raises((ValueError, PermissionError)):
        save_report(payload, tmp_path / "reports", auth=flow.auth, safety=flow.safety)
    assert not (tmp_path / "reports").exists()


def test_note_cannot_inject_markdown_or_exceed_brief_limit(
    record, inference, auth_session
):
    flow, case, token = pending_draft(record, inference, auth_session)
    with pytest.raises(ValueError):
        flow.prepare_report_note(case, "x" * 601, token)
    note = "# REVIEWED\n![tracking](https://example.invalid/x)<img src=x>"
    state = flow.prepare_report_note(case, note, token)
    assert "\n# REVIEWED" not in state["draft"] and "![tracking](" not in state["draft"]
    assert "<img" not in state["draft"] and state["draft"].count("\n#") == 0
    assert state["clinician_note"]["text"] == note


def test_ct_inspection_measurements_and_evidence_are_in_combined_report(
    nodule_store, inference, tmp_path
):
    store, token = nodule_store
    accepted = approve_nodule(store, token)
    flow = MedicalHistoryOrchestrator(inference, auth=store.auth)
    case, events = flow.start_patient("synthetic-checklist", store.path)
    list(events)
    flow.acknowledge_safety(case, review_for(flow.state(case), safety=True), token)
    state = flow.state(case)
    assert "CT inspection" in state["draft"] and "1 candidate" in state["draft"]
    assert "5.00 mm" in state["draft"]
    assert (
        state["imaging"][0]["manifest"]["study"]["model"]["synthetic_fixture"] is True
    )
    assert "No accepted CT study" not in state["draft"]
    assert "SHA-256" not in state["draft"] and "Source key" not in state["draft"]
    assert (
        state["report_evidence"]["ct_studies"][0]["archive_sha256"]
        == accepted["archive_sha256"]
    )
    assert len(state["draft"].split()) < 450 and state["draft"].count("# ") == 1
    assert "imaging" not in inference.calls[0][1]
    flow.prepare_report_note(case, "", token)  # preview is required
    flow.review(case, review_for(state), token)
    assert "5.00 mm" in flow.export(case)["final_report"]

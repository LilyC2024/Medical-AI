"""Bind approval to hidden evidence/images as well as simplified visible report text."""

import json

from medical_assistant.report import digest


def content_digest(state):
    """Stable clinical content only; mutable workflow/review bookkeeping is excluded."""
    fields = (
        "draft",
        "record",
        "assessments",
        "evidence",
        "imaging",
        "report_evidence",
        "clinician_note",
        "model",
        "source_file",
        "safety_decision",
        "safety_ack",
        "final_safety_decision",
    )
    return digest(
        json.dumps(
            {
                "format": "lovisa-combined-summary-v1",
                **{key: state.get(key) for key in fields},
            },
            sort_keys=True,
            ensure_ascii=False,
        )
    )


def verify_content_binding(state, receipt, auth, reviewer):
    actor = auth.verify_receipt(
        receipt, "clinical-content:" + state["case_id"], content_digest(state)
    )
    if actor != reviewer:
        raise PermissionError("Report content approval belongs to a different reviewer")

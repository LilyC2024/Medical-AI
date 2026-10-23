"""Authenticate report-note authorship without treating commentary as clinical facts."""

from medical_assistant.models import ReportNote
from medical_assistant.report import digest


def verify_note(state, auth):
    note = state.get("clinician_note")
    receipt = state.get("note_receipt")
    if note is None:
        if receipt:
            raise ValueError("Report-note receipt has no matching note")
        return
    value = ReportNote.model_validate(note)
    actor = auth.verify_receipt(
        receipt, "report-note:" + state["case_id"], digest(value.model_dump_json())
    )
    if actor != value.reviewer:
        raise PermissionError(
            "Report-note author does not match its authenticated receipt"
        )

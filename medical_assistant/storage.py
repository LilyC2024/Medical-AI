"""Read explicitly selected local JSON records; atomically save reviewed reports."""

import json
import os
import tempfile
from pathlib import Path
from uuid import uuid4

from medical_assistant.models import PatientRecord, Review
from medical_assistant.report import digest

ROOT = Path(__file__).resolve().parents[1]
PATIENT_DIR = ROOT / "data" / "patients"
REPORT_DIR = ROOT / "data" / "reports"


def load_record(path: Path) -> PatientRecord:
    if path.stat().st_size > 100_000:
        raise ValueError("Record exceeds the prototype's 100 KB input limit")
    record = PatientRecord.model_validate_json(path.read_text(encoding="utf-8"))
    if sum(len(entry.text) for entry in record.entries) > 24_000:
        raise ValueError("Record is too long for the prototype's bounded model context")
    return record


def save_report(payload: dict, directory: Path = REPORT_DIR, *, auth=None, safety=None) -> Path:
    if auth is None:
        raise ValueError("Authenticated approval verification is required before saving")
    if payload.get("status") != "complete" or not payload.get("reviewed") or not payload.get("approval_receipt") or not payload.get("review", {}).get("approved"):
        raise ValueError("Only clinician-approved final reports may be saved")
    review = Review.model_validate(payload["review"])
    if not review.approved or review.draft_sha256 != digest(payload.get("final_report", "")):
        raise ValueError("Final report does not match clinician approval")
    from medical_assistant.grounding import validate_record_grounding
    from medical_assistant.report import compose
    from medical_assistant.safety import SafetyAgent
    record = validate_record_grounding(PatientRecord.model_validate(payload["record"]))
    actor = auth.verify_receipt(payload["approval_receipt"], "clinical-review:" + payload["case_id"],
                                digest(review.model_dump_json()))
    if actor != review.reviewer:
        raise ValueError("Authenticated reviewer identity mismatch")
    generated = compose(record, payload["source_file"], payload["assessments"], payload["evidence"])
    if payload.get("generated_draft") != generated or payload["final_report"] != generated:
        raise ValueError("Clinical report no longer matches its grounded source snapshot")
    decision = (safety or SafetyAgent()).evaluate(record)
    if decision["decision_sha256"] != payload["safety_decision"]["decision_sha256"] or decision != payload["final_safety_decision"]:
        raise ValueError("Safety policy or records changed before report persistence")
    if decision["state"] == "urgent":
        raise ValueError("Urgent workflow holds cannot be finalized")
    if decision["state"] == "uncertain":
        acknowledgement = Review.model_validate(payload["safety_ack"])
        auth.verify_receipt(payload["safety_receipt"], "safety-review:" + payload["case_id"], digest(acknowledgement.model_dump_json()))
        if not acknowledgement.approved or acknowledgement.draft_sha256 != decision["decision_sha256"]:
            raise ValueError("Safety uncertainty was not acknowledged")
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"report-{uuid4().hex}.json"
    descriptor, temporary = tempfile.mkstemp(prefix=".report-", dir=directory)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return target

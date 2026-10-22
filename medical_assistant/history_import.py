"""Separate history-management workflow: validate → extract → approve → append."""
import json
from uuid import uuid4

from medical_assistant.database import attach_original, get_history, write_synthetic
from medical_assistant.grounding import validate_record_grounding
from medical_assistant.history import MedicalHistoryAgent, MedicationAgent
from medical_assistant.models import PatientRecord, Review
from medical_assistant.report import digest
from medical_assistant.auth import LocalAuth


class HistoryManagement:
    def __init__(self, path, *, auth=None):
        self.path = path
        self.auth = auth or LocalAuth(path)
        self.pending = {}

    def prepare(self, raw: str, filename: str):
        if len(raw.encode()) > 100_000:
            raise ValueError("Import exceeds 100 KB")
        record = attach_original(PatientRecord.model_validate_json(raw), filename, raw)
        validate_record_grounding(record)
        duplicates = []
        try:
            existing = get_history(record.patient_id, self.path)
        except LookupError:
            existing = None
        if existing:
            if existing.display_name != record.display_name:
                raise ValueError("Patient identity conflicts with stored synthetic record")
            old = {entry.id: entry for entry in existing.entries}
            for entry in record.entries:
                if entry.id in old:
                    left = entry.model_dump(exclude={"source_id", "verification_status"})
                    right = old[entry.id].model_dump(exclude={"source_id", "verification_status"})
                    if left != right:
                        raise ValueError("Conflicting encounter ID, date or clinical facts; manual reconciliation required")
                    duplicates.append(entry.id)
            combined = {**old, **{entry.id: entry for entry in record.entries}}
        else:
            combined = {entry.id: entry for entry in record.entries}
        if len(combined) > 100 or sum(len(entry.text) for entry in combined.values()) > 24_000:
            raise ValueError("Cumulative patient history exceeds the prototype limit (100 facts / 24,000 text characters)")
        proposal = {
            "record": record.model_dump(mode="json"), "duplicate_ids": duplicates,
            "history": MedicalHistoryAgent().run(record).model_dump(mode="json"),
            "medications": MedicationAgent().run(record).model_dump(mode="json"),
        }
        proposal_id = uuid4().hex
        proposal["sha256"] = digest(json.dumps(proposal, sort_keys=True))
        self.pending[proposal_id] = json.dumps(proposal)
        return proposal_id, proposal

    def approve(self, proposal_id, review: Review, token=None):
        review = Review.model_validate(review.model_dump())
        if self.auth.require(token) != review.reviewer:
            raise PermissionError("Authenticated clinician must match the import reviewer")
        proposal = json.loads(self.pending[proposal_id])
        if not review.approved or review.draft_sha256 != proposal["sha256"]:
            raise ValueError("Matching explicit human import approval is required")
        record = PatientRecord.model_validate(proposal["record"])
        # Exact duplicate retries are harmless; overlapping bundles append new facts only.
        entries = [entry for entry in record.entries if entry.id not in proposal["duplicate_ids"]]
        if entries:
            data = record.model_dump(mode="json")
            data["entries"] = [entry.model_dump(mode="json") for entry in entries]
            for entry in data["entries"]:
                entry["verification_status"] = "verified"
            write_synthetic(PatientRecord.model_validate(data), self.path, actor=review.reviewer,
                            action="human_approved_import", approval=review.model_dump())
        else:
            self.auth.audit("approved_duplicate_import", record.patient_id, token, review.model_dump())
        del self.pending[proposal_id]
        return get_history(record.patient_id, self.path)

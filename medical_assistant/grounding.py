"""Source grounding for JSON medical imports; no semantic facts are invented."""
import json

from medical_assistant.models import Entry, PatientRecord


def validate_record_grounding(record: PatientRecord):
    if not record.sources:
        raise ValueError("Original sources are required")
    originals = {}
    for source in record.sources:
        payload = json.loads(source.content)
        if not isinstance(payload, dict) or not isinstance(payload.get("entries"), list) or not payload["entries"]:
            raise ValueError("Original source must contain a JSON record object with non-empty entries")
        if payload.get("fictional") is not True or payload.get("patient_id") != record.patient_id:
            raise ValueError("Source patient identity or synthetic-only constraint failed")
        if payload.get("display_name") != record.display_name:
            raise ValueError("Original source display name conflicts with synthetic patient identity")
        entries = [Entry.model_validate(item) for item in payload["entries"]]
        if len({entry.id for entry in entries}) != len(entries):
            raise ValueError("Duplicate entry IDs in original source")
        originals[source.id] = {entry.id: entry for entry in entries}
    for entry in record.entries:
        # A missing source_id finds no original and fails closed just below.
        original = originals.get(entry.source_id, {}).get(entry.id)  # type: ignore[arg-type]
        if original is None:
            raise ValueError("Extracted fact is missing from its original source")
        fields = ("date", "source_type", "kind", "text", "medication", "blood_pressure", "warning_screen")
        if any(getattr(entry, field) != getattr(original, field) for field in fields):
            raise ValueError("Extracted clinical assertion or date is unsupported by its original source")
    return record

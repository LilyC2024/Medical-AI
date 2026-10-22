"""Limited synthetic hypothesis selection, not general clinical reasoning.

The local LLM selects from this transparent catalog. Exact record text remains
untrusted quoted evidence; these constraints do not clinically validate a cause,
identify emergencies, or establish that a selected source supports causation.
"""
import re

from medical_assistant.models import Assessment, PatientRecord

MEDICATION_HYPOTHESIS = "Medication-related contribution"
SLEEP_HYPOTHESIS = "Sleep-related contribution"
OTHER_HYPOTHESIS = "Insufficient information; other causes remain unestablished"
UNCERTAINTY = (
    "This is an unverified hypothesis from a limited synthetic catalog. The supplied records "
    "do not establish a cause, current clinical status or treatment need; clinician verification is required."
)
CONSIDERATIONS = (
    "Clarify symptom onset, duration and pattern.",
    "Review current medications and documented changes without changing treatment.",
    "Clarify sleep timing, duration and shift work.",
    "Obtain current blood-pressure measurements and relevant examination findings for clinician assessment.",
    "Clarify syncope, falls, fluid intake, comorbidities, allergies and current warning signs.",
)
MISSING_INFORMATION = (
    "Current assessment is not supplied.",
    "Current blood-pressure measurements require clinician verification.",
    "Symptom timing and relevant history require clarification.",
)
CLINICIAN_QUESTIONS = (
    "Which additional history and examination findings are needed to assess these hypotheses?",
    "Have the source excerpts, current symptoms and medication history been verified?",
)


def eligible_labels(record: PatientRecord) -> list[str]:
    labels = [OTHER_HYPOTHESIS]
    if any(entry.kind == "medication" or entry.medication is not None for entry in record.entries):
        labels.append(MEDICATION_HYPOTHESIS)
    if any(re.search(r"\bsleep\b", entry.text, re.IGNORECASE) for entry in record.entries):
        labels.append(SLEEP_HYPOTHESIS)
    return labels


def constrain_schema(schema: dict, record: PatientRecord, reference_ids: list[str]) -> dict:
    """Constrain both narrative vocabulary and evidence before generation."""
    # Deleted role fields leave unused Pydantic definitions behind. Removing
    # those saves context for record text without weakening the active schema.
    schema["$defs"] = {key: value for key, value in schema["$defs"].items()
                       if key in {"Claim", "Explanation"}}
    schema["properties"]["findings"]["maxItems"] = 0
    schema["properties"]["explanations"]["minItems"] = 1
    schema["required"] = ["explanations"]
    # Bind quote, attribution and ID together during generation. Independent
    # enums allowed a real model to mix a reported quote with documented status.
    schema["$defs"]["Claim"] = {"anyOf": [{
        "type": "object", "additionalProperties": False,
        "properties": {"kind": {"const": entry.source_type}, "text": {"const": entry.text},
                       "evidence_ids": {"type": "array", "items": {"const": entry.id}, "minItems": 1, "maxItems": 1}},
        "required": ["kind", "text", "evidence_ids"],
    } for entry in record.entries]}
    explanation = schema["$defs"]["Explanation"]["properties"]
    explanation["possibility"]["enum"] = eligible_labels(record)
    explanation["uncertainty"]["const"] = UNCERTAINTY
    explanation["clinician_may_consider"]["items"]["enum"] = list(CONSIDERATIONS)
    if reference_ids:
        explanation["reference_ids"]["items"]["enum"] = reference_ids
    else:
        explanation["reference_ids"]["maxItems"] = 0
    schema["properties"]["missing_information"]["items"]["enum"] = list(MISSING_INFORMATION)
    schema["properties"]["clinician_questions"]["items"]["enum"] = list(CLINICIAN_QUESTIONS)
    return schema


def validate_reasoning(assessment: Assessment, record: PatientRecord, reference_ids: set[str]) -> None:
    """Reject off-catalog model text even if a transport ignores the schema."""
    if assessment.findings or not assessment.explanations:
        raise ValueError("Reasoning requires catalog hypotheses and no additional findings")
    if any(item not in MISSING_INFORMATION for item in assessment.missing_information):
        raise ValueError("Reasoning returned off-catalog missing information")
    if any(item not in CLINICIAN_QUESTIONS for item in assessment.clinician_questions):
        raise ValueError("Reasoning returned an off-catalog clinician question")
    entries = {entry.id: entry for entry in record.entries}
    labels = eligible_labels(record)
    for explanation in assessment.explanations:
        if explanation.possibility not in labels or explanation.uncertainty != UNCERTAINTY:
            raise ValueError("Reasoning returned an ineligible hypothesis or off-catalog uncertainty")
        if any(item not in CONSIDERATIONS for item in explanation.clinician_may_consider):
            raise ValueError("Reasoning returned an off-catalog consideration")
        if any(ref not in reference_ids for ref in explanation.reference_ids):
            raise ValueError("Model invented or used an unapproved medical reference")
        for claim in explanation.supporting + explanation.conflicting:
            if claim.kind == "hypothesis" or any(
                entry_id not in entries or claim.text != entries[entry_id].text
                for entry_id in claim.evidence_ids
            ):
                raise ValueError("Reasoning evidence must be exact complete text from every cited entry")

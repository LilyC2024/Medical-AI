"""Adversarial validation of the limited synthetic hypothesis selector."""
import pytest

from medical_assistant.agents import SpecialistAgent
from medical_assistant.models import Assessment, PatientRecord
from medical_assistant.reasoning_constraints import (
    CLINICIAN_QUESTIONS, CONSIDERATIONS, MEDICATION_HYPOTHESIS, MISSING_INFORMATION,
    OTHER_HYPOTHESIS, SLEEP_HYPOTHESIS, UNCERTAINTY, eligible_labels,
)


def output_for(record):
    entry = record.entries[-1]
    return {
        "explanations": [{"possibility": OTHER_HYPOTHESIS, "status": "hypothesis",
            "supporting": [{"kind": entry.source_type, "text": entry.text, "evidence_ids": [entry.id]}],
            "conflicting": [], "uncertainty": UNCERTAINTY, "clinician_may_consider": [CONSIDERATIONS[0]],
            "reference_ids": []}],
        "missing_information": [MISSING_INFORMATION[0]], "clinician_questions": [CLINICIAN_QUESTIONS[0]],
    }


class Scripted:
    def __init__(self, payload):
        self.payload = payload
        self.schema = None

    def assess(self, system, user, *, schema):
        self.schema = schema
        return Assessment.model_validate(self.payload)


def test_schema_constrains_every_reasoning_narrative_field(record):
    scripted = Scripted(output_for(record))
    result = SpecialistAgent("reasoning", scripted).run(record, {})
    schema = scripted.schema
    assert result["findings"] == []
    assert schema["properties"]["findings"]["maxItems"] == 0
    assert schema["properties"]["explanations"]["minItems"] == 1
    explanation = schema["$defs"]["Explanation"]["properties"]
    assert explanation["possibility"]["enum"] == eligible_labels(record)
    assert explanation["uncertainty"]["const"] == UNCERTAINTY
    assert explanation["reference_ids"]["maxItems"] == 0
    assert {item["properties"]["text"]["const"] for item in schema["$defs"]["Claim"]["anyOf"]} == {e.text for e in record.entries}


def test_generation_schema_binds_source_text_id_and_attribution(record):
    import jsonschema
    scripted = Scripted(output_for(record))
    SpecialistAgent("reasoning", scripted).run(record, {})
    contract = scripted.schema["$defs"]["Claim"]
    entry = record.entries[-1]
    valid = {"kind": entry.source_type, "text": entry.text, "evidence_ids": [entry.id]}
    jsonschema.validate(valid, contract)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({**valid, "kind": "documented"}, contract)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({**valid, "evidence_ids": [record.entries[0].id]}, contract)


@pytest.mark.parametrize("field,value", [
    ("possibility", "Blood pressure measured 120/80"),
    ("uncertainty", "The patient has normal blood pressure."),
    ("clinician_may_consider", ["Stop all medications immediately."]),
    ("reference_ids", ["invented-reference"]),
])
def test_schema_ignoring_model_cannot_emit_unrestricted_explanation_text(record, field, value):
    payload = output_for(record)
    payload["explanations"][0][field] = value
    with pytest.raises(ValueError):
        SpecialistAgent("reasoning", Scripted(payload)).run(record, {})


@pytest.mark.parametrize("field,value", [
    ("missing_information", ["Blood pressure is normal at 120/80."]),
    ("clinician_questions", ["Discontinue medication now."]),
    ("findings", [{"kind": "hypothesis", "text": "Unsupported additional finding", "evidence_ids": ["report-2025-03-10"]}]),
    ("explanations", []),
])
def test_schema_ignoring_model_cannot_emit_unrestricted_top_level_text(record, field, value):
    payload = output_for(record)
    payload[field] = value
    with pytest.raises(ValueError):
        SpecialistAgent("reasoning", Scripted(payload)).run(record, {})


def test_evidence_cannot_be_shortened_or_linked_to_unrelated_entry(record):
    payload = output_for(record)
    claim = payload["explanations"][0]["supporting"][0]
    claim["text"] = record.entries[-1].text[:20]
    with pytest.raises(ValueError, match="complete text"):
        SpecialistAgent("reasoning", Scripted(payload)).run(record, {})
    claim["text"] = record.entries[-1].text
    claim["evidence_ids"].append(record.entries[0].id)
    # The second entry has a different source_type, which also fails closed.
    with pytest.raises(ValueError):
        SpecialistAgent("reasoning", Scripted(payload)).run(record, {})


def test_catalog_eligibility_is_transparent_and_conservative(record):
    assert set(eligible_labels(record)) == {OTHER_HYPOTHESIS, SLEEP_HYPOTHESIS, MEDICATION_HYPOTHESIS}
    payload = record.model_dump(mode="json", exclude={"sources"})
    payload["entries"] = [{"id": "symptom", "date": None, "source_type": "patient_reported", "kind": "symptom", "text": "Tiredness reported."}]
    sparse = PatientRecord.model_validate(payload)
    assert eligible_labels(sparse) == [OTHER_HYPOTHESIS]
    for label in (MEDICATION_HYPOTHESIS, SLEEP_HYPOTHESIS):
        output = output_for(sparse)
        output["explanations"][0]["possibility"] = label
        with pytest.raises(ValueError, match="ineligible"):
            SpecialistAgent("reasoning", Scripted(output)).run(sparse, {})


def test_only_retrieved_approved_reference_ids_are_accepted(record):
    payload = output_for(record)
    payload["explanations"][0]["reference_ids"] = ["approved-fixture"]
    scripted = Scripted(payload)
    result = SpecialistAgent("reasoning", scripted).run(record, {}, [{"id": "approved-fixture"}])
    assert result["explanations"][0]["reference_ids"] == ["approved-fixture"]
    assert scripted.schema["$defs"]["Explanation"]["properties"]["reference_ids"]["items"]["enum"] == ["approved-fixture"]

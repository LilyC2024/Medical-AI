import pytest

from medical_assistant.agents import SpecialistAgent
from medical_assistant.models import Assessment
from medical_assistant.reasoning_constraints import OTHER_HYPOTHESIS, UNCERTAINTY, CONSIDERATIONS


@pytest.mark.parametrize("role,allowed", [
    ("history", {"findings", "missing_information", "clinician_questions"}),
    ("medications", {"findings", "medications", "missing_information", "clinician_questions"}),
    ("reasoning", {"findings", "explanations", "missing_information", "clinician_questions"}),
    ("safety", {"findings", "safety_flags", "missing_information", "clinician_questions"}),
])
def test_each_agent_sends_its_own_schema(record, role, allowed):
    class Capture:
        def assess(self, system, user, *, schema):
            assert set(schema["properties"]) == allowed
            assert schema["additionalProperties"] is False
            if role == "reasoning":
                return Assessment(explanations=[{"possibility": OTHER_HYPOTHESIS,
                    "supporting": [{"kind": record.entries[0].source_type, "text": record.entries[0].text, "evidence_ids": [record.entries[0].id]}],
                    "conflicting": [], "uncertainty": UNCERTAINTY, "clinician_may_consider": [CONSIDERATIONS[0]]}])
            return Assessment(missing_information=["Current assessment is not supplied."])
    SpecialistAgent(role, Capture()).run(record, {})


def test_empty_and_out_of_role_responses_fail(record):
    class Empty:
        def assess(self, *args, **kwargs):
            return Assessment()
    with pytest.raises(ValueError, match="empty assessment"):
        SpecialistAgent("safety", Empty()).run(record, {})

    class WrongRole:
        def assess(self, *args, **kwargs):
            return Assessment(safety_flags=[{"urgency": "unknown", "text": "Current status unknown.",
                              "evidence_ids": ["report-2025-03-10"], "escalation": "Clinician review required."}])
    with pytest.raises(ValueError, match="out-of-role"):
        SpecialistAgent("history", WrongRole()).run(record, {})

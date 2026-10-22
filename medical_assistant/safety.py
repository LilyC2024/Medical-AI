"""Deterministic safety agent. No model response can modify this policy result."""
import json
from datetime import date, datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Literal

from pydantic import Field

from medical_assistant.models import Assessment, PatientRecord, SafetyFlag, StrictModel
from medical_assistant.report import digest
from medical_assistant.storage import ROOT

POLICY_PATH = ROOT / "config" / "safety_policy.json"


class SafetyPolicy(StrictModel):
    version: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    require_current_warning_screen: Literal[True]
    require_current_blood_pressure: Literal[True]
    screen_max_age_days: int = Field(ge=0, le=1)
    reported_warning_action: Literal["urgent_human_review_stop"]
    missing_information_action: Literal["uncertain_human_review_pause"]
    model_may_override: Literal[False]


class SafetyAgent:
    def __init__(self, policy_path: Path = POLICY_PATH):
        self.policy_path = policy_path

    def evaluate(self, record: PatientRecord, *, as_of: date | None = None):
        as_of = as_of or datetime.now(ZoneInfo("Europe/Amsterdam")).date()
        raw = self.policy_path.read_text()
        policy = SafetyPolicy.model_validate_json(raw)
        scope_ids = [entry.id for entry in record.entries]
        current = [entry for entry in record.entries if entry.date and 0 <= (as_of - entry.date).days <= policy.screen_max_age_days]
        flags, missing = [], []
        # Explicit reported warning signs cannot be overwritten by another entry,
        # model reassurance or a human 'continue' command in the same case.
        warnings = [entry.id for entry in record.entries if entry.warning_screen == "present"]
        if warnings:
            flags.append(SafetyFlag(urgency="urgent", text="An explicit warning-sign report requires immediate human assessment; automated reasoning is stopped.",
                         evidence_ids=warnings, escalation="Human review required. This is a workflow hold, not an automated emergency diagnosis."))
        screening_known = any(entry.warning_screen == "absent" for entry in current)
        screening_unknown = any(entry.warning_screen == "unknown" for entry in current)
        if not screening_known or screening_unknown:
            missing.append("Current warning-sign screening is unavailable or uncertain.")
        if not any(entry.blood_pressure is not None for entry in current):
            missing.append("Current blood-pressure measurements are unavailable; no normal value may be inferred.")
        if missing:
            flags.append(SafetyFlag(urgency="unknown", text=" ".join(missing), evidence_ids=scope_ids,
                         escalation="Pause for an authenticated clinician to assess the missing information before any reasoning."))
        state = "urgent" if warnings else "uncertain" if missing else "ordinary_eligible"
        assessment = Assessment(safety_flags=flags, missing_information=missing,
            clinician_questions=["Assess the current warning-sign history and blood pressure; the prototype cannot establish clinical safety."])
        result = {
            "state": state, "policy_version": policy.version, "policy_sha256": digest(raw),
            "record_sha256": digest(record.model_dump_json()), "as_of": as_of.isoformat(),
            "assessment": assessment.model_dump(mode="json"),
            "meaning": "Workflow routing only; ordinary_eligible does not mean the patient is clinically safe.",
        }
        result["decision_sha256"] = digest(json.dumps(result, sort_keys=True))
        return result

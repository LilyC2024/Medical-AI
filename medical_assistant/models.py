"""Validated record, specialist output, and human review contracts."""

from datetime import date as Date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class MedicationOrder(StrictModel):
    name: str = Field(min_length=1)
    dose: str = Field(min_length=1)
    frequency: str = Field(min_length=1)


class BloodPressure(StrictModel):
    systolic: float = Field(gt=0, allow_inf_nan=False)
    diastolic: float = Field(gt=0, allow_inf_nan=False)
    unit: Literal["mmHg"] = "mmHg"


class SourceDocument(StrictModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)
    id: str = Field(min_length=1)
    filename: str = Field(min_length=1)
    date: Date | None = None
    content: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    verification_status: Literal["unverified", "verified"] = "unverified"

    @model_validator(mode="after")
    def valid_digest(self):
        import hashlib

        if hashlib.sha256(self.content.encode()).hexdigest() != self.sha256:
            raise ValueError("Original source content does not match its digest")
        return self


class Entry(StrictModel):
    id: str = Field(min_length=1)
    date: Date | None = None
    source_type: Literal["documented", "patient_reported"]
    kind: Literal["encounter", "diagnosis", "symptom", "procedure", "lab", "medication"]
    text: str = Field(min_length=1, max_length=8000)
    source_id: str | None = None
    verification_status: Literal["unverified", "verified"] = "unverified"
    medication: MedicationOrder | None = None
    blood_pressure: BloodPressure | None = None
    warning_screen: Literal["present", "absent", "unknown"] | None = None


class PatientRecord(StrictModel):
    fictional: Literal[True]
    patient_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    display_name: str = Field(min_length=1)
    entries: list[Entry] = Field(min_length=1, max_length=100)
    sources: list[SourceDocument] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_ids(self):
        ids = [entry.id for entry in self.entries]
        if len(ids) != len(set(ids)):
            raise ValueError("Source entry IDs must be unique")
        source_ids = [source.id for source in self.sources]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("Original source IDs must be unique")
        if self.sources and any(
            entry.source_id not in source_ids for entry in self.entries
        ):
            raise ValueError("Every extracted fact must reference an original source")
        return self


class Claim(StrictModel):
    kind: Literal["documented", "patient_reported", "hypothesis"]
    text: str = Field(min_length=1)
    evidence_ids: list[str] = Field(min_length=1)


class Medication(StrictModel):
    name: str = Field(min_length=1)
    dose: str | None = None
    frequency: str | None = None
    source_type: Literal["documented", "patient_reported"]
    evidence_ids: list[str] = Field(min_length=1)
    reconciliation_question: str = Field(min_length=1)


class DoseChange(StrictModel):
    name: str
    previous_dose: str
    documented_dose: str
    date: Date
    evidence_ids: list[str] = Field(min_length=2)
    interpretation: Literal[
        "documented change; current use requires reconciliation"
    ] = "documented change; current use requires reconciliation"


class Explanation(StrictModel):
    status: Literal["hypothesis"] = "hypothesis"
    possibility: str = Field(min_length=1)
    supporting: list[Claim] = Field(min_length=1)
    conflicting: list[Claim]
    uncertainty: str = Field(min_length=1)
    clinician_may_consider: list[str] = Field(min_length=1)
    reference_ids: list[str] = Field(default_factory=list)

    @field_validator("possibility")
    @classmethod
    def no_confirmed_diagnosis(cls, value):
        import re

        if re.search(r"\b(confirmed|definitive|proven)\b|diagnosed with", value, re.I):
            raise ValueError("Diagnostic considerations must remain hypotheses")
        return value


class SafetyFlag(StrictModel):
    urgency: Literal["urgent", "prompt", "unknown"]
    text: str = Field(min_length=1)
    evidence_ids: list[str] = Field(min_length=1)
    escalation: str = Field(min_length=1)


class Assessment(StrictModel):
    findings: list[Claim] = Field(default_factory=list)
    medications: list[Medication] = Field(default_factory=list)
    dose_changes: list[DoseChange] = Field(default_factory=list)
    known_dates: dict[str, Date] = Field(default_factory=dict)
    missing_dates: list[str] = Field(default_factory=list)
    explanations: list[Explanation] = Field(default_factory=list)
    safety_flags: list[SafetyFlag] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    clinician_questions: list[str] = Field(default_factory=list)

    def validate_sources(self, record: PatientRecord) -> "Assessment":
        sources = {entry.id: entry for entry in record.entries}

        def check(ids, source_type=None):
            if any(source_id not in sources for source_id in ids):
                raise ValueError("Specialist returned an unknown source ID")
            if source_type and any(sources[i].source_type != source_type for i in ids):
                raise ValueError(
                    "Specialist confused documented and patient-reported evidence"
                )

        claims = list(self.findings)
        for explanation in self.explanations:
            if not explanation.supporting:
                raise ValueError(
                    "Each diagnostic possibility needs supporting evidence"
                )
            claims.extend(explanation.supporting + explanation.conflicting)
        for claim in claims:
            check(
                claim.evidence_ids, None if claim.kind == "hypothesis" else claim.kind
            )
            if claim.kind != "hypothesis" and not any(
                claim.text in sources[i].text for i in claim.evidence_ids
            ):
                raise ValueError(
                    "Unsupported clinical-record assertion: factual text must be an exact source excerpt"
                )
        for explanation in self.explanations:
            if any(
                item.kind == "hypothesis"
                for item in explanation.supporting + explanation.conflicting
            ):
                raise ValueError(
                    "Hypotheses cannot be presented as supporting or conflicting facts"
                )
        for medication in self.medications:
            check(medication.evidence_ids, medication.source_type)
            orders = [
                sources[i].medication
                for i in medication.evidence_ids
                if sources[i].medication
            ]
            if not any(
                (order.name.casefold(), order.dose, order.frequency)
                == (medication.name.casefold(), medication.dose, medication.frequency)
                for order in orders
            ):
                raise ValueError(
                    "Unsupported medication name, dose or frequency in cited source orders"
                )
        for flag in self.safety_flags:
            check(flag.evidence_ids)
        for change in self.dose_changes:
            check(change.evidence_ids, "documented")
            entries = [sources[i] for i in change.evidence_ids]
            old = [
                entry
                for entry in entries
                if entry.medication
                and entry.medication.name.casefold() == change.name.casefold()
                and entry.medication.dose == change.previous_dose
                and entry.date
                and entry.date < change.date
            ]
            new = [
                entry
                for entry in entries
                if entry.medication
                and entry.medication.name.casefold() == change.name.casefold()
                and entry.medication.dose == change.documented_dose
                and entry.date == change.date
            ]
            if not old or not new or change.previous_dose == change.documented_dose:
                raise ValueError(
                    "Unsupported dose change or date in cited source orders"
                )
        for entry_id, known_date in self.known_dates.items():
            check([entry_id])
            if sources[entry_id].date != known_date:
                raise ValueError("Invented or conflicting encounter date")
        for entry_id in self.missing_dates:
            check([entry_id])
            if sources[entry_id].date is not None:
                raise ValueError("Known date incorrectly labeled missing")
        return self


class Review(StrictModel):
    approved: bool = Field(strict=True)
    reviewer: str = Field(min_length=2, max_length=120)
    clinician_attestation: bool = Field(strict=True)
    draft_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    notes: str = Field(default="", max_length=8000)

    @field_validator("clinician_attestation")
    @classmethod
    def must_attest(cls, value):
        if not value:
            raise ValueError(
                "A clinician must attest to reviewing the report and sources"
            )
        return value


class ReportNote(StrictModel):
    """An attributed reviewer comment, separate from record facts and model output."""

    reviewer: str = Field(min_length=2, max_length=120)
    text: str = Field(max_length=600)

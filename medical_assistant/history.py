"""Extractive history and medication agents for typed synthetic source records."""
from collections import defaultdict
from datetime import date

from langchain_core.runnables import RunnableLambda

from medical_assistant.models import Assessment, Claim, DoseChange, Medication, PatientRecord


def chronology(entry):
    return (entry.date is None, entry.date or date.max, entry.id)


class MedicalHistoryAgent:
    def run(self, record: PatientRecord) -> Assessment:
        def extract(record):
            missing = [entry.id for entry in record.entries if entry.date is None]
            by_content = defaultdict(list)
            for entry in record.entries:
                by_content[(entry.date, entry.kind, entry.source_type, entry.text.casefold())].append(entry.id)
            duplicates = [ids for ids in by_content.values() if len(ids) > 1]
            return Assessment(
                findings=[Claim(kind=entry.source_type, text=entry.text, evidence_ids=[entry.id])
                          for entry in sorted(record.entries, key=chronology)],
                known_dates={entry.id: entry.date for entry in record.entries if entry.date},
                missing_dates=missing,
                missing_information=[f"Date unavailable for {entry_id}; chronological placement is unknown." for entry_id in missing]
                    + [f"Possible duplicate source entries {', '.join(ids)}; clinician must reconcile whether these describe the same event. All original entries are preserved." for ids in duplicates],
                clinician_questions=["Verify source facts and resolve any undated entries before updating history."],
            ).validate_sources(record)
        return RunnableLambda(extract).invoke(record)


class MedicationAgent:
    def run(self, record: PatientRecord) -> Assessment:
        def extract(record):
            medications, changes, missing = [], [], []
            by_name = defaultdict(list)
            for entry in sorted(record.entries, key=chronology):
                if entry.medication:
                    order = entry.medication
                    medications.append(Medication(name=order.name, dose=order.dose,
                        frequency=order.frequency, source_type=entry.source_type, evidence_ids=[entry.id],
                        reconciliation_question="Confirm current use, dose, frequency and adherence; this is a historical source entry."))
                    if entry.source_type == "documented" and entry.date:
                        by_name[order.name.casefold()].append(entry)
                    elif not entry.date:
                        missing.append(f"Medication date unavailable for {entry.id}; do not infer a dose-change sequence.")
                elif entry.kind == "medication":
                    missing.append(f"Structured dose/frequency unavailable for {entry.id}; requires human extraction from the source.")
            for entries in by_name.values():
                # Ambiguous same-date ordering never becomes a directional change.
                if len({entry.date for entry in entries}) != len(entries):
                    missing.append(f"Conflicting or multiple same-date orders for {entries[0].medication.name}; reconcile their sequence.")
                    continue
                for previous, current in zip(entries, entries[1:]):
                    if previous.medication.dose != current.medication.dose:
                        changes.append(DoseChange(name=current.medication.name, previous_dose=previous.medication.dose,
                            documented_dose=current.medication.dose, date=current.date, evidence_ids=[previous.id, current.id]))
            if not medications:
                missing.append("No structured medication orders available; current medication list requires reconciliation.")
            return Assessment(medications=medications, dose_changes=changes, missing_information=missing,
                              clinician_questions=["Does the documented medication history match actual current use?"]).validate_sources(record)
        return RunnableLambda(extract).invoke(record)

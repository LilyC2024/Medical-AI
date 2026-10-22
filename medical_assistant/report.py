"""Deterministic seven-section composition; citations never come from model text."""

import hashlib
import html
import re

from medical_assistant.models import Assessment, PatientRecord

NOTICE = "Educational and experimental fictional case. Not a diagnostic device. All clinical conclusions require clinician verification."


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def inline_text(value) -> str:
    """Render untrusted data as one literal Markdown line, never active markup.

    Original quotations remain untouched in source storage. Presentation folds
    whitespace so a record cannot add headings, lists or reference definitions.
    Ordinary filename underscores stay readable; intraword underscores cannot
    open CommonMark emphasis. HTML, links, images and code delimiters are escaped.
    """
    text = html.escape(" ".join(str(value).split()), quote=True)
    text = re.sub(r"([\\`*\[\]{}()!#|~:])", r"\\\1", text)
    return re.sub(r"(?<!\w)_|_(?!\w)", r"\\_", text)


def compose(record: PatientRecord, source_file: str, outputs: dict[str, dict], evidence=None) -> str:
    sources = {entry.id: entry for entry in record.entries}
    assessments = {role: Assessment.model_validate(value).validate_sources(record)
                   for role, value in outputs.items()}

    def cite(ids):
        documents = {source.id: source for source in record.sources}
        return "; ".join(f"[{inline_text(documents[sources[i].source_id].filename if sources[i].source_id in documents else source_file)} | "
                         f"{sources[i].date.isoformat() if sources[i].date else 'date unavailable'} | {inline_text(i)}]" for i in ids)

    def claim(item):
        return f"- **{item.kind}**: {inline_text(item.text)} {cite(item.evidence_ids)}"

    lines = ["# Clinical report", NOTICE, "", f"Fictional patient: {inline_text(record.display_name)} ({inline_text(record.patient_id)})",
             "", "## 1. Medical history timeline"]
    from medical_assistant.history import chronology
    for entry in sorted(record.entries, key=chronology):
        lines.append(f"- {entry.date or 'Date unavailable — not placed in chronology'} — **{entry.source_type}**, {entry.kind}: {inline_text(entry.text)} {cite([entry.id])}")
    lines += ["", "## 2. Current clinical summary",
              "Historical entries may not reflect current status. Model interpretations below are unverified."]
    findings = [item for role in ("history", "medications", "reasoning", "safety")
                for item in assessments[role].findings]
    lines.extend(claim(item) for item in findings)
    if not findings:
        lines.append("No additional summary extracted; review the source timeline.")
    lines += ["", "## 3. Medication overview",
              "Historical and reported medication entries require reconciliation; no treatment changes are recommended."]
    for item in assessments["medications"].medications:
        lines.append(f"- **{inline_text(item.name)}** ({item.source_type}): dose {inline_text(item.dose or 'not supplied')}; "
                     f"frequency {inline_text(item.frequency or 'not supplied')}. {cite(item.evidence_ids)} "
                     f"Reconciliation question: {inline_text(item.reconciliation_question)}")
    if not assessments["medications"].medications:
        lines.append("No medication list extracted; current treatment remains unverified.")
    for change in assessments["medications"].dose_changes:
        lines.append(f"- **Documented dose change**: {inline_text(change.name)}, {inline_text(change.previous_dose)} → {inline_text(change.documented_dose)} on {change.date}. "
                     f"{cite(change.evidence_ids)} Historical record only; current use requires reconciliation.")
    lines += ["", "## 4. Possible diagnostic explanations and evidence"]
    for item in assessments["reasoning"].explanations:
        lines += [f"### Hypothesis: {inline_text(item.possibility)}", "Supporting evidence:"]
        lines.extend(claim(evidence) for evidence in item.supporting)
        lines.append("Conflicting evidence:")
        lines.extend(claim(evidence) for evidence in item.conflicting)
        if not item.conflicting:
            lines.append("- No conflicting evidence identified in supplied records; this does not confirm the hypothesis.")
        lines.append(f"Uncertainty: {inline_text(item.uncertainty)}")
        lines.append("Clinician may consider:")
        lines.extend(f"- {inline_text(test)}" for test in item.clinician_may_consider)
    if not assessments["reasoning"].explanations:
        lines.append("Insufficient evidence to propose an explanation; clinician assessment required.")
    lines.append("Approved local evidence:")
    for item in evidence or []:
        lines.append(f"- [{inline_text(item['id'])}] {inline_text(item['title'])} — local file {inline_text(item['path'])}; SHA-256 {inline_text(item['sha256'])}")
    if not evidence:
        lines.append("- No approved local references retrieved. Diagnostic hypotheses lack verified reference support and require clinician review.")
    lines += ["", "## 5. Missing information"]
    for item in dict.fromkeys(item for assessment in assessments.values() for item in assessment.missing_information):
        lines.append(f"- {inline_text(item)}")
    lines.append("- Verify present symptoms, current observations, allergies, medication reconciliation and current safety status.")
    if not any(entry.blood_pressure for entry in record.entries):
        lines.append("- Blood-pressure measurements are unavailable in the supplied record; do not infer normal blood pressure.")
    else:
        lines.append("- Confirm whether the supplied blood-pressure measurements reflect the current symptoms.")
        for entry in record.entries:
            if entry.blood_pressure:
                lines.append(f"- Supplied blood pressure: {entry.blood_pressure.systolic:g}/{entry.blood_pressure.diastolic:g} mmHg. {cite([entry.id])}")
    lines.append("- Confirm symptom onset/date, relation to medication changes, syncope/falls history, fluid intake, comorbidities and current warning signs.")
    lines += ["", "## 6. Safety flags",
              "This prototype cannot rule out an emergency. If an emergency warning sign is present now, seek urgent professional help immediately; do not wait for a report."]
    for item in assessments["safety"].safety_flags:
        lines.append(f"- **{item.urgency.upper()}**: {inline_text(item.text)} {cite(item.evidence_ids)} Action: {inline_text(item.escalation)}")
    lines += ["", "## 7. Questions for clinician review"]
    for item in dict.fromkeys(item for assessment in assessments.values() for item in assessment.clinician_questions):
        lines.append(f"- {inline_text(item)}")
    lines.append("- Have all record-derived claims, hypotheses, safety flags and medication discrepancies been checked against the sources?")
    return "\n".join(lines) + "\n"

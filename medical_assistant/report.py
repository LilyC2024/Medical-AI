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


def compose(
    record: PatientRecord,
    source_file: str,
    outputs: dict[str, dict],
    evidence=None,
    imaging=None,
) -> str:
    """Quote each source once; use compact evidence keys elsewhere, retaining all seven sections."""
    from medical_assistant.history import chronology

    entries = sorted(record.entries, key=chronology)
    keys = {e.id: f"S{i + 1}" for i, e in enumerate(entries)}
    documents = {s.id: s for s in record.sources}
    assessments = {
        role: Assessment.model_validate(value).validate_sources(record)
        for role, value in outputs.items()
    }

    def refs(ids):
        return " ".join(f"[{keys[i]}]" for i in dict.fromkeys(ids))

    def unique(values):
        return list(dict.fromkeys(values))

    lines = [
        "# Clinical report",
        NOTICE,
        "",
        f"Fictional patient: {inline_text(record.display_name)} ({inline_text(record.patient_id)})",
        "",
        "## 1. Medical history timeline",
    ]
    for e in entries:
        lines.append(
            f"- [{keys[e.id]}] {e.date or 'Date unavailable'} · **{e.source_type}** · {e.kind}: {inline_text(e.text)}"
        )
    symptom_refs = refs([e.id for e in entries if e.kind == "symptom"])
    lines += [
        "",
        "## 2. Current clinical summary",
        f"Supplied symptom history: {symptom_refs or 'not supplied'}. No current cause is established.",
        "Source history only; current status remains unverified. See the timeline and outstanding questions below.",
        "",
        "## 3. Medication overview",
        "Historical orders; reconcile current use. No treatment changes recommended.",
    ]
    for item in assessments["medications"].medications:
        lines.append(
            f"- {inline_text(item.name)} {inline_text(item.dose or 'dose unavailable')} · {inline_text(item.frequency or 'frequency unavailable')} ({item.source_type}). {refs(item.evidence_ids)}"
        )
    if not assessments["medications"].medications:
        lines.append("- No structured medication list supplied.")
    for c in assessments["medications"].dose_changes:
        lines.append(
            f"- **Documented dose change**: {inline_text(c.name)} {inline_text(c.previous_dose)} → {inline_text(c.documented_dose)} on {c.date}. {refs(c.evidence_ids)}"
        )
    lines += ["", "## 4. Possible diagnostic explanations and evidence"]
    explanations = assessments["reasoning"].explanations
    for item in explanations:
        support = [i for c in item.supporting for i in c.evidence_ids]
        conflict = [i for c in item.conflicting for i in c.evidence_ids]
        lines += [
            f"### Hypothesis: {inline_text(item.possibility)}",
            f"Support: {refs(support)}. Conflict: {refs(conflict) if conflict else 'none supplied; absence does not confirm a cause'}.",
        ]
    if not explanations:
        lines.append("Insufficient evidence to propose an explanation.")
    for text in unique(item.uncertainty for item in explanations):
        lines.append(inline_text(text))
    if evidence:
        for item in evidence:
            lines.append(
                f"- Approved reference [{inline_text(item['id'])}]: {inline_text(item['title'])} · {inline_text(item['path'])} · SHA-256 {inline_text(item['sha256'])}."
            )
    else:
        lines.append(
            "No approved local references retrieved; hypotheses lack verified reference support."
        )
    lines += ["", "## 5. Missing information"]
    missing = unique(x for a in assessments.values() for x in a.missing_information)
    lines += [f"- {inline_text(x)}" for x in missing]
    if not any(e.blood_pressure for e in entries):
        lines.append(
            "- Blood-pressure measurements are unavailable; do not infer normal values."
        )
    else:
        for e in entries:
            if e.blood_pressure:
                lines.append(
                    f"- Historical BP {e.blood_pressure.systolic:g}/{e.blood_pressure.diastolic:g} mmHg; verify current relevance. {refs([e.id])}"
                )
    lines.append(
        "- Clarify symptom timing, syncope/falls, fluid intake, comorbidities, allergies and current warning signs."
    )
    lines += [
        "",
        "## 6. Safety flags",
        "This prototype cannot exclude an emergency. Current warning signs require urgent professional assessment; do not wait for this report.",
    ]
    for f in assessments["safety"].safety_flags:
        lines.append(
            f"- **{f.urgency.upper()}**: {inline_text(f.text)} {refs(f.evidence_ids)} Action: {inline_text(f.escalation)}"
        )
    lines += ["", "## 7. Questions for clinician review"]
    questions = unique(
        [x for a in assessments.values() for x in a.clinician_questions]
        + [x for item in explanations for x in item.clinician_may_consider]
    )
    lines += [f"- {inline_text(x)}" for x in questions]
    lines += [
        "- Verify sources, hypotheses, current medicines and unresolved safety information.",
        "",
        "### Source key",
    ]
    for e in entries:
        name = (
            documents[e.source_id].filename if e.source_id in documents else source_file
        )
        lines.append(
            f"- [{keys[e.id]}] [{inline_text(name)} | {e.date.isoformat() if e.date else 'date unavailable'} | {inline_text(e.id)}]"
        )
    if imaging:
        lines += imaging_appendix(imaging)
    return "\n".join(lines) + "\n"


def imaging_appendix(imaging):
    """Brief reviewed result; full source/model/review metadata remains in the JSON export."""
    from medical_assistant.imaging_results import summarize
    from medical_assistant.nodule_support import verify_nodule_snapshot

    lines = [
        "",
        "### Research imaging appendix",
        "Accepted synthetic artifacts, not confirmed clinical findings. Imaging is excluded from LLM reasoning.",
    ]
    for snapshot in imaging:
        manifest = snapshot["manifest"]
        review = (
            verify_nodule_snapshot(snapshot)
            if manifest.get("schema_version") == "mhcra-lung-nodules-v2"
            else None
        )
        result = summarize(manifest, review.model_dump(mode="json") if review else None)
        lines.append(
            f"- Study {inline_text(result['study_id'])} · {inline_text(result['mode'])} · acquisition date unavailable. {inline_text(result['conclusion'])}"
        )
        for row in result["rows"]:
            caliper = (
                f"; reviewer caliper {row['Caliper mm']:.2f} mm"
                if row["Caliper mm"] is not None
                else ""
            )
            lines.append(
                f"- {inline_text(row['Candidate'])}: {inline_text(row['Review'])}; score {row['Detector score']:.4f} (not malignancy risk); source slices {row['Source slices']}{caliper}. Box extents are not lesion diameters."
            )
            lines.append(f"- Evidence source slice SHA-256 {row['Source SHA-256']}.")
        if not result["rows"] and "voxel_counts" in result:
            lines.append(
                f"- Tissue-class voxel counts: {result['voxel_counts']}; not lesion measurements."
            )
        checkpoint = (
            manifest["study"]["model"]["checkpoint_sha256"]
            if "study" in manifest
            else manifest["checkpoint_sha256"]
        )
        lines.append(
            f"- Source imaging-{snapshot['manifest_sha256']} · bundle.json · checkpoint SHA-256 {checkpoint}. Full provenance and review are retained in JSON; producer identity is not independently authenticated."
        )
    return lines

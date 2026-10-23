"""Concise source-bound summaries; detailed provenance stays in the evidence package."""

import hashlib
import html
import re

from medical_assistant.endo_support import (
    is_endoscopy,
    summarize_endo,
    verify_endo_snapshot,
)
from medical_assistant.models import Assessment, PatientRecord, ReportNote

NOTICE = "Educational, experimental synthetic case. Not a diagnostic device; clinician verification required."


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


def evidence_index(record, outputs, imaging=None):
    """Keep every exact source excerpt and selected evidence link outside the short prose."""
    documents = {source.id: source for source in record.sources}
    assessments = {
        role: Assessment.model_validate(value).validate_sources(record)
        for role, value in outputs.items()
    }
    result = {
        "record_entries": [
            {
                "entry_id": e.id,
                "source_id": e.source_id,
                "filename": documents[e.source_id].filename,
                "date": e.date.isoformat() if e.date else None,
                "source_type": e.source_type,
                "excerpt": e.text,
            }
            for e in record.entries
        ],
        "hypotheses": [
            {
                "possibility": item.possibility,
                "supporting_ids": list(
                    dict.fromkeys(i for c in item.supporting for i in c.evidence_ids)
                ),
                "conflicting_ids": list(
                    dict.fromkeys(i for c in item.conflicting for i in c.evidence_ids)
                ),
                "reference_ids": item.reference_ids,
            }
            for item in assessments["reasoning"].explanations
        ],
        "ct_studies": [
            {
                "study_id": s["manifest"]["study_id"],
                "manifest_sha256": s["manifest_sha256"],
                "archive_sha256": s["archive_sha256"],
            }
            for s in imaging or []
            if not is_endoscopy(s["manifest"])
        ],
    }
    endo = [s for s in imaging or [] if is_endoscopy(s["manifest"])]
    if endo:
        result["endoscopy_studies"] = [
            {
                "study_id": s["manifest"]["study_id"],
                "manifest_sha256": s["manifest_sha256"],
                "archive_sha256": s["archive_sha256"],
            }
            for s in endo
        ]
    return result


def ct_summary(imaging):
    """Aggregate accepted inspections; include reviewed calipers, never box-size diagnoses."""
    from medical_assistant.imaging_results import summarize
    from medical_assistant.nodule_support import verify_nodule_snapshot

    imaging = [s for s in imaging or [] if not is_endoscopy(s["manifest"])]
    if not imaging:
        return "No accepted CT study is included. Inspect and accept CT before preparing a new report if imaging is needed."
    results = []
    for snapshot in imaging:
        review = verify_nodule_snapshot(snapshot)
        results.append(
            summarize(
                snapshot["manifest"], review.model_dump(mode="json") if review else None
            )
        )
    lung = [result for result in results if "candidate_count" in result]
    legacy = len(results) - len(lung)
    parts = [
        f"{len(results)} accepted artificial CT {'study' if len(results) == 1 else 'studies'} included."
    ]
    if lung:
        proposed = sum(r["candidate_count"] for r in lung)
        accepted = sum(r["accepted_count"] for r in lung)
        parts.append(
            f"{proposed} {'candidate' if proposed == 1 else 'candidates'} proposed; inspection accepted {accepted} and rejected {proposed - accepted} for research review."
        )
        calipers = [
            (i, row)
            for i, result in enumerate(results, 1)
            for row in result["rows"]
            if row["Caliper mm"] is not None
        ]
        if calipers:
            parts.append(
                "Reviewed calipers: "
                + "; ".join(
                    f"study {i}, {row['Candidate']} {row['Caliper mm']:.2f} mm"
                    for i, row in calipers[:3]
                )
                + "."
            )
            if len(calipers) > 3:
                parts.append(
                    f"{len(calipers) - 3} further caliper(s) are in the evidence package."
                )
        else:
            parts.append("No reviewer caliper was supplied.")
        if any(r["mode"] == "Non-ML fixture" for r in lung):
            parts.append("Includes a non-ML demonstration fixture.")
        parts.append(
            "Candidates do not establish malignancy or explain symptoms; zero/rejected candidates do not establish a normal CT."
        )
    if legacy:
        parts.append(
            f"{legacy} legacy tissue-mask study/studies; these are not nodule detections or lesion measurements."
        )
    parts.append("Acquisition dates are unavailable.")
    return " ".join(parts)


def endoscopy_summary(imaging):
    studies = [s for s in imaging or [] if is_endoscopy(s["manifest"])]
    if not studies:
        return None
    results = [
        summarize_endo(s["manifest"], verify_endo_snapshot(s).model_dump(mode="json"))
        for s in studies
    ]
    proposed = sum(r["candidate_count"] for r in results)
    accepted = sum(r["accepted_count"] for r in results)
    areas = [
        str(row["Area (pixels)"])
        for r in results
        for row in r["rows"]
        if row["Review"] == "accept"
    ]
    text = f"{len(studies)} accepted artificial image study/studies; {proposed} candidate region(s), {accepted} accepted on inspection."
    if areas:
        text += " Accepted mask areas: " + ", ".join(areas[:3]) + " pixels."
        if len(areas) > 3:
            text += " Further areas are retained in the evidence package."
    if any(r["mode"] == "synthetic-fixture" for r in results):
        text += " Includes a non-ML demonstration."
    text += " No calibrated physical size, anatomical location or histology is supplied. These regions do not establish cancer, explain symptoms or exclude missed polyps."
    return text


def summary_parts(record, outputs, imaging=None, clinician_note=None):
    """Plain-text report blocks shared by Markdown and portable HTML presentation."""
    assessments = {
        role: Assessment.model_validate(value).validate_sources(record)
        for role, value in outputs.items()
    }
    reasoning = assessments["reasoning"]
    explanations = reasoning.explanations
    if explanations:
        labels = list(dict.fromkeys(e.possibility for e in explanations))
        analysis = (
            "; ".join(labels)
            + ". These are unverified hypotheses selected by the local model, not diagnoses."
        )
        kinds = list(
            dict.fromkeys(
                ("patient-reported " if c.kind == "patient_reported" else "documented ")
                + next(e.kind for e in record.entries if e.id == c.evidence_ids[0])
                + " evidence"
                for item in explanations
                for c in item.supporting
            )
        )
        analysis += " The model considered " + ", ".join(kinds) + "."
        analysis += (
            " Model-selected counterevidence also needs review."
            if any(e.conflicting for e in explanations)
            else " No counterevidence was selected; this does not confirm a cause."
        )
    else:
        analysis = "Insufficient evidence for a model-selected explanation; no cause is established."
    changes = assessments["medications"].dose_changes
    if changes:
        analysis += (
            " Documented medication changes: "
            + "; ".join(
                f"{c.name} {c.previous_dose} → {c.documented_dose} on {c.date}"
                for c in changes[:2]
            )
            + "; reconcile current use."
        )
        if len(changes) > 2:
            analysis += " Further changes are retained in the evidence package."
    analysis += (
        " No approved reference support was selected."
        if not any(e.reference_ids for e in explanations)
        else "Selected local reference support is retained in the evidence package."
    )
    safety = assessments["safety"]
    gaps = list(dict.fromkeys(safety.missing_information))
    if not any(e.blood_pressure for e in record.entries) and not any(
        "blood-pressure" in x.casefold() for x in gaps
    ):
        gaps.append("Blood-pressure measurements are unavailable.")
    followup = " ".join(gaps[:3])
    followup += " Clarify symptom timing, current medicines, syncope/falls, fluid intake, allergies and current warning signs."
    if any(f.urgency == "urgent" for f in safety.safety_flags):
        followup = (
            "Urgent human assessment is required; automated reasoning must stop. "
            + followup
        )
    note = ReportNote.model_validate(clinician_note) if clinician_note else None
    note_text = f"{note.reviewer}: {note.text}" if note and note.text else "Not added."
    parts = [
        ("Patient", record.display_name),
        ("AI history analysis", analysis),
        ("CT inspection", ct_summary(imaging)),
        ("For clinician review", followup.strip()),
        ("Clinician note", note_text),
    ]
    endo = endoscopy_summary(imaging)
    if endo:
        parts.insert(3, ("Endoscopy inspection", endo))
    return parts


def compose(
    record: PatientRecord,
    source_file: str,
    outputs: dict[str, dict],
    evidence=None,
    imaging=None,
    clinician_note=None,
) -> str:
    """One concise section; full exact excerpts/citations remain in report_evidence and originals."""
    parts = summary_parts(record, outputs, imaging, clinician_note)
    return (
        "# Clinical summary\n\n"
        + "\n\n".join(f"**{label}.** {inline_text(text)}" for label, text in parts)
        + "\n\n"
        + NOTICE
        + "\n"
    )

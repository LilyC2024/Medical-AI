"""Reusable presentation components. Escape every source-derived HTML value."""

import html
from pathlib import Path

import streamlit as st

from medical_assistant.history import MedicationAgent, chronology
from medical_assistant.report import inline_text
from medical_assistant.ui.navigation import go_to


def safe(value):
    return html.escape(str(value), quote=True).replace("\n", "<br>")


def styles():
    st.html((Path(__file__).with_name("theme.css")).read_text(encoding="utf-8"))


def sidebar_brand():
    st.markdown(
        '<div class="lv-side-brand"><div class="lv-monogram">L</div><div><div class="lv-side-name">LOVISA</div><div class="lv-side-sub">CLINICAL RESEARCH WORKSPACE</div></div></div>',
        unsafe_allow_html=True,
    )


def header():
    left, right = st.columns([5, 2], vertical_alignment="center")
    with left:
        st.markdown(
            '<div class="lv-eyebrow">A clearer view of the patient story</div>',
            unsafe_allow_html=True,
        )
        st.title("LOVISA")
        st.markdown(
            '<div class="lv-subtitle">Medical History & Clinical Reasoning Assistant</div>',
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            '<span class="lv-top-badge"><span class="lv-dot"></span> PRIVATE WORKSPACE · LOCAL AI</span>',
            unsafe_allow_html=True,
        )


def patient_header(record, decision, *, safety_reviewed=False):
    initials = "".join(word[0] for word in record.display_name.split()[:2]).upper()
    label = {
        "urgent": "Human assessment required",
        "uncertain": "Safety review needed",
        "ordinary_eligible": "Ready for source review",
    }[decision["state"]]
    if safety_reviewed and decision["state"] == "uncertain":
        label = "Safety assessment recorded"
    color = {"urgent": "red", "uncertain": "amber", "ordinary_eligible": "teal"}[
        decision["state"]
    ]
    st.markdown(
        f'<div class="lv-hero"><div class="lv-patient"><div class="lv-avatar">{safe(initials)}</div><div><h2>{safe(record.display_name)}</h2><div class="lv-small">Artificial patient record</div></div></div><span class="lv-pill {color}">{label}</span></div>',
        unsafe_allow_html=True,
    )
    metrics = [
        (sum(e.kind == "encounter" for e in record.entries), "Recorded encounters"),
        (sum(e.date is None for e in record.entries), "Dates to clarify"),
    ]
    st.markdown(
        '<div class="lv-stats">'
        + "".join(
            f'<div class="lv-stat"><strong>{n}</strong><span>{label}</span></div>'
            for n, label in metrics
        )
        + "</div>",
        unsafe_allow_html=True,
    )


def timeline(record):
    st.subheader("The patient story")
    st.caption("What the supplied records say, with dates and attribution kept intact.")
    sources = {s.id: s for s in record.sources}
    cards = []
    for e in sorted(record.entries, key=chronology):
        date = e.date.strftime("%d %b %Y") if e.date else "Date not supplied"
        attribution = (
            "Patient reported"
            if e.source_type == "patient_reported"
            else "Documented in source"
        )
        source = sources.get(e.source_id)
        name = source.filename if source else "Source unavailable"
        cards.append(
            f'<div class="lv-entry"><div class="lv-entry-top"><span class="lv-entry-date">{date}</span><span class="lv-entry-kind">{safe(e.kind)}</span></div><p>{safe(e.text)}</p><div class="lv-cite">{attribution} · {safe(name)}</div></div>'
        )
    st.markdown(
        '<div class="lv-timeline">' + "".join(cards) + "</div>", unsafe_allow_html=True
    )


def medications(record):
    assessment = MedicationAgent().run(record)
    st.subheader("Medication history")
    st.caption(
        "Historical entries need reconciliation; no treatment changes are suggested."
    )
    for e in sorted(record.entries, key=chronology):
        if e.medication:
            order = e.medication
            date = e.date.strftime("%d %b %Y") if e.date else "Date not supplied"
            st.markdown(
                f'<div class="lv-med"><h4>{safe(order.name)}</h4><p><strong>{safe(order.dose)}</strong> · {safe(order.frequency)}</p><p>{date} · {safe(e.source_type.replace("_", " "))}</p><div class="lv-cite">Historical record · current use unverified</div></div>',
                unsafe_allow_html=True,
            )
        elif e.kind == "medication":
            st.markdown(
                f'<div class="lv-med"><h4>Medication mentioned in a source</h4><p>{safe(e.text)}</p><div class="lv-cite">Structured order not supplied</div></div>',
                unsafe_allow_html=True,
            )
    if not any(e.kind == "medication" or e.medication for e in record.entries):
        empty(
            "No medication history supplied",
            "Ask the reviewer to reconcile the current medication list; an empty record does not mean no medication use.",
        )
    for change in assessment.dose_changes:
        st.info(
            f"Documented change: {inline_text(change.name)}, {inline_text(change.previous_dose)} → {inline_text(change.documented_dose)} on {change.date}. Current use requires reconciliation."
        )
    if assessment.missing_information:
        with st.expander("What needs medication reconciliation"):
            for item in assessment.missing_information:
                st.text(item)


def original_sources(record):
    st.subheader("Source records")
    st.caption(
        "Original wording for this patient. Use these excerpts to check the history and report."
    )
    for source in record.sources:
        with st.expander(inline_text(source.filename), expanded=True):
            for entry in sorted(
                (e for e in record.entries if e.source_id == source.id), key=chronology
            ):
                st.caption(
                    (
                        entry.date.strftime("%d %b %Y")
                        if entry.date
                        else "Date not supplied"
                    )
                    + " · "
                    + (
                        "Patient reported"
                        if entry.source_type == "patient_reported"
                        else "Documented"
                    )
                )
                st.text(entry.text)
            st.download_button(
                "Download original record",
                source.content,
                file_name=source.filename,
                key="source_download_" + source.id,
            )


def empty(title, copy):
    st.markdown(
        f'<div class="lv-empty"><div class="lv-empty-title">{safe(title)}</div><p>{safe(copy)}</p></div>',
        unsafe_allow_html=True,
    )


def next_action(state=None, *, urgent=False):
    state = state or {}
    if urgent:
        return "safety-check", "Next action: review the warning sign"
    if "proposal" in st.session_state:
        return "source-records", "Next action: review the pending record"
    proposal = st.session_state.get("imaging_proposal")
    from medical_assistant.endo_support import is_endoscopy

    if proposal and is_endoscopy(proposal[1]["manifest"]):
        return "endoscopy-review", "Next action: review or discard the endoscopy image"
    endo_job = st.session_state.get("endo_job")
    if endo_job and endo_job.status() in ("running", "complete"):
        return "endoscopy-review", "Next action: inspect the endoscopy result"
    job = st.session_state.get("ct_job")
    if "imaging_proposal" in st.session_state or (
        job and job.status() in ("running", "complete")
    ):
        return "ct-review", "Next action: review or discard the CT study"
    if state.get("status") in ("awaiting_clinician_review", "complete"):
        return "clinical-report", "Next action: open the clinical report"
    if state.get("status") == "running":
        return "safety-check", "Next action: generate the draft"
    return "safety-check", "Next action: complete the safety check"


def guide(view, state=None, *, running=False, signed_in=False):
    st.markdown("### Your review steps")
    steps = [
        ("Choose a patient", "choose-patient"),
        ("Review the history", "patient-overview"),
        ("Review CT · optional", "ct-review"),
        ("Review endoscopy · optional", "endoscopy-review"),
        ("Complete safety check", "safety-check"),
        ("Review the report", "clinical-report"),
    ]
    for i, (title, target) in enumerate(steps, 1):
        st.button(
            f"{i}. {title}",
            key="guide_" + target,
            on_click=go_to,
            args=(target,),
            width="stretch",
        )
    st.button(
        "View source records",
        key="guide_sources",
        on_click=go_to,
        args=("source-records",),
        width="stretch",
    )
    st.caption(
        "Each step opens the right place. Safety review comes before generation; final approval comes after the draft."
    )
    st.caption(
        "Artificial records only. Clinical conclusions require clinician verification."
    )


def footer():
    st.markdown(
        '<div class="lv-footer"><span>LOVISA · Medical History & Clinical Reasoning Assistant</span><span>Local only · Synthetic research · Human review</span></div>',
        unsafe_allow_html=True,
    )

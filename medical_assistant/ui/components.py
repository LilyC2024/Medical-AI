"""Reusable presentation components. Escape every source-derived HTML value."""

import html
from pathlib import Path
import streamlit as st
from medical_assistant.history import chronology, MedicationAgent
from medical_assistant.report import inline_text


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
        f'<div class="lv-hero"><div class="lv-patient"><div class="lv-avatar">{safe(initials)}</div><div><h2>{safe(record.display_name)}</h2><div class="lv-small">Fictional patient · {safe(record.patient_id)}</div></div></div><span class="lv-pill {color}">{label}</span></div>',
        unsafe_allow_html=True,
    )
    metrics = [
        (len(record.entries), "Source entries"),
        (sum(e.kind == "encounter" for e in record.entries), "Recorded encounters"),
        (sum(e.date is None for e in record.entries), "Dates to clarify"),
        (len(record.sources), "Original documents"),
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
            f'<div class="lv-entry"><div class="lv-entry-top"><span class="lv-entry-date">{date}</span><span class="lv-entry-kind">{safe(e.kind)}</span></div><p>{safe(e.text)}</p><div class="lv-cite">{attribution} · {safe(name)} · {safe(e.id)}</div></div>'
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
                f'<div class="lv-med"><h4>{safe(order.name)}</h4><p><strong>{safe(order.dose)}</strong> · {safe(order.frequency)}</p><p>{date} · {safe(e.source_type.replace("_", " "))}</p><div class="lv-cite">Source entry {safe(e.id)} · current use unverified</div></div>',
                unsafe_allow_html=True,
            )
        elif e.kind == "medication":
            st.markdown(
                f'<div class="lv-med"><h4>Medication mentioned in a source</h4><p>{safe(e.text)}</p><div class="lv-cite">Structured order not supplied · {safe(e.id)}</div></div>',
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
    with st.expander("Structured extraction · technical details"):
        st.json(assessment.model_dump(mode="json"))


def original_sources(record):
    with st.expander("Original sources and verification details"):
        st.caption(
            "These immutable originals support the readable timeline. Hashes establish content identity, not clinical verification."
        )
        for source in record.sources:
            st.text(f"{source.filename} · {source.id}")
            st.caption("SHA-256: " + source.sha256)
            st.code(source.content, language="json")


def empty(title, copy):
    st.markdown(
        f'<div class="lv-empty"><div class="lv-empty-title">{safe(title)}</div><p>{safe(copy)}</p></div>',
        unsafe_allow_html=True,
    )


def guide(view, state=None, *, running=False, signed_in=False):
    state = state or {}
    status = state.get("status", "")
    next_step = (
        "Processing locally. You can keep using the workspace or cancel this run."
        if running
        else "Assess the missing information in the safety step at the bottom."
        if status == "awaiting_safety_review"
        else "Read the draft and check its sources. Final approval is a separate step."
        if status == "awaiting_clinician_review"
        else "The reviewed report is ready for download."
        if status == "complete"
        else "Inspect the source images and each candidate. Accepting CT does not approve a clinical report."
        if view == "CT review"
        else "Review the history and optional CT, then complete the bottom safety check."
    )
    st.markdown("### How to use LOVISA")
    st.markdown(
        '<div class="lv-guide-intro">Your next steps, in one place.</div>',
        unsafe_allow_html=True,
    )
    steps = [
        ("Choose a patient", "Use a fictional demo record from the left."),
        ("Review the story", "Check the timeline, medicines and missing dates."),
        ("Add CT, if useful", "Inspect candidates and optional calipers."),
        ("Prepare a draft", "Complete the safety check at the bottom, then generate."),
        (
            "Review and approve",
            "Check sources, then explicitly approve the final report.",
        ),
    ]
    active = (
        4
        if status == "complete"
        else 3
        if status.startswith("awaiting") or running
        else 2
        if view == "CT review"
        else 1
    )
    step_html = []
    for i, (title, copy) in enumerate(steps):
        step_html.append(
            f'<div class="lv-step {"active" if i == active else ""}"><div class="lv-step-num">{i + 1}</div><div><div class="lv-step-title">{title}</div><div class="lv-step-copy">{copy}</div></div></div>'
        )
    st.markdown("".join(step_html), unsafe_allow_html=True)
    st.markdown(
        f'<div class="lv-next"><strong>YOUR NEXT STEP</strong><p>{safe(next_step)}</p></div>',
        unsafe_allow_html=True,
    )
    if not signed_in:
        st.caption("Sign in to approve imports, imaging or reports.")
    st.caption(
        "Analysis and CT runs stop at 110 seconds if needed. Progress updates automatically. Human review time is up to you."
    )
    st.divider()
    st.caption(
        "Research with synthetic records only. Hypotheses are unverified; clinician review is required."
    )


def footer():
    st.markdown(
        '<div class="lv-footer"><span>LOVISA · Medical History & Clinical Reasoning Assistant</span><span>Local only · Synthetic research · Human review</span></div>',
        unsafe_allow_html=True,
    )

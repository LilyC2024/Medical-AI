"""Source-first endoscopy inspection; every candidate needs explicit human review."""

import numpy as np
import streamlit as st
from PIL import Image

from medical_assistant.endo_contracts import Review as EndoReview
from medical_assistant.endo_contracts import digest
from medical_assistant.endo_support import is_endoscopy, summarize_endo
from medical_assistant.imaging import ImagingStore
from medical_assistant.imaging_actions import collect
from medical_assistant.ui.imaging_actions import image_actions
from medical_assistant.models import Review
from medical_assistant.nodule_support import imaging_acceptance_digest
from medical_assistant.ui.errors import error_message
from medical_assistant.ui.navigation import go_to


def image_results(manifest, path_for, review=None):
    result = summarize_endo(manifest, review)
    candidates = manifest["study"]["candidates"]
    focus = st.selectbox(
        "Highlight a region",
        ["All regions", *[c["candidate_id"] for c in candidates]],
        key=("reviewed_" if review else "pending_")
        + "endo_focus_"
        + manifest["job_id"],
    )
    overlay = str(path_for("overlay_preview", 0))
    caption = "Candidate outlines · not a diagnosis"
    if focus != "All regions":
        with Image.open(overlay) as image:
            overlay = np.array(image.convert("RGB"))
        c = next(c for c in candidates if c["candidate_id"] == focus)
        x0, y0, x1, y1 = c["box_xyxy"]
        width = max(2, overlay.shape[1] // 250)
        overlay[y0 : min(y0 + width, y1), x0:x1] = [0, 210, 210]
        overlay[max(y0, y1 - width) : y1, x0:x1] = [0, 210, 210]
        overlay[y0:y1, x0 : min(x0 + width, x1)] = [0, 210, 210]
        overlay[y0:y1, max(x0, x1 - width) : x1] = [0, 210, 210]
        caption = "Highlighted: " + focus
    a, b = st.columns(2)
    a.image(
        str(path_for("source_preview", 0)),
        caption="Endoscopy source",
        width="stretch",
    )
    b.image(
        overlay,
        caption=caption,
        width="stretch",
    )
    st.subheader("Endoscopy analysis results")
    a, b = st.columns(2)
    a.metric("Candidate regions", result["candidate_count"])
    b.metric(
        "Accepted on inspection", result["accepted_count"] if review else "Pending"
    )
    if result["rows"]:
        st.dataframe(
            [
                {
                    k: v
                    for k, v in row.items()
                    if k not in ("Model score", "Area (pixels)")
                }
                for row in result["rows"]
            ],
            hide_index=True,
        )
    st.caption(
        "Candidate regions require inspection; physical size and histology are unavailable."
    )
    if not manifest["synthetic"]:
        st.caption("Public research image · fictional composite case")


def endoscopy_ui(path, auth, token, user, record, *, locked=False, case_imaging=None):
    st.subheader("Endoscopy review")
    st.caption(
        "Inspect image candidates and include reviewed findings before preparing the clinical report."
    )
    if "imaging_store" not in st.session_state:
        st.session_state.imaging_store = ImagingStore(path, auth)
    store = st.session_state.imaging_store
    collect(st.session_state, store, "endoscopy", record.patient_id)
    image_actions("endoscopy", store, auth, token, record)
    proposal = st.session_state.get("imaging_proposal")
    if proposal and not is_endoscopy(proposal[1]["manifest"]):
        st.info("Resolve the pending CT study before adding endoscopy.")
        st.button(
            "Open pending CT", on_click=go_to, args=("ct-review",), key="endo_open_ct"
        )
        return
    try:
        accepted = (
            store.snapshots(record.patient_id) if case_imaging is None else case_imaging
        )
        if case_imaging is not None:
            store.verify(accepted)
        accepted = [s for s in accepted if is_endoscopy(s["manifest"])]
        if accepted:
            selected = st.selectbox(
                "Reviewed endoscopy study",
                [s["manifest"]["study_id"] for s in accepted],
                key="accepted_endo_study",
            )
            snapshot = next(
                s for s in accepted if s["manifest"]["study_id"] == selected
            )
            st.caption(
                "Included in a newly prepared report; final approval remains separate."
            )
            image_results(
                snapshot["manifest"],
                store.preview_resolver(snapshot),
                snapshot["endo_review"],
            )
    except (ValueError, OSError):
        st.error("Accepted imaging needs an integrity check before use.")
        return
    proposal = st.session_state.get("imaging_proposal")
    if locked:
        st.caption(
            "This report snapshot is fixed. Start a new review to add another image."
        )
    if proposal:
        key, item = proposal
        manifest = item["manifest"]
        if manifest["patient_id"] != record.patient_id:
            st.error("Patient association mismatch.")
            return
        try:
            directory = store.root / "pending" / key
            store._verify_directory(directory, item)

            def preview(role, index):
                return directory / next(
                    a["path"]
                    for a in manifest["artifacts"]
                    if a["role"] == role and a["slice_index"] == index
                )

            st.caption("Awaiting image review · not yet in the report")
            image_results(manifest, preview)
            with st.form("endo_acceptance"):
                choices = [
                    {
                        "candidate_id": c["candidate_id"],
                        "decision": st.radio(
                            "Review " + c["candidate_id"],
                            ["uncertain", "accept", "reject"],
                            index=None,
                            format_func=lambda x: {
                                "uncertain": "Pause · decide later",
                                "accept": "Include candidate",
                                "reject": "Exclude candidate",
                            }[x],
                            key="endo_decision_" + key + c["candidate_id"],
                        ),
                    }
                    for c in manifest["study"]["candidates"]
                ]
                notes = st.text_area(
                    "Image review note (optional)", key="endo_notes", max_chars=600
                )
                attested = st.checkbox(
                    "I inspected the image, candidate decisions and case association.",
                    key="endo_attest",
                    value=False,
                )
                submit = st.form_submit_button(
                    "Include reviewed endoscopy in report",
                    key="endo_accept",
                    disabled=locked or not token,
                )
            if submit:
                if any(c["decision"] is None for c in choices):
                    raise ValueError("Choose a decision for every candidate")
                review = EndoReview(
                    study_digest=digest(manifest["study"]),
                    reviewer=user,
                    attested=attested,
                    decisions=choices,
                )
                receipt = Review(
                    approved=True,
                    reviewer=user,
                    clinician_attestation=attested,
                    notes=notes,
                    draft_sha256=imaging_acceptance_digest(item, endo_review=review),
                )
                store.approve(key, receipt, token, endo_review=review)
                st.session_state.pop("imaging_proposal", None)
                st.session_state.pop("endo_job", None)
                st.rerun()
        except (ValueError, OSError, PermissionError) as error:
            st.error(
                "Image review could not be saved: " + error_message(error)
                + ". Choose include or exclude for every candidate and select the confirmation; notes are optional."
            )
        if st.button("Discard endoscopy proposal", key="endo_discard"):
            store.discard(key)
            st.session_state.pop("imaging_proposal", None)
            st.session_state.pop("endo_job", None)
            st.rerun()
    elif not accepted:
        st.info(
            "No endoscopy result yet. Upload an image or review ZIP, then click Analyze. Or choose a local example."
        )

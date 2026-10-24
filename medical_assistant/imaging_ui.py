"""Imaging inspection UI; acceptance is separate from final clinical approval."""

import streamlit as st

from medical_assistant.endo_support import is_endoscopy
from medical_assistant.imaging import ImagingStore
from medical_assistant.imaging_actions import collect
from medical_assistant.imaging_results import summarize
from medical_assistant.models import Review
from medical_assistant.nodule_support import imaging_acceptance_digest, is_nodule
from medical_assistant.nodule_ui import (
    build_nodule_review,
    candidate_controls,
    nodule_viewer,
    preview_calipers,
)

from medical_assistant.ui.errors import error_message
from medical_assistant.ui.imaging_actions import image_actions


def _viewer(manifest, path_for, key, *, review=None):
    if is_nodule(manifest):
        return nodule_viewer(manifest, path_for, key, review=review)
    st.caption(
        "Synthetic research output · acquisition date unavailable · teal: class 1; amber: class 2; purple: class 3. Class 0 does not establish normality."
    )
    depth = manifest["geometry"]["shape_zyx"][0]
    index = (
        st.slider("Source-grid slice", 0, depth - 1, depth // 2, key=key)
        if depth > 1
        else 0
    )
    left, right = st.columns(2)
    left.image(
        str(path_for("source_preview", index)),
        caption=f"Synthetic source · slice {index}",
        width="stretch",
    )
    right.image(
        str(path_for("overlay_preview", index)),
        caption=f"Unvalidated candidate overlay · slice {index}",
        width="stretch",
    )
    st.caption("Legacy tissue-mask example; this does not detect nodules.")


def result_summary(manifest, review=None):
    result = summarize(manifest, review)
    st.subheader("CT analysis results")
    st.caption("Reviewed study" if review else "Study awaiting your review")
    if "candidate_count" in result:
        a, b, c = st.columns(3)
        a.metric("Candidates proposed", result["candidate_count"])
        b.metric(
            "Accepted on review", result["accepted_count"] if review else "Pending"
        )
        c.metric("Reviewed calipers", result["caliper_count"] if review else "Pending")
        if result["rows"]:
            st.dataframe(
                [
                    {
                        k: v
                        for k, v in row.items()
                        if k not in ("Source SHA-256", "Detector score")
                    }
                    for row in result["rows"]
                ],
                hide_index=True,
            )
    else:
        st.caption("Legacy tissue-mask result; no nodule measurements.")
    st.caption(
        "Candidate regions require inspection; counts do not establish a diagnosis."
    )
    st.caption(
        "Inspect the source images and annotations below. Calipers require human review."
    )


def imaging_ui(path, auth, token, user, record, *, locked=False, case_imaging=None):
    st.subheader("CT review")
    st.caption(
        "Inspect CT images, candidates and optional calipers. Include the reviewed study before preparing the clinical report."
    )
    if "imaging_store" not in st.session_state:
        st.session_state.imaging_store = ImagingStore(path, auth)
    store = st.session_state.imaging_store

    collect(st.session_state, store, "ct", record.patient_id)
    image_actions("ct", store, auth, token, record)

    pending = st.session_state.get("imaging_proposal")
    if pending and is_endoscopy(pending[1]["manifest"]):
        from medical_assistant.ui.navigation import go_to

        st.info("Resolve the pending endoscopy study before adding CT.")
        st.button(
            "Open pending endoscopy",
            on_click=go_to,
            args=("endoscopy-review",),
            key="ct_open_endo",
        )
        return
    job = st.session_state.get("ct_job")
    accepted = []
    try:
        accepted = (
            store.snapshots(record.patient_id) if case_imaging is None else case_imaging
        )
        if case_imaging is not None:
            store.verify(accepted)
        accepted = [s for s in accepted if not is_endoscopy(s["manifest"])]
        if accepted:
            st.subheader("Accepted research imaging")
            selected = st.selectbox(
                "Accepted study",
                [s["manifest"]["study_id"] for s in accepted],
                key="accepted_ct_study",
            )
            snapshot = next(
                s for s in accepted if s["manifest"]["study_id"] == selected
            )
            st.caption(
                f"Accepted by {snapshot['review']['reviewer']}. A newly prepared report includes this accepted study."
            )
            result_summary(snapshot["manifest"], snapshot.get("nodule_review"))
            _viewer(
                snapshot["manifest"],
                store.preview_resolver(snapshot),
                "accepted_ct_slice_" + snapshot["archive_sha256"],
                review=snapshot.get("nodule_review"),
            )
    except (ValueError, OSError) as error:
        st.error("Accepted imaging integrity check failed: " + error_message(error))
    if not accepted and "imaging_proposal" not in st.session_state:
        st.info(
            "No CT result is attached to this report. Upload a review ZIP and click Analyze to add one."
            if locked
            else "No CT result yet. Upload a review ZIP, then click Analyze. Or choose a local example."
        )
    if locked:
        st.caption(
            "This case snapshot is fixed. Existing CT results remain available for inspection."
        )
    if "imaging_proposal" in st.session_state:
        key, proposal = st.session_state.imaging_proposal
        manifest = proposal["manifest"]
        st.subheader("Inspect this study before accepting")
        st.caption("Pending review · not yet included in the clinical report.")
        if manifest["patient_id"] != record.patient_id:
            st.warning("Select the matching patient or discard this proposal.")
        else:
            directory = store.root / "pending" / key
            try:
                store._verify_directory(directory, proposal)
                result_summary(manifest)

                def preview(role, index):
                    item = next(
                        a
                        for a in manifest["artifacts"]
                        if a["role"] == role and a["slice_index"] == index
                    )
                    return directory / item["path"]

                _viewer(manifest, preview, "pending_ct_slice_" + key)
                with st.form("imaging_acceptance"):
                    decisions = (
                        candidate_controls(manifest, key)
                        if is_nodule(manifest)
                        else None
                    )
                    notes = st.text_area(
                        "Image review note (optional)", key="imaging_notes"
                    )
                    attested = st.checkbox(
                        "I inspected the images, candidate decisions and case association.",
                        key="imaging_attest",
                        value=False,
                    )
                    submit = st.form_submit_button(
                        "Include reviewed CT in report",
                        key="imaging_accept",
                        disabled=locked or not token,
                    )
                    measurement_preview = (
                        st.form_submit_button(
                            "Preview nodule measurements",
                            key="nodule_measurement_preview",
                        )
                        if is_nodule(manifest)
                        else False
                    )
                if measurement_preview:
                    preview_calipers(manifest, preview, decisions)
                if submit:
                    nodule_review = (
                        build_nodule_review(manifest, decisions, user or "", attested)
                        if is_nodule(manifest)
                        else None
                    )
                    review = Review(
                        approved=True,
                        reviewer=user or "",
                        clinician_attestation=attested,
                        notes=notes,
                        draft_sha256=imaging_acceptance_digest(proposal, nodule_review),
                    )
                    store.approve(key, review, token, nodule_review=nodule_review)
                    del st.session_state.imaging_proposal
                    if job is not None and job.study_id == manifest["study_id"]:
                        st.session_state.pop("ct_job", None)
                    st.rerun()
            except (ValueError, OSError, PermissionError) as error:
                st.error("Imaging acceptance blocked: " + error_message(error))
        if st.button("Discard imaging proposal", key="imaging_discard"):
            store.discard(key)
            del st.session_state.imaging_proposal
            if job is not None and job.study_id == manifest["study_id"]:
                st.session_state.pop("ct_job", None)
            st.rerun()

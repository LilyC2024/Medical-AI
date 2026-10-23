"""Reusable Upload / Analyze controls and visible local-worker errors."""

import streamlit as st

from medical_assistant.imaging_actions import analyze, blocker, failure_detail
from medical_assistant.report import inline_text


def image_actions(modality, store, auth, token, record):
    prefix = "ct" if modality == "ct" else "endo"
    job = st.session_state.get(prefix + "_job")
    running = bool(job and job.status() == "running")
    modes = {"Use uploaded file": "auto"}
    if record.patient_id == "research-composite-demo":
        modes["Local research example · included results"] = "research-example"
    if modality == "ct":
        modes.update(
            {
                "Artificial nodule example · no model": "lung-fixture",
                "Installed lung detector · artificial CT": "lung-pretrained",
                "Legacy tissue example · artificial CT": "legacy",
            }
        )
    else:
        modes.update(
            {
                "Artificial polyp example · no model": "fixture",
                "Installed polyp model · artificial image": "installed",
            }
        )
    with st.container(border=True):
        choice = st.selectbox("Model / example", list(modes), key=prefix + "_mode")
        left, right = st.columns(2)
        with left:
            with st.popover("Upload", width="stretch"):
                uploaded = st.file_uploader(
                    "CT review ZIP"
                    if modality == "ct"
                    else "Endoscopy image or review ZIP",
                    type=["zip"] if modality == "ct" else ["jpg", "jpeg", "png", "zip"],
                    key=prefix + "_bundle",
                    max_upload_size=64,
                )
                st.caption(
                    "Use a CT companion ZIP containing source images and results. Raw DICOM and screenshots need preparation in the CT companion."
                    if modality == "ct"
                    else "Use a prepared research JPG/PNG in the Jordan composite case, or a companion review ZIP matching the selected patient."
                )
        with right:
            clicked = st.button(
                "Analyze",
                key=prefix + "_generate",
                type="primary",
                width="stretch",
                disabled=running,
            )
        if uploaded is not None:
            st.caption("Selected: " + inline_text(uploaded.name))
            st.caption(
                "ZIP: opens the included results; it does not rerun a model."
                if uploaded.name.lower().endswith(".zip")
                else "Image: runs the installed local polyp model on this upload."
            )
        if "case_id" in st.session_state or "analysis_task" in st.session_state:
            st.info(
                "Analyze starts a fresh, unreviewed report context. Saved reports stay intact; complete the safety check again after including the images."
            )
        reason = blocker(st.session_state)
        if reason:
            st.warning(reason)
        if clicked:
            try:
                analyze(
                    st.session_state,
                    store,
                    auth,
                    token,
                    record.patient_id,
                    modality,
                    upload=(uploaded.name, uploaded.getvalue())
                    if uploaded is not None
                    else None,
                    mode=modes[choice],
                )
                st.rerun()
            except (ValueError, OSError, PermissionError, RuntimeError) as error:
                st.session_state[modality + "_action_error"] = (
                    f"Analysis could not start: {error}"
                )
                st.session_state.pop(modality + "_action_notice", None)
        error = st.session_state.get(modality + "_action_error")
        if error:
            st.error(inline_text(error))
        elif st.session_state.get(modality + "_action_notice"):
            st.success(st.session_state[modality + "_action_notice"])
        if job and job.status() not in ("running", "complete"):
            st.error(inline_text(failure_detail(job)))
        if job and getattr(job, "validation_error", None) and not error:
            st.error(
                "Result could not be verified: " + inline_text(job.validation_error)
            )
        if (
            job
            and job.status() == "complete"
            and not getattr(job, "inspection_ready", False)
            and not reason
        ):
            st.info(
                "A completed analysis is waiting. Select Use uploaded file and click Analyze with no upload to open it."
            )
    if running:
        image_progress(job, prefix)


@st.fragment(run_every=1)
def image_progress(job, prefix):
    if job.status() != "running":
        st.rerun()
    st.info(job.progress(), icon="⏳")
    st.caption(
        f"{job.elapsed:.0f} seconds elapsed · automatic stop at {job.timeout:.0f} seconds. Results open automatically."
    )
    if st.button("Cancel analysis", key=prefix + "_cancel"):
        job.cancel()
        st.rerun()

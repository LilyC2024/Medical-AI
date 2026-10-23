"""Source-first endoscopy inspection; every candidate needs explicit human review."""

import os

import streamlit as st

from medical_assistant.endo_contracts import Review as EndoReview
from medical_assistant.endo_contracts import digest
from medical_assistant.endo_support import is_endoscopy, summarize_endo
from medical_assistant.endo_worker import LocalEndoscopyJob
from medical_assistant.imaging import ImagingStore
from medical_assistant.models import Review
from medical_assistant.nodule_support import imaging_acceptance_digest
from medical_assistant.ui.navigation import go_to


def image_results(manifest, path_for, review=None):
    result = summarize_endo(manifest, review)
    a, b = st.columns(2)
    a.image(
        str(path_for("source_preview", 0)),
        caption="Artificial endoscopy source",
        width="stretch",
    )
    b.image(
        str(path_for("overlay_preview", 0)),
        caption="Candidate outlines · not a diagnosis",
        width="stretch",
    )
    st.subheader("Endoscopy analysis results")
    a, b = st.columns(2)
    a.metric("Candidate regions", result["candidate_count"])
    b.metric(
        "Accepted on inspection", result["accepted_count"] if review else "Pending"
    )
    if result["rows"]:
        st.dataframe(result["rows"], hide_index=True)
    st.caption(
        "Non-ML demonstration"
        if result["mode"] == "synthetic-fixture"
        else "Installed image model · " + result["scope"].replace("-", " ")
    )
    st.info(
        "Areas are source-image pixels, not millimetres. Candidate regions do not establish cancer, explain symptoms or exclude missed polyps."
    )


def endoscopy_ui(path, auth, token, user, record, *, locked=False, case_imaging=None):
    st.subheader("Endoscopy review")
    st.caption(
        "Inspect artificial image candidates and include reviewed findings before preparing the clinical report."
    )
    if "imaging_store" not in st.session_state:
        st.session_state.imaging_store = ImagingStore(path, auth)
    store = st.session_state.imaging_store
    proposal = st.session_state.get("imaging_proposal")
    if proposal and not is_endoscopy(proposal[1]["manifest"]):
        st.info("Resolve the pending CT study before adding endoscopy.")
        st.button(
            "Open pending CT", on_click=go_to, args=("ct-review",), key="endo_open_ct"
        )
        return
    job = st.session_state.get("endo_job")
    if (
        job
        and job.status() == "complete"
        and not getattr(job, "inspection_ready", False)
        and not locked
        and "imaging_proposal" not in st.session_state
    ):
        if job.patient_id != record.patient_id:
            st.error("Select the matching patient before inspecting this result.")
            return
        try:
            st.session_state.imaging_proposal = store.prepare(
                job.bundle_path.read_bytes(), record.patient_id, study_id=job.study_id
            )
        except (ValueError, OSError):
            st.error(
                "The endoscopy result could not be verified. Discard it and retry."
            )
            job.validation_error = True
        job.inspection_ready = True
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
                        "decision": st.selectbox(
                            "Review " + c["candidate_id"],
                            ["uncertain", "accept", "reject"],
                            key="endo_decision_" + key + c["candidate_id"],
                        ),
                    }
                    for c in manifest["study"]["candidates"]
                ]
                notes = st.text_area(
                    "Brief image review note", key="endo_notes", max_chars=600
                )
                attested = st.checkbox(
                    "I inspected the source, candidate outlines, patient association and research limitations.",
                    key="endo_attest",
                )
                submit = st.form_submit_button(
                    "Include reviewed endoscopy in report",
                    key="endo_accept",
                    disabled=locked or not token,
                )
            if submit:
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
        except (ValueError, OSError, PermissionError):
            st.error(
                "Review every candidate, add a short note and confirm image inspection before including this study."
            )
        if st.button("Discard endoscopy proposal", key="endo_discard"):
            store.discard(key)
            st.session_state.pop("imaging_proposal", None)
            st.session_state.pop("endo_job", None)
            st.rerun()
    elif not accepted:
        st.info(
            "No endoscopy study yet. Run an artificial example or upload a supported synthetic bundle."
        )
    ct = st.session_state.get("ct_job")
    busy_ct = bool(ct and ct.status() in ("running", "complete"))
    with st.expander(
        "Add an endoscopy image study", expanded=not accepted and proposal is None
    ):
        mode = st.selectbox(
            "Analysis mode",
            ["Artificial workflow example (non-ML)", "Installed polyp research model"],
            key="endo_mode",
        )
        running = job is not None and job.status() == "running"
        if st.button(
            "Run endoscopy analysis",
            key="endo_generate",
            disabled=locked or running or busy_ct or proposal is not None or not token,
        ):
            try:
                st.session_state.endo_job = LocalEndoscopyJob(
                    record.patient_id,
                    jobs=store.root / "endo-jobs",
                    mode="fixture" if mode.startswith("Artificial") else "installed",
                    backend="onnx-cpu"
                    if mode.startswith("Artificial")
                    else os.environ.get("LOVISA_ENDO_BACKEND", "onnx-cpu"),
                )
                st.rerun()
            except (ValueError, OSError):
                st.error(
                    "Endoscopy setup needs attention. Install the companion environment and register a model for installed-model mode; the artificial example needs no weights."
                )
        if job:
            if running:
                endo_progress(job)
            elif job.status() != "complete":
                st.warning(job.error)
            if job.status() != "running" and st.button(
                "Dismiss endoscopy job", key="endo_dismiss"
            ):
                st.session_state.pop("endo_job", None)
                st.rerun()
        uploaded = st.file_uploader(
            "Synthetic endoscopy bundle (.zip)", type=["zip"], key="endo_bundle"
        )
        if st.button(
            "Inspect uploaded endoscopy",
            key="endo_upload",
            disabled=locked
            or proposal is not None
            or running
            or busy_ct
            or uploaded is None
            or not token,
        ):
            try:
                from medical_assistant.endo_contracts import read_exchange

                read_exchange(uploaded.getvalue(), record.patient_id)
                st.session_state.imaging_proposal = store.prepare(
                    uploaded.getvalue(), record.patient_id
                )
                st.rerun()
            except (ValueError, OSError):
                st.error(
                    "Only verified artificial endoscopy bundles for the selected patient are accepted."
                )
        st.caption(
            "Public research images are supported in the standalone endoscopy app; they are not imported into synthetic patient records."
        )


@st.fragment(run_every=1)
def endo_progress(job):
    if job.status() != "running":
        st.rerun()
    st.info(job.progress())
    st.caption(
        f"{job.elapsed:.0f} seconds elapsed · automatic stop at {job.timeout:.0f} seconds"
    )
    if st.button("Cancel endoscopy analysis", key="endo_cancel"):
        job.cancel()
        st.rerun()

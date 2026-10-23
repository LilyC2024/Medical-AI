"""Imaging inspection UI; acceptance is separate from final clinical approval."""

import os

import streamlit as st

from medical_assistant.ct_worker import (
    LocalCTJob,
    configured_ct_model,
)
from medical_assistant.endo_support import is_endoscopy
from medical_assistant.imaging import ImagingStore
from medical_assistant.imaging_results import summarize
from medical_assistant.models import Review
from medical_assistant.nodule_support import imaging_acceptance_digest, is_nodule
from medical_assistant.nodule_ui import (
    build_nodule_review,
    candidate_controls,
    nodule_viewer,
    preview_calipers,
)


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

    def prepare(payload, *, study_id=None):
        result = store.prepare(payload, record.patient_id, study_id=study_id)
        if "imaging_proposal" in st.session_state:
            store.discard(st.session_state.imaging_proposal[0])
        st.session_state.imaging_proposal = result

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
    if job:
        status = job.status()
        if (
            status == "complete"
            and job.patient_id == record.patient_id
            and not getattr(job, "inspection_ready", False)
            and not locked
        ):
            try:
                prepare(job.bundle_path.read_bytes(), study_id=job.study_id)
                job.inspection_ready = True
            except (ValueError, OSError) as error:
                st.error("The completed CT study could not be verified.")
                st.caption(
                    "Discard this study and run it again, or ask the local administrator to check the source bundle."
                )
                job.validation_error = str(error)
                job.inspection_ready = True
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
        st.error(f"Accepted imaging integrity check failed: {error}")
    if not accepted and "imaging_proposal" not in st.session_state:
        st.info(
            "No CT result is attached to this report snapshot. Start a new case to add CT."
            if locked
            else "No CT result yet. Run the local CT analysis below, or upload a supported synthetic bundle. Results will appear here automatically."
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
                        value=True,
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
                st.error(f"Imaging acceptance blocked: {error}")
        if st.button("Discard imaging proposal", key="imaging_discard"):
            store.discard(key)
            del st.session_state.imaging_proposal
            if job is not None and job.study_id == manifest["study_id"]:
                st.session_state.pop("ct_job", None)
            st.rerun()
    with st.expander(
        "Run or upload CT analysis",
        expanded=not accepted and "imaging_proposal" not in st.session_state,
    ):
        job = st.session_state.get("ct_job")
        running = job is not None and job.status() == "running"
        other_job = st.session_state.get("endo_job")
        cannot_add = (
            locked
            or not token
            or "imaging_proposal" in st.session_state
            or bool(other_job and other_job.status() in ("running", "complete"))
        )
        if record.patient_id == "research-composite-demo":
            st.caption(
                "Real research example · limited CT excerpt · unrelated to the endoscopy subject"
            )
            if st.button(
                "Open real CT example",
                key="ct_real_example",
                disabled=cannot_add or running,
            ):
                try:
                    from medical_assistant.research_examples import example_bundle

                    prepare(example_bundle("ct", record.patient_id))
                    st.rerun()
                except (ValueError, OSError):
                    st.error(
                        "Prepare the local research-image kit first; see docs/RESEARCH_IMAGES.md."
                    )
        mode = st.selectbox(
            "CT workflow",
            [
                "Lung nodule fixture (non-ML)",
                "Installed pretrained lung detector",
                "Legacy tissue-mask demonstration",
            ],
            key="ct_mode",
        )
        modes = {
            "Lung nodule fixture (non-ML)": "lung-fixture",
            "Installed pretrained lung detector": "lung-pretrained",
            "Legacy tissue-mask demonstration": "legacy",
        }
        model_dir = None
        device = "cpu"
        if modes[mode] == "lung-pretrained":
            model_dir = str(configured_ct_model())
            device = os.environ.get("MHCRA_CT_DEVICE", "cpu")
            st.caption(
                "Uses the installed detector on artificial CT images. No model download is needed."
            )
        if st.button(
            "Run CT analysis",
            key="ct_generate",
            disabled=cannot_add or running,
        ):
            try:
                st.session_state.ct_job = LocalCTJob(
                    record.patient_id,
                    jobs=store.root / "jobs",
                    mode=modes[mode],
                    model_dir=model_dir,
                    device=device,
                )
                st.rerun()
            except (ValueError, OSError) as error:
                st.error(str(error))
        if job:
            status = job.status()
            if getattr(job, "validation_error", None):
                st.error("CT output could not be verified: " + job.validation_error)
            st.caption(f"Study {job.study_id} · {status.replace('_', ' ')}")
            if status == "running":
                ct_progress(job)
            elif status == "complete":
                if st.button(
                    "Inspect completed CT bundle",
                    key="ct_inspect",
                    disabled=locked or job.patient_id != record.patient_id,
                ):
                    try:
                        prepare(job.bundle_path.read_bytes(), study_id=job.study_id)
                    except (ValueError, OSError) as error:
                        st.error(f"Imaging rejected: {error}")
            else:
                st.warning(job.error)
            if status != "running" and st.button("Dismiss CT job", key="ct_dismiss"):
                del st.session_state.ct_job
                st.rerun()
        with st.expander("Or upload an existing CT review bundle"):
            uploaded = st.file_uploader(
                "CT review bundle (.zip)", type=["zip"], key="ct_bundle"
            )
            if st.button(
                "Inspect uploaded CT bundle",
                key="ct_upload",
                disabled=cannot_add or running or uploaded is None,
            ):
                try:
                    prepare(uploaded.getvalue())
                except (ValueError, OSError) as error:
                    st.error("This CT bundle could not be verified.")
                    st.text(str(error))


@st.fragment(run_every=1)
def ct_progress(job):
    if job.status() != "running":
        st.rerun()
    st.info(job.progress(), icon="⏳")
    st.caption(
        f"{job.elapsed:.0f} seconds elapsed · automatic stop at {job.timeout:.0f} seconds. The study opens automatically when ready."
    )
    left, right = st.columns(2)
    with left:
        st.button("Refresh CT job", key="ct_refresh")
    with right:
        if st.button("Cancel CT job", key="ct_cancel"):
            job.cancel()
            st.rerun()

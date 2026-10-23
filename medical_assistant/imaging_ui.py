"""Imaging inspection UI; acceptance is separate from final clinical approval."""

import streamlit as st

from medical_assistant.ct_worker import (
    LocalCTJob,
    configured_ct_root,
    configured_ct_model,
)
from medical_assistant.imaging import ImagingStore
from medical_assistant.models import Review
from medical_assistant.nodule_support import is_nodule, imaging_acceptance_digest
from medical_assistant.nodule_ui import (
    nodule_viewer,
    candidate_controls,
    build_nodule_review,
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
    st.dataframe(
        [
            {
                "Class": i,
                "Heuristic meaning": manifest["classes"][str(i)],
                "Source-grid voxels": manifest["voxel_counts"][i],
                "Candidate volume (mm³)": manifest["candidate_volumes_mm3"][i],
            }
            for i in range(4)
        ],
        hide_index=True,
    )
    st.caption(
        f"Bundle-reported entropy mean: {manifest['uncertainty_mean']:.3f} — model behavior, not clinical confidence. Raw predictions; producer declares ONNX parity passed."
    )
    with st.expander("Imaging identity and source provenance"):
        st.json(manifest)


def imaging_ui(path, auth, token, user, record, *, locked=False):
    st.subheader("CT review")
    st.caption(
        "Add image context to the patient story. Inspect candidates and optional measurements before accepting a research appendix."
    )
    if "imaging_store" not in st.session_state:
        st.session_state.imaging_store = ImagingStore(path, auth)
    store = st.session_state.imaging_store

    def prepare(payload, *, study_id=None):
        result = store.prepare(payload, record.patient_id, study_id=study_id)
        if "imaging_proposal" in st.session_state:
            store.discard(st.session_state.imaging_proposal[0])
        st.session_state.imaging_proposal = result

    job = st.session_state.get("ct_job")
    running = job is not None and job.status() == "running"
    with st.expander("Local CT connection · settings"):
        st.text("Companion: " + str(configured_ct_root()))
        st.caption(
            "Uses a separate local Python environment. No images are sent to the language model."
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
        model_dir = st.text_input(
            "Installed local nodule model directory",
            str(configured_ct_model()),
            key="ct_model_dir",
        )
        device = st.selectbox("CT inference device", ["cpu", "cuda"], key="ct_device")
        st.caption(
            "Uses installed weights on generated synthetic CT. No download occurs; unavailable CUDA fails explicitly."
        )
    if st.button(
        "Generate synthetic CT demonstration",
        key="ct_generate",
        disabled=locked or running or not token,
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
                with st.expander("CT validation details"):
                    st.text(str(error))
                job.inspection_ready = True
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
    with st.expander("Or upload an existing synthetic CT bundle"):
        uploaded = st.file_uploader(
            "Synthetic CT review bundle (.zip)", type=["zip"], key="ct_bundle"
        )
        if st.button(
            "Inspect uploaded CT bundle",
            key="ct_upload",
            disabled=locked or uploaded is None,
        ):
            try:
                prepare(uploaded.getvalue())
            except (ValueError, OSError) as error:
                st.error("This CT bundle could not be verified.")
                st.text(str(error))
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
                    notes = st.text_area("Imaging review notes", key="imaging_notes")
                    attested = st.checkbox(
                        "I checked the synthetic patient/study association, overlays, geometry and research limitations.",
                        key="imaging_attest",
                    )
                    submit = st.form_submit_button(
                        "Accept imaging for research appendix",
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
    try:
        accepted = store.snapshots(record.patient_id)
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
                f"Accepted by {snapshot['review']['reviewer']}. A new clinical case includes this fixed imaging snapshot in its draft appendix."
            )
            _viewer(
                snapshot["manifest"],
                store.preview_resolver(snapshot),
                "accepted_ct_slice_" + snapshot["archive_sha256"],
                review=snapshot.get("nodule_review"),
            )
    except (ValueError, OSError) as error:
        st.error(f"Accepted imaging integrity check failed: {error}")


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

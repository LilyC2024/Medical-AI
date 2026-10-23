"""Authenticated image input routing, independent of Streamlit rendering.

ZIPs contain existing predictions: Analyze validates and opens them for review.
Only a raw, permitted endoscopy image launches inference on uploaded pixels.
Nothing in this module accepts a study or approves a clinical report.
"""

import os
from pathlib import Path

from medical_assistant.ct_worker import LocalCTJob, configured_ct_model
from medical_assistant.endo_support import is_endoscopy
from medical_assistant.endo_worker import LocalEndoscopyJob
from medical_assistant.imaging_contract import MAX_ARCHIVE
from medical_assistant.research_examples import example_bundle, matching_endoscopy
from medical_assistant.ui.navigation import reset_report_context


def job_pending(job):
    """A collected result is represented by its proposal, not a stale job handle."""
    return bool(
        job
        and (
            job.status() == "running"
            or (
                job.status() == "complete"
                and not getattr(job, "inspection_ready", False)
            )
        )
    )


def failure_detail(job):
    """Return the bounded worker exception, without a traceback or full log dump."""
    message = job.error or "Image processing failed. Retry Analyze."
    try:
        path = job.log_path
        with path.open("rb") as handle:
            handle.seek(max(0, path.stat().st_size - 4096))
            lines = handle.read(4096).decode("utf-8", errors="replace").splitlines()
        detail = next(
            (
                line.strip()
                for line in reversed(lines)
                if "Error:" in line or line.startswith("Error: ")
            ),
            "",
        )
        if detail:
            return message + " " + detail[:500]
    except (AttributeError, OSError):
        pass
    return message


def blocker(state):
    if state.get("proposal"):
        return "Finish or discard the record import in Source records first."
    if state.get("imaging_proposal"):
        manifest = state["imaging_proposal"][1]["manifest"]
        view = "Endoscopy review" if is_endoscopy(manifest) else "CT review"
        return (
            f"Include or discard the pending study in {view} before analyzing another."
        )
    for key, name in (("ct_job", "CT"), ("endo_job", "Endoscopy")):
        job = state.get(key)
        if job and job.status() == "running":
            return f"{name} analysis is running. Wait for the result or cancel it in {name} review."
    return None


def analyze(state, store, auth, token, patient, modality, *, upload=None, mode="auto"):
    """Validate input before retiring a frozen report; never silently use a demo.

    ``upload`` is (filename, bytes). Mode applies only when there is no upload.
    An uploaded ZIP always opens its included results, regardless of example mode.
    Failed input validation leaves the existing report and all approvals intact.
    """
    auth.require(token)
    if modality not in ("ct", "endoscopy"):
        raise ValueError("Unknown imaging section")
    reason = blocker(state)
    if reason:
        raise ValueError(reason)
    payload = None
    job = None
    completed = None
    if upload is not None:
        name, raw = upload
        if not raw or len(raw) > MAX_ARCHIVE:
            raise ValueError("Upload a nonempty file no larger than 64 MiB.")
        suffix = Path(name).suffix.lower()
        if suffix == ".zip":
            payload = raw
        elif modality == "endoscopy" and suffix in (".jpg", ".jpeg", ".png"):
            provenance = matching_endoscopy(raw, patient)
            job = LocalEndoscopyJob(
                patient,
                jobs=store.root / "endo-jobs",
                mode="installed",
                image_bytes=raw,
                research=provenance,
                backend=os.environ.get("LOVISA_ENDO_BACKEND", "onnx-cpu"),
            )
        else:
            raise ValueError(
                "CT requires a companion review ZIP, not a preview image or raw DICOM."
                if modality == "ct"
                else "Upload an endoscopy JPG, PNG or review ZIP."
            )
    elif (
        mode == "auto"
        and (completed := state.get("ct_job" if modality == "ct" else "endo_job"))
        and completed.status() == "complete"
        and not getattr(completed, "inspection_ready", False)
    ):
        if completed.patient_id != patient:
            raise ValueError("Completed result belongs to another patient.")
        payload = completed.bundle_path.read_bytes()
    elif mode == "research-example":
        payload = example_bundle(modality, patient)
    elif modality == "ct" and mode in ("lung-fixture", "lung-pretrained", "legacy"):
        job = LocalCTJob(
            patient,
            jobs=store.root / "jobs",
            mode=mode,
            model_dir=str(configured_ct_model()) if mode == "lung-pretrained" else None,
            device=os.environ.get("MHCRA_CT_DEVICE", "cpu")
            if mode == "lung-pretrained"
            else "cpu",
        )
    elif modality == "endoscopy" and mode in ("fixture", "installed"):
        job = LocalEndoscopyJob(
            patient,
            jobs=store.root / "endo-jobs",
            mode=mode,
            backend=os.environ.get("LOVISA_ENDO_BACKEND", "onnx-cpu")
            if mode == "installed"
            else "onnx-cpu",
        )
    else:
        raise ValueError(
            "Choose a file with Upload, or select a local example under Model / example."
        )
    result = None
    if payload is not None:
        result = store.prepare(
            payload, patient, study_id=completed.study_id if completed else None
        )
        try:
            manifest = result[1]["manifest"]
            if is_endoscopy(manifest) != (modality == "endoscopy"):
                raise ValueError(
                    "This file belongs to the other imaging section. Upload it there."
                )
            if any(
                s["manifest"]["study_id"] == manifest["study_id"]
                for s in store.snapshots(patient)
            ):
                raise ValueError(
                    "This study is already included. Inspect its results below or upload a different study."
                )
        except Exception:
            store.discard(result[0])
            raise
    reset_report_context(state)
    # A new Analyze action supersedes this section's old terminal job. Other
    # uninspected results remain discoverable; their proposal is never replaced.
    state.pop("ct_job" if modality == "ct" else "endo_job", None)
    state.pop(f"{modality}_action_error", None)
    if result is not None:
        state["imaging_proposal"] = result
        if completed:
            completed.inspection_ready = True
        state[f"{modality}_action_notice"] = (
            "Included analysis loaded and verified. Inspect the results below before including them in the report."
        )
    else:
        state["ct_job" if modality == "ct" else "endo_job"] = job
        state[f"{modality}_action_notice"] = (
            "Analysis started locally. Results will appear below when ready."
        )


def collect(state, store, modality, patient):
    """Publish one completed result without overwriting a pending/frozen review."""
    job = state.get("ct_job" if modality == "ct" else "endo_job")
    if (
        not job
        or job.status() != "complete"
        or getattr(job, "inspection_ready", False)
        or state.get("imaging_proposal")
        or state.get("case_id")
        or state.get("analysis_task")
    ):
        return
    try:
        if job.patient_id != patient:
            raise ValueError(
                "Result belongs to another patient; select the matching patient."
            )
        result = store.prepare(
            job.bundle_path.read_bytes(), patient, study_id=job.study_id
        )
        if is_endoscopy(result[1]["manifest"]) != (modality == "endoscopy"):
            store.discard(result[0])
            raise ValueError("Worker result belongs to the other imaging section.")
        state["imaging_proposal"] = result
        state.pop(f"{modality}_action_error", None)
        state[f"{modality}_action_notice"] = (
            "Analysis complete. Inspect the results below before including them in the report."
        )
    except (ValueError, OSError) as error:
        job.validation_error = str(error)
        state[f"{modality}_action_error"] = f"Result could not be verified: {error}"
    job.inspection_ready = True

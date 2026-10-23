"""Responsive clinical UI; only explicit human actions issue review receipts."""

import json

import streamlit as st

from medical_assistant import ollama_client, storage
from medical_assistant.jobs import BudgetInference, WorkTask
from medical_assistant.models import Review
from medical_assistant.report import digest
from medical_assistant.report_assets import inspection_figures, portable_html
from medical_assistant.ui.components import empty
from medical_assistant.ui.navigation import clear_patient, go_to
from medical_assistant.workflow import MedicalHistoryOrchestrator

STAGES = {
    "safety": "Organizing the supplied history",
    "history": "Checking medication sources",
    "medications": "Looking up approved local references",
    "evidence_retrieval": "Preparing hypotheses with local AI",
    "reasoning": "Rechecking safety and source evidence",
    "safety_review": "Composing your review draft",
    "orchestrator": "Preparing the clinician review",
    "__interrupt__": "Ready for human review",
}


def make_review(approved, user, checked, notes, sha256):
    return Review(
        approved=approved,
        reviewer=user or "",
        clinician_attestation=checked,
        notes=notes,
        draft_sha256=sha256,
    )


def start_task(path, auth, patient_id, model, *, review=None, token=None):
    def run(progress, budget):
        client = ollama_client.OllamaClient(model)
        workflow = MedicalHistoryOrchestrator(
            BudgetInference(client, budget), auth=auth
        )
        try:
            progress("Checking safety and the source snapshot")
            case, events = workflow.start_patient(patient_id, path, safety_only=True)
            for event in events:
                budget.check()
                progress(
                    next(
                        (STAGES[k] for k in event if k in STAGES),
                        "Checking the review workflow",
                    )
                )
            if review is not None:
                workflow.acknowledge_safety(case, review, token, safety_only=True)
            budget.check()
            workflow.inference = client
            return workflow, case
        except Exception:
            client.close()
            raise

    return WorkTask(run, title="Checking your source record")


def resume_task(workflow, case, review, token):
    def run(progress, budget):
        original = workflow.inference
        workflow.inference = BudgetInference(original, budget)
        try:
            progress("Applying your decision and preparing local reasoning")
            workflow.acknowledge_safety(case, review, token, safety_only=True)
            budget.check()
            return workflow, case
        finally:
            workflow.inference = original
            if budget.stopped.is_set():
                original.close()

    return WorkTask(run, title="Applying the safety review")


def collect_task():
    """Publish only a completed, in-budget result into this Streamlit session."""
    task = st.session_state.get("analysis_task")
    if task is None:
        return
    snap = task.snapshot()
    if snap["state"] == "running":
        return
    st.session_state.last_analysis_seconds = round(snap["elapsed"], 2)
    if snap["state"] == "complete":
        workflow, case = task.result()
        st.session_state.workflow = workflow
        st.session_state.case_id = case
        st.session_state.pop("run_error", None)
        if workflow.state(case)["status"] == "awaiting_clinician_review":
            st.session_state.navigate_to = "Clinical report"
    else:
        st.session_state.run_error = snap["error"]
    del st.session_state.analysis_task


@st.fragment(run_every=1)
def task_progress():
    task = st.session_state.get("analysis_task")
    if task is None:
        return
    snap = task.snapshot()
    if snap["state"] != "running":
        st.rerun()
    st.info(snap["step"], icon="⏳")
    st.caption(
        f"{snap['elapsed']:.0f} seconds elapsed · automatic stop at {snap['limit']:.0f} seconds. You can cancel at any time."
    )
    if st.button("Cancel analysis", key="analysis_cancel"):
        task.cancel()
        st.rerun()


@st.fragment(run_every=1)
def background_progress():
    """Keep completion responsive when the reviewer opens a different view."""
    task = st.session_state.get("analysis_task")
    if task is not None:
        if task.snapshot()["state"] != "running":
            st.rerun()
        st.caption(
            "Preparing your report… Open Safety check for progress or cancellation."
        )


def generate_task(workflow, case, token):
    def run(progress, budget):
        original = workflow.inference
        workflow.inference = BudgetInference(original, budget)
        try:
            progress("Preparing your source-linked draft with local AI")
            workflow.continue_analysis(case, token)
            budget.check()
            return workflow, case
        finally:
            workflow.inference = original
            if budget.stopped.is_set():
                original.close()

    return WorkTask(run, title="Rechecking safety before clinical reasoning")


def bottom_actions(path, auth, record, model, token, user, decision):
    """Safety first, then one explicit bottom-of-page generation action."""
    st.subheader("Safety check")
    st.caption(
        "Review the missing information below, record your decision, then generate a draft."
    )
    task = st.session_state.get("analysis_task")
    state = (
        st.session_state.workflow.state(st.session_state.case_id)
        if "case_id" in st.session_state and task is None
        else {}
    )
    ct = st.session_state.get("ct_job")
    endo = st.session_state.get("endo_job")
    pending = (
        "proposal" in st.session_state
        or "imaging_proposal" in st.session_state
        or bool(ct and ct.status() in ("running", "complete"))
        or bool(endo and endo.status() in ("running", "complete"))
    )
    status = state.get("status")
    stale = bool(
        state
        and state["safety_decision"]["decision_sha256"] != decision["decision_sha256"]
    )
    ready = False
    if task:
        task_progress()
    elif decision["state"] == "urgent":
        st.error(
            "Stop: a warning sign is recorded. Human assessment is required; draft generation is blocked. Start a new case only after an approved source update when appropriate."
        )
    elif stale:
        st.error(
            "Sources, policy or date changed. Start a new case and repeat the safety check."
        )
    elif st.session_state.get("run_error"):
        failure()
    elif status == "running":
        ready = True
        st.success(
            "Required safety checks are complete for this snapshot. You can now generate the draft."
        )
        st.caption(
            "This is permission to run the research workflow, not a finding that the patient is safe."
        )
    elif status == "awaiting_clinician_review":
        st.info(
            "Your draft is ready in Clinical report. Check its sources and submit the separate final review."
        )
    elif status == "complete":
        st.success("The reviewed report is ready in Clinical report.")
    elif status == "stopped_for_human_review":
        st.warning(
            "You kept this case paused for human assessment. Start a new case to reassess it."
        )
    elif pending:
        st.info("A pending record or imaging study needs review first.")
        target = "source-records" if "proposal" in st.session_state else "ct-review"
        from medical_assistant.endo_support import is_endoscopy

        proposal = st.session_state.get("imaging_proposal")
        if (proposal and is_endoscopy(proposal[1]["manifest"])) or (
            endo and endo.status() in ("running", "complete")
        ):
            target = "endoscopy-review"
        st.button(
            "Open pending changes", key="open_pending", on_click=go_to, args=(target,)
        )
    elif decision["state"] == "uncertain":
        st.markdown("**Safety check: current information needs review**")
        for item in decision["assessment"]["missing_information"]:
            st.text("• " + item)
        st.caption(
            "Assess these gaps first. Saving this decision will not start the model or approve the final report."
        )
        with st.form("safety_form"):
            notes = st.text_area(
                "Your assessment of the missing information", key="safety_notes"
            )
            checked = st.checkbox(
                "I reviewed these gaps and take responsibility for the decision below.",
                key="safety_attest",
            )
            action = st.radio(
                "Next step",
                [
                    "Keep analysis paused",
                    "Allow draft generation after my safety assessment",
                ],
                key="safety_action",
            )
            submit = st.form_submit_button(
                "Save safety assessment", key="submit_safety", disabled=not token
            )
        if submit:
            try:
                auth.require(token)
                review = make_review(
                    action.startswith("Allow"),
                    user,
                    checked,
                    notes,
                    decision["decision_sha256"],
                )
                st.session_state.analysis_task = (
                    resume_task(
                        st.session_state.workflow,
                        st.session_state.case_id,
                        review,
                        token,
                    )
                    if status == "awaiting_safety_review"
                    else start_task(
                        path, auth, record.patient_id, model, review=review, token=token
                    )
                )
                st.rerun()
            except (ValueError, PermissionError):
                st.error(
                    "Add assessment notes and tick the review checkbox before saving. If the record changed, start a new review."
                )
    else:
        st.info(
            "The required current structured observations are supplied. Confirm the source snapshot before generation."
        )
        if st.button(
            "Confirm required safety checks", key="preflight", disabled=not token
        ):
            st.session_state.analysis_task = start_task(
                path, auth, record.patient_id, model, token=token
            )
            st.rerun()
    if st.button(
        "Generate draft for clinician review",
        key="generate",
        type="primary",
        width="stretch",
        disabled=not ready or bool(task) or pending or stale or not token,
    ):
        try:
            auth.require(token)
            st.session_state.analysis_task = generate_task(
                st.session_state.workflow, st.session_state.case_id, token
            )
            st.rerun()
        except (ValueError, PermissionError) as error:
            st.error(str(error))
    st.caption(
        "Final clinician approval is a separate step after the draft. Research use only; this safety gate is not regulatory certification."
    )


def failure():
    st.error(
        "This run stopped before producing a reviewed report. Start a new case or retry the draft."
    )
    st.caption(
        "Check the local service and source records, then start a new review. No report has been approved."
    )


def new_report_with_ct():
    clear_patient(st.session_state)
    go_to("ct-review")


def report_content(state, workflow):
    """Short summary and verified representative CT images, with optional readable evidence."""
    with st.container(key="report_paper"):
        st.markdown(state.get("final_report", state["draft"]))
        figures = inspection_figures(state, workflow.imaging_store)
        for figure in figures:
            left, right = st.columns(2)
            left.image(figure.source_png, caption=figure.source_label, width="stretch")
            right.image(
                figure.overlay_png, caption=figure.annotation_label, width="stretch"
            )
            st.caption(figure.caption)
        if len(state.get("imaging", [])) > len(figures):
            st.caption(
                "Representative images from the first three studies are shown; all studies remain in the imaging review views and the evidence package."
            )
    if not state.get("imaging"):
        st.button(
            "Start a new report with CT",
            key="new_report_ct",
            on_click=new_report_with_ct,
        )
    indexed = {e["entry_id"]: e for e in state["report_evidence"]["record_entries"]}
    with st.expander("Evidence behind the analysis · optional"):
        for hypothesis in state["report_evidence"]["hypotheses"]:
            st.text(hypothesis["possibility"] + " — unverified hypothesis")
            for label, field in [
                ("Model-selected support", "supporting_ids"),
                ("Model-selected counterevidence", "conflicting_ids"),
            ]:
                for entry_id in hypothesis[field]:
                    entry = indexed[entry_id]
                    st.text(
                        f"{label} · {entry['filename']} · {entry['date'] or 'date not supplied'} · {entry['source_type'].replace('_', ' ')}"
                    )
                    st.text(entry["excerpt"])
        st.caption(
            "Full source links, original documents and imaging provenance remain in the evidence package."
        )


def report_panel(auth, token, user, record, *, urgent=False):
    if st.session_state.get("analysis_task"):
        empty(
            "Your draft is being prepared",
            "The workspace stays available while local processing runs. Open Safety check for progress and cancellation.",
        )
        return
    if st.session_state.get("run_error"):
        failure()
        return
    if "case_id" not in st.session_state:
        empty(
            "A clearer report starts with the source",
            "Review the patient story and optional imaging, open Safety check, then generate a draft. Final approval comes later.",
        )
        return
    workflow, case = st.session_state.workflow, st.session_state.case_id
    state = workflow.state(case)
    decision = state.get("safety_decision")
    if urgent and decision and decision["state"] != "urgent":
        st.error(
            "A newly supplied warning is outside this case snapshot. Stop review and start a new case for human assessment."
        )
        return
    if state["status"] in ("running", "awaiting_safety_review"):
        empty(
            "Complete the safety check",
            "Open Safety check, then choose Generate draft for clinician review. No reasoning runs when you save a safety assessment.",
        )
    elif state["status"] == "stopped_for_human_review":
        st.info(
            "Analysis stopped for human assessment. No clinical report was completed."
        )
    elif state["status"] == "awaiting_clinician_review":
        if not state.get("report_evidence"):
            st.info(
                "This draft uses the earlier report format. Start a new review to create the concise combined report."
            )
            st.button(
                "Start a new report", key="new_report_ct", on_click=new_report_with_ct
            )
            return
        if st.session_state.pop("report_note_changed", False):
            st.session_state.pop("attested", None)
            st.success(
                "Note added to the preview. Read the updated report, then confirm your review again."
            )
        st.subheader("Draft report")
        st.caption(
            "Unverified · clinician review required. Hypotheses are not confirmed diagnoses."
        )
        try:
            workflow._verify_report(state)
            report_content(state, workflow)
        except (ValueError, OSError, PermissionError):
            st.error(
                "Report evidence needs rechecking. Start a new review before approval."
            )
            return
        with st.form("clinical_review"):
            st.subheader("Your review decision")
            notes = st.text_area(
                "Brief clinician note / review feedback",
                key="review_notes",
                max_chars=600,
            )
            st.caption(
                "Preview this note to include it in the report. New clinical facts need an approved record import."
            )
            preview_note = st.form_submit_button(
                "Preview note in report", key="preview_report_note", disabled=not token
            )
            checked = st.checkbox(
                "I reviewed the clinical summary, imaging inspections, source evidence and remaining limitations.",
                key="attested",
            )
            action = st.radio(
                "Review decision",
                ["Request corrections / keep pending", "Approve report"],
                key="decision",
            )
            submit = st.form_submit_button(
                "Submit clinician review",
                key="submit_review",
                disabled=not token,
                type="primary",
            )
        if preview_note:
            try:
                workflow.prepare_report_note(case, notes, token)
                st.session_state.report_note_changed = True
                st.rerun()
            except (ValueError, PermissionError, OSError):
                st.error(
                    "The note could not be added. Keep it within 600 characters and recheck the report sources."
                )
        if submit:
            try:
                if (
                    action == "Approve report"
                    and state.get("clinician_note", {}).get("text") != notes.strip()
                ):
                    raise ValueError("Preview the changed note before approval")
                workflow.review(
                    case,
                    make_review(
                        action == "Approve report",
                        user,
                        checked,
                        notes,
                        digest(state["draft"]),
                    ),
                    token,
                )
                st.rerun()
            except (ValueError, PermissionError):
                st.error(
                    "Preview your current note first, then check the review checkbox and sign-in before approving."
                )

    elif state["status"] == "complete":
        try:
            payload = workflow.export(case)
            if "saved_path" not in st.session_state:
                st.session_state.saved_path = str(
                    storage.save_report(payload, auth=auth, safety=workflow.safety)
                )
            st.success(
                "Reviewed report ready. Approved by " + payload["review"]["reviewer"]
            )
            a, b, c = st.columns(3)
            with a:
                st.download_button(
                    "Download report with imaging (HTML)"
                    if any(
                        s["manifest"].get("schema_version") == "lovisa-endo-image-v1"
                        for s in payload.get("imaging", [])
                    )
                    else "Download report with CT images (HTML)",
                    portable_html(payload, auth=auth, safety=workflow.safety),
                    file_name=f"reviewed-{case}.html",
                    mime="text/html",
                    width="stretch",
                )
            with b:
                st.download_button(
                    "Download reviewed report (Markdown)",
                    payload["final_report"],
                    file_name=f"reviewed-{case}.md",
                    mime="text/markdown",
                    width="stretch",
                )
            with c:
                st.download_button(
                    "Download evidence package (JSON)",
                    json.dumps(payload, indent=2),
                    file_name=f"reviewed-{case}.json",
                    mime="application/json",
                    width="stretch",
                )
            report_content(payload, workflow)
        except (ValueError, PermissionError, OSError):
            st.error("Final export blocked. The source or approval needs rechecking.")

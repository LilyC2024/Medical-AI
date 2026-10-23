"""Responsive clinical UI; only explicit human actions issue review receipts."""

import json
import streamlit as st
from medical_assistant import ollama_client, storage
from medical_assistant.jobs import WorkTask, BudgetInference
from medical_assistant.models import Review
from medical_assistant.report import digest
from medical_assistant.workflow import MedicalHistoryOrchestrator
from medical_assistant.ui.components import empty

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

    return WorkTask(run, title="Rechecking safety before clinical reasoning")


def bottom_actions(path, auth, record, model, token, user, decision):
    """Safety first, then one explicit bottom-of-page generation action."""
    st.divider()
    st.subheader("Before you generate the draft")
    st.caption(
        "1. Review the sources and optional CT. 2. Resolve the safety check. 3. Generate an unreviewed draft."
    )
    task = st.session_state.get("analysis_task")
    state = (
        st.session_state.workflow.state(st.session_state.case_id)
        if "case_id" in st.session_state and task is None
        else {}
    )
    ct = st.session_state.get("ct_job")
    pending = (
        "proposal" in st.session_state
        or "imaging_proposal" in st.session_state
        or bool(ct and ct.status() in ("running", "complete"))
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
        st.info(
            "Review or discard the pending history/CT changes before completing the safety check."
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
            except (ValueError, PermissionError) as error:
                st.error(
                    "Add assessment notes and tick the review checkbox before saving. "
                    + str(error)
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
    with st.expander("Why this run stopped"):
        st.text(st.session_state.run_error)


def report_panel(auth, token, user, record, *, urgent=False):
    if st.session_state.get("analysis_task"):
        empty(
            "Your draft is being prepared",
            "The workspace stays available while local processing runs. Progress and cancellation are shown at the bottom.",
        )
        return
    if st.session_state.get("run_error"):
        failure()
        return
    if "case_id" not in st.session_state:
        empty(
            "A clearer report starts with the source",
            "Review the patient story and optional CT, complete the safety check at the bottom, then generate a draft. Final approval comes later.",
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
            "Complete the steps below",
            "Resolve the safety check at the bottom, then choose Generate draft for clinician review. No reasoning runs when you save a safety assessment.",
        )
    elif state["status"] == "stopped_for_human_review":
        st.info(
            "Analysis stopped for human assessment. No clinical report was completed."
        )
    elif state["status"] == "awaiting_clinician_review":
        st.subheader("Draft report")
        st.caption(
            "Unverified · clinician review required. Hypotheses are not confirmed diagnoses."
        )
        with st.container(key="report_paper"):
            st.markdown(state["draft"])
        with st.form("clinical_review"):
            st.subheader("Your review decision")
            notes = st.text_area(
                "Review notes and required corrections", key="review_notes"
            )
            checked = st.checkbox(
                "I verified sources, hypotheses, medication reconciliation and safety limitations.",
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
        if submit:
            try:
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
            except (ValueError, PermissionError) as error:
                st.error("Review rejected. Check your notes, attestation and sign-in.")
                with st.expander("Review details"):
                    st.text(str(error))
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
            a, b = st.columns(2)
            with a:
                st.download_button(
                    "Download reviewed report (Markdown)",
                    payload["final_report"],
                    file_name=f"reviewed-{case}.md",
                    mime="text/markdown",
                    width="stretch",
                )
            with b:
                st.download_button(
                    "Download reviewed report (JSON)",
                    json.dumps(payload, indent=2),
                    file_name=f"reviewed-{case}.json",
                    mime="application/json",
                    width="stretch",
                )
            with st.container(key="report_paper"):
                st.markdown(payload["final_report"])
            with st.expander("Local save location"):
                st.text(st.session_state.saved_path)
        except (ValueError, PermissionError, OSError) as error:
            st.error("Final export blocked. The source or approval needs rechecking.")
            with st.expander("Export details"):
                st.text(str(error))

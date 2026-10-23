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


def start_task(path, auth, patient_id, model):
    def run(progress, budget):
        client = ollama_client.OllamaClient(model)
        workflow = MedicalHistoryOrchestrator(
            BudgetInference(client, budget), auth=auth
        )
        try:
            progress("Checking safety and the source snapshot")
            case, events = workflow.start_patient(patient_id, path)
            for event in events:
                budget.check()
                progress(
                    next(
                        (STAGES[k] for k in event if k in STAGES),
                        "Checking the review workflow",
                    )
                )
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
            workflow.acknowledge_safety(case, review, token)
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


def action_bar(path, auth, record, model, *, urgent=False):
    task = st.session_state.get("analysis_task")
    ct = st.session_state.get("ct_job")
    pending = not urgent and (
        "imaging_proposal" in st.session_state
        or (ct and ct.status() in ("running", "complete"))
    )
    active = "case_id" in st.session_state or task is not None
    left, right = st.columns([3, 2], vertical_alignment="center")
    with left:
        st.caption("A source-linked draft, with you in control of every approval.")
        if pending:
            st.caption(
                "Review or discard the pending CT study before preparing a draft."
            )
        elif "proposal" in st.session_state:
            st.caption("Review or discard the pending history import first.")
    with right:
        if st.button(
            "Generate draft for clinician review",
            key="generate",
            type="primary",
            width="stretch",
            disabled=active or "proposal" in st.session_state or bool(pending),
        ):
            try:
                st.session_state.pop("run_error", None)
                st.session_state.analysis_task = start_task(
                    path, auth, record.patient_id, model
                )
                st.rerun()
            except Exception as error:
                st.session_state.run_error = str(error)
    if task is not None:
        task_progress()


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
            "The workspace stays available while local processing runs. Progress and cancellation are shown above.",
        )
        return
    if st.session_state.get("run_error"):
        failure()
        return
    if "case_id" not in st.session_state:
        empty(
            "A clearer report starts with the source",
            "Review the patient story and optional CT, then choose Generate draft for clinician review. You will approve the final report separately.",
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
    if decision:
        message = (
            "Human assessment is required. Automated reasoning cannot continue in this urgent case."
            if decision["state"] == "urgent"
            else "Current safety information is incomplete. A human assessment is required before reasoning."
            if decision["state"] == "uncertain"
            else "The record is eligible for this workflow. This does not establish clinical safety."
        )
        (
            st.error
            if decision["state"] == "urgent"
            else st.warning
            if decision["state"] == "uncertain"
            else st.info
        )(message)
        with st.expander("Safety decision and source scope · details"):
            st.text(decision["meaning"])
            st.json(decision)
    if state["status"] == "awaiting_safety_review":
        st.subheader("Human safety assessment required before reasoning")
        st.caption(
            "Review the missing information. Continuing is an explicit human decision, not a safety clearance."
        )
        with st.form("safety_form"):
            notes = st.text_area(
                "Safety review notes",
                key="safety_notes",
                placeholder="Record your assessment of the missing information…",
            )
            checked = st.checkbox(
                "I assessed the missing information and understand this remains an uncertain synthetic case.",
                key="safety_attest",
            )
            action = st.radio(
                "Safety decision",
                [
                    "Stop for human assessment",
                    "Continue after clinician assessment of uncertainty",
                ],
                key="safety_action",
                disabled=decision["state"] == "urgent",
            )
            submit = st.form_submit_button(
                "Submit safety decision",
                key="submit_safety",
                disabled=not token,
                type="primary",
            )
        if submit:
            try:
                review = make_review(
                    action.startswith("Continue"),
                    user,
                    checked,
                    notes,
                    decision["decision_sha256"],
                )
                # Authentication is checked immediately and again inside the graph.
                if auth.require(token) != review.reviewer:
                    raise PermissionError("Reviewer identity mismatch")
                st.session_state.analysis_task = resume_task(
                    workflow, case, review, token
                )
                st.rerun()
            except Exception as error:
                st.error(
                    "Safety decision rejected. Check the notes, attestation and sign-in."
                )
                with st.expander("Review details"):
                    st.text(str(error))
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

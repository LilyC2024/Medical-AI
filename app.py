"""MHCRA AI: loopback-only synthetic history management and clinical review."""
import json
from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

import medical_assistant  # noqa: F401 — tracing disabled before LangGraph imports
import streamlit as st

from medical_assistant.database import get_history, list_patients
from medical_assistant.history import MedicationAgent, chronology
from medical_assistant.history_import import HistoryManagement
from medical_assistant.models import Review
from medical_assistant.ollama_client import OllamaClient
from medical_assistant.report import NOTICE, digest
from medical_assistant.runtime import get_services
from medical_assistant.storage import save_report
from medical_assistant.workflow import MedicalHistoryOrchestrator


def account_ui(auth):
    token = st.session_state.get("auth_token")
    if token:
        try:
            user = auth.require(token)
            st.sidebar.success(f"Signed in: {user}")
            if st.sidebar.button("Sign out", key="logout"):
                auth.logout(token)
                st.session_state.pop("auth_token", None)
                st.rerun()
            return token, user
        except PermissionError:
            st.session_state.pop("auth_token", None)
    if not auth.has_users():
        st.sidebar.info("Create a local reviewer account with: .venv/bin/python -m medical_assistant.auth")
    with st.sidebar.form("login_form"):
        username = st.text_input("Local clinician account", key="login_user")
        password = st.text_input("Password", type="password", key="login_password")
        submitted = st.form_submit_button("Sign in", key="login")
    if submitted:
        try:
            st.session_state.auth_token = auth.login(username, password)
            st.rerun()
        except PermissionError as error:
            st.sidebar.error(str(error))
    return None, None


def make_review(approved, user, checked, notes, sha256):
    return Review(approved=approved, reviewer=user or "", clinician_attestation=checked,
                  notes=notes, draft_sha256=sha256)


def history_ui(path, auth, token, user, record):
    if "imports" not in st.session_state:
        st.session_state.imports = HistoryManagement(path, auth=auth)
    manager = st.session_state.imports
    def replace_proposal(result):
        if "proposal" in st.session_state:
            manager.pending.pop(st.session_state.proposal[0], None)
        st.session_state.proposal = result
    with st.expander("Import a synthetic medical record / add observations"):
        uploaded = st.file_uploader("Synthetic JSON record", type=["json"], key="import_file")
        if st.button("Preview JSON import", key="preview_import", disabled=uploaded is None):
            try:
                proposal_id, proposal = manager.prepare(uploaded.getvalue().decode("utf-8"), uploaded.name)
                replace_proposal((proposal_id, proposal))
            except (ValueError, OSError, LookupError) as error:
                st.error(f"Import rejected: {error}")
        with st.form("symptom_form"):
            symptom = st.text_area("Synthetic symptoms / history to add", key="symptoms")
            known = st.checkbox("The observation date is known", key="symptom_date_known")
            day = st.date_input("Observation date (used only when known)", datetime.now(ZoneInfo("Europe/Amsterdam")).date(), key="symptom_date")
            warning = st.selectbox("Explicit current warning-sign screening", ["unknown", "absent", "present"], key="warning_screen")
            measured = st.checkbox("A blood-pressure measurement was supplied", key="bp_supplied")
            left, right = st.columns(2)
            systolic = left.number_input("Supplied systolic (mmHg)", min_value=1.0, value=120.0, key="systolic")
            diastolic = right.number_input("Supplied diastolic (mmHg)", min_value=1.0, value=80.0, key="diastolic")
            preview = st.form_submit_button("Prepare observation proposal", key="prepare_symptom")
        st.caption("Numbers are used only if the measurement checkbox is selected. The app does not classify blood-pressure values or diagnose emergencies.")
        if preview:
            try:
                if not symptom.strip():
                    raise ValueError("Enter synthetic symptom/history text before preparing a proposal")
                data = {"fictional": True, "patient_id": record.patient_id, "display_name": record.display_name,
                    "entries": [{"id": "observation-" + uuid4().hex, "date": day.isoformat() if known else None,
                        "source_type": "patient_reported", "kind": "symptom", "text": symptom,
                        "warning_screen": warning, "blood_pressure": {"systolic": systolic, "diastolic": diastolic} if measured else None}]}
                replace_proposal(manager.prepare(json.dumps(data), "synthetic-observation.json"))
            except ValueError as error:
                st.error(f"Observation proposal rejected: {error}")
    if "proposal" in st.session_state:
        proposal_id, proposal = st.session_state.proposal
        st.subheader("Pending history import — no database update yet")
        st.json(proposal)
        with st.form("import_approval"):
            notes = st.text_area("Import review notes", key="import_notes")
            checked = st.checkbox("I verified this synthetic source and the proposed facts.", key="import_attest")
            submit = st.form_submit_button("Approve history import", key="approve_import", disabled=not token)
        if submit:
            try:
                review = make_review(True, user, checked, notes, proposal["sha256"])
                manager.approve(proposal_id, review, token)
                del st.session_state.proposal
                st.rerun()
            except (ValueError, PermissionError, LookupError) as error:
                st.error(f"Import approval rejected: {error}")
        if st.button("Discard import proposal", key="discard_import"):
            manager.pending.pop(proposal_id, None)
            del st.session_state.proposal
            st.rerun()


def clinical_ui(path, auth, token, user, record, model):
    active = "case_id" in st.session_state
    if st.button("Generate draft for clinician review", key="generate", type="primary", disabled=active or "proposal" in st.session_state):
        st.session_state.pop("run_error", None)
        try:
            workflow = MedicalHistoryOrchestrator(OllamaClient(model), auth=auth)
            st.session_state.workflow = workflow
            case_id, events = workflow.start_patient(record.patient_id, path)
            st.session_state.case_id = case_id
            with st.status("Applying deterministic safety policy…"):
                for event in events:
                    st.write(", ".join(event))
            st.rerun()
        except Exception as error:
            st.session_state.run_error = str(error)
            st.error("Analysis stopped: " + str(error))
    if "case_id" not in st.session_state:
        return
    workflow, case_id = st.session_state.workflow, st.session_state.case_id
    state = workflow.state(case_id)
    decision = state.get("safety_decision")
    if decision:
        (st.error if decision["state"] == "urgent" else st.warning if decision["state"] == "uncertain" else st.info)(
            f"Safety workflow: {decision['state']} · policy {decision['policy_version']}. {decision['meaning']}")
        for flag in decision["assessment"]["safety_flags"]:
            st.warning(flag["text"] + " " + flag["escalation"])
        with st.expander("Deterministic safety decision and source scope"):
            st.json(decision)
    if st.session_state.get("run_error"):
        st.error("Run stopped; no reviewed report was produced. Start a new case after correcting the issue. " + st.session_state.run_error)
        return
    if state["status"] == "awaiting_safety_review":
        st.subheader("Human safety assessment required before reasoning")
        with st.form("safety_form"):
            notes = st.text_area("Safety review notes", key="safety_notes")
            checked = st.checkbox("I assessed the missing information and understand this remains an uncertain synthetic case.", key="safety_attest")
            action = st.radio("Safety decision", ["Stop for human assessment", "Continue after clinician assessment of uncertainty"], key="safety_action",
                              disabled=decision["state"] == "urgent")
            submit = st.form_submit_button("Submit safety decision", key="submit_safety", disabled=not token)
        if submit:
            try:
                review = make_review(action.startswith("Continue"), user, checked, notes, decision["decision_sha256"])
                with st.status("Running source review and local model reasoning…"):
                    workflow.acknowledge_safety(case_id, review, token)
                st.rerun()
            except Exception as error:
                st.error(f"Safety decision or analysis rejected: {error}")
                if workflow.state(case_id).get("status") == "running":
                    st.session_state.run_error = str(error)
    elif state["status"] == "stopped_for_human_review":
        st.info("Analysis stopped for human assessment. No clinical report was completed.")
    elif state["status"] == "awaiting_clinician_review":
        st.subheader("Unverified draft — clinician review required")
        st.markdown(state["draft"])
        st.caption("Report text is source-bound. Reject with notes; correct facts via an approved source import and start a new case.")
        with st.form("clinical_review"):
            notes = st.text_area("Review notes and required corrections", key="review_notes")
            checked = st.checkbox("I verified sources, hypotheses, medication reconciliation and safety limitations.", key="attested")
            action = st.radio("Review decision", ["Request corrections / keep pending", "Approve report"], key="decision")
            submit = st.form_submit_button("Submit clinician review", key="submit_review", disabled=not token)
        if submit:
            try:
                workflow.review(case_id, make_review(action == "Approve report", user, checked, notes, digest(state["draft"])), token)
                st.rerun()
            except (ValueError, PermissionError) as error:
                st.error(f"Review rejected: {error}")
    elif state["status"] == "complete":
        try:
            payload = workflow.export(case_id)
            if "saved_path" not in st.session_state:
                st.session_state.saved_path = str(save_report(payload, auth=auth, safety=workflow.safety))
            st.success(f"Reviewed by authenticated account: {payload['review']['reviewer']}")
            st.markdown(payload["final_report"])
            st.caption("Saved locally: " + st.session_state.saved_path)
            st.download_button("Download reviewed report (JSON)", json.dumps(payload, indent=2), file_name=f"reviewed-{case_id}.json", mime="application/json")
            st.download_button("Download reviewed report (Markdown)", payload["final_report"], file_name=f"reviewed-{case_id}.md", mime="text/markdown")
        except (ValueError, PermissionError, OSError) as error:
            st.error(f"Final export blocked: {error}")


def main():
    st.set_page_config(page_title="MHCRA AI", page_icon="📋", layout="wide")
    st.title("MHCRA AI — Medical History & Clinical Reasoning Assistant")
    st.caption("Synthetic records · SQLite · LangGraph · local Ollama inference")
    st.info(NOTICE)
    st.warning("Do not enter real patient data. This prototype does not diagnose emergencies. If urgent help is needed, do not wait for this app.")
    path, auth = get_services()
    token, user = account_ui(auth)
    if st.sidebar.button("Start a new case", key="new_case"):
        if "workflow" in st.session_state:
            st.session_state.workflow.inference.close()
        for key in ("workflow", "case_id", "run_error", "saved_path"):
            st.session_state.pop(key, None)
        st.rerun()
    patients = list_patients(path)
    if not patients:
        st.error("No synthetic patients found. Initialize the local SQLite database.")
        return
    active = "case_id" in st.session_state
    selected = st.sidebar.selectbox("Patient from SQLite", [patient["id"] for patient in patients],
        format_func=lambda key: next(patient["display_name"] for patient in patients if patient["id"] == key),
        disabled=active or "proposal" in st.session_state, key="patient")
    model = st.sidebar.text_input("Installed local Ollama model", value="gemma4:e2b", disabled=active, key="model")
    st.sidebar.caption("Only http://127.0.0.1:11434 is permitted. Local accounts do not verify clinical credentials.")
    try:
        record = get_history(selected, path)
        st.subheader(record.display_name)
        with st.expander("Longitudinal timeline and original sources", expanded=not active):
            for entry in sorted(record.entries, key=chronology):
                st.text(f"{entry.date or 'Date unavailable'} · {entry.source_type} · {entry.kind} · {entry.id}\n{entry.text}\nSource: {entry.source_id}; verification: {entry.verification_status}")
            for source in record.sources:
                st.caption(f"Original: {source.filename} · {source.id} · SHA-256 {source.sha256}")
                st.text(source.content)
        with st.expander("Medication reconciliation overview"):
            st.json(MedicationAgent().run(record).model_dump(mode="json"))
        if not active:
            history_ui(path, auth, token, user, record)
        clinical_ui(path, auth, token, user, record, model)
    except (ValueError, LookupError, OSError) as error:
        st.error(f"Record validation failed: {error}")


if __name__ == "__main__":
    main()

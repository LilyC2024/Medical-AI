"""LOVISA local workspace: reusable UI, bounded jobs and human review."""

import streamlit as st

import medical_assistant  # noqa: F401 — disable tracing before graph imports
from medical_assistant.database import get_history, list_patients
from medical_assistant.endo_ui import endoscopy_ui
from medical_assistant.imaging_ui import imaging_ui
from medical_assistant.runtime import get_services
from medical_assistant.safety import SafetyAgent
from medical_assistant.ui import components as ui
from medical_assistant.ui.clinical import (
    background_progress,
    bottom_actions,
    collect_task,
    report_panel,
)
from medical_assistant.ui.history import history_ui
from medical_assistant.ui.navigation import (
    DESTINATIONS,
    anchor,
    clear_patient,
    ensure_patient,
    focus_pending,
    go_to,
)


def account_ui(auth):
    token = st.session_state.get("auth_token")
    if token:
        try:
            user = auth.require(token)
            st.sidebar.caption("REVIEWER ACCOUNT")
            st.sidebar.success("Signed in: " + user)
            if st.sidebar.button("Sign out", key="logout"):
                auth.logout(token)
                clear_private_state()
                st.rerun()
            return token, user
        except PermissionError:
            clear_private_state()
    with st.sidebar.expander("Sign in to review", expanded=True):
        if not auth.has_users():
            st.caption(
                "Create a local account from the setup guide: .venv/bin/python -m medical_assistant.auth"
            )
        with st.form("login_form"):
            name = st.text_input("Local clinician account", key="login_user")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Sign in", key="login", width="stretch")
        if submitted:
            try:
                st.session_state.auth_token = auth.login(name, password)
                st.rerun()
            except PermissionError:
                st.error("Check your username and password.")
    return None, None


def clear_private_state():
    """Signing out hides every case and prevents background results reappearing."""
    clear_patient(st.session_state, preserve_login=False, preserve_patient=False)
    st.session_state.clear()


def switch_patient():
    clear_patient(st.session_state)


def reset_case():
    task = st.session_state.get("analysis_task")
    if task is not None:
        task.cancel()
    elif "workflow" in st.session_state:
        st.session_state.workflow.inference.close()
    for key in (
        "analysis_task",
        "workflow",
        "case_id",
        "run_error",
        "saved_path",
        "last_analysis_seconds",
    ):
        st.session_state.pop(key, None)
    for key in (
        "safety_notes",
        "safety_attest",
        "safety_action",
        "review_notes",
        "attested",
        "decision",
        "report_note_changed",
    ):
        st.session_state.pop(key, None)
    st.session_state.navigate_to = "Patient overview"
    st.session_state.focus_target = "patient-overview"


def main():
    st.set_page_config(
        page_title="LOVISA",
        page_icon="◈",
        layout="wide",
        initial_sidebar_state="auto",
    )
    ui.styles()
    path, auth = get_services()
    with st.sidebar:
        ui.sidebar_brand()
    token, user = account_ui(auth)
    ui.header()
    if not token:
        ui.empty(
            "Sign in to open your local demo",
            "Patient examples, imaging studies and reports are available after sign-in. Use the local account form in the sidebar.",
        )
        st.caption(
            "LOVISA uses fictional records and local processing. A local account does not verify clinical qualifications."
        )
        ui.footer()
        return
    patients = list_patients(path)
    if not patients:
        st.error("No fictional patient records are available.")
        return
    anchor("choose-patient")
    selected = st.selectbox(
        "Patient",
        [p["id"] for p in patients],
        format_func=lambda key: next(
            p["display_name"] for p in patients if p["id"] == key
        ),
        index=None,
        placeholder="Choose a patient…",
        key="patient",
        on_change=switch_patient,
    )
    if selected is None:
        ui.empty(
            "Choose a patient to begin",
            "Open one fictional record using the Patient menu above.",
        )
        focus_pending()
        ui.footer()
        return
    ensure_patient(st.session_state, selected)
    collect_task()
    ensure_patient(st.session_state, selected)
    if "navigate_to" in st.session_state:
        view_name = st.session_state.pop("navigate_to")
        go_to(
            next(
                k
                for k, v in DESTINATIONS.items()
                if v == view_name and k != "choose-patient"
            )
        )
    active = "case_id" in st.session_state or "analysis_task" in st.session_state
    ct = st.session_state.get("ct_job")
    running_ct = ct is not None and ct.status() == "running"
    st.sidebar.button(
        "Start a new review", key="new_case", on_click=reset_case, width="stretch"
    )
    st.sidebar.caption("Artificial records · Local research only")
    model = "gemma4:e2b"
    try:
        record = get_history(selected, path)
        decision = SafetyAgent().evaluate(record)
        urgent = decision["state"] == "urgent"
        state = {}
        if "case_id" in st.session_state and "analysis_task" not in st.session_state:
            state = st.session_state.workflow.state(st.session_state.case_id)
        ui.patient_header(
            record,
            decision,
            safety_reviewed=bool(state.get("safety_ack", {}).get("approved"))
            and state["safety_decision"]["decision_sha256"]
            == decision["decision_sha256"],
        )
        if urgent:
            st.error(
                "A structured warning-sign report requires human assessment. Automated clinical reasoning is blocked; do not wait for imaging inspection."
            )
        next_target, next_label = ui.next_action(state, urgent=urgent)
        st.button(
            next_label,
            key="next_action",
            type="primary",
            on_click=go_to,
            args=(next_target,),
        )
        view = st.radio(
            "Workspace",
            [
                "Patient overview",
                "CT review",
                "Endoscopy review",
                "Safety check",
                "Clinical report",
                "Source records",
            ],
            horizontal=True,
            label_visibility="collapsed",
            key="workspace",
        )
        with st.container(key="workspace_shell"):
            workspace, guide = st.columns([3.3, 1.18], gap="large")
            with workspace:
                if view == "Patient overview":
                    anchor("patient-overview")
                    ui.timeline(record)
                    ui.medications(record)
                elif view == "CT review":
                    anchor("ct-review")
                    if urgent:
                        st.warning(
                            "CT inspection is paused while this warning requires human assessment."
                        )
                        if running_ct and st.button(
                            "Cancel CT job", key="ct_cancel_urgent"
                        ):
                            ct.cancel()
                            st.rerun()
                    else:
                        imaging_ui(
                            path,
                            auth,
                            token,
                            user,
                            record,
                            locked=active or "proposal" in st.session_state,
                            case_imaging=state.get("imaging") if active else None,
                        )
                elif view == "Endoscopy review":
                    anchor("endoscopy-review")
                    if urgent:
                        st.warning(
                            "Endoscopy inspection is paused while this warning requires human assessment."
                        )
                        endo_job = st.session_state.get("endo_job")
                        if (
                            endo_job
                            and endo_job.status() == "running"
                            and st.button(
                                "Cancel image analysis", key="endo_cancel_urgent"
                            )
                        ):
                            endo_job.cancel()
                            st.rerun()
                    else:
                        endoscopy_ui(
                            path,
                            auth,
                            token,
                            user,
                            record,
                            locked=active or "proposal" in st.session_state,
                            case_imaging=state.get("imaging") if active else None,
                        )
                elif view == "Safety check":
                    anchor("safety-check")
                    bottom_actions(path, auth, record, model, token, user, decision)
                elif view == "Source records":
                    anchor("source-records")
                    ui.original_sources(record)
                    if not active:
                        history_ui(path, auth, token, user, record)
                else:
                    anchor("clinical-report")
                    report_panel(auth, token, user, record, urgent=urgent)
                if view != "Safety check" and "analysis_task" in st.session_state:
                    background_progress()
            with guide:
                with st.container(key="help_rail"):
                    ui.guide(
                        view,
                        state,
                        running="analysis_task" in st.session_state,
                        signed_in=bool(token),
                    )
        focus_pending()
        ui.footer()
    except (ValueError, LookupError, OSError):
        st.error("This record needs attention before it can be displayed.")
        st.info(
            "Choose another patient or start a new review. The record has not been changed."
        )


if __name__ == "__main__":
    main()

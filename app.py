"""LOVISA local workspace: reusable UI, bounded jobs and human review."""

import medical_assistant  # noqa: F401 — disable tracing before graph imports
import streamlit as st
from medical_assistant.database import get_history, list_patients
from medical_assistant.runtime import get_services
from medical_assistant.safety import SafetyAgent
from medical_assistant.imaging_ui import imaging_ui
from medical_assistant.ui import components as ui
from medical_assistant.ui.history import history_ui
from medical_assistant.ui.clinical import collect_task, action_bar, report_panel


def account_ui(auth):
    token = st.session_state.get("auth_token")
    if token:
        try:
            user = auth.require(token)
            st.sidebar.caption("REVIEWER ACCOUNT")
            st.sidebar.success("Signed in: " + user)
            if st.sidebar.button("Sign out", key="logout"):
                auth.logout(token)
                st.session_state.pop("auth_token", None)
                st.rerun()
            return token, user
        except PermissionError:
            st.session_state.pop("auth_token", None)
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
    st.session_state.navigate_to = "Patient overview"


def main():
    st.set_page_config(
        page_title="LOVISA",
        page_icon="◈",
        layout="wide",
        initial_sidebar_state="auto",
    )
    ui.styles()
    path, auth = get_services()
    collect_task()
    if "navigate_to" in st.session_state:
        st.session_state.workspace = st.session_state.pop("navigate_to")
    with st.sidebar:
        ui.sidebar_brand()
        st.caption("PATIENT WORKSPACE")
    patients = list_patients(path)
    if not patients:
        st.error("No fictional patient records are available.")
        return
    active = "case_id" in st.session_state or "analysis_task" in st.session_state
    ct = st.session_state.get("ct_job")
    running_ct = ct is not None and ct.status() == "running"
    selected = st.sidebar.selectbox(
        "Patient",
        [p["id"] for p in patients],
        format_func=lambda key: next(
            p["display_name"] for p in patients if p["id"] == key
        ),
        disabled=active or "proposal" in st.session_state or running_ct,
        key="patient",
    )
    st.sidebar.button(
        "Start a new case", key="new_case", on_click=reset_case, width="stretch"
    )
    st.sidebar.divider()
    token, user = account_ui(auth)
    with st.sidebar.expander("Local AI settings"):
        model = st.text_input(
            "Installed local Ollama model",
            value="gemma4:e2b",
            disabled=active,
            key="model",
        )
        st.caption(
            "Only the installed local model is used. No cloud inference or paid API."
        )
    st.sidebar.caption(
        "Fictional records only. Local accounts do not verify clinical qualifications."
    )
    ui.header()
    try:
        record = get_history(selected, path)
        decision = SafetyAgent().evaluate(record)
        urgent = decision["state"] == "urgent"
        ui.patient_header(record, decision)
        if urgent:
            st.error(
                "A structured warning-sign report requires human assessment. Automated clinical reasoning is blocked; do not wait for imaging inspection."
            )
        action_bar(path, auth, record, model, urgent=urgent)
        view = st.radio(
            "Workspace",
            ["Patient overview", "CT review", "Clinical report"],
            horizontal=True,
            label_visibility="collapsed",
            key="workspace",
        )
        state = {}
        if "case_id" in st.session_state and "analysis_task" not in st.session_state:
            state = st.session_state.workflow.state(st.session_state.case_id)
        with st.container(key="workspace_shell"):
            workspace, guide = st.columns([3.3, 1.18], gap="large")
            with workspace:
                if view == "Patient overview":
                    ui.timeline(record)
                    ui.medications(record)
                    ui.original_sources(record)
                    if not active:
                        st.divider()
                        st.subheader("Add to the record")
                        history_ui(path, auth, token, user, record)
                elif view == "CT review":
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
                        )
                else:
                    report_panel(auth, token, user, record, urgent=urgent)
            with guide:
                with st.container(key="help_rail"):
                    ui.guide(
                        view,
                        state,
                        running="analysis_task" in st.session_state,
                        signed_in=bool(token),
                    )
        ui.footer()
    except (ValueError, LookupError, OSError) as error:
        st.error("This record needs attention before it can be displayed.")
        with st.expander("Record validation details"):
            st.text(str(error))


if __name__ == "__main__":
    main()

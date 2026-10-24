"""Human-approved history import UI; source data is never guessed or overwritten."""

import json
from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

import streamlit as st

from medical_assistant.history_import import HistoryManagement
from medical_assistant.models import PatientRecord
from medical_assistant.ui.clinical import make_review
from medical_assistant.ui.components import timeline
from medical_assistant.ui.errors import error_message


def history_ui(path, auth, token, user, record):
    if "imports" not in st.session_state:
        st.session_state.imports = HistoryManagement(path, auth=auth)
    manager = st.session_state.imports

    def replace_proposal(result):
        if result[1]["record"]["patient_id"] != record.patient_id:
            manager.pending.pop(result[0], None)
            raise ValueError("Choose a record belonging to the selected patient.")
        if "proposal" in st.session_state:
            manager.pending.pop(st.session_state.proposal[0], None)
        st.session_state.proposal = result
        st.rerun()

    with st.expander("Import a synthetic medical record / add observations"):
        uploaded = st.file_uploader(
            "Synthetic JSON record", type=["json"], key="import_file"
        )
        if st.button(
            "Preview JSON import", key="preview_import", disabled=uploaded is None
        ):
            try:
                proposal_id, proposal = manager.prepare(
                    uploaded.getvalue().decode("utf-8"), uploaded.name
                )
                replace_proposal((proposal_id, proposal))
            except (ValueError, OSError, LookupError) as error:
                st.error("Import rejected: " + error_message(error))
        with st.form("symptom_form"):
            symptom = st.text_area(
                "Synthetic symptoms / history to add", key="symptoms"
            )
            known = st.checkbox(
                "The observation date is known", key="symptom_date_known"
            )
            day = st.date_input(
                "Observation date (used only when known)",
                datetime.now(ZoneInfo("Europe/Amsterdam")).date(),
                key="symptom_date",
            )
            warning = st.selectbox(
                "Explicit current warning-sign screening",
                ["unknown", "absent", "present"],
                key="warning_screen",
            )
            measured = st.checkbox(
                "A blood-pressure measurement was supplied", key="bp_supplied"
            )
            left, right = st.columns(2)
            systolic = left.number_input(
                "Supplied systolic (mmHg)", min_value=1.0, value=120.0, key="systolic"
            )
            diastolic = right.number_input(
                "Supplied diastolic (mmHg)", min_value=1.0, value=80.0, key="diastolic"
            )
            preview = st.form_submit_button(
                "Prepare observation proposal", key="prepare_symptom"
            )
        st.caption(
            "Numbers are used only if the measurement checkbox is selected. The app does not classify blood-pressure values or diagnose emergencies."
        )
        if preview:
            try:
                if not symptom.strip():
                    raise ValueError(
                        "Enter synthetic symptom/history text before preparing a proposal"
                    )
                data = {
                    "fictional": True,
                    "patient_id": record.patient_id,
                    "display_name": record.display_name,
                    "entries": [
                        {
                            "id": "observation-" + uuid4().hex,
                            "date": day.isoformat() if known else None,
                            "source_type": "patient_reported",
                            "kind": "symptom",
                            "text": symptom,
                            "warning_screen": warning,
                            "blood_pressure": {
                                "systolic": systolic,
                                "diastolic": diastolic,
                            }
                            if measured
                            else None,
                        }
                    ],
                }
                replace_proposal(
                    manager.prepare(json.dumps(data), "synthetic-observation.json")
                )
            except ValueError as error:
                st.error("Observation proposal rejected: " + error_message(error))
    if "proposal" in st.session_state:
        proposal_id, proposal = st.session_state.proposal
        st.subheader("Pending history import — no database update yet")
        proposed = PatientRecord.model_validate(proposal["record"])
        timeline(proposed)
        if proposal["duplicate_ids"]:
            st.caption(
                f"{len(proposal['duplicate_ids'])} exact duplicate entries will be skipped."
            )
        with st.form("import_approval"):
            notes = st.text_area("Import review note (optional)", key="import_notes")
            checked = st.checkbox(
                "I verified this synthetic source and the proposed facts.",
                key="import_attest",
                value=False,
            )
            submit = st.form_submit_button(
                "Approve history import", key="approve_import", disabled=not token
            )
        if submit:
            try:
                review = make_review(True, user, checked, notes, proposal["sha256"])
                manager.approve(proposal_id, review, token)
                del st.session_state.proposal
                st.rerun()
            except (ValueError, PermissionError, LookupError) as error:
                st.error("Import approval rejected: " + error_message(error))
        if st.button("Discard import proposal", key="discard_import"):
            manager.pending.pop(proposal_id, None)
            del st.session_state.proposal
            st.rerun()

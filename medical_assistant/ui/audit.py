"""Read-only audit replay for the selected patient; it grants and changes nothing."""

import streamlit as st

from medical_assistant.audit import audit_events


def audit_trail(auth, record):
    events = audit_events(auth.path, record.patient_id, auth)
    with st.expander(f"Audit trail for this patient ({len(events)} records)"):
        if not events:
            st.caption("No audited actions yet.")
            return
        st.dataframe(
            [
                {
                    "Time (UTC)": e["time"],
                    "Action": e["label"],
                    "By": e["actor"],
                    "Approved": {True: "yes", False: "no", None: "—"}[e["approved"]],
                    "Receipt": e["receipt"],
                }
                for e in events
            ],
            hide_index=True,
            width="stretch",
        )
        st.caption(
            "Replay of local audit rows. The log is not tamper-evident, local accounts do "
            "not verify qualifications, and receipts from an earlier process key cannot "
            "be re-verified."
        )

"""Patient-scoped UI lifecycle and fixed, source-independent navigation targets."""

import json
from uuid import uuid4

import streamlit as st
from streamlit.components.v1 import html as local_component

DESTINATIONS = {
    "choose-patient": "Patient overview",
    "patient-overview": "Patient overview",
    "ct-review": "CT review",
    "safety-check": "Safety check",
    "clinical-report": "Clinical report",
    "source-records": "Source records",
}


def clear_patient(state, *, preserve_login=True, preserve_patient=True):
    """Cancel abandoned work and drop every patient-specific widget/proposal."""
    keep = {
        key
        for key, allowed in (
            ("auth_token", preserve_login),
            ("patient", preserve_patient),
        )
        if allowed
    }
    task = state.get("analysis_task")
    if task:
        task.cancel()
        if task.snapshot()["state"] == "complete":
            task.result()[0].inference.close()
    job = state.get("ct_job")
    if job and job.status() == "running":
        job.cancel()
    if not task and "workflow" in state:
        state["workflow"].inference.close()
    store, proposal = state.get("imaging_store"), state.get("imaging_proposal")
    if store and proposal:
        try:
            store.discard(proposal[0])
        except (OSError, ValueError, KeyError):
            # Temporary-file cleanup must never retain another patient's UI.
            pass
    for key in list(state):
        if key not in keep:
            del state[key]
    state["workspace"] = "Patient overview"
    state["focus_target"] = "choose-patient"


def ensure_patient(state, patient):
    """Fail closed before rendering/collecting a mismatched patient snapshot."""
    mismatch = state.get("patient_scope") not in (None, patient)
    workflow, case = state.get("workflow"), state.get("case_id")
    if workflow and case and not state.get("analysis_task"):
        mismatch = mismatch or workflow.state(case)["record"]["patient_id"] != patient
    proposal = state.get("imaging_proposal")
    if proposal:
        mismatch = mismatch or proposal[1]["manifest"]["patient_id"] != patient
    history = state.get("proposal")
    if history:
        mismatch = mismatch or history[1]["record"]["patient_id"] != patient
    job = state.get("ct_job")
    if job:
        mismatch = mismatch or job.patient_id != patient
    if mismatch:
        clear_patient(state)
    state["patient_scope"] = patient
    return not mismatch


def destination(target):
    if target not in DESTINATIONS:
        raise ValueError("Unknown workspace destination")
    return DESTINATIONS[target]


def go_to(target, *, state=None):
    state = st.session_state if state is None else state
    state["workspace"] = destination(target)
    state["focus_target"] = target


def anchor(target):
    destination(target)
    st.html(f'<span id="{target}" class="lv-anchor" tabindex="-1"></span>')


def focus_pending():
    """Scroll only to fixed app anchors; never interpolate record/model text into JS."""
    target = st.session_state.pop("focus_target", None)
    if target is None:
        return
    destination(target)
    # Bounded retries wait for Streamlit to render this fixed, app-owned anchor.
    local_component(
        f"<!-- navigation {uuid4().hex} --><script>(()=>{{const id="
        + json.dumps(target)
        + """;let tries=0;
    function jump(){const el=window.parent.document.getElementById(id);
      if(el){el.scrollIntoView({block:"start",behavior:"instant"});el.focus({preventScroll:true});}
      else if(++tries<40){setTimeout(jump,50);}}
    requestAnimationFrame(()=>setTimeout(jump,150));})();</script>""",
        height=0,
        scrolling=False,
    )

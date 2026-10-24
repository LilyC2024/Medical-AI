"""Local traces stay redacted and opt-in; audit replay reports receipts honestly."""

import json

from test_ui import login, ui  # noqa: F401
from test_workflow import pending_draft, review_for

from medical_assistant.audit import audit_events
from medical_assistant.auth import LocalAuth
from medical_assistant.tracing import case_ref


def test_traces_are_opt_in_local_and_redacted(
    record, inference, auth_session, tmp_path, monkeypatch
):
    trace = tmp_path / "traces/lovisa.jsonl"
    monkeypatch.setenv("LOVISA_TRACE_FILE", str(trace))
    orchestrator, case_id, token = pending_draft(record, inference, auth_session)
    orchestrator.review(case_id, review_for(orchestrator.state(case_id)), token)
    spans = [json.loads(line) for line in trace.read_text().splitlines()]
    steps = [s["attributes"]["lovisa.step"] for s in spans]
    assert {"safety", "history", "medications", "reasoning", "orchestrator"} <= set(steps)
    assert all(s["attributes"]["lovisa.case_ref"] == case_ref(case_id) for s in spans)
    assert any(s["attributes"]["lovisa.outcome"] == "paused-for-human" for s in spans)
    text = trace.read_text()
    for secret in [record.patient_id, record.display_name, case_id]:
        assert secret not in text
    assert all(entry.text not in text for entry in record.entries)


def test_no_trace_file_without_opt_in(record, inference, auth_session, tmp_path):
    pending_draft(record, inference, auth_session)
    assert not list(tmp_path.rglob("*.jsonl"))


def test_audit_replay_lists_actions_and_flags_unverifiable_receipts(
    record, inference, auth_session
):
    orchestrator, case_id, token = pending_draft(record, inference, auth_session)
    orchestrator.review(case_id, review_for(orchestrator.state(case_id)), token)
    auth = auth_session[0]
    events = audit_events(auth.path, record.patient_id, auth)
    final = [e for e in events if e["kind"] == "clinical-review"]
    assert final and final[-1]["approved"] is True
    assert final[-1]["receipt"] == "verified" and final[-1]["actor"] == "dr.example"
    restarted = LocalAuth(auth.path)  # new ephemeral key, as after a restart
    later = audit_events(auth.path, record.patient_id, restarted)
    assert {e["receipt"] for e in later if e["kind"] == "clinical-review"} == {
        "not verifiable with the current receipt key"
    }
    assert audit_events(auth.path, "another-patient", auth) == []


def test_audit_trail_expander_is_read_only(ui):  # noqa: F811
    app, _, _, _ = ui
    login(app)
    app.radio(key="workspace").set_value("Clinical report").run()
    assert not app.exception
    assert any("Audit trail for this patient" in e.label for e in app.expander)

"""Read-only chronological replay of a patient's audit records and receipt checks.

The audit table is append-only by convention but not tamper-evident: a database
administrator can rewrite it. Receipts signed under another process's ephemeral
key cannot be re-verified and are reported as such, not as tampering.
"""

import json

from medical_assistant.database import connect

KINDS = {
    "record-import": "History import approved",
    "safety-review": "Safety decision",
    "report-note": "Report note previewed",
    "clinical-review": "Final report decision",
    "clinical-content": "Report content approved",
    "imaging-import": "Imaging accepted",
}


def audit_events(path, patient_id, auth):
    """Return ``[{time, kind, label, actor, approved, receipt}]`` oldest first."""
    with connect(path) as db:
        rows = db.execute(
            "SELECT timestamp, action, actor, payload FROM audit "
            "WHERE patient_id=? ORDER BY id",
            (patient_id,),
        ).fetchall()
    events = []
    for timestamp, action, actor, payload in rows:
        kind = action.split(":", 1)[0]
        try:
            body = json.loads(payload)
        except ValueError:
            body = {}
        receipt = body.get("receipt") if isinstance(body, dict) else None
        decision = (
            body.get("decision") or body.get("approval") if isinstance(body, dict) else None
        )
        events.append(
            {
                "time": timestamp,
                "kind": kind,
                "label": KINDS.get(kind, kind),
                "actor": actor,
                "approved": decision.get("approved") if isinstance(decision, dict) else None,
                "receipt": _receipt_status(auth, receipt, action, actor),
            }
        )
    return events


def _receipt_status(auth, receipt, action, actor):
    if not isinstance(receipt, dict):
        return "no receipt recorded"
    if receipt.get("action") != action or receipt.get("actor") != actor:
        return "mismatch with audit row"
    try:
        auth.verify_receipt(receipt, action, receipt.get("content_sha256"))
    except PermissionError:
        return "not verifiable with the current receipt key"
    return "verified"

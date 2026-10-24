"""Durable receipt key and workflow checkpoints for restart-safe pending reviews.

Pending graphs persist only when the receipt key is durable (``LOVISA_RECEIPT_KEY``
or the OS keyring); with an ephemeral key, saved receipts could not be verified
after a restart, so workflows stay in memory. SQLite files are not encrypted by
LOVISA; keep the data directory on an encrypted disk.
"""

import argparse
import os
import secrets
import sqlite3
import threading
from pathlib import Path

from langgraph.checkpoint.memory import InMemorySaver

RECEIPT_KEY_ENV = "LOVISA_RECEIPT_KEY"
KEYRING_SERVICE, KEYRING_USER = "lovisa", "receipt-key"
CHECKPOINT_FILE = "workflow_checkpoints.sqlite3"
RESUMABLE = ("awaiting_safety_review", "awaiting_clinician_review")
_savers, _lock = {}, threading.Lock()


def _parse(value, source):
    try:
        key = bytes.fromhex(value.strip())
    except ValueError as error:
        raise ValueError(f"{source} receipt key must be hexadecimal") from error
    if len(key) < 32:
        raise ValueError(f"{source} receipt key must be at least 32 bytes (64 hex)")
    return key


def _keyring_value():
    try:
        import keyring

        return keyring.get_password(KEYRING_SERVICE, KEYRING_USER)
    except Exception:  # noqa: BLE001 - absent package or backend means no keyring key
        return None


def resolve_receipt_key():
    """Return ``(key, source)``; source is ``env``, ``keyring`` or ``ephemeral``."""
    value = os.environ.get(RECEIPT_KEY_ENV)
    if value:
        return _parse(value, RECEIPT_KEY_ENV), "env"
    value = _keyring_value()
    if value:
        return _parse(value, "Keyring"), "keyring"
    return secrets.token_bytes(32), "ephemeral"


def workflow_checkpointer(database_path, durable):
    """One shared SQLite saver per database when durable, else a private memory saver."""
    if not durable:
        return InMemorySaver()
    from langgraph.checkpoint.sqlite import SqliteSaver

    database = Path(database_path).resolve()
    path = database.with_name(database.name + "." + CHECKPOINT_FILE)
    with _lock:
        if path not in _savers:
            connection = sqlite3.connect(path, check_same_thread=False)
            _savers[path] = SqliteSaver(connection)
        return _savers[path]


def resumable_cases(checkpointer, patient_id):
    """Latest checkpoint per pending case for this patient, newest first."""
    seen, cases = set(), []
    for item in checkpointer.list(None):
        thread = item.config["configurable"]["thread_id"]
        if thread in seen:
            continue
        seen.add(thread)
        values = item.checkpoint.get("channel_values", {})
        record = values.get("record") or {}
        if record.get("patient_id") == patient_id and values.get("status") in RESUMABLE:
            cases.append(
                {"case_id": thread, "status": values["status"], "saved_at": item.checkpoint["ts"]}
            )
    return sorted(cases, key=lambda c: c["saved_at"], reverse=True)


def main(argv=None):
    p = argparse.ArgumentParser(description="Create a durable LOVISA receipt key")
    p.add_argument(
        "--store-keyring",
        action="store_true",
        help="Store in the OS keyring instead of printing it",
    )
    a = p.parse_args(argv)
    value = secrets.token_hex(32)
    if a.store_keyring:
        import keyring

        if keyring.get_password(KEYRING_SERVICE, KEYRING_USER):
            raise SystemExit("A receipt key already exists in the keyring")
        keyring.set_password(KEYRING_SERVICE, KEYRING_USER, value)
        print("Receipt key stored in the OS keyring")
    else:
        print(f"Set {RECEIPT_KEY_ENV} to this value and keep it secret:\n{value}")


if __name__ == "__main__":
    main()

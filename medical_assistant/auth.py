"""Local password authentication and short-lived in-process clinician sessions."""
import getpass
import hashlib
import hmac
import re
import secrets
import time
from pathlib import Path

from medical_assistant.database import DATABASE_PATH, connect, initialize


class LocalAuth:
    def __init__(self, path: Path = DATABASE_PATH):
        self.path = path
        initialize(path)
        self.sessions = {}
        self._receipt_key = secrets.token_bytes(32)
        with connect(path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS clinicians (username TEXT PRIMARY KEY, salt TEXT NOT NULL, password_hash TEXT NOT NULL)")

    def has_users(self):
        with connect(self.path) as db:
            return bool(db.execute("SELECT COUNT(*) FROM clinicians").fetchone()[0])

    def create_clinician(self, username: str, password: str):
        if not re.fullmatch(r"[A-Za-z0-9_.-]{3,80}", username) or len(password) < 12:
            raise ValueError("Use a 3–80 character account name and password of at least 12 characters")
        salt = secrets.token_hex(16)
        derived = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 600_000).hex()
        with connect(self.path) as db:
            db.execute("INSERT INTO clinicians VALUES (?,?,?)", (username, salt, derived))

    def login(self, username: str, password: str):
        with connect(self.path) as db:
            row = db.execute("SELECT salt,password_hash FROM clinicians WHERE username=?", (username,)).fetchone()
        salt = row[0] if row else "0" * 32
        derived = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 600_000).hex()
        if not row or not hmac.compare_digest(derived, row[1]):
            raise PermissionError("Invalid clinician credentials")
        token = secrets.token_urlsafe(32)
        self.sessions[token] = (username, time.monotonic() + 3600)
        return token

    def require(self, token):
        session = self.sessions.get(token or "")
        if not session or session[1] <= time.monotonic():
            raise PermissionError("An authenticated clinician session is required")
        return session[0]

    def logout(self, token):
        self.sessions.pop(token, None)

    def audit(self, action, patient_id, token, payload):
        import json
        actor = self.require(token)
        with connect(self.path) as db:
            db.execute("INSERT INTO audit(action,patient_id,actor,payload) VALUES (?,?,?,?)",
                       (action, patient_id, actor, json.dumps(payload)))

    def receipt(self, token, action, content_sha256):
        actor = self.require(token)
        message = f"{actor}|{action}|{content_sha256}"
        return {"actor": actor, "action": action, "content_sha256": content_sha256,
                "signature": hmac.new(self._receipt_key, message.encode(), "sha256").hexdigest()}

    def verify_receipt(self, receipt, action, content_sha256):
        if not receipt or receipt.get("action") != action or receipt.get("content_sha256") != content_sha256:
            raise PermissionError("Missing authenticated approval receipt")
        message = f"{receipt['actor']}|{action}|{content_sha256}"
        expected = hmac.new(self._receipt_key, message.encode(), "sha256").hexdigest()
        if not hmac.compare_digest(receipt.get("signature", ""), expected):
            raise PermissionError("Invalid approval receipt")
        return receipt["actor"]

    def record_receipt(self, receipt, patient_id, payload):
        import json
        self.verify_receipt(receipt, receipt["action"], receipt["content_sha256"])
        with connect(self.path) as db:
            db.execute("INSERT INTO audit(action,patient_id,actor,payload) VALUES (?,?,?,?)",
                (receipt["action"], patient_id, receipt["actor"], json.dumps({"receipt": receipt, "decision": payload})))


if __name__ == "__main__":
    auth = LocalAuth()
    username = input("New local clinician username: ").strip()
    password = getpass.getpass("New password (at least 12 characters): ")
    if password != getpass.getpass("Repeat password: "):
        raise SystemExit("Passwords differ")
    auth.create_clinician(username, password)
    print("Local synthetic-review account created. Clinical credentials are not externally verified.")

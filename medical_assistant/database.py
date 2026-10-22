"""Transactional SQLite storage. Models have no access to these write functions."""

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from medical_assistant.models import Entry, PatientRecord, SourceDocument
from medical_assistant.grounding import validate_record_grounding
from medical_assistant.report import digest
from medical_assistant.storage import ROOT, load_record

DATABASE_PATH = ROOT / "data" / "medical_history.sqlite3"


@contextmanager
def connect(path: Path):
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize(path: Path = DATABASE_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS patients (
            id TEXT PRIMARY KEY, display_name TEXT NOT NULL,
            fictional INTEGER NOT NULL CHECK(fictional=1));
        CREATE TABLE IF NOT EXISTS sources (
            patient_id TEXT NOT NULL REFERENCES patients(id),
            id TEXT NOT NULL, filename TEXT NOT NULL, source_date TEXT,
            content TEXT NOT NULL, sha256 TEXT NOT NULL, verification_status TEXT NOT NULL,
            PRIMARY KEY(patient_id, id));
        CREATE TABLE IF NOT EXISTS facts (
            patient_id TEXT NOT NULL REFERENCES patients(id), id TEXT NOT NULL,
            source_id TEXT NOT NULL, encounter_date TEXT, payload TEXT NOT NULL,
            PRIMARY KEY(patient_id, id),
            FOREIGN KEY(patient_id, source_id) REFERENCES sources(patient_id, id));
        CREATE TABLE IF NOT EXISTS audit (
            id INTEGER PRIMARY KEY, timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            action TEXT NOT NULL, patient_id TEXT NOT NULL, actor TEXT NOT NULL,
            payload TEXT NOT NULL);
        """)


def attach_original(record: PatientRecord, filename: str, raw: str) -> PatientRecord:
    """Convert legacy synthetic JSON to immutable source + separately stored facts."""
    if record.sources:
        return record
    source = SourceDocument(id="source-" + digest(raw)[:20], filename=filename,
                            content=raw, sha256=digest(raw))
    data = record.model_dump(mode="json")
    data["sources"] = [source.model_dump(mode="json")]
    for entry in data["entries"]:
        entry["source_id"] = source.id
    return PatientRecord.model_validate(data)


def write_synthetic(record: PatientRecord, path: Path, *, actor: str, action: str, approval=None):
    """Internal atomic append; existing IDs are immutable and exact retries are no-ops."""
    record = PatientRecord.model_validate(record.model_dump(mode="json"))
    if not record.sources:
        raise ValueError("Original source documents are required before persistence")
    validate_record_grounding(record)
    with connect(path) as db:
        stored_facts = {row["id"]: Entry.model_validate_json(row["payload"])
                        for row in db.execute("SELECT id,payload FROM facts WHERE patient_id=?", (record.patient_id,))}
        combined = {**stored_facts, **{entry.id: entry for entry in record.entries}}
        if len(combined) > 100 or sum(len(entry.text) for entry in combined.values()) > 24_000:
            raise ValueError("Cumulative patient history exceeds the prototype limit (100 facts / 24,000 text characters); no records were changed")
        existing = db.execute("SELECT display_name FROM patients WHERE id=?", (record.patient_id,)).fetchone()
        if existing and existing[0] != record.display_name:
            raise ValueError("Patient identity conflicts with stored synthetic record")
        db.execute("INSERT OR IGNORE INTO patients VALUES (?,?,1)", (record.patient_id, record.display_name))
        changed = False
        for source in record.sources:
            prior = db.execute("SELECT sha256,filename,source_date FROM sources WHERE patient_id=? AND id=?", (record.patient_id, source.id)).fetchone()
            source_date = source.date.isoformat() if source.date else None
            if prior and tuple(prior) != (source.sha256, source.filename, source_date):
                raise ValueError("Conflicting original source ID; stored originals are immutable")
            if not prior:
                db.execute("INSERT INTO sources VALUES (?,?,?,?,?,?,?)", (
                    record.patient_id, source.id, source.filename, source.date.isoformat() if source.date else None,
                    source.content, source.sha256, source.verification_status))
                changed = True
        for entry in record.entries:
            payload = entry.model_dump_json()
            prior = db.execute("SELECT payload FROM facts WHERE patient_id=? AND id=?", (record.patient_id, entry.id)).fetchone()
            if prior and Entry.model_validate_json(prior[0]).model_dump() != entry.model_dump():
                raise ValueError("Conflicting encounter/fact ID or date; no records were changed")
            if not prior:
                db.execute("INSERT INTO facts VALUES (?,?,?,?,?)", (
                    record.patient_id, entry.id, entry.source_id,
                    entry.date.isoformat() if entry.date else None, payload))
                changed = True
        if changed:
            db.execute("INSERT INTO audit(action,patient_id,actor,payload) VALUES (?,?,?,?)",
                       (action, record.patient_id, actor, json.dumps({"source_ids": [s.id for s in record.sources],
                                                                  "entry_ids": [e.id for e in record.entries], "approval": approval})))


def get_history(patient_id: str, path: Path = DATABASE_PATH) -> PatientRecord:
    with connect(path) as db:
        patient = db.execute("SELECT * FROM patients WHERE id=?", (patient_id,)).fetchone()
        if not patient:
            raise LookupError("Synthetic patient was not found")
        sources = [SourceDocument(id=row["id"], filename=row["filename"], date=row["source_date"],
                                  content=row["content"], sha256=row["sha256"], verification_status=row["verification_status"])
                   for row in db.execute("SELECT * FROM sources WHERE patient_id=? ORDER BY id", (patient_id,))]
        facts = [Entry.model_validate_json(row[0]) for row in db.execute(
            "SELECT payload FROM facts WHERE patient_id=? ORDER BY encounter_date IS NULL, encounter_date, id", (patient_id,))]
    return PatientRecord(fictional=True, patient_id=patient_id, display_name=patient["display_name"], entries=facts, sources=sources)


def list_patients(path: Path = DATABASE_PATH):
    with connect(path) as db:
        return [dict(row) for row in db.execute("SELECT id,display_name FROM patients ORDER BY id")]


def seed(path: Path = DATABASE_PATH):
    """Explicit built-in synthetic fixture creation; never imports arbitrary files."""
    initialize(path)
    for filename in ("fictional_patient.json", "checklist_patient.json"):
        source_path = ROOT / "data" / "patients" / filename
        record = attach_original(load_record(source_path), filename, source_path.read_text())
        write_synthetic(record, path, actor="built-in-synthetic-fixture", action="seed")


if __name__ == "__main__":
    seed()
    print(f"Synthetic SQLite database ready: {DATABASE_PATH}")

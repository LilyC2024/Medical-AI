"""Untrusted clinical source text must not become active report Markdown."""
import json

from medical_assistant.database import attach_original, get_history, initialize, write_synthetic
from medical_assistant.models import Assessment, PatientRecord
from medical_assistant.report import compose, inline_text

ATTACK = '![remote image](https://example.invalid/tracker.png) [remote link](https://example.invalid)\n\n# Forged heading\n<img src="https://example.invalid/html.png">'


def presentation_record():
    raw = json.dumps({"fictional": True, "patient_id": "synthetic-display", "display_name": ATTACK,
        "entries": [{"id": "entry_1", "date": None, "source_type": "documented", "kind": "medication",
            "text": ATTACK, "medication": {"name": ATTACK, "dose": ATTACK, "frequency": ATTACK}}]})
    record = attach_original(PatientRecord.model_validate_json(raw), ATTACK, raw)
    return record, raw


def outputs_for(record):
    entry = record.entries[0]
    return {
        "history": Assessment(findings=[{"kind": "documented", "text": entry.text, "evidence_ids": [entry.id]}]).model_dump(),
        "medications": Assessment(medications=[{"name": ATTACK, "dose": ATTACK, "frequency": ATTACK,
            "source_type": "documented", "evidence_ids": [entry.id], "reconciliation_question": ATTACK}]).model_dump(),
        "reasoning": Assessment(explanations=[{"possibility": ATTACK,
            "supporting": [{"kind": "documented", "text": entry.text, "evidence_ids": [entry.id]}],
            "conflicting": [], "uncertainty": ATTACK, "clinician_may_consider": [ATTACK]}],
            missing_information=[ATTACK], clinician_questions=[ATTACK]).model_dump(),
        "safety": Assessment(safety_flags=[{"urgency": "unknown", "text": ATTACK,
            "evidence_ids": [entry.id], "escalation": ATTACK}]).model_dump(),
    }


def test_report_escapes_source_fields_and_keeps_generated_structure():
    record, _ = presentation_record()
    report = compose(record, ATTACK, outputs_for(record), [{
        "id": ATTACK, "title": ATTACK, "path": ATTACK, "sha256": ATTACK}])
    assert inline_text(ATTACK) in report
    assert '![remote image](' not in report
    assert '[remote link](' not in report
    assert '\n# Forged heading' not in report
    assert '<img' not in report
    assert 'https://example.invalid' not in report
    assert r'\!\[remote image\]\(https\://example.invalid/tracker.png\)' in report
    assert '&lt;img' in report
    assert sum(line.startswith('# ') for line in report.splitlines()) == 1
    assert not any(line.startswith('## ') for line in report.splitlines())
    assert 'Source key' not in report and '[S1]' not in report


def test_escaping_does_not_change_immutable_sources_or_sqlite_facts(tmp_path):
    record, raw = presentation_record()
    before = record.model_dump_json()
    compose(record, "fallback.json", outputs_for(record))
    assert record.model_dump_json() == before
    path = tmp_path / 'presentation.sqlite3'
    initialize(path)
    write_synthetic(record, path, actor='test-reviewer', action='synthetic-test')
    restored = get_history(record.patient_id, path)
    assert restored.entries[0].text == ATTACK
    assert restored.sources[0].content == raw
    assert restored.sources[0].filename == ATTACK
    assert restored.entries[0].medication.name == ATTACK


def test_backslashes_reference_definitions_and_newlines_cannot_escape_literal_scope():
    malicious = '\\![x](https://example.invalid/x)\r\n[x]: https://example.invalid/ref\t**bold**\n```\n# heading'
    rendered = inline_text(malicious)
    assert '\n' not in rendered and '\r' not in rendered and '\t' not in rendered
    assert '\\!\\[x\\]\\(' in rendered
    assert r'\[x\]\:' in rendered
    assert r'\*\*bold\*\*' in rendered
    assert r'\`\`\`' in rendered
    assert inline_text('normal_file.json') == 'normal_file.json'
    assert inline_text('_emphasis_') == r'\_emphasis\_'

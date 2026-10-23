import json

import pytest

from medical_assistant.database import get_history, seed
from medical_assistant.evidence import LocalEvidenceCollection
from medical_assistant.history import MedicalHistoryAgent, MedicationAgent
from medical_assistant.models import Assessment
from medical_assistant.report import compose, digest


def test_unsupported_assertion_with_real_source_id_still_fails(record):
    with pytest.raises(ValueError, match="Unsupported clinical-record"):
        Assessment(
            findings=[
                {
                    "kind": "documented",
                    "text": "Blood pressure is normal at 120/80.",
                    "evidence_ids": [record.entries[0].id],
                }
            ]
        ).validate_sources(record)


def test_confirmed_diagnosis_label_rejected():
    with pytest.raises(ValueError, match="hypotheses"):
        Assessment(
            explanations=[
                {
                    "possibility": "Confirmed hypotension",
                    "supporting": [],
                    "conflicting": [],
                    "uncertainty": "none",
                    "clinician_may_consider": ["review"],
                }
            ]
        )


def test_local_evidence_approved_hash_bound_and_path_confined(tmp_path):
    text = "Synthetic evidence fixture: timing alone does not establish causation."
    (tmp_path / "approved.md").write_text(text)
    (tmp_path / "unapproved.md").write_text("Must never be returned")
    manifest = {
        "documents": [
            {
                "id": "fixture",
                "title": "Timing",
                "path": "approved.md",
                "sha256": digest(text),
                "approved": True,
            },
            {
                "id": "unapproved",
                "title": "Timing",
                "path": "unapproved.md",
                "sha256": "0" * 64,
                "approved": False,
            },
        ]
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    collection = LocalEvidenceCollection(tmp_path)
    assert [item["id"] for item in collection.retrieve("timing")] == ["fixture"]
    (tmp_path / "approved.md").write_text("changed")
    with pytest.raises(ValueError, match="approval must be renewed"):
        collection.retrieve("timing")
    manifest["documents"][0]["path"] = "../outside.md"
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="outside"):
        collection.retrieve("timing")


def test_report_hypotheses_sources_and_missing_bp_and_history(tmp_path):
    path = tmp_path / "history.sqlite3"
    seed(path)
    record = get_history("synthetic-checklist", path)
    symptom = next(entry for entry in record.entries if entry.id == "symptom-undated")
    reasoning = Assessment(
        explanations=[
            {
                "possibility": "Possible contribution of the reported medication change",
                "status": "hypothesis",
                "supporting": [
                    {
                        "kind": "patient_reported",
                        "text": symptom.text,
                        "evidence_ids": [symptom.id],
                    }
                ],
                "conflicting": [],
                "uncertainty": "Blood pressure and symptom dates are unavailable; association does not establish causation.",
                "clinician_may_consider": [
                    "Establish current blood-pressure measurements and symptom history."
                ],
            }
        ]
    ).validate_sources(record)
    report = compose(
        record,
        "checklist_patient.json",
        {
            "history": MedicalHistoryAgent().run(record).model_dump(mode="json"),
            "medications": MedicationAgent().run(record).model_dump(mode="json"),
            "safety": Assessment(
                missing_information=["Current screening unavailable."]
            ).model_dump(mode="json"),
            "reasoning": reasoning.model_dump(mode="json"),
        },
    )
    assert "unverified hypotheses" in report
    assert "5 mg → 10 mg" in report
    assert "Source key" not in report
    assert "Blood-pressure measurements are unavailable" in report
    assert "syncope/falls" in report and "fluid intake" in report
    assert "Source key" not in report and "unverified hypotheses" in report
    # Full original citations remain separately available without cluttering the prose.
    assert len(report.split()) < 450
    assert "[S1]" not in report

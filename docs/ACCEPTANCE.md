# Acceptance requirements and evidence

[Overview](../README.md) · [Evaluation](../EVALUATION.md)

These checks concern synthetic software behavior, not clinical validation.

| Check | Regression evidence |
| --- | --- |
| Patient history loads from SQLite without missing or duplicated encounters | `test_sqlite_retrieval_has_exact_encounters_and_no_duplicates`: two seed runs preserve exactly five facts and two encounters; conflicts roll back. Cumulative-limit adversarial tests reject unreadable appends. |
| Medication Agent identifies the documented dose change correctly | `test_medication_agent_extracts_documented_dose_change_and_source_dates`: amlodipine 5 mg → 10 mg on 2025-02-10, linked to both original order IDs. Forged names/doses/dates are rejected. |
| History Agent distinguishes known dates from missing dates | `test_history_agent_never_invents_missing_dates`: four known dates and an explicit undated symptom report. Possible duplicate content is flagged without silently deleting sources. |
| Possible causes remain hypotheses | `test_report_hypotheses_sources_and_missing_bp_and_history`, `test_confirmed_diagnosis_label_rejected`, and the constrained-reasoning tests. The model selects bounded synthetic hypothesis labels and exact evidence; it cannot establish diagnoses. |
| Report identifies unavailable BP and relevant missing history | Report tests assert missing measurements, symptom timing, syncope/falls and fluid-intake questions. Observation UI tests verify unselected placeholder measurements are not stored. |
| Safety follows the defined policy and the model cannot bypass it | `test_safety_policy.py`, `test_review_safety.py`, workflow/UI tests: missing/stale/unknown data pauses before inference; explicit warning flags stop; forged receipts and changed policy fail closed. Rules are in `config/safety_policy.json`, a procedural review policy, not a clinical triage protocol. |
| Clinical-record claims link to actual record sources | Original JSON hashes and extracted facts are checked; factual text/ID/attribution are bound together in the generation schema and revalidated. Medication and dose-change values must match cited orders. Markdown injection is rendered literally. |
| Clinician approval precedes reviewed status | Workflow/UI tests require authenticated, case-bound, hash-bound review, attestation and notes. Rejection remains pending. No final download or save is allowed before valid approval. |

The current report uses one concise section. Full exact quotations, source IDs,
filenames/dates and model evidence selections remain in the JSON evidence package;
the optional evidence view makes them readable without inline citation clutter.
Accepted CT results/calipers and representative images appear in the combined
report. Note-preview, stale-approval, HTML-export and tampered-artifact regressions
extend the original checklist. [Report details](REPORTS.md).

## Image-first endoscopy extension

Endoscopy adds explicit candidate review, source/overlay reconstruction checks, separate artificial/public-research import schemas, patient-switch cleanup and combined report/export binding. Tests use scripted reviewers; real worker smokes stop before approval. [Scope](ENDOSCOPY.md).

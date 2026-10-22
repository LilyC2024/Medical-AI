# Software evaluation — 22 October 2026

These checks use deliberately synthetic records. They establish prototype
software behavior, not clinical accuracy, diagnostic validity or triage safety.

## Requested acceptance checklist

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

## Executed checks

- Foundation gate: 20 tests passed, plus a real local structured-response
  connection check against the installed `gemma4:e2b` model.
- History gate: 24 cumulative foundation/history tests passed.
- Initial orchestration gate: 48 full regression tests passed.
- Safety gate: 76 non-UI regression/adversarial tests passed.
- First integrated release pass: 85 tests passed, including authenticated UI
  rejection/approval/export, observation imports, urgent stops and independent
  review regressions. Further source-binding and duplicate checks were then added;
  **Final release run: 87 tests passed in 18.10 seconds.**
- `python -m pip check`: no broken requirements.
- `python -m compileall -q app.py medical_assistant scripts tests`: passed.
- `git diff --check`: passed.
- Published release `7863ad89ee03fcf43c772d320f2adfea1a90a6ad`: GitHub
  [CI run #1](https://github.com/LilyC2024/Medical-AI/actions/runs/39783171014)
  passed on **Python 3.10 and Python 3.12**, including dependency consistency,
  compilation and the complete offline regression suite. The published source
  tree matched the reviewed local tree exactly.

The initial revised live smoke correctly held missing-data cases, then rejected
a model response that confused documented and patient-reported evidence. No
report was approved or saved. The schema was tightened to bind quote, attribution
and source ID atomically. **The corrected real local smoke passed:** the missing-
data fixture paused without an approval; a separate, explicitly synthetic
ordinary-eligible fixture completed real `gemma4:e2b` reasoning, final safety
review and composition, then paused at clinician approval with `reviewed=false`.
No safety hold or final clinical report was automatically approved or saved.
Automated model responses are scripted and are never presented as live inference.

## Independent agent review and fixes

Illustrated documentation review on 22 October 2026: three independent development
subagents checked records/UI, safety/workflow and documentation/release behavior.
The README now embeds the clinical and technical illustrations, explains runtime
specialists separately from development subagents, and documents actual setup,
review, import and export actions. Source review corrected wording about automatic
fixture seeding, fixed case snapshots and historical warning flags. The full local
suite passed again: **87 tests in 17.86 seconds**. Dependency consistency,
compilation and whitespace checks passed. This pass changes documentation and a
module docstring; live inference behavior is unchanged and the live smoke was not
rerun. The earlier live-model result above remains separately identified.

Separate development subagents reviewed storage/provenance, safety/approval,
presentation, architecture and publication documentation. Their adversarial tests
found and helped resolve forged export receipts, unrestricted report revisions,
fabricated medication values, cumulative imports that could leave histories
unreadable, malformed source identities and Markdown injection. They are coding
review assistants, not runtime clinical agents or clinical validators.

## Remaining boundaries

- Synthetic-only, single-machine prototype; no real clinical deployment.
- Local account authentication does not verify professional credentials.
- Evidence manifest is empty; no approved medical reference support is claimed.
- Reasoning uses a deliberately small transparent synthetic catalog. Source
  selection does not demonstrate a causal link or clinical relevance.
- Only structured JSON imports; bounded histories (100 facts, 24,000 text
  characters) and conservative model prompt limits.
- The safety policy examines structured flags/current-day observations; it is not
  a comprehensive free-text emergency detector or numerical triage protocol.
- Pending cases, proposals, sessions and receipt verification keys are in memory.
  SQLite accounts/sources/audit records and saved reports persist locally.
- Databases/exports are not encrypted; filesystem/process administrators remain
  trusted. Runtime data and credentials are excluded from publication.
- Local verification used Python 3.10.12; hosted CI additionally passed on
  Python 3.10 and Python 3.12. Live Ollama inference was verified locally, not in CI.
- No project redistribution license has been selected. Model/dependency licenses
  remain applicable; model weights are not bundled.

Suggested next task after publication: have a clinician review and version a
local evidence collection and evaluate the bounded prototype on a larger,
independently labeled synthetic dataset. Do not extend it to real patient records
without a separate security, privacy, clinical and regulatory design.

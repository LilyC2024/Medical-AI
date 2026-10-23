# Current lung CT compatibility evaluation — 23 October 2026

MHCRA v0.2 and CT v0.10 implement the nodule-v2 exchange; legacy tissue-mask v1
remains supported. This records software behavior, not clinical performance.

| Executed check | Actual outcome |
| --- | --- |
| Previous MHCRA baseline | 120 passed in 32.91s |
| First nodule/worker/legacy UI focused check | 25 passed in 14.74s |
| Consumer phase gate | 144 passed in 51.12s, including adversarial and scripted-review tests |
| Final expanded regression | 146 passed in 44.55s; caliper preview/persistence and urgent-before-optional-nodule tests included |
| Added caliper UI checks | 2 passed in 4.39s; preview alone persists no acceptance |
| Actual fixture producer/receiver smoke | PASS; 32×64×64 HU, 1 non-ML candidate, 66 artifacts |
| Actual installed-pretrained CPU producer/receiver smoke | PASS; 32×64×64 HU, 1 candidate, 66 artifacts; no inference-time download |
| Actual legacy producer/receiver smoke | PASS; 20×48×48, 41 artifacts, declared ONNX parity true |
| Actual gemma4:e2b local smoke | PASS; missing-data fixture holds before reasoning; separate eligible synthetic fixture reaches final review |
| Approval status of actual smokes | No imaging, safety or final report approval issued |
| Shared schemas/report/renderer | Exact match after one import-path rewrite |
| Dependencies/documentation | pip check and local Markdown target checks passed; no dependency upgrades |

Offline tests use scripted model/reviewer identities and temporary SQLite, never
real clinician approval. Candidate decisions and calipers are hash-bound to the
authenticated actor; no unresolved decision can be accepted. NPY allocation,
source/overlay pixel, report, patient/public-input and byte-tamper attempts fail
closed. Source records remain separate from accepted imaging and outside pixels.
Imaging never enters the LLM or lowers deterministic safety escalation. Final
clinical approval remains required even after imaging acceptance.

Remaining limits: bounded synthetic-only imaging; full DICOM/public research and
training stay standalone CT. The generated phantom has no clinical sensitivity,
malignancy accuracy or time-savings interpretation. Actual CUDA/NPU execution was
not performed for this update. Local accounts do not verify professional status;
producer declarations/hashes establish consistency, not independent authenticity.
Browser visual inspection was unavailable; Streamlit AppTest exercised both
legacy and nodule controls. Current hosted results are added after execution.

## Previous release evaluation

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

### Shared CT workbench integration — 22 October 2026

- **120 MHCRA tests passed in 31.61 seconds**, including 33 imaging/worker/UI
  checks. Tests cover wrong patient/study, rejected/tampered archives, NPY header
  allocation attempts, malformed metadata, overlay/count/geometry consistency,
  authenticated imaging acceptance, immutable studies, commit-failure recovery,
  interrupted promotion retry, fixed snapshots and final report/export guards.
  UI regressions also ensure image inspection cannot delay urgent routing and a
  newly supplied warning blocks review/download of an older case snapshot.
- The separate CT Python 3.12 environment passed **32 tests in 10.708 seconds**,
  plus Ruff and dependency consistency. These include actual synthetic DICOM,
  ONNX export/parity, source-grid restoration and the new bundle exporter.
- **Real cross-project imaging smoke passed**: the separate CT worker generated
  20 synthetic 48×48 slices, trained its 12-epoch tiny demonstration model and
  returned a bundle accepted by MHCRA's receiver validation. Source-grid class
  counts were `[40218, 128, 5734, 0]`; all 41 artifacts verified. The smoke prepared
  an import but issued **no imaging, safety or final report approval**.
- **Real local `gemma4:e2b` smoke passed again**, separately: missing-data holds
  preceded inference; the eligible synthetic case reached final clinician review
  with `reviewed=false`. Images and reviewer notes are excluded from LLM input.
- A scientific contact-sheet illustration was generated from the actual synthetic
  source/overlay previews and counts; it contains no real patient pixels.
  The tiny model has weak teacher agreement and is not an anatomical/lesion model.
- Independent review found and resolved oversized NPY allocation attempts,
  malformed numeric metadata, commit-failure recovery and job-study binding.
  Producer-declared provenance is labeled explicitly. Hash consistency cannot
  independently prove synthetic origin or model execution.
- Streamlit automated UI checks passed. Interactive browser preview was unavailable
  because browser origin access was declined; no browser workaround was used.

These results supersede the earlier suite total; historical phase results below
are retained. The published GitHub checks are reported separately after execution.

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
- Optional imaging is generated-synthetic only. Candidate measurements and entropy
  are research outputs, not validated clinical findings/confidence. CT worker logs,
  source/model artifacts, accepted originals and pending bundles stay ignored.

Suggested next task after publication: have a clinician review and version a
local evidence collection and evaluate the bounded prototype on a larger,
independently labeled synthetic dataset. Do not extend it to real patient records
without a separate security, privacy, clinical and regulatory design.

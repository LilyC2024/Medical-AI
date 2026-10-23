# LOVISA evaluation record

These results concern synthetic software behavior, not diagnostic accuracy,
clinical safety or clinician time savings. [Reproduce checks](docs/VALIDATION.md)
· [Eight acceptance requirements](docs/ACCEPTANCE.md).

## Workspace and response-budget release — 23 October 2026

| Executed check | Actual outcome |
| --- | --- |
| Full LOVISA regression | **176 passed in 65.48s**; temporary DBs and scripted models/reviewers |
| Final focused UI/compact regressions | 17 passed in 8.39s after final component formatting |
| CT regression | 81 passed in 36.99s; 13 focused exchange checks passed in 4.31s after stage-order assertions |
| Phase gates | Performance foundation: 163 full tests; reusable UI: 166 full tests; final compact protocol: 176 |
| Actual local Ollama | Missing-data case held; eligible synthetic case reached final review in **23.40s** total smoke time |
| Earlier actual full-output Ollama smoke | 44.58s; individual runs are not a controlled benchmark |
| Actual fixture CT → receiver | **1.65s**, generated 32×64×64 input, one non-ML candidate, 66 artifacts checked |
| Actual installed pretrained CPU CT → receiver | **12.43s**, same generated shape, one candidate, 66 artifacts checked |
| Actual retained legacy CT → receiver | Passed: 20×48×48, 41 artifacts and ONNX parity; no approvals |
| Browser checks | Real localhost page, 1440px responsive desktop and native 609px viewport; readable overview, sticky right guide, auto-opening pending CT and safety pause |
| Integrity/dependencies/docs | Exact shared-contract equality, pip check, compileall and 27 maintained Markdown local-target checks passed |
| Approval status | No imaging acceptance, safety continuation, final approval or reviewed clinical report issued by actual smokes/browser checks |

The UI now separates overview, CT and report views. Technical data is collapsed;
source text and attribution remain visible. Clinical tasks expose progress/cancel,
stop publication at 110 seconds and reject late results. CT has a matching process
watchdog. Scripted slow-task/cancel/timeout tests establish software behavior;
actual PC load/browser scheduling can delay display. Successful inference within
two minutes is not guaranteed on arbitrary hardware.

The local model selects eligible hypothesis/evidence/catalog IDs. Python restores
exact excerpts and validates the full assessment. Invented/unknown/duplicate IDs,
extra prose, incomplete JSON and unsupported sources fail closed. A smaller output
format changes generation cost, not the catalog, safety policy or human review.
Tests use scripted inference; the Ollama result above is a separate actual run.

No packages, weights or model versions changed. No new GPU/NPU training/execution,
full-size CT latency, patient accuracy or clinical time-saving result is claimed.
The retained legacy workflow remains separate. [Implementation](docs/PERFORMANCE.md)
· [Workspace screenshots](docs/INTERFACE.md).

## LOVISA naming/documentation update — 23 October 2026

| Executed check | Result |
| --- | --- |
| Full LOVISA suite after UI/report rename | 146 passed in 42.35s on the final rerun |
| CT documentation/regression check | 81 passed in 23.90s; Ruff and format checks passed |
| Documentation links | All 25 maintained Markdown files per repository passed local-target checks |
| Dependency/compile/shared contract | pip check, compileall and exact CT/LOVISA contract equality passed |
| Actual local gemma4:e2b smoke | Passed: missing-data case held before reasoning; eligible synthetic case reached final review |
| Approval state in that smoke | No safety/final approval issued; no reviewed report saved |
| Reused figures | Existing workflow, technical and CT images inspected; historical brand/fixture status explained |

This pass changes documentation, visible branding and the existing title assertion;
it adds no clinical logic, models or exchange format. Tests use scripted inference/reviewers; the Ollama result above is a separate
actual local run.

### Hosted publication checks

[LOVISA run 39929551523](https://github.com/LilyC2024/Medical-AI/actions/runs/39929551523)
passed at `a37a716b7933a671532ef090781255929bbd1b97`: Python 3.10/3.12, all
maintained documentation links, dependency checks, contract equality and actual
fixture/pretrained/legacy CT receiver smokes.

[CT run 39929548618](https://github.com/LilyC2024/ai-medimg-2.5D-CT/actions/runs/39929548618)
passed at `281c2446d39736075d41aec74ceb9c9fb9002411`: Windows/Linux regression,
updated link checks, actual pretrained/bridge smoke and Linux container checks.
Original PNG illustrations remain byte-for-byte unchanged and have current captions.
Both published trees matched local staged trees. This final verification-record
commit changes documentation only; it does not alter the tested implementation.

## Verified compatibility release

| Check | Recorded outcome |
| --- | --- |
| LOVISA (then MHCRA AI) | 146 tests, 44.55s |
| CT | 81 tests, 25.74s |
| Actual fixture → receiver | 32×64×64 HU; 1 non-ML candidate; 66 artifacts verified |
| Actual installed-pretrained CPU → receiver | Same source shape; 1 candidate; 66 artifacts verified; no inference-time download |
| Actual legacy → receiver | 20×48×48; 41 artifacts verified; producer ONNX parity passed |
| Shared contracts/report/renderer | Exact match after one import rewrite |
| Approval state | No imaging, safety or final report approval issued by actual smokes |

[LOVISA hosted run 39922198090](https://github.com/LilyC2024/Medical-AI/actions/runs/39922198090)
passed at `607c8a586fc820f9757b5b5a9b715247005df52f`: Python 3.10/3.12, dependency/
document checks, contract equality and all three actual CT transfers. Its producer
pin is `e0704b22177a23b323e4d3aff455c447d0579542`.

[CT hosted run 39922103738](https://github.com/LilyC2024/ai-medimg-2.5D-CT/actions/runs/39922103738)
passed Windows/Linux regression, fixture/pretrained bridges, real pretrained
phantom smoke and Linux container checks. Hosted CPU execution is software CI;
the app itself uses no cloud inference provider.

## Historical implementation gates

| Gate | Recorded result |
| --- | --- |
| Foundation | 20 tests and actual local structured-model connection |
| History import/extraction | 24 cumulative tests |
| Orchestration | 48 full tests |
| Safety/authentication | 76 non-UI tests |
| First complete UI release | 87 tests; corrected actual local reasoning smoke passed |
| Legacy CT workbench | 120 LOVISA tests, 32 CT tests and actual local transfer |
| Nodule producer/consumer | 26 producer/review checks; 144 consumer-phase tests before final additions |

The first model smoke rejected an attribution-confused response. Binding excerpt,
source ID and attribution together fixed the constraint; the corrected actual
smoke passed and still paused for final approval. Earlier coding review subagents
also found forged receipts, fabricated medication fields, cumulative-import limits,
Markdown injection and archive-allocation/recovery defects. These were software
reviews, not clinician verification. [Development](docs/DEVELOPMENT.md).

## What remains unproven

- No patient-data diagnostic accuracy, external clinical validation or reader study.
- LOVISA is synthetic-only; the evidence collection is empty by default.
- The safety policy covers structured fields, not every free-text emergency.
- Actual new-detector CUDA/NPU execution and GPU training are not demonstrated.
- Local accounts do not verify qualifications; hashes do not authenticate producer origin.
- Pending state is in memory; disk storage is unencrypted and administrators are trusted.
- Interactive browser review was unavailable in the earlier compatibility pass.
  The workspace release above adds actual browser checks; automated UI tests still
  use scripted models and reviewer identities.

[Security](SECURITY.md) · [Release/migration](docs/RELEASE.md).

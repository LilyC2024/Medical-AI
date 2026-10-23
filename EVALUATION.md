# LOVISA evaluation record

These results concern synthetic software behavior, not diagnostic accuracy,
clinical safety or clinician time savings. [Reproduce checks](docs/VALIDATION.md)
· [Eight acceptance requirements](docs/ACCEPTANCE.md).

## Concise combined report — 23 October 2026

| Executed check | Actual outcome |
| --- | --- |
| Final complete regression | **220 passed in 79.04s** |
| Earlier full regressions before content-manifest binding | 218 passed in 77.75s; 218 passed in 105.05s during a separate actual local Ollama smoke |
| Summary/note/source/CT foundation | 76 focused checks passed in 35.96s |
| Portable export and combined UI | 13 focused checks passed in 19.43s; 17 later checks passed in 19.67s |
| CT companion regression | **81 passed in 22.42s**, with 11 existing dependency/legacy-export warnings; 25 documentation files passed local-target checks |
| Final actual local gemma4:e2b smoke | Passed: missing-data hold, eligible reasoning and final clinician-review pause; no approval |
| Actual installed-pretrained CPU transfer | Passed: generated 32×64×64 source, one candidate, 66 verified artifacts; no imaging or final approval |
| Scripted documentation example | 178 words, one heading, generated non-ML phantom and 8.00 mm scripted caliper; no actual clinician verification |
| Browser example verification | One heading, no subheadings; both 64×64 embedded source/annotation images loaded; no horizontal overflow |
| Actual app browser | Demo sign-in and patient/report navigation; generated fixture opened automatically with explicit Include reviewed CT in report action |
| Approvals in actual app/smokes | None issued. The local CT study remains pending; example/test reviewer decisions exist only in temporary scripted databases |

The report now combines history hypotheses, accepted CT inspection, essential gaps
and an attributed brief reviewer note in one section. Exact source excerpts,
filenames/dates/IDs and model support/counterevidence stay in `report_evidence` and
the JSON package. Markdown remains text-only; approved HTML embeds verified CT
source/annotation pictures and reviewer calipers. Images/notes remain outside the
LLM; no clinical vocabulary or diagnostic capability was added.

A signed content manifest binds approval to the underlying record, model evidence,
CT snapshots and note, as well as the visible-text hash. A regression substitutes
a different valid accepted CT with identical short prose and verifies that saving
and HTML export reject it. Other checks cover changed notes/stale approval,
forged authorship/evidence, zero candidates, absent CT, legacy-mask HTML, later CT
acceptance requiring a new report, script/markup injection and altered images.

Automated tests and the example use scripted inference/reviewers. The separate
actual local Ollama smoke exercises real inference and stops at clinician review.
No actual clinical safety decision or qualified clinician approval is established.
CT code/contracts, model weights, the hypothesis catalog and dependencies are
unchanged. The companion changes only integration documentation. Existing saved
reports are not rewritten. [Report rules](docs/REPORTS.md).

## Focused patient workspace — 23 October 2026

| Executed check | Actual result |
| --- | --- |
| Final complete regression | **206 passed in 69.42s** after literal source-filename rendering; prior 205-test UI release passed in 72.31s |
| Focused regression | 59 formatted UI/navigation/imaging checks in 38.32s; 23 final navigation/CT checks in 15.96s; 6 source/navigation UI checks in 9.65s |
| Actual local gemma4:e2b smoke | Passed: missing-data hold, eligible reasoning and final clinician-review pause; no approvals |
| Dependencies / shared CT contract / compile | pip check, exact contract equality and compileall passed |
| Documentation | 28 maintained Markdown files passed local-target checks |
| Generated scroll scripts | All six fixed destinations passed Node syntax checks; this is separate from browser execution |
| Actual browser navigation | Guide opens/focuses patient menu, history, CT, safety, sources and report; repeat CT/safety links work |
| Actual browser isolation/safety | Morgan → Riley clears pending CT; only selected patient displayed; Casey warning keeps generation blocked |
| Actual local CT runs | Fixture and installed-pretrained phantom runs completed, one candidate each, both source/overlay images loaded; no acceptance |
| Responsive check | Temporary desktop override reset; native 609px view has no horizontal overflow and safety anchor lands at 88px |
| Actual human approvals | None issued: no safety continuation, imaging acceptance or final approval; local demo left at Morgan's unsubmitted safety form |

Tests use temporary databases, scripted inference and synthetic reviewer identities.
New checks cover explicit patient selection, guide navigation, pending-CT resolution,
patient switching during analysis, dropped late results, cleared notes and discarded
pending studies. Final approval and source/policy checks remain mandatory.

The first full regression exposed a ZIP-retry fixture that generated a fresh
archive, allowing ZIP timestamp metadata to change its identity. The test now
retries the original bytes; archive verification was not weakened. An outdated
navigation test double was also updated to expose the real task snapshot API.
The successful full run above includes both corrections.

No dependency, model, clinical policy, hypothesis catalog or CT wire contract was
changed. CT's producer repository is unchanged. The UI removes technical dumps,
keeps readable original excerpts in Source records and adds fixed local navigation
anchors. Browser verification caught and corrected a scroll-helper execution/quoting
issue and repeated same-destination rendering; each click now creates a fresh,
fixed-ID local component. No source/model text is executed. Existing response
budgets and research limitations still apply. Hosted publication is recorded below.

### Hosted focused-workspace publication

[Run 39967554491](https://github.com/LilyC2024/Medical-AI/actions/runs/39967554491)
passed at `d3c39b092e3f3181825ece15f2f48d24d71db640`: Python 3.10/3.12,
dependency/document checks, exact shared contracts and actual fixture/pretrained/
legacy CT producer-consumer smokes. The published tree matched the staged local
tree.

[Final run 39968159029](https://github.com/LilyC2024/Medical-AI/actions/runs/39968159029)
passed at `f3634b758e03821c127bb96087bc5a0d5a99e454`: Python 3.10/3.12,
dependency/document checks, exact shared contracts and actual fixture/pretrained/
legacy CT producer-consumer smokes. This includes literal source-filename rendering
and the 206-test suite. Its published tree matches the local checkout. The final
verification-record commit changes documentation only and skips duplicate CI.
The loopback demo is left at Morgan's unsubmitted Safety check; no clinical or
imaging approval was issued by these actual checks.

## Guided demonstration release — 23 October 2026

| Executed check | Actual result |
| --- | --- |
| Final complete regression | 187 passed in 59.89s |
| Earlier full regression before final result-order correction | 187 passed in 93.55s while a separate local model smoke was running |
| Staged safety, demos, grounding and wire budgets | 35 focused checks passed in 7.02s |
| Guided UI/service/source-presentation checks | 24 passed in 26.26s |
| CT result-order correction | 12 focused UI checks passed in 17.47s |
| Actual local gemma4:e2b smoke | Passed: missing-data hold, eligible synthetic reasoning, final clinician-review pause; no approvals |
| Shared CT contract / dependencies / compile | Exact equality, pip check and compileall passed |
| Real browser checks | Requested demo login; seven case choices; disabled bottom Generate; fixture and installed-pretrained result summaries with both images loaded |
| Responsive check | Temporary 1440px override reset; native 609px layout had no horizontal overflow and both CT images remained loaded |
| Approval state in actual checks | No safety continuation, imaging acceptance or final clinician approval issued; pretrained study left pending |
| Local credential setup | Requested local demo account created with a salted hash; account database/password not committed |

An intermediate verification rerun ended with signal 143 before a pytest verdict;
it is excluded from passing counts. The final full run above completed normally.

Five authored complex cases are loaded idempotently from original JSON. Automated
checks preserve unknown dates, identify documented dose changes, reject reasoning
before safety preparation and keep Casey's urgent case stopped. Four scripted
nonurgent drafts retain seven sections, each original entry once, evidence keys
and fewer than 1,250 whitespace-separated words per tested case. These are tests
with scripted inference and reviewer identities, not actual clinician review.

The actual local Ollama smoke remains separate. Larger compact requests are checked
against the actual transmitted prompt/schema budget; no record text is truncated.
The model, hypothesis catalog, safety policy and CT wire contract are unchanged.
This work establishes software behavior, not regulatory compliance, diagnostic
accuracy or qualifications of a local account. [Examples](docs/DEMO_CASES.md).

### Hosted guided-demo publication

[Run 39949841373](https://github.com/LilyC2024/Medical-AI/actions/runs/39949841373)
passed for `89257100df6514b5f4e6be3e42a1036dbee8ee75`: Python 3.10/3.12 tests,
dependency/document checks, exact shared-contract equality and actual fixture,
installed-pretrained CPU and retained legacy producer/receiver smokes. The
published implementation tree matched the local staged tree. This follow-up
verification record changes documentation only. The local demo remains on
loopback with a pending, unapproved pretrained study available for inspection.

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

### Hosted workspace publication

[LOVISA run 39938918945](https://github.com/LilyC2024/Medical-AI/actions/runs/39938918945)
passed at `3c5e2d5e8a30c76c0cfda5f1925c740d004bbc5f`: Python 3.10/3.12 regression,
dependency/document checks, exact shared contracts and actual fixture/pretrained/
legacy CT transfers using the pinned producer below.

[CT run 39938445818](https://github.com/LilyC2024/ai-medimg-2.5D-CT/actions/runs/39938445818)
passed at `5ba347cf6cd66b1931eaad3cd7d8cb27d4136606`: Windows/Linux regression,
actual pretrained inference/bridge and Linux container checks. Both published
implementation trees matched local staged trees. The verification-record follow-up
changes documentation only. The local server was restarted with the published
code and verified at its native narrow viewport without horizontal overflow;
sidebar collapse/reopen works and the temporary desktop viewport was reset.

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

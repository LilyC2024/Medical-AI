# LOVISA evaluation record

## Durable pending reviews — 24 October 2026

Persistence change; no clinical logic, policy, catalog, model or approval rule
changed. With `LOVISA_RECEIPT_KEY` (or a keyring key) pending graphs use a LangGraph
SQLite checkpointer and can be resumed; without one, behaviour is unchanged.

| Executed check | Actual outcome |
| --- | --- |
| `python -m pytest -q` (Python 3.13.17, local container) | **284 passed in 79.66s** (279 before + 5 new in `test_persistence.py`) |
| New persistence tests | Key sources/validation; resume and approve after simulated restart; rotated key cannot approve; ephemeral key writes no checkpoint file; UI **Resume saved review** after session loss |
| `scripts/check_docs.py` / `generate_api_docs.py --check` / `pip check` / `compileall` | Passed / matches / no broken requirements / compiled |
| `ruff check .` (ruff 0.17.2, default rules) | 95 findings, identical set to baseline |

Not run: OS keyring backends (no keyring package/backend here), an actual Streamlit
process restart in a browser, Python 3.10/Windows, live Ollama, hosted CI.

## Expert review and joint release — 24 October 2026

Three independent coding reviewers audited LOVISA, CT and endoscopy. Repairs
were tested before the documentation phase. Root READMEs are now concise; linked
subject guides and generated source/class/function references carry the detail.
[Reproduced findings](docs/REVIEW.md) · [Development agents](docs/DEVELOPMENT.md).

| Executed check | Actual outcome |
| --- | --- |
| Final LOVISA regression | **279 passed in 149.79s**; scripted inference/review and temporary databases |
| Final CT regression | **105 passed in 29.40s**, 11 existing dependency/legacy warnings |
| Final endoscopy regression | **72 passed in 5.76s**, two existing ONNX exporter warnings |
| Actual registered MONAI model, generated phantom | **8.39s**, one candidate; unreviewed report remains blocked |
| Actual CT producer → receiver | Fixture/pretrained nodule-v2 each 66 verified artifacts; legacy-v1 41 artifacts; no approvals |
| Actual installed endoscopy producer → receiver | **0.91s**, one generated-input region, four verified artifacts; pending review |
| Actual local Upload/Analyze | CT ZIP **0.69s**, endoscopy ZIP **0.51s**, actual raw-JPG model **2.74s**; no image/safety/final approval |
| Actual local gemma4:e2b smoke | Passed uncertainty hold and eligible fictional reasoning; stopped before final approval |
| Actual real CT + endoscopy + local LLM paired report | **66.48s**, 170 words and four embedded pictures; approvals scripted only in disposable SQLite |
| Documentation | **82 maintained Markdown documents** across repos pass local file/heading checks; source references match AST, also checked across Python 3.10/3.12 |
| Supporting checks | All three pip consistency/compilation checks and applicable Ruff checks passed; shared CT and endoscopy sources match exactly |

Eight LOVISA regressions cover capacity exhaustion/retry, source-supplied Markdown
in validation errors, actual failure reason, active-task cancellation by CT upload,
late draft rejection and deferred cross-modality result collection. Source,
safety/auth/content-binding and immutable accepted-image checks were preserved.
The current static source diagram was rendered and inspected locally; this is
not new manual browser visual verification. The retained scroll component emits
an existing Streamlit deprecation log and was not replaced without browser-focus QA.

CT/endoscopy models, dependencies, wire schemas and the clinical hypothesis catalog
were unchanged. Actual research image/model checks are not clinical validation;
no new training, negative-examination evaluation, CUDA or NPU execution is claimed.
Actual-app patient data, image acceptance and clinical approvals were not modified.
Earlier sections below are dated historical evidence, not current capability promises.

The previous Upload/Analyze hosted run [40019579036](https://github.com/LilyC2024/Medical-AI/actions/runs/40019579036)
was confirmed successful before this review. New source publication, joint paired-
report results and hosted outcomes are recorded after execution below.

## Upload/Analyze repair — 23 October 2026

The original failure was a frozen clinical-context lock on all image actions,
combined with separate run/import buttons and completed-job handles used as
cross-panel locks. Both image panels now use Upload/Analyze. Successful input
starts a fresh unreviewed context; malformed input preserves the existing report.
Pending review is never overwritten, and neither an upload nor Analyze supplies
image, safety or clinical approval.

| Executed check | Actual outcome |
| --- | --- |
| Action/navigation foundation, before panel integration | 25 passed in 10.32s |
| Focused actions/uploads/review/report/UI | 39 passed in 49.84s |
| Full offline regression | **267 passed in 189.43s** under concurrent live-smoke load |
| Actual CT `ct-real.mhcra.zip` through Upload/Analyze | **0.72s** to visible results, one candidate; existing predictions validated, no inference rerun |
| Actual `endoscopy-03.endo.zip` through Upload/Analyze | **0.51s** to visible results, two regions; existing predictions validated |
| Actual `endoscopy-03.jpg` through Upload/Analyze | **2.84s** to visible results, two regions; installed local polyp model ran on exact uploaded bytes |
| Actual local `gemma4:e2b` smoke | Passed uncertainty hold and separate eligible fictional reasoning; final approval still required |
| Supporting checks | Dependency consistency, compilation, 33 Markdown file-link checks, focused syntax/undefined-name checks, whitespace and exact CT/endo contract sync passed |

The real-file smoke redirects only services to disposable SQLite; it issues no
imaging, safety or final approvals and makes no LLM call. Automated UI regressions
use actual upload widgets with artificial pixels/scripted clinical inference.
This was not manual browser visual verification. The first smoke-harness startup
exceeded AppTest's default three-second initialization limit during concurrent
checks; increasing the harness initialization budget to 30 seconds allowed the
actual upload checks above. Runtime worker deadlines remain 110 seconds.

Invalid/empty/wrong-patient/wrong-modality files, pending study replacement,
expired authentication, stale jobs, failed-output collection, retry, exact raw
image routing and frozen-report preservation are covered. Saved reports and old
workflow content remain untouched; a new report must pass safety and final review
again. No model, dependency, safety policy or producer contract was changed.
CT input here remains a prepared source-mapped review ZIP; full DICOM inference
is offline companion work. Arbitrary unprovenanced research JPGs are rejected.

[Reproduce upload smoke](docs/VALIDATION.md#uploadanalyze-regressions) ·
[Operation](docs/INTERFACE.md#consistent-image-actions). Publication and local restart
outcomes are recorded below after completion.

## Real-image composite and clearer review — 23 October 2026

| Executed check | Actual outcome |
| --- | --- |
| Final LOVISA regression | **243 passed in 102.56s** |
| CT companion final regression | **83 passed in 34.61s**, 11 existing dependency/legacy warnings |
| Endoscopy companion final regression | **37 passed in 5.15s**, two existing ONNX-export deprecation warnings |
| Real CT excerpt inference | **11.98s**, registered pretrained MONAI CPU, one candidate, declared 32×96×96 ROI at (168,313,300) |
| Real raw endoscopy -> worker -> LOVISA validation | **3.16s**, five regions, four verified artifacts; no approvals |
| Actual local gemma4:e2b standard smoke | Passed uncertainty hold and eligible fictional reasoning; final review still required |
| Actual real CT + endoscopy + local LLM combined-report smoke | **34.32s**, 170 words, one heading and four embedded source/annotation images |
| Approval simulation | Scripted solely in a disposable test database; no actual-app imaging, safety or final approval issued |
| Real-image UI smoke | Actual CT/endo example buttons, cyan region focus, blank image notes and four draft pictures passed with scripted model/reviews in a disposable database; final review stayed pending |
| Review UX | Checked confirmation defaults, optional blank notes, explicit submit, paused defaults, candidate uncertainty blocks, patient-switch reset and changed-note preview tested |
| Data boundaries | Separate public/synthetic schemas, exact pixels/boxes/crop coverage, old stored synthetic-manifest compatibility and local example path/hash guards tested |
| Source/dependencies | Shared contracts match; pip consistency, compilation, Ruff checks and local documentation links passed |

The signed-in Jordan example has **fictional history** and unrelated public imaging:
TCIA LIDC-IDRI-0002 (CC BY 3.0) and Kvasir-SEG (research/education terms; subject
identity unknown). Their original sources, predictions, reference annotations,
permission declarations and acquisition-date uncertainty remain distinct.
The local kit has three fixed Kvasir JPEGs and pending result ZIPs; no pixels,
weights, accounts or runtime reports were committed.

The CT ROI was selected using an official reader contour **before inference**.
Two reader observations matched a declared localization proxy; this is neither
detection accuracy nor an independent benchmark, and LUNA overlap is possible.
The whole-scan CPU attempt was stopped after roughly 28 minutes without a result.
**Full CT training was not run** because this host lacks the required CUDA GPU.
The successful excerpt test must not be read as full-examination coverage.

Endoscopy was actually retrained for 24 CPU epochs (365.949s under concurrent CT
load), with validation-loss checkpoint selection. Mean Dice **0.5439824** and IoU
**0.4131187** on 168 positive images improve on the earlier 0.446 baseline, but
this previously examined split is exploratory, has no negatives and does not
establish patient independence. No cancer/clinical performance claim follows.
[Commands, data terms and reproducibility](docs/RESEARCH_IMAGES.md).

The report is shorter and hides model scores/hashes from primary panels while
retaining content-bound evidence. Initially blank unchanged final notes no longer demand a note
preview; changed nonempty notes still do. Preselected confirmations record no
approval until explicit authenticated submission. Urgent routing and model
grounding remain enforced in Python. Browser styling is covered by automated
Streamlit/UI checks; no new manual browser-layout screenshot is claimed.

Compatible producer commits: CT `b73a72188efda899f9d0a0d321f905002bc7dac3`,
endoscopy `81ff9f53a0baa9b40ff396283ef1dd9f430bf170`. Hosted publication outcomes
are recorded after the corresponding runs finish.

The sections below are historical evidence, with their then-current scope/counts.

Results distinguish manufactured software tests from actual local model/research-image
experiments. None establishes diagnostic accuracy, clinical safety or clinician time savings. [Reproduce checks](docs/VALIDATION.md)
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

### Hosted combined-report publication

[Run 39988179817](https://github.com/LilyC2024/Medical-AI/actions/runs/39988179817)
passed for `40502923d4990ebca9184f7fb0bdd7144e8d3695`: Python 3.10/3.12,
dependency/compile/document checks, exact shared-contract equality and actual
fixture, installed-pretrained CPU and legacy CT producer-consumer transfers.
The published implementation tree matched the staged local tree.

CT integration documentation was published at
[`a3da979c06c120914193d21371286b0892b15526`](https://github.com/LilyC2024/ai-medimg-2.5D-CT/commit/a3da979c06c120914193d21371286b0892b15526).
It changes documentation only, passed 81 local tests/25 document checks and skips
duplicate hosted CI. The producer-code pin is unchanged. Both local checkouts
matched their published trees. This final verification record changes only
LOVISA documentation and skips duplicate CI; no actual clinician approval was issued.

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


## 0.7.0 endoscopy integration — 23 October 2026

Implemented typed `lovisa-endo-image-v1` source/probability/mask/overlay validation,
a separate bounded local CV worker and Endoscopy review view. Candidate decisions,
notes and explicit attestation bind authenticated image acceptance. Endoscopy and
CT snapshots share report content binding and offline HTML pictures, while their
validators/coordinates remain separate. The LLM receives no imaging pixels/notes;
its catalog and safety routing are unchanged.

**Local regression: 231 tests passed in 103.88s.** This includes all prior 220 tests
and 11 new endoscopy source/review/workflow/patient-isolation/UI/worker tests.
Models/reviewers in clinical tests are scripted in temporary databases. Actual
endoscopy fixture/installed-model producer-consumer smokes passed (1.04s/1.08s,
one region and four verified artifacts each); neither issued an image or clinical
approval. Exact shared contract/worker equality and the unchanged CT contract
checks passed. Real local `gemma4:e2b` smoke passed and paused before final approval.

The standalone companion trained/evaluated a real CPU Kvasir-SEG baseline; mean
positive Dice 0.446343 on 168 test images (zero negative images). This is limited,
exploratory software research, not evidence of clinical detection or screening
specificity. [Full companion evidence](https://github.com/LilyC2024/AI-MedImg-Endo/blob/main/EVALUATION.md).
No NPU/Windows, external dataset, cancer classification or physical endoscopy-size
accuracy is claimed. Public research images remain outside synthetic LOVISA cases.

A separate localhost browser test port was denied by a saved browser permission;
no workaround was attempted. New UI interactions were checked with Streamlit
AppTest; live visual verification of the endoscopy view remains uncompleted.
Final documentation, CI and publication outcomes are appended after execution.

Final local checks: 32 Markdown files, exact endoscopy contract/worker equality and unchanged CT contract equality passed. Actual CT fixture and configured pretrained CPU smokes passed with 66 artifacts each and approvals pending. An explicit stale `models/luna16` directory first failed its registration check; the configured registered `models/luna16-full` then passed without weakening validation or silently falling back.

The cross-repository endoscopy workflow pins producer `bff92c23dd9e2679d38a7dcd4274b1cb5035a35f` and checks fixture plus actually trained artificial ONNX inference against the LOVISA receiver. Hosted outcomes are recorded after completion.

The producer pin includes the Windows POSIX-path correction; shared evidence contracts are unchanged. Local companion tests now total 35; LOVISA remains 231.


### Endoscopy release publication verified

[Hosted run 40002402873](https://github.com/LilyC2024/Medical-AI/actions/runs/40002402873)
passed on implementation/pin source `3774415b602fdc27e6bafcce54fab50221bdcdc1`:
Python 3.10 and 3.12 tests, endoscopy fixture and actually trained artificial ONNX
producer-consumer checks, and retained fixture/pretrained/legacy CT checks.
[Endoscopy Linux/Windows run 40002316931](https://github.com/LilyC2024/AI-MedImg-Endo/actions/runs/40002316931)
also passed after fixing canonical POSIX split paths. There are 231 local LOVISA
and 35 local companion tests. Optional OpenVINO CPU parity passed locally; NPU
hardware remains untested. No imaging or clinical approvals were issued by smokes.

Both source updates are published. The local LOVISA server was restarted to load
fresh UI modules; loopback health returned HTTP 200. A new sign-in is required.
The old pending in-memory UI state is not a reviewed report. Final documentation
updates change no tested runtime behavior. Live visual verification remains
limited by the saved browser permission described above.

## Final research-image release checks

Receiver source `2c6f2ead4886f646662be2deaf5ef05d9279f375` passed the [hosted LOVISA workflow](https://github.com/LilyC2024/Medical-AI/actions/runs/40015437588): Python 3.10, Python 3.12, all configured CT producer/receiver smokes and the endoscopy producer/receiver smoke. CT [hosted checks](https://github.com/LilyC2024/ai-medimg-2.5D-CT/actions/runs/40014638635) and repaired endoscopy [Linux/Windows checks](https://github.com/LilyC2024/AI-MedImg-Endo/actions/runs/40015138472) passed. The final follow-up changes are Markdown evidence/reference updates only.

Local demo restarted on loopback `127.0.0.1:8501`; health, existing demo-account sign-in and both real-image bundles verified. The composite case remains unapproved in the actual database. An additional real-image AppTest used only a disposable DB/scripted model and review submissions, validating both example buttons, candidate highlight, default confirmations, optional blank image notes, and four draft pictures with final review pending.

## Upload/Analyze delivery

Tested source `aa06c9e160010e0992734eb2190f29eba652da3d` is published in
[LilyC2024/Medical-AI](https://github.com/LilyC2024/Medical-AI/commit/aa06c9e160010e0992734eb2190f29eba652da3d).
[Hosted workflow 40019579036](https://github.com/LilyC2024/Medical-AI/actions/runs/40019579036)
was in progress at local handover; no hosted success is claimed for this release
until that run completes. The follow-up publication changes only evaluation/phase
records, not the tested runtime source.

The existing localhost process was restarted on `127.0.0.1:8501`; health returned
HTTP 200 and the existing `demo` account login was verified. Sign in again after
refreshing. The smoke made no changes to the app's patient/imaging/report data.
The prepared-kit README and maintained guides now describe Upload/Analyze.

## Reviewed producer source pins

The reviewed CT source [9a3cdfe](https://github.com/LilyC2024/ai-medimg-2.5D-CT/commit/9a3cdfeb0dc71cb5a7e479e54d5a8430ddbe967c)
and endoscopy source [9391192](https://github.com/LilyC2024/AI-MedImg-Endo/commit/9391192d2f68cc7e50ba21a1085b21d1b3af2664)
are published. LOVISA's integration CI now pins those exact producer commits.
Shared contracts are unchanged and exact sync plus all local producer/consumer
smokes passed. No hosted outcome is inferred from a local result.

## Publication and hosted verification — 24 October 2026

Tested source [4567b17](https://github.com/LilyC2024/Medical-AI/commit/4567b1711ba6cc4b0482d7831ceed63af8d79d56) is published.
[Hosted workflow 40099153159](https://github.com/LilyC2024/Medical-AI/actions/runs/40099153159)
completed successfully. Python 3.10/3.12 tests, exact pinned endoscopy
producer/consumer and fixture/pretrained/legacy CT transfers all passed. The CT
[hosted release](https://github.com/LilyC2024/ai-medimg-2.5D-CT/actions/runs/40099064726)
and endoscopy [Linux/Windows release](https://github.com/LilyC2024/AI-MedImg-Endo/actions/runs/40099084727)
also passed. All 456 local tests and actual local smokes above remain separate
from these hosted software checks.

The local demo was started on loopback 127.0.0.1:8501; HTTP health and the existing
demo-account sign-in passed. No actual-app import, image/safety/final approval or
clinical-record modification was issued. New manual browser QA is not claimed.

Final follow-up changes only phase/evaluation Markdown records; tested runtime,
models, protocols and generated source references are unchanged. Local branch
and publication trees are checked for equality before synchronization.

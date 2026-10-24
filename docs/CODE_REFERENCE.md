# LOVISA code and folder reference

[Overview](../README.md) · [Architecture](ARCHITECTURE.md)

Use the architectural map here, then the detailed function contracts:
[clinical services](reference/CLINICAL.md), [imaging services](reference/IMAGING.md)
and [complete callable/subfunction signatures](reference/CALLABLES.md).

| Area | Modules | Responsibility |
| --- | --- | --- |
| UI/bootstrap | app.py, runtime.py | Patient selection, lazy workspace routing, local services and fixture seed |
| Design system/forms | ui/components.py, ui/theme.css, ui/history.py, ui/clinical.py | Escaped readable cards, right-hand guide, import/clinical forms and task progress |
| Patient navigation | ui/navigation.py | Fixed action links, scrolling, patient-state cleanup and mismatched-result guards |
| Response budget | jobs.py | Bounded workers, cancellation, deadline and late-result rejection |
| Record contracts | models.py, grounding.py | Strict fields and original-source comparisons |
| Persistence | database.py, storage.py | Parameterized SQLite and guarded report saving |
| Extraction/import | history.py, history_import.py | Chronology, orders and approved source appends |
| LLM/references | agents.py, compact_reasoning.py, reasoning_constraints.py, ollama_client.py, evidence.py | Bounded hypotheses, local inference and approved text retrieval |
| Safety/auth/graph | safety.py, auth.py, workflow.py | Python policy, content-bound approvals and sequential LangGraph |
| Reporting | report.py, report_notes.py, report_binding.py | One-section summary, detailed evidence index and signed reviewer-note verification |
| Report pictures/export | report_assets.py | Verified representative CT/caliper pictures and approval-gated self-contained HTML |
| CT result summaries | imaging_results.py | Deterministic candidate/review/caliper summary shared by the viewer and concise report |
| Imaging actions | imaging_actions.py, ui/imaging_actions.py | Authenticated upload/example routing, fresh report context, shared Upload/Analyze, visible worker errors and retries |
| CT execution | ct_worker.py | Separate interpreter, mode/device, cancellation and watchdog |
| CT validation/storage | imaging_contract.py, imaging.py | Version dispatch, pending originals and immutable accepted snapshots |
| Producer trust | producer_signature.py (shared copy), producer_trust.py, producer_ui.py | Ed25519 verification against pinned keys, signature policy, status and false-positive display |
| Nodule contract | nodule_models.py, nodule_exchange.py | Vendored typed geometry/review, canonical report and wire renderer |
| Nodule review/UI | nodule_support.py, nodule_ui.py, imaging_ui.py | Candidate/caliper controls, actor/hash binding and local inspection |

## Folders

| Folder | Contents |
| --- | --- |
| medical_assistant | Runtime modules listed above |
| config | Versioned safety policy |
| data/patients | Reviewed fictional JSON fixtures |
| data/evidence | Local reference manifest; empty by default |
| data/imaging, data/reports | Ignored accepted images, jobs and exports |
| docs, docs/reference, docs/images | Subject guides, function details and retained pictures |
| scripts | Smoke, contract synchronization and documentation checks |
| tests | Temporary-database, scripted inference/review and Streamlit regressions |
| third_party | Preserved CT-vendored MIT notice |
| .github/workflows, .streamlit | Hosted checks, loopback UI/telemetry settings |
| .venv | Ignored local environment |

[Exact tracked-file inventory](FILE_INVENTORY.md) · [Stable names](NAMING.md).

## Image-first endoscopy extension

`endo_contracts/` supplies shared ML-free schemas and worker lifecycle; `endo_worker.py` launches local CV; `endo_support.py` binds decisions; `endo_ui.py` renders image review. Shared imaging storage and report modules dispatch by modality. [Contract and behavior](ENDOSCOPY.md).

## Research demo extension

| Module/script | Responsibility |
| --- | --- |
| `research_examples._manifest`, `_read` | Bounded local manifest/file loading and hash checks |
| `research_examples.example_bundle` | Case/modality-specific prepared evidence |
| `research_examples.matching_endoscopy` | Exact permitted JPG bytes → declared dataset provenance |
| `endo_worker.LocalEndoscopyJob` | Artificial or public RGB subprocess, fixed local model and watchdog |
| `endo_contracts.PublicResearchSource`, `Bundle` | Separate public/synthetic formats; derived pixel validation |
| `nodule_exchange.NoduleBundle.verify_research_crop` | Physical geometry, source slices and enclosed boxes against original metadata |
| `scripts/prepare_research_demo.py` | Build unapproved CT/endo evidence and upload examples from local research data |
| `scripts/smoke_research_pair.py` | Actual image-pair report smoke with scripted approvals in an isolated temporary database |

[Data sources, commands and limits](RESEARCH_IMAGES.md).

`scripts/smoke_uploads.py` exercises real CT ZIP/endoscopy ZIP/JPG uploads and actual
local polyp inference through Streamlit in a temporary database, issuing no reviews.

## Error and documentation services

`ui/errors.py:error_message(error, limit=600)` renders literal, bounded explanations.
Structured validation shows at most three locations/messages without echoing input
values or help URLs. Clinical capacity errors preserve safety state and offer a
recoverable retry; failed runs show their actual bounded reason.

The [source API inventory](reference/CALLABLES.md) now includes class fields,
exact signatures, nested helpers, direct calls, explicit raises and code-line links.
Regenerate with `scripts/generate_api_docs.py --write`; `--check` detects drift.
The inventory imports no model or application. Subject contracts remain the source
for operational guarantees, not static call lists.

# LOVISA code and folder reference

[Overview](../README.md) · [Architecture](ARCHITECTURE.md)

Use the architectural map here, then the detailed function contracts:
[clinical services](reference/CLINICAL.md), [imaging services](reference/IMAGING.md)
and [complete callable/subfunction signatures](reference/CALLABLES.md).

| Area | Modules | Responsibility |
| --- | --- | --- |
| UI/bootstrap | app.py, runtime.py | Patient selection, lazy workspace routing, local services and fixture seed |
| Design system/forms | ui/components.py, ui/theme.css, ui/history.py, ui/clinical.py | Escaped readable cards, right-hand guide, import/clinical forms and task progress |
| Response budget | jobs.py | Bounded workers, cancellation, deadline and late-result rejection |
| Record contracts | models.py, grounding.py | Strict fields and original-source comparisons |
| Persistence | database.py, storage.py | Parameterized SQLite and guarded report saving |
| Extraction/import | history.py, history_import.py | Chronology, orders and approved source appends |
| LLM/references | agents.py, compact_reasoning.py, reasoning_constraints.py, ollama_client.py, evidence.py | Bounded hypotheses, local inference and approved text retrieval |
| Safety/auth/graph | safety.py, auth.py, workflow.py | Python policy, content-bound approvals and sequential LangGraph |
| Reporting | report.py | Seven sections, exact citations and escaped research appendix |
| CT execution | ct_worker.py | Separate interpreter, mode/device, cancellation and watchdog |
| CT validation/storage | imaging_contract.py, imaging.py | Version dispatch, pending originals and immutable accepted snapshots |
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

# Clinical service contracts

[Reference index](../CODE_REFERENCE.md) · [All signatures](CALLABLES.md) · [Architecture](../ARCHITECTURE.md)

| API / helper | Input → result and invariant |
| --- | --- |
| database.seed / get_history | Fictional fixtures → idempotent SQLite / complete patient snapshot; conflicting IDs roll back |
| database.attach_original | Parsed record plus original filename/text → source-linked immutable record |
| grounding validation | Extracted entries and original JSON → exact field/attribution checks; unsupported facts fail |
| HistoryManagement.prepare | Supported synthetic JSON → hashed proposal with chronology/orders/discrepancies; no import |
| HistoryManagement.approve | Proposal plus authenticated, matching attested Review → transactional append |
| MedicalHistoryAgent.run / chronology | Valid record → known-date ordering, explicit undated facts and attribution |
| MedicationAgent.run | Valid structured orders → medication overview/dose changes; dates and documented source pairs required |
| LocalEvidenceCollection.retrieve / local_search | Query → at most three approved local hash-checked excerpts ranked by word overlap |
| SpecialistAgent reasoning | Source snapshot and approved references → schema/catalog-constrained hypotheses with exact excerpts |
| compact_reasoning.prepare / expand | Same record/catalog → bounded ID schema → exact excerpts and fully revalidated Assessment; invalid/duplicate IDs fail |
| jobs.Budget / WorkTask / BudgetInference | Finite local operation → staged progress or terminal stop; cancellation/deadline prevents late result publication |
| ui.components / ui.history / ui.clinical | Escaped display, explicit import/review forms and background actions; workers never write Streamlit state |
| ui.navigation.clear_patient / ensure_patient | Cancel abandoned work, discard unaccepted proposals and clear widgets; reject mismatched patient snapshots before display |
| ui.navigation.go_to / anchor / focus_pending | Allowlisted app destination → selected view and local scroll; no record/model input or approval |
| OllamaClient | Bounded prompt/schema → JSON from fixed-loopback local model; reject remote-backed metadata and oversized requests |
| SafetyAgent.evaluate | Snapshot, date and versioned policy → urgent/uncertain/ordinary decision with input binding |
| LocalAuth.create_clinician / login / require | Credentials/token → salted local account / expiring identity; not a credential registry |
| LocalAuth.receipt / verify_receipt | Action and content hash → signed process-local approval binding; mismatches fail |
| MedicalHistoryOrchestrator.start / start_patient | Valid record or SQLite ID → fixed case snapshot and graph event iterator |
| _initial_safety / _safety_review | Policy decision → stop or authenticated interrupt before reasoning |
| _retrieve_evidence / _reasoning | Eligible case → approved references and checked hypotheses; no image/model tools |
| _final_safety / _verify_safety_ack | Same snapshot/policy/date → repeated routing and acknowledgment validation |
| _verify_imaging / _compose | Accepted imaging plus assessments → verified concise combined summary with a separate evidence index |
| _review / _complete | Exact draft and human Review → pending correction or guarded reviewed state |
| ready_for_analysis / continue_analysis | Prepared history checkpoint + authenticated session → recheck exact safety/imaging and explicitly run reasoning |
| acknowledge_safety / review / _response | Account/session plus exact case/content Review → authenticated graph resume |
| revise | Arbitrary text revision is unsupported; factual corrections need an approved new source/case |
| export / storage.save_report | Reviewed state/payload → recheck sources, safety, artifacts and approval before export/save |
| report.compose / summary_parts / evidence_index | One concise section plus separate exact source/model/CT links; no inline technical citation list |
| report_binding.content_digest / verify_content_binding | Signed case-bound hidden evidence/image manifest complements the visible-text approval hash; identical prose cannot authorize different CT/source content |
| prepare_report_note / report_notes.verify_note | Authenticated, case-bound comment → new preview/hash; stale approvals fail |
| report_assets.inspection_figures / portable_html | Verified CT previews/calipers → representative figures / final approved offline HTML |
| storage.validate_reviewed_report | Recheck sources, note receipt, evidence links, CT and exact content before any final export |
| report.digest / inline_text | Content identity and literal Markdown presentation |

Model facts are not free-text edits. A failed constraint blocks the affected
operation. No model call follows final approval. All helper signatures, including
internal UI functions, are indexed in [Callables](CALLABLES.md).

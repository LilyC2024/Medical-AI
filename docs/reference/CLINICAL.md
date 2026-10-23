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
| OllamaClient | Bounded prompt/schema → JSON from fixed-loopback local model; reject remote-backed metadata and oversized requests |
| SafetyAgent.evaluate | Snapshot, date and versioned policy → urgent/uncertain/ordinary decision with input binding |
| LocalAuth.create_clinician / login / require | Credentials/token → salted local account / expiring identity; not a credential registry |
| LocalAuth.receipt / verify_receipt | Action and content hash → signed process-local approval binding; mismatches fail |
| MedicalHistoryOrchestrator.start / start_patient | Valid record or SQLite ID → fixed case snapshot and graph event iterator |
| _initial_safety / _safety_review | Policy decision → stop or authenticated interrupt before reasoning |
| _retrieve_evidence / _reasoning | Eligible case → approved references and checked hypotheses; no image/model tools |
| _final_safety / _verify_safety_ack | Same snapshot/policy/date → repeated routing and acknowledgment validation |
| _verify_imaging / _compose | Accepted imaging plus assessments → verified, escaped seven-section draft |
| _review / _complete | Exact draft and human Review → pending correction or guarded reviewed state |
| acknowledge_safety / review / _response | Account/session plus exact case/content Review → authenticated graph resume |
| revise | Arbitrary text revision is unsupported; factual corrections need an approved new source/case |
| export / storage.save_report | Reviewed state/payload → recheck sources, safety, artifacts and approval before export/save |
| report.digest / inline_text / citation helpers | Text/source IDs → content identity and escaped source-linked presentation |

Model facts are not free-text edits. A failed constraint blocks the affected
operation. No model call follows final approval. All helper signatures, including
internal UI functions, are indexed in [Callables](CALLABLES.md).

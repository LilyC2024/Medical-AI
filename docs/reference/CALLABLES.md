# Callable and subfunction inventory

[Reference index](../CODE_REFERENCE.md) · [Clinical contracts](CLINICAL.md) · [Imaging contracts](IMAGING.md)

Current source AST, including validators and nested helpers. See linked implementations for full invariants. Runtime data and model artifacts are excluded.

## [app.py](../../app.py)

LOVISA local workspace: reusable UI, bounded jobs and human review.

| Callable | Purpose/contract |
| --- | --- |
| `account_ui(auth)` | See linked implementation and subject contract. |
| `clear_private_state()` | Signing out hides every case and prevents background results reappearing. |
| `switch_patient()` | See linked implementation and subject contract. |
| `reset_case()` | See linked implementation and subject contract. |
| `main()` | See linked implementation and subject contract. |

## [medical_assistant/agents.py](../../medical_assistant/agents.py)

Constrained specialist prompt templates and local inference validation. The clinical graph uses this wrapper for reasoning only. History, medication and safety roles run through dedicated deterministic Python components.

| Callable | Purpose/contract |
| --- | --- |
| `Inference.assess(self, system: str, user: str, *, schema: dict &#124; None=None)` | See linked implementation and subject contract. |
| `SpecialistAgent.__init__(self, role: str, inference: Inference)` | See linked implementation and subject contract. |
| `SpecialistAgent.run(self, record: PatientRecord, earlier: dict[str, dict], evidence=None)` | See linked implementation and subject contract. |

## [medical_assistant/auth.py](../../medical_assistant/auth.py)

Local password authentication and short-lived in-process clinician sessions.

| Callable | Purpose/contract |
| --- | --- |
| `LocalAuth.__init__(self, path: Path=DATABASE_PATH)` | See linked implementation and subject contract. |
| `LocalAuth.has_users(self)` | See linked implementation and subject contract. |
| `LocalAuth.create_clinician(self, username: str, password: str, *, local_demo=False)` | See linked implementation and subject contract. |
| `LocalAuth.login(self, username: str, password: str)` | See linked implementation and subject contract. |
| `LocalAuth.require(self, token)` | See linked implementation and subject contract. |
| `LocalAuth.logout(self, token)` | See linked implementation and subject contract. |
| `LocalAuth.audit(self, action, patient_id, token, payload)` | See linked implementation and subject contract. |
| `LocalAuth.receipt(self, token, action, content_sha256)` | See linked implementation and subject contract. |
| `LocalAuth.verify_receipt(self, receipt, action, content_sha256)` | See linked implementation and subject contract. |
| `LocalAuth.record_receipt(self, receipt, patient_id, payload)` | See linked implementation and subject contract. |

## [medical_assistant/compact_reasoning.py](../../medical_assistant/compact_reasoning.py)

Compact local-model selection; Python restores exact immutable record excerpts. No new clinical vocabulary, sources or decisions are introduced. The expanded Assessment passes the same grounding/catalog checks as the full-output path.

| Callable | Purpose/contract |
| --- | --- |
| `catalog(prefix, values)` | See linked implementation and subject contract. |
| `prepare(user)` | See linked implementation and subject contract. |
| `expand(raw, record, refs, maps)` | See linked implementation and subject contract. |
| `expand.choose(ids, mapping)` | See linked implementation and subject contract. |
| `expand.claims(ids)` | See linked implementation and subject contract. |

## [medical_assistant/ct_worker.py](../../medical_assistant/ct_worker.py)

Bounded local CT subprocesses. No shell, uploads, downloads or model tools.

| Callable | Purpose/contract |
| --- | --- |
| `configured_ct_root()` | See linked implementation and subject contract. |
| `configured_ct_model(root=None)` | See linked implementation and subject contract. |
| `LocalCTJob.__init__(self, patient_id, *, root=None, jobs=None, timeout=MAX_JOB_SECONDS, mode='legacy', model_dir=None, device='cpu')` | See linked implementation and subject contract. |
| `LocalCTJob.bundle_path(self)` | See linked implementation and subject contract. |
| `LocalCTJob._watch(self, timeout)` | See linked implementation and subject contract. |
| `LocalCTJob.cancel(self, *, timed_out=False)` | See linked implementation and subject contract. |
| `LocalCTJob.status(self)` | See linked implementation and subject contract. |
| `LocalCTJob.elapsed(self)` | See linked implementation and subject contract. |
| `LocalCTJob.progress(self)` | See linked implementation and subject contract. |

## [medical_assistant/database.py](../../medical_assistant/database.py)

Transactional SQLite storage. Models have no access to these write functions.

| Callable | Purpose/contract |
| --- | --- |
| `connect(path: Path)` | See linked implementation and subject contract. |
| `initialize(path: Path=DATABASE_PATH)` | See linked implementation and subject contract. |
| `attach_original(record: PatientRecord, filename: str, raw: str)` | Convert legacy synthetic JSON to immutable source + separately stored facts. |
| `write_synthetic(record: PatientRecord, path: Path, *, actor: str, action: str, approval=None)` | Internal atomic append; existing IDs are immutable and exact retries are no-ops. |
| `get_history(patient_id: str, path: Path=DATABASE_PATH)` | See linked implementation and subject contract. |
| `list_patients(path: Path=DATABASE_PATH)` | See linked implementation and subject contract. |
| `seed(path: Path=DATABASE_PATH)` | Explicit built-in synthetic fixture creation; never imports arbitrary files. |

## [medical_assistant/endo_contracts/__init__.py](../../medical_assistant/endo_contracts/__init__.py)

ML-free, bounded RGB evidence protocol shared with LOVISA. No clinical inference.

| Callable | Purpose/contract |
| --- | --- |
| `sha(data)` | Hash supplied bytes with SHA-256 for consistency checking. |
| `digest(value)` | Hash canonical structured content without claiming producer authenticity. |
| `ModelInfo.matching(self)` | Keep fixture provenance and evaluation scope consistent. |
| `Study.bounds(self)` | Check candidate identities, box bounds and fixture scope. |
| `Review.explicit(cls, value)` | Require a literal true human image-review attestation. |
| `Review.verify(self, study)` | Recheck original-source association and every derived workspace annotation. |
| `Artifact.safe(cls, path)` | Reject absolute, traversal and reserved artifact paths. |
| `PublicResearchSource.explicit_composite(cls, value)` | See linked implementation and subject contract. |
| `Bundle.consistent(self)` | Require distinct schemas for artificial and deidentified public pixels. |
| `regions(probability, threshold, min_area)` | 4-connected predicted components, half-open source coordinates; no GT use. |
| `overlay_pixels(source, mask, candidates)` | Render deterministic amber candidate masks and boxes over source pixels. |
| `png(array)` | Encode a canonical PNG artifact without external resources. |
| `array_bytes(array)` | Encode a non-object NumPy array for bounded source verification. |
| `_image(data, mode, shape)` | Validate image dimensions and format before decoding pixel arrays. |
| `_probability(data, shape)` | Bound array headers and payload before allocating a finite probability map. |
| `unique(pairs)` | Reject duplicate JSON keys instead of silently accepting the last value. |
| `read_exchange(payload, patient_id)` | Verify all bytes and derived pixels before storing; hashes are not authenticity. |

## [medical_assistant/endo_contracts/worker.py](../../medical_assistant/endo_contracts/worker.py)

Bounded local subprocess lifecycle shared by the endoscopy interfaces.

| Callable | Purpose/contract |
| --- | --- |
| `LocalJob.__init__(self, command, *, cwd, directory, output, timeout=110, input_files=None)` | Initialise the explicit local model or bounded worker without remote fallback. |
| `LocalJob._watch(self)` | Publish completion only after successful process exit within the deadline. |
| `LocalJob.cancel(self, *, timed_out=False)` | Stop the worker process tree and prevent late result publication. |
| `LocalJob.elapsed(self)` | Return local monotonic time since the job began. |
| `LocalJob.status(self)` | Read worker lifecycle state under its lock. |
| `LocalJob.progress(self)` | Read only allowlisted stage markers from the bounded log tail. |

## [medical_assistant/endo_support.py](../../medical_assistant/endo_support.py)

Modality-specific candidate review binding; no clinical or safety decisions.

| Callable | Purpose/contract |
| --- | --- |
| `is_endoscopy(manifest)` | See linked implementation and subject contract. |
| `checked_endo_review(manifest, review, *, reviewer=None)` | See linked implementation and subject contract. |
| `endo_acceptance_digest(proposal, review)` | See linked implementation and subject contract. |
| `verify_endo_snapshot(snapshot)` | See linked implementation and subject contract. |
| `summarize_endo(manifest, review=None)` | See linked implementation and subject contract. |

## [medical_assistant/endo_ui.py](../../medical_assistant/endo_ui.py)

Source-first endoscopy inspection; every candidate needs explicit human review.

| Callable | Purpose/contract |
| --- | --- |
| `image_results(manifest, path_for, review=None)` | See linked implementation and subject contract. |
| `endoscopy_ui(path, auth, token, user, record, *, locked=False, case_imaging=None)` | See linked implementation and subject contract. |

## [medical_assistant/endo_worker.py](../../medical_assistant/endo_worker.py)

Explicit local Endoscopy Agent adapter; bounded CV worker, no LLM or downloads.

| Callable | Purpose/contract |
| --- | --- |
| `configured_endo_root()` | See linked implementation and subject contract. |
| `configured_endo_model(root=None)` | See linked implementation and subject contract. |
| `LocalEndoscopyJob.__init__(self, patient_id, *, root=None, jobs=None, mode='fixture', model_dir=None, backend='onnx-cpu', timeout=110, image_bytes=None, research=None)` | See linked implementation and subject contract. |

## [medical_assistant/evidence.py](../../medical_assistant/evidence.py)

Retrieve only explicitly approved, hash-verified files in a local collection.

| Callable | Purpose/contract |
| --- | --- |
| `LocalEvidenceCollection.__init__(self, directory: Path)` | See linked implementation and subject contract. |
| `LocalEvidenceCollection.retrieve(self, query: str)` | See linked implementation and subject contract. |
| `LocalEvidenceCollection.retrieve.local_search(query)` | See linked implementation and subject contract. |

## [medical_assistant/grounding.py](../../medical_assistant/grounding.py)

Source grounding for JSON medical imports; no semantic facts are invented.

| Callable | Purpose/contract |
| --- | --- |
| `validate_record_grounding(record: PatientRecord)` | See linked implementation and subject contract. |

## [medical_assistant/history.py](../../medical_assistant/history.py)

Extractive history and medication agents for typed synthetic source records.

| Callable | Purpose/contract |
| --- | --- |
| `chronology(entry)` | See linked implementation and subject contract. |
| `MedicalHistoryAgent.run(self, record: PatientRecord)` | See linked implementation and subject contract. |
| `MedicalHistoryAgent.run.extract(record)` | See linked implementation and subject contract. |
| `MedicationAgent.run(self, record: PatientRecord)` | See linked implementation and subject contract. |
| `MedicationAgent.run.extract(record)` | See linked implementation and subject contract. |

## [medical_assistant/history_import.py](../../medical_assistant/history_import.py)

Separate history-management workflow: validate → extract → approve → append.

| Callable | Purpose/contract |
| --- | --- |
| `HistoryManagement.__init__(self, path, *, auth=None)` | See linked implementation and subject contract. |
| `HistoryManagement.prepare(self, raw: str, filename: str)` | See linked implementation and subject contract. |
| `HistoryManagement.approve(self, proposal_id, review: Review, token=None)` | See linked implementation and subject contract. |

## [medical_assistant/imaging.py](../../medical_assistant/imaging.py)

Human-reviewed synthetic imaging storage, separate from clinical source facts.

| Callable | Purpose/contract |
| --- | --- |
| `ImagingStore.__init__(self, path, auth=None)` | See linked implementation and subject contract. |
| `ImagingStore.prepare(self, payload, patient_id, *, study_id=None)` | See linked implementation and subject contract. |
| `ImagingStore.discard(self, key)` | See linked implementation and subject contract. |
| `ImagingStore._directory(self, patient_id, study_id)` | See linked implementation and subject contract. |
| `ImagingStore._verify_directory(directory, snapshot)` | See linked implementation and subject contract. |
| `ImagingStore.approve(self, key, review, token=None, *, nodule_review=None, endo_review=None)` | See linked implementation and subject contract. |
| `ImagingStore.snapshots(self, patient_id)` | See linked implementation and subject contract. |
| `ImagingStore.verify(self, snapshots)` | See linked implementation and subject contract. |
| `ImagingStore.preview_path(self, snapshot, role, index)` | See linked implementation and subject contract. |
| `ImagingStore.preview_resolver(self, snapshot)` | Verify the archive once per view, then hash only requested artifacts. Acceptance, composition, completion, export and saving still perform full independent validation. Nothing is globally cached or shared across patients. |
| `ImagingStore.preview_resolver.resolve(role, index)` | See linked implementation and subject contract. |

## [medical_assistant/imaging_contract.py](../../medical_assistant/imaging_contract.py)

Bounded synthetic imaging exchange. Model artifacts are never clinical facts.

| Callable | Purpose/contract |
| --- | --- |
| `Artifact.local_relative(cls, value)` | See linked implementation and subject contract. |
| `Geometry.physical(self)` | See linked implementation and subject contract. |
| `ImagingBundle.boolean_only(cls, value)` | See linked implementation and subject contract. |
| `ImagingBundle.consistent(self)` | See linked implementation and subject contract. |
| `file_digest(payload)` | See linked implementation and subject contract. |
| `validate_bundle(payload: bytes, patient_id: str)` | Read bounded bytes without extracting arbitrary archive paths or pickle. |
| `_verify_pixels(bundle, artifacts)` | See linked implementation and subject contract. |

## [medical_assistant/imaging_results.py](../../medical_assistant/imaging_results.py)

Small, deterministic CT summaries shared by the viewer and clinical summary.

| Callable | Purpose/contract |
| --- | --- |
| `summarize(manifest, review=None)` | See linked implementation and subject contract. |

## [medical_assistant/imaging_ui.py](../../medical_assistant/imaging_ui.py)

Imaging inspection UI; acceptance is separate from final clinical approval.

| Callable | Purpose/contract |
| --- | --- |
| `_viewer(manifest, path_for, key, *, review=None)` | See linked implementation and subject contract. |
| `result_summary(manifest, review=None)` | See linked implementation and subject contract. |
| `imaging_ui(path, auth, token, user, record, *, locked=False, case_imaging=None)` | See linked implementation and subject contract. |

## [medical_assistant/jobs.py](../../medical_assistant/jobs.py)

Session-owned background work with a hard publication deadline; no UI in workers.

| Callable | Purpose/contract |
| --- | --- |
| `Budget.__init__(self, seconds=MAX_JOB_SECONDS)` | See linked implementation and subject contract. |
| `Budget.elapsed(self)` | See linked implementation and subject contract. |
| `Budget.check(self)` | See linked implementation and subject contract. |
| `WorkTask.__init__(self, target, *, seconds=MAX_JOB_SECONDS, title='Preparing your workspace')` | See linked implementation and subject contract. |
| `WorkTask._timeout(self)` | See linked implementation and subject contract. |
| `WorkTask.progress(self, message)` | See linked implementation and subject contract. |
| `WorkTask._run(self, target)` | See linked implementation and subject contract. |
| `WorkTask.cancel(self)` | See linked implementation and subject contract. |
| `WorkTask.snapshot(self)` | See linked implementation and subject contract. |
| `WorkTask.result(self)` | See linked implementation and subject contract. |
| `BudgetInference.__init__(self, inference, budget)` | See linked implementation and subject contract. |
| `BudgetInference.assess(self, *args, **kwargs)` | See linked implementation and subject contract. |
| `BudgetInference.close(self)` | See linked implementation and subject contract. |

## [medical_assistant/models.py](../../medical_assistant/models.py)

Validated record, specialist output, and human review contracts.

| Callable | Purpose/contract |
| --- | --- |
| `SourceDocument.valid_digest(self)` | See linked implementation and subject contract. |
| `PatientRecord.unique_ids(self)` | See linked implementation and subject contract. |
| `Explanation.no_confirmed_diagnosis(cls, value)` | See linked implementation and subject contract. |
| `Assessment.validate_sources(self, record: PatientRecord)` | See linked implementation and subject contract. |
| `Assessment.validate_sources.check(ids, source_type=None)` | See linked implementation and subject contract. |
| `Review.must_attest(cls, value)` | See linked implementation and subject contract. |

## [medical_assistant/nodule_exchange.py](../../medical_assistant/nodule_exchange.py)

Shared, ML-free MHCRA nodule exchange v2 validation and pixel rendering. Vendored by MHCRA with only the contracts import rewritten; CI checks equality. Hashes bind artifacts but do not authenticate producer execution or synthetic origin.

| Callable | Purpose/contract |
| --- | --- |
| `byte_digest(payload)` | See linked implementation and subject contract. |
| `ExchangeArtifact.safe_path(cls, value)` | See linked implementation and subject contract. |
| `PublicResearchSource.explicit_composite(cls, value)` | See linked implementation and subject contract. |
| `NoduleBundle.consistent(self)` | See linked implementation and subject contract. |
| `NoduleBundle.verify_research_crop(self)` | Bind a limited HU excerpt to exact original geometry and candidate coordinates. Whole-source hashes record provenance; they do not authenticate a producer. The consumer independently checks excerpt pixels/previews, not absent full scans. |
| `wire_pixels(study, hu, index, *, calipers=())` | Portable NumPy-only source/box/caliper pixels; no font-version dependency. |
| `source_pixels(bundle, artifacts)` | Bound NPY header and exact payload before allocating source HU. |
| `unique_object(pairs)` | See linked implementation and subject contract. |
| `read_exchange(payload, patient_id)` | Validate bounded ZIP without extracting paths; all source/overlay pixels checked. |

## [medical_assistant/nodule_models.py](../../medical_assistant/nodule_models.py)

Versioned immutable-by-convention records; all persisted data is revalidated.

| Callable | Purpose/contract |
| --- | --- |
| `digest(value)` | Canonical content identity; consistency check, not source authenticity. |
| `Geometry.valid_geometry(self)` | See linked implementation and subject contract. |
| `Geometry.to_lps(self, points_zyx)` | Map source voxel centers to physical LPS millimetres, including obliquity. |
| `Geometry.from_lps(self, points_lps)` | See linked implementation and subject contract. |
| `Candidate.ordered_box(self)` | See linked implementation and subject contract. |
| `Study.consistent(self)` | See linked implementation and subject contract. |
| `Caliper.length_mm(self, geometry)` | See linked implementation and subject contract. |
| `Review.literal_booleans(cls, value)` | See linked implementation and subject contract. |
| `Review.verify(self, study)` | See linked implementation and subject contract. |
| `research_report(study, review)` | Compose only approved, structured observations; no LLM or cancer inference. |

## [medical_assistant/nodule_support.py](../../medical_assistant/nodule_support.py)

Typed nodule review binding; does not change clinical facts or safety routing.

| Callable | Purpose/contract |
| --- | --- |
| `is_nodule(manifest)` | See linked implementation and subject contract. |
| `checked_nodule_review(manifest, review, *, reviewer=None)` | See linked implementation and subject contract. |
| `imaging_acceptance_digest(proposal, nodule_review=None, *, endo_review=None)` | See linked implementation and subject contract. |
| `verify_nodule_snapshot(snapshot)` | See linked implementation and subject contract. |

## [medical_assistant/nodule_ui.py](../../medical_assistant/nodule_ui.py)

Nodule source inspection and typed candidate/caliper controls; no inference.

| Callable | Purpose/contract |
| --- | --- |
| `pixels_for(manifest, path_for)` | See linked implementation and subject contract. |
| `nodule_viewer(manifest, path_for, key, *, review=None)` | See linked implementation and subject contract. |
| `candidate_controls(manifest, key)` | Return typed local choices; nothing is persisted or approved by these controls. |
| `build_nodule_review(manifest, decisions, reviewer, attested)` | See linked implementation and subject contract. |
| `preview_calipers(manifest, path_for, decisions)` | See linked implementation and subject contract. |

## [medical_assistant/ollama_client.py](../../medical_assistant/ollama_client.py)

Ollama HTTP adapter: fixed loopback, no proxies, redirects, or cloud models.

| Callable | Purpose/contract |
| --- | --- |
| `OllamaClient.__init__(self, model: str='gemma4:e2b', *, transport=None)` | See linked implementation and subject contract. |
| `OllamaClient.close(self)` | See linked implementation and subject contract. |
| `OllamaClient._post(self, path: str, body: dict)` | See linked implementation and subject contract. |
| `OllamaClient.ensure_local(self)` | See linked implementation and subject contract. |
| `OllamaClient.assess(self, system: str, user: str, *, schema: dict &#124; None=None)` | See linked implementation and subject contract. |

## [medical_assistant/reasoning_constraints.py](../../medical_assistant/reasoning_constraints.py)

Limited synthetic hypothesis selection, not general clinical reasoning. The local LLM selects from this transparent catalog. Exact record text remains untrusted quoted evidence; these constraints do not clinically validate a cause, identify emergencies, or establish that a selected source supports causation.

| Callable | Purpose/contract |
| --- | --- |
| `eligible_labels(record: PatientRecord)` | See linked implementation and subject contract. |
| `constrain_schema(schema: dict, record: PatientRecord, reference_ids: list[str])` | Constrain both narrative vocabulary and evidence before generation. |
| `validate_reasoning(assessment: Assessment, record: PatientRecord, reference_ids: set[str])` | Reject off-catalog model text even if a transport ignores the schema. |

## [medical_assistant/report.py](../../medical_assistant/report.py)

Concise source-bound summaries; detailed provenance stays in the evidence package.

| Callable | Purpose/contract |
| --- | --- |
| `digest(text: str)` | See linked implementation and subject contract. |
| `inline_text(value)` | Render untrusted data as one literal Markdown line, never active markup. Original quotations remain untouched in source storage. Presentation folds whitespace so a record cannot add headings, lists or reference definitions. Ordinary filename underscores stay readable; intraword underscores cannot open CommonMark emphasis. HTML, links, images and code delimiters are escaped. |
| `evidence_index(record, outputs, imaging=None)` | Keep every exact source excerpt and selected evidence link outside the short prose. |
| `ct_summary(imaging)` | Short inspected result; exact source/model/coverage evidence stays bound separately. |
| `endoscopy_summary(imaging)` | Keep the report focused on inspected regions rather than model metadata. |
| `summary_parts(record, outputs, imaging=None, clinician_note=None)` | Plain-text report blocks shared by Markdown and portable HTML presentation. |
| `compose(record: PatientRecord, source_file: str, outputs: dict[str, dict], evidence=None, imaging=None, clinician_note=None)` | One concise section; full exact excerpts/citations remain in report_evidence and originals. |

## [medical_assistant/report_assets.py](../../medical_assistant/report_assets.py)

Verified representative CT images and self-contained, approval-gated HTML reports.

| Callable | Purpose/contract |
| --- | --- |
| `inspection_figures(state, store)` | Render at most three representative study slices, never omit summary counts. |
| `portable_html(payload, *, auth, safety=None)` | Final download with embedded verified CT pictures; no scripts, external assets or draft export. |

## [medical_assistant/report_binding.py](../../medical_assistant/report_binding.py)

Bind approval to hidden evidence/images as well as simplified visible report text.

| Callable | Purpose/contract |
| --- | --- |
| `content_digest(state)` | Stable clinical content only; mutable workflow/review bookkeeping is excluded. |
| `verify_content_binding(state, receipt, auth, reviewer)` | See linked implementation and subject contract. |

## [medical_assistant/report_notes.py](../../medical_assistant/report_notes.py)

Authenticate report-note authorship without treating commentary as clinical facts.

| Callable | Purpose/contract |
| --- | --- |
| `verify_note(state, auth)` | See linked implementation and subject contract. |

## [medical_assistant/research_examples.py](../../medical_assistant/research_examples.py)

Read a local, bounded public-research upload kit; never downloads or approves.

| Callable | Purpose/contract |
| --- | --- |
| `_manifest(root=None)` | See linked implementation and subject contract. |
| `_read(root, name, expected, limit)` | See linked implementation and subject contract. |
| `example_bundle(modality, patient, *, root=None, index=0)` | Load only the requested modality/case; full archive verification follows at import. |
| `matching_endoscopy(raw, patient, *, root=None)` | Recognise the exact permitted demo source bytes without guessing dataset provenance. |

## [medical_assistant/runtime.py](../../medical_assistant/runtime.py)

Shared local authentication service; patient/case state stays session-scoped.

| Callable | Purpose/contract |
| --- | --- |
| `get_services()` | See linked implementation and subject contract. |

## [medical_assistant/safety.py](../../medical_assistant/safety.py)

Deterministic safety agent. No model response can modify this policy result.

| Callable | Purpose/contract |
| --- | --- |
| `SafetyAgent.__init__(self, policy_path: Path=POLICY_PATH)` | See linked implementation and subject contract. |
| `SafetyAgent.evaluate(self, record: PatientRecord, *, as_of: date &#124; None=None)` | See linked implementation and subject contract. |

## [medical_assistant/storage.py](../../medical_assistant/storage.py)

Read explicitly selected local JSON records; atomically save reviewed reports.

| Callable | Purpose/contract |
| --- | --- |
| `load_record(path: Path)` | See linked implementation and subject contract. |
| `validate_reviewed_report(payload: dict, *, auth, safety=None)` | Recheck approval, sources, note authorship and CT integrity before any final export. |
| `save_report(payload: dict, directory: Path=REPORT_DIR, *, auth=None, safety=None)` | See linked implementation and subject contract. |

## [medical_assistant/ui/clinical.py](../../medical_assistant/ui/clinical.py)

Responsive clinical UI; only explicit human actions issue review receipts.

| Callable | Purpose/contract |
| --- | --- |
| `make_review(approved, user, checked, notes, sha256)` | See linked implementation and subject contract. |
| `start_task(path, auth, patient_id, model, *, review=None, token=None)` | See linked implementation and subject contract. |
| `start_task.run(progress, budget)` | See linked implementation and subject contract. |
| `resume_task(workflow, case, review, token)` | See linked implementation and subject contract. |
| `resume_task.run(progress, budget)` | See linked implementation and subject contract. |
| `collect_task()` | Publish only a completed, in-budget result into this Streamlit session. |
| `task_progress()` | See linked implementation and subject contract. |
| `background_progress()` | Keep completion responsive when the reviewer opens a different view. |
| `generate_task(workflow, case, token)` | See linked implementation and subject contract. |
| `generate_task.run(progress, budget)` | See linked implementation and subject contract. |
| `bottom_actions(path, auth, record, model, token, user, decision)` | Safety first, then one explicit bottom-of-page generation action. |
| `failure()` | See linked implementation and subject contract. |
| `new_report_with_ct()` | See linked implementation and subject contract. |
| `report_content(state, workflow)` | Short summary and verified representative CT images, with optional readable evidence. |
| `report_panel(auth, token, user, record, *, urgent=False)` | See linked implementation and subject contract. |

## [medical_assistant/ui/components.py](../../medical_assistant/ui/components.py)

Reusable presentation components. Escape every source-derived HTML value.

| Callable | Purpose/contract |
| --- | --- |
| `safe(value)` | See linked implementation and subject contract. |
| `styles()` | See linked implementation and subject contract. |
| `sidebar_brand()` | See linked implementation and subject contract. |
| `header()` | See linked implementation and subject contract. |
| `patient_header(record, decision, *, safety_reviewed=False)` | See linked implementation and subject contract. |
| `timeline(record)` | See linked implementation and subject contract. |
| `medications(record)` | See linked implementation and subject contract. |
| `original_sources(record)` | See linked implementation and subject contract. |
| `empty(title, copy)` | See linked implementation and subject contract. |
| `next_action(state=None, *, urgent=False)` | See linked implementation and subject contract. |
| `guide(view, state=None, *, running=False, signed_in=False)` | See linked implementation and subject contract. |
| `footer()` | See linked implementation and subject contract. |

## [medical_assistant/ui/history.py](../../medical_assistant/ui/history.py)

Human-approved history import UI; source data is never guessed or overwritten.

| Callable | Purpose/contract |
| --- | --- |
| `history_ui(path, auth, token, user, record)` | See linked implementation and subject contract. |
| `history_ui.replace_proposal(result)` | See linked implementation and subject contract. |

## [medical_assistant/ui/navigation.py](../../medical_assistant/ui/navigation.py)

Patient-scoped UI lifecycle and fixed, source-independent navigation targets.

| Callable | Purpose/contract |
| --- | --- |
| `reset_report_context(state)` | Release only the current draft context; retain uploads and accepted studies. Persisted reports and workflow checkpoints are never edited or approved here. A subsequent draft must pass the safety workflow again. |
| `clear_patient(state, *, preserve_login=True, preserve_patient=True)` | Cancel abandoned work and drop every patient-specific widget/proposal. |
| `ensure_patient(state, patient)` | Fail closed before rendering/collecting a mismatched patient snapshot. |
| `destination(target)` | See linked implementation and subject contract. |
| `go_to(target, *, state=None)` | See linked implementation and subject contract. |
| `anchor(target)` | See linked implementation and subject contract. |
| `focus_pending()` | Scroll only to fixed app anchors; never interpolate record/model text into JS. |

## [medical_assistant/workflow.py](../../medical_assistant/workflow.py)

Clinical-review graph with deterministic safety holds and authenticated review.

| Callable | Purpose/contract |
| --- | --- |
| `MedicalHistoryOrchestrator.__init__(self, inference: Inference, evidence_collection=None, *, auth=None, safety=None)` | See linked implementation and subject contract. |
| `MedicalHistoryOrchestrator._initial_safety(self, state)` | See linked implementation and subject contract. |
| `MedicalHistoryOrchestrator._checked_review(self, state, response, action)` | See linked implementation and subject contract. |
| `MedicalHistoryOrchestrator._safety_review(self, state)` | See linked implementation and subject contract. |
| `MedicalHistoryOrchestrator._retrieve_evidence(self, state)` | See linked implementation and subject contract. |
| `MedicalHistoryOrchestrator._reasoning(self, state)` | See linked implementation and subject contract. |
| `MedicalHistoryOrchestrator._verify_safety_ack(self, state)` | See linked implementation and subject contract. |
| `MedicalHistoryOrchestrator._final_safety(self, state)` | See linked implementation and subject contract. |
| `MedicalHistoryOrchestrator._verify_imaging(self, state)` | See linked implementation and subject contract. |
| `MedicalHistoryOrchestrator._compose(self, state)` | See linked implementation and subject contract. |
| `MedicalHistoryOrchestrator._verify_report(self, state)` | See linked implementation and subject contract. |
| `MedicalHistoryOrchestrator._review(self, state)` | See linked implementation and subject contract. |
| `MedicalHistoryOrchestrator._complete(self, state)` | See linked implementation and subject contract. |
| `MedicalHistoryOrchestrator.config(case_id)` | See linked implementation and subject contract. |
| `MedicalHistoryOrchestrator.start(self, record: PatientRecord, source_file: str, *, imaging=None, safety_only=False)` | See linked implementation and subject contract. |
| `MedicalHistoryOrchestrator.start_patient(self, patient_id, path, *, safety_only=False)` | See linked implementation and subject contract. |
| `MedicalHistoryOrchestrator.state(self, case_id)` | See linked implementation and subject contract. |
| `MedicalHistoryOrchestrator._response(self, case_id, review, token, action)` | See linked implementation and subject contract. |
| `MedicalHistoryOrchestrator.acknowledge_safety(self, case_id, review: Review, token=None, *, safety_only=False)` | See linked implementation and subject contract. |
| `MedicalHistoryOrchestrator.ready_for_analysis(self, case_id, token=None)` | Authenticate and recheck the exact prepared snapshot before generation. |
| `MedicalHistoryOrchestrator.continue_analysis(self, case_id, token=None)` | See linked implementation and subject contract. |
| `MedicalHistoryOrchestrator.revise(self, case_id, draft: str, token=None)` | See linked implementation and subject contract. |
| `MedicalHistoryOrchestrator.prepare_report_note(self, case_id, text, token=None)` | Preview a signed reviewer comment; any changed report requires fresh approval. |
| `MedicalHistoryOrchestrator.review(self, case_id, review: Review, token=None)` | See linked implementation and subject contract. |
| `MedicalHistoryOrchestrator.export(self, case_id)` | See linked implementation and subject contract. |

## [scripts/check_docs.py](../../scripts/check_docs.py)

Validate repository Markdown file links without contacting external websites.

| Callable | Purpose/contract |
| --- | --- |
| `main()` | See linked implementation and subject contract. |

## [scripts/prepare_research_demo.py](../../scripts/prepare_research_demo.py)

Build local upload examples from separately obtained, permitted research datasets. No downloads, training, clinical approval or linking of real patient histories. The real CT workspace must already have been produced by the CT companion.

| Callable | Purpose/contract |
| --- | --- |
| `sha(path)` | See linked implementation and subject contract. |
| `main()` | See linked implementation and subject contract. |
| `main.run(root, *args)` | See linked implementation and subject contract. |

## [scripts/smoke_endoscopy.py](../../scripts/smoke_endoscopy.py)

Actual bounded synthetic producer/receiver smoke; no imaging or final approvals.

| Callable | Purpose/contract |
| --- | --- |
| `main()` | See linked implementation and subject contract. |

## [scripts/smoke_imaging.py](../../scripts/smoke_imaging.py)

Real local CT worker and receiver; no human or final approval is simulated.

| Callable | Purpose/contract |
| --- | --- |
| `main()` | See linked implementation and subject contract. |

## [scripts/smoke_local.py](../../scripts/smoke_local.py)

Real local model smoke: verify an uncertainty hold and a separate fully synthetic ordinary-eligible fixture. Never approve a safety hold or final clinical report.

| Callable | Purpose/contract |
| --- | --- |
| `main()` | See linked implementation and subject contract. |

## [scripts/smoke_research_pair.py](../../scripts/smoke_research_pair.py)

Actual local image-pair/report smoke with SCRIPTED reviews in a TEMPORARY DB. The approvals below test plumbing only. They are never clinical review and never modify the demo application's database. No image pixels are sent to the LLM.

| Callable | Purpose/contract |
| --- | --- |
| `main()` | See linked implementation and subject contract. |

## [scripts/sync_ct_contracts.py](../../scripts/sync_ct_contracts.py)

Vendor/check ML-free CT contracts; no CT model, torch or database tools imported.

| Callable | Purpose/contract |
| --- | --- |
| `sync(ct_root, *, write=False)` | See linked implementation and subject contract. |
| `main()` | See linked implementation and subject contract. |

## [scripts/sync_endo_contracts.py](../../scripts/sync_endo_contracts.py)

Check exact ML-free endoscopy contract/worker equality with the companion.

| Callable | Purpose/contract |
| --- | --- |
| `main()` | See linked implementation and subject contract. |

## [medical_assistant/imaging_actions.py](../../medical_assistant/imaging_actions.py)

Authenticated image input routing, independent of Streamlit rendering. ZIPs contain existing predictions: Analyze validates and opens them for review. Only a raw, permitted endoscopy image launches inference on uploaded pixels. Nothing in this module accepts a study or approves a clinical report.

| Callable | Purpose/contract |
| --- | --- |
| `job_pending(job)` | A collected result is represented by its proposal, not a stale job handle. |
| `failure_detail(job)` | Return the bounded worker exception, without a traceback or full log dump. |
| `blocker(state)` | See linked implementation and subject contract. |
| `analyze(state, store, auth, token, patient, modality, *, upload=None, mode='auto')` | Validate input before retiring a frozen report; never silently use a demo. ``upload`` is (filename, bytes). Mode applies only when there is no upload. An uploaded ZIP always opens its included results, regardless of example mode. Failed input validation leaves the existing report and all approvals intact. |
| `collect(state, store, modality, patient)` | Publish one completed result without overwriting a pending/frozen review. |


## [medical_assistant/ui/imaging_actions.py](../../medical_assistant/ui/imaging_actions.py)

Reusable Upload / Analyze controls and visible local-worker errors.

| Callable | Purpose/contract |
| --- | --- |
| `image_actions(modality, store, auth, token, record)` | See linked implementation and subject contract. |
| `image_progress(job, prefix)` | See linked implementation and subject contract. |


## [scripts/smoke_uploads.py](../../scripts/smoke_uploads.py)

Exercise real local Upload/Analyze widgets in a disposable database. Uses prepared research pixels and actual local polyp inference; no scripted model, no LLM call, no image/safety/report approval, and no application database changes. The local research kit and installed companion are prerequisites, not downloads.

| Callable | Purpose/contract |
| --- | --- |
| `main()` | See linked implementation and subject contract. |

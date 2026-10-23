# Code and folder reference

[Overview](../README.md) · [Architecture](ARCHITECTURE.md) · [Imaging contract](IMAGING.md)

## Modules and boundaries

| Module/group | Responsibility |
| --- | --- |
| app.py, runtime.py | Streamlit record selection, session services, idempotent bootstrap and review UI |
| models.py, grounding.py | Strict source/fact/assessment contracts; original JSON versus extracted values |
| database.py, storage.py | Parameterized transactional SQLite, immutable originals, guarded report persistence |
| history.py, history_import.py | Deterministic chronology/orders, proposed source imports and authenticated append |
| agents.py, reasoning_constraints.py | Structured inference, exact excerpts, bounded synthetic hypotheses/questions |
| evidence.py, data/evidence | Explicitly approved, hash-verified local text references; empty by default |
| safety.py, config/safety_policy.json | Versioned Python urgent/uncertain routing and immutable-input bindings |
| workflow.py | Sequential LangGraph, pre-reasoning safety interrupt, final review and integrity-checked export |
| auth.py | Salted password hashes, expiring local sessions, content-bound receipts and audit |
| ollama_client.py | Loopback-only local model validation and bounded JSON generation; no tools |
| report.py | Seven deterministic sections, escaped source citations and research appendix |
| ct_worker.py | Own CT interpreter, explicit fixture/pretrained/legacy mode, watchdog and cancellation |
| imaging_contract.py | Dispatch nodule-v2 versus legacy mask contract; bounded independent validation |
| imaging.py | Pending proposals, immutable original ZIP/artifacts, transactional authenticated acceptance |
| imaging_ui.py, nodule_ui.py | Local source/overlay viewing, typed candidate decisions and caliper preview |
| nodule_models.py | Vendored CT geometry/source/candidate/review contracts and canonical research report |
| nodule_exchange.py | Vendored bounded v2 wire contract, source array checks and portable renderer |
| nodule_support.py | Authenticated reviewer matching and bundle-plus-decisions acceptance digest |

## Review-sensitive call paths

- `HistoryManagement.prepare → approve`: validate source JSON, compare immutable IDs,
  bind the proposal hash, require authenticated attestation, then append transactionally.
- `ImagingStore.prepare → approve`: independently validate every original byte;
  for nodules, `checked_nodule_review` verifies a fully resolved review and matching
  authenticated actor, then `imaging_acceptance_digest` binds exact choices/calipers.
- `ImagingStore.verify → _verify_directory → validate_bundle`: re-read immutable
  originals and extracted artifacts; `verify_nodule_snapshot` also checks the
  accepted review/digest. Called again by report completion/export/save.
- `pixels_for → source_pixels → wire_pixels`: revalidate bounded source HU and
  draw reviewer-selected physical in-plane calipers. UI previews never persist approval.
- `MedicalHistoryOrchestrator._initial_safety → _safety_review`: urgent cannot
  continue; uncertainty needs a matching authenticated acknowledgment before reasoning.
- `_reasoning → _final_safety → _compose → _review → _complete`: constrained
  source-grounded inference, recheck safety, add accepted imaging in Python, human
  final approval, guarded completion. `export` checks everything again.
- `export_synthetic_exchange` in CT defaults to requiring local CT review. Only
  its dedicated MHCRA bridge requests pending export; neither path approves MHCRA.

## Function and subfunction inventory

The inventory below is generated from the current Python AST. Signatures show
inputs; source docstrings describe behavior where present. Class validators and
internal graph/UI helpers are listed as well. Detailed invariants are in the
subject guides above and the linked implementation, rather than duplicated here.

### [app.py](../app.py)

MHCRA AI: loopback-only synthetic history management and clinical review.

| Callable | Contract/purpose |
| --- | --- |
| `account_ui(auth)` | Implementation and invariants in linked source/subject guide. |
| `make_review(approved, user, checked, notes, sha256)` | Implementation and invariants in linked source/subject guide. |
| `history_ui(path, auth, token, user, record)` | Implementation and invariants in linked source/subject guide. |
| `history_ui.replace_proposal(result)` | Implementation and invariants in linked source/subject guide. |
| `clinical_ui(path, auth, token, user, record, model, *, urgent=False)` | Implementation and invariants in linked source/subject guide. |
| `main()` | Implementation and invariants in linked source/subject guide. |

### [medical_assistant/agents.py](../medical_assistant/agents.py)

Constrained specialist prompt templates and local inference validation.

| Callable | Contract/purpose |
| --- | --- |
| `Inference.assess(self, system: str, user: str, *, schema: dict &#124; None=None)` | Implementation and invariants in linked source/subject guide. |
| `SpecialistAgent.__init__(self, role: str, inference: Inference)` | Implementation and invariants in linked source/subject guide. |
| `SpecialistAgent.run(self, record: PatientRecord, earlier: dict[str, dict], evidence=None)` | Implementation and invariants in linked source/subject guide. |

### [medical_assistant/auth.py](../medical_assistant/auth.py)

Local password authentication and short-lived in-process clinician sessions.

| Callable | Contract/purpose |
| --- | --- |
| `LocalAuth.__init__(self, path: Path=DATABASE_PATH)` | Implementation and invariants in linked source/subject guide. |
| `LocalAuth.has_users(self)` | Implementation and invariants in linked source/subject guide. |
| `LocalAuth.create_clinician(self, username: str, password: str)` | Implementation and invariants in linked source/subject guide. |
| `LocalAuth.login(self, username: str, password: str)` | Implementation and invariants in linked source/subject guide. |
| `LocalAuth.require(self, token)` | Implementation and invariants in linked source/subject guide. |
| `LocalAuth.logout(self, token)` | Implementation and invariants in linked source/subject guide. |
| `LocalAuth.audit(self, action, patient_id, token, payload)` | Implementation and invariants in linked source/subject guide. |
| `LocalAuth.receipt(self, token, action, content_sha256)` | Implementation and invariants in linked source/subject guide. |
| `LocalAuth.verify_receipt(self, receipt, action, content_sha256)` | Implementation and invariants in linked source/subject guide. |
| `LocalAuth.record_receipt(self, receipt, patient_id, payload)` | Implementation and invariants in linked source/subject guide. |

### [medical_assistant/ct_worker.py](../medical_assistant/ct_worker.py)

Bounded local CT subprocesses. No shell, uploads, downloads or model tools.

| Callable | Contract/purpose |
| --- | --- |
| `configured_ct_root()` | Implementation and invariants in linked source/subject guide. |
| `configured_ct_model(root=None)` | Implementation and invariants in linked source/subject guide. |
| `LocalCTJob.__init__(self, patient_id, *, root=None, jobs=None, timeout=180, mode='legacy', model_dir=None, device='cpu')` | Implementation and invariants in linked source/subject guide. |
| `LocalCTJob.bundle_path(self)` | Implementation and invariants in linked source/subject guide. |
| `LocalCTJob._watch(self, timeout)` | Implementation and invariants in linked source/subject guide. |
| `LocalCTJob.cancel(self, *, timed_out=False)` | Implementation and invariants in linked source/subject guide. |
| `LocalCTJob.status(self)` | Implementation and invariants in linked source/subject guide. |

### [medical_assistant/database.py](../medical_assistant/database.py)

Transactional SQLite storage. Models have no access to these write functions.

| Callable | Contract/purpose |
| --- | --- |
| `connect(path: Path)` | Implementation and invariants in linked source/subject guide. |
| `initialize(path: Path=DATABASE_PATH)` | Implementation and invariants in linked source/subject guide. |
| `attach_original(record: PatientRecord, filename: str, raw: str)` | Convert legacy synthetic JSON to immutable source + separately stored facts. |
| `write_synthetic(record: PatientRecord, path: Path, *, actor: str, action: str, approval=None)` | Internal atomic append; existing IDs are immutable and exact retries are no-ops. |
| `get_history(patient_id: str, path: Path=DATABASE_PATH)` | Implementation and invariants in linked source/subject guide. |
| `list_patients(path: Path=DATABASE_PATH)` | Implementation and invariants in linked source/subject guide. |
| `seed(path: Path=DATABASE_PATH)` | Explicit built-in synthetic fixture creation; never imports arbitrary files. |

### [medical_assistant/evidence.py](../medical_assistant/evidence.py)

Retrieve only explicitly approved, hash-verified files in a local collection.

| Callable | Contract/purpose |
| --- | --- |
| `LocalEvidenceCollection.__init__(self, directory: Path)` | Implementation and invariants in linked source/subject guide. |
| `LocalEvidenceCollection.retrieve(self, query: str)` | Implementation and invariants in linked source/subject guide. |
| `LocalEvidenceCollection.retrieve.local_search(query)` | Implementation and invariants in linked source/subject guide. |

### [medical_assistant/grounding.py](../medical_assistant/grounding.py)

Source grounding for JSON medical imports; no semantic facts are invented.

| Callable | Contract/purpose |
| --- | --- |
| `validate_record_grounding(record: PatientRecord)` | Implementation and invariants in linked source/subject guide. |

### [medical_assistant/history.py](../medical_assistant/history.py)

Extractive history and medication agents for typed synthetic source records.

| Callable | Contract/purpose |
| --- | --- |
| `chronology(entry)` | Implementation and invariants in linked source/subject guide. |
| `MedicalHistoryAgent.run(self, record: PatientRecord)` | Implementation and invariants in linked source/subject guide. |
| `MedicalHistoryAgent.run.extract(record)` | Implementation and invariants in linked source/subject guide. |
| `MedicationAgent.run(self, record: PatientRecord)` | Implementation and invariants in linked source/subject guide. |
| `MedicationAgent.run.extract(record)` | Implementation and invariants in linked source/subject guide. |

### [medical_assistant/history_import.py](../medical_assistant/history_import.py)

Separate history-management workflow: validate → extract → approve → append.

| Callable | Contract/purpose |
| --- | --- |
| `HistoryManagement.__init__(self, path, *, auth=None)` | Implementation and invariants in linked source/subject guide. |
| `HistoryManagement.prepare(self, raw: str, filename: str)` | Implementation and invariants in linked source/subject guide. |
| `HistoryManagement.approve(self, proposal_id, review: Review, token=None)` | Implementation and invariants in linked source/subject guide. |

### [medical_assistant/imaging.py](../medical_assistant/imaging.py)

Human-reviewed synthetic imaging storage, separate from clinical source facts.

| Callable | Contract/purpose |
| --- | --- |
| `ImagingStore.__init__(self, path, auth=None)` | Implementation and invariants in linked source/subject guide. |
| `ImagingStore.prepare(self, payload, patient_id, *, study_id=None)` | Implementation and invariants in linked source/subject guide. |
| `ImagingStore.discard(self, key)` | Implementation and invariants in linked source/subject guide. |
| `ImagingStore._directory(self, patient_id, study_id)` | Implementation and invariants in linked source/subject guide. |
| `ImagingStore._verify_directory(directory, snapshot)` | Implementation and invariants in linked source/subject guide. |
| `ImagingStore.approve(self, key, review, token=None, *, nodule_review=None)` | Implementation and invariants in linked source/subject guide. |
| `ImagingStore.snapshots(self, patient_id)` | Implementation and invariants in linked source/subject guide. |
| `ImagingStore.verify(self, snapshots)` | Implementation and invariants in linked source/subject guide. |
| `ImagingStore.preview_path(self, snapshot, role, index)` | Implementation and invariants in linked source/subject guide. |

### [medical_assistant/imaging_contract.py](../medical_assistant/imaging_contract.py)

Bounded synthetic imaging exchange. Model artifacts are never clinical facts.

| Callable | Contract/purpose |
| --- | --- |
| `Artifact.local_relative(cls, value)` | Implementation and invariants in linked source/subject guide. |
| `Geometry.physical(self)` | Implementation and invariants in linked source/subject guide. |
| `ImagingBundle.boolean_only(cls, value)` | Implementation and invariants in linked source/subject guide. |
| `ImagingBundle.consistent(self)` | Implementation and invariants in linked source/subject guide. |
| `file_digest(payload)` | Implementation and invariants in linked source/subject guide. |
| `validate_bundle(payload: bytes, patient_id: str)` | Read bounded bytes without extracting arbitrary archive paths or pickle. |
| `_verify_pixels(bundle, artifacts)` | Implementation and invariants in linked source/subject guide. |

### [medical_assistant/imaging_ui.py](../medical_assistant/imaging_ui.py)

Imaging inspection UI; acceptance is separate from final clinical approval.

| Callable | Contract/purpose |
| --- | --- |
| `_viewer(manifest, path_for, key, *, review=None)` | Implementation and invariants in linked source/subject guide. |
| `imaging_ui(path, auth, token, user, record, *, locked=False)` | Implementation and invariants in linked source/subject guide. |
| `imaging_ui.prepare(payload, *, study_id=None)` | Implementation and invariants in linked source/subject guide. |

### [medical_assistant/models.py](../medical_assistant/models.py)

Validated record, specialist output, and human review contracts.

| Callable | Contract/purpose |
| --- | --- |
| `SourceDocument.valid_digest(self)` | Implementation and invariants in linked source/subject guide. |
| `PatientRecord.unique_ids(self)` | Implementation and invariants in linked source/subject guide. |
| `Explanation.no_confirmed_diagnosis(cls, value)` | Implementation and invariants in linked source/subject guide. |
| `Assessment.validate_sources(self, record: PatientRecord)` | Implementation and invariants in linked source/subject guide. |
| `Assessment.validate_sources.check(ids, source_type=None)` | Implementation and invariants in linked source/subject guide. |
| `Review.must_attest(cls, value)` | Implementation and invariants in linked source/subject guide. |

### [medical_assistant/nodule_exchange.py](../medical_assistant/nodule_exchange.py)

Shared, ML-free MHCRA nodule exchange v2 validation and pixel rendering.

| Callable | Contract/purpose |
| --- | --- |
| `byte_digest(payload)` | Implementation and invariants in linked source/subject guide. |
| `ExchangeArtifact.safe_path(cls, value)` | Implementation and invariants in linked source/subject guide. |
| `NoduleBundle.literal_synthetic(cls, value)` | Implementation and invariants in linked source/subject guide. |
| `NoduleBundle.consistent(self)` | Implementation and invariants in linked source/subject guide. |
| `wire_pixels(study, hu, index, *, calipers=())` | Portable NumPy-only source/box/caliper pixels; no font-version dependency. |
| `source_pixels(bundle, artifacts)` | Bound NPY header and exact payload before allocating source HU. |
| `unique_object(pairs)` | Implementation and invariants in linked source/subject guide. |
| `read_exchange(payload, patient_id)` | Validate bounded ZIP without extracting paths; all source/overlay pixels checked. |

### [medical_assistant/nodule_models.py](../medical_assistant/nodule_models.py)

Versioned immutable-by-convention records; all persisted data is revalidated.

| Callable | Contract/purpose |
| --- | --- |
| `digest(value)` | Canonical content identity; consistency check, not source authenticity. |
| `Geometry.valid_geometry(self)` | Implementation and invariants in linked source/subject guide. |
| `Geometry.to_lps(self, points_zyx)` | Map source voxel centers to physical LPS millimetres, including obliquity. |
| `Geometry.from_lps(self, points_lps)` | Implementation and invariants in linked source/subject guide. |
| `Candidate.ordered_box(self)` | Implementation and invariants in linked source/subject guide. |
| `Study.consistent(self)` | Implementation and invariants in linked source/subject guide. |
| `Caliper.length_mm(self, geometry)` | Implementation and invariants in linked source/subject guide. |
| `Review.literal_booleans(cls, value)` | Implementation and invariants in linked source/subject guide. |
| `Review.verify(self, study)` | Implementation and invariants in linked source/subject guide. |
| `research_report(study, review)` | Compose only approved, structured observations; no LLM or cancer inference. |

### [medical_assistant/nodule_support.py](../medical_assistant/nodule_support.py)

Typed nodule review binding; does not change clinical facts or safety routing.

| Callable | Contract/purpose |
| --- | --- |
| `is_nodule(manifest)` | Implementation and invariants in linked source/subject guide. |
| `checked_nodule_review(manifest, review, *, reviewer=None)` | Implementation and invariants in linked source/subject guide. |
| `imaging_acceptance_digest(proposal, nodule_review=None)` | Implementation and invariants in linked source/subject guide. |
| `verify_nodule_snapshot(snapshot)` | Implementation and invariants in linked source/subject guide. |

### [medical_assistant/nodule_ui.py](../medical_assistant/nodule_ui.py)

Nodule source inspection and typed candidate/caliper controls; no inference.

| Callable | Contract/purpose |
| --- | --- |
| `pixels_for(manifest, path_for)` | Implementation and invariants in linked source/subject guide. |
| `nodule_viewer(manifest, path_for, key, *, review=None)` | Implementation and invariants in linked source/subject guide. |
| `candidate_controls(manifest, key)` | Return typed local choices; nothing is persisted or approved by these controls. |
| `build_nodule_review(manifest, decisions, reviewer, attested)` | Implementation and invariants in linked source/subject guide. |
| `preview_calipers(manifest, path_for, decisions)` | Implementation and invariants in linked source/subject guide. |

### [medical_assistant/ollama_client.py](../medical_assistant/ollama_client.py)

Ollama HTTP adapter: fixed loopback, no proxies, redirects, or cloud models.

| Callable | Contract/purpose |
| --- | --- |
| `OllamaClient.__init__(self, model: str='gemma4:e2b', *, transport=None)` | Implementation and invariants in linked source/subject guide. |
| `OllamaClient.close(self)` | Implementation and invariants in linked source/subject guide. |
| `OllamaClient._post(self, path: str, body: dict)` | Implementation and invariants in linked source/subject guide. |
| `OllamaClient.ensure_local(self)` | Implementation and invariants in linked source/subject guide. |
| `OllamaClient.assess(self, system: str, user: str, *, schema: dict &#124; None=None)` | Implementation and invariants in linked source/subject guide. |

### [medical_assistant/reasoning_constraints.py](../medical_assistant/reasoning_constraints.py)

Limited synthetic hypothesis selection, not general clinical reasoning.

| Callable | Contract/purpose |
| --- | --- |
| `eligible_labels(record: PatientRecord)` | Implementation and invariants in linked source/subject guide. |
| `constrain_schema(schema: dict, record: PatientRecord, reference_ids: list[str])` | Constrain both narrative vocabulary and evidence before generation. |
| `validate_reasoning(assessment: Assessment, record: PatientRecord, reference_ids: set[str])` | Reject off-catalog model text even if a transport ignores the schema. |

### [medical_assistant/report.py](../medical_assistant/report.py)

Deterministic seven-section composition; citations never come from model text.

| Callable | Contract/purpose |
| --- | --- |
| `digest(text: str)` | Implementation and invariants in linked source/subject guide. |
| `inline_text(value)` | Render untrusted data as one literal Markdown line, never active markup. |
| `compose(record: PatientRecord, source_file: str, outputs: dict[str, dict], evidence=None, imaging=None)` | Implementation and invariants in linked source/subject guide. |
| `compose.cite(ids)` | Implementation and invariants in linked source/subject guide. |
| `compose.claim(item)` | Implementation and invariants in linked source/subject guide. |

### [medical_assistant/runtime.py](../medical_assistant/runtime.py)

Shared local authentication service; patient/case state stays session-scoped.

| Callable | Contract/purpose |
| --- | --- |
| `get_services()` | Implementation and invariants in linked source/subject guide. |

### [medical_assistant/safety.py](../medical_assistant/safety.py)

Deterministic safety agent. No model response can modify this policy result.

| Callable | Contract/purpose |
| --- | --- |
| `SafetyAgent.__init__(self, policy_path: Path=POLICY_PATH)` | Implementation and invariants in linked source/subject guide. |
| `SafetyAgent.evaluate(self, record: PatientRecord, *, as_of: date &#124; None=None)` | Implementation and invariants in linked source/subject guide. |

### [medical_assistant/storage.py](../medical_assistant/storage.py)

Read explicitly selected local JSON records; atomically save reviewed reports.

| Callable | Contract/purpose |
| --- | --- |
| `load_record(path: Path)` | Implementation and invariants in linked source/subject guide. |
| `save_report(payload: dict, directory: Path=REPORT_DIR, *, auth=None, safety=None)` | Implementation and invariants in linked source/subject guide. |

### [medical_assistant/workflow.py](../medical_assistant/workflow.py)

Clinical-review graph with deterministic safety holds and authenticated review.

| Callable | Contract/purpose |
| --- | --- |
| `MedicalHistoryOrchestrator.__init__(self, inference: Inference, evidence_collection=None, *, auth=None, safety=None)` | Implementation and invariants in linked source/subject guide. |
| `MedicalHistoryOrchestrator._initial_safety(self, state)` | Implementation and invariants in linked source/subject guide. |
| `MedicalHistoryOrchestrator._checked_review(self, state, response, action)` | Implementation and invariants in linked source/subject guide. |
| `MedicalHistoryOrchestrator._safety_review(self, state)` | Implementation and invariants in linked source/subject guide. |
| `MedicalHistoryOrchestrator._retrieve_evidence(self, state)` | Implementation and invariants in linked source/subject guide. |
| `MedicalHistoryOrchestrator._reasoning(self, state)` | Implementation and invariants in linked source/subject guide. |
| `MedicalHistoryOrchestrator._verify_safety_ack(self, state)` | Implementation and invariants in linked source/subject guide. |
| `MedicalHistoryOrchestrator._final_safety(self, state)` | Implementation and invariants in linked source/subject guide. |
| `MedicalHistoryOrchestrator._verify_imaging(self, state)` | Implementation and invariants in linked source/subject guide. |
| `MedicalHistoryOrchestrator._compose(self, state)` | Implementation and invariants in linked source/subject guide. |
| `MedicalHistoryOrchestrator._review(self, state)` | Implementation and invariants in linked source/subject guide. |
| `MedicalHistoryOrchestrator._complete(self, state)` | Implementation and invariants in linked source/subject guide. |
| `MedicalHistoryOrchestrator.config(case_id)` | Implementation and invariants in linked source/subject guide. |
| `MedicalHistoryOrchestrator.start(self, record: PatientRecord, source_file: str, *, imaging=None)` | Implementation and invariants in linked source/subject guide. |
| `MedicalHistoryOrchestrator.start_patient(self, patient_id, path)` | Implementation and invariants in linked source/subject guide. |
| `MedicalHistoryOrchestrator.state(self, case_id)` | Implementation and invariants in linked source/subject guide. |
| `MedicalHistoryOrchestrator._response(self, case_id, review, token, action)` | Implementation and invariants in linked source/subject guide. |
| `MedicalHistoryOrchestrator.acknowledge_safety(self, case_id, review: Review, token=None)` | Implementation and invariants in linked source/subject guide. |
| `MedicalHistoryOrchestrator.revise(self, case_id, draft: str, token=None)` | Implementation and invariants in linked source/subject guide. |
| `MedicalHistoryOrchestrator.review(self, case_id, review: Review, token=None)` | Implementation and invariants in linked source/subject guide. |
| `MedicalHistoryOrchestrator.export(self, case_id)` | Implementation and invariants in linked source/subject guide. |

### [scripts/check_docs.py](../scripts/check_docs.py)

Validate repository Markdown file links without contacting external websites.

| Callable | Contract/purpose |
| --- | --- |
| `main()` | Implementation and invariants in linked source/subject guide. |

### [scripts/smoke_imaging.py](../scripts/smoke_imaging.py)

Real local CT worker and receiver; no human or final approval is simulated.

| Callable | Contract/purpose |
| --- | --- |
| `main()` | Implementation and invariants in linked source/subject guide. |

### [scripts/smoke_local.py](../scripts/smoke_local.py)

Real local model smoke: verify an uncertainty hold and a separate fully synthetic

| Callable | Contract/purpose |
| --- | --- |
| `main()` | Implementation and invariants in linked source/subject guide. |

### [scripts/sync_ct_contracts.py](../scripts/sync_ct_contracts.py)

Vendor/check ML-free CT contracts; no CT model, torch or database tools imported.

| Callable | Contract/purpose |
| --- | --- |
| `sync(ct_root, *, write=False)` | Implementation and invariants in linked source/subject guide. |
| `main()` | Implementation and invariants in linked source/subject guide. |

## Folders

| Folder | Contents and persistence |
| --- | --- |
| medical_assistant | Runtime schemas, services, specialists, policy adapter, UI helpers and graph |
| config | Versioned local safety policy; model cannot edit it |
| data/patients | Deliberately fictional JSON fixtures |
| data/evidence | Approved local reference manifest and instructions; empty initial collection |
| data/imaging | Ignored job/pending/original HU and preview artifacts; not committed |
| data/reports | Ignored reviewed report exports; tracked placeholder only |
| docs, docs/images | Concise subject guides, generated/synthetic figures and editable flow source |
| scripts | Local model/worker smokes, shared contract synchronization and documentation link checks |
| tests | Temporary SQLite, scripted model/reviewer, UI and adversarial regressions |
| .github/workflows | Python 3.10/3.12 offline tests and commit-pinned CT integration |
| .streamlit | Loopback binding and disabled usage telemetry |
| .venv | Existing local runtime; ignored, never distributed |

[Exact tracked-file inventory](FILE_INVENTORY.md) · [Actual test outcomes](../EVALUATION.md).

# Source API and subfunction reference

[Module guide](../CODE_REFERENCE.md) · [Root overview](../../README.md)

Generated from maintained Python source with `scripts/generate_api_docs.py`. This is a navigation/reference index; subject guides define operation and research boundaries. It imports no application, model or clinical data. Source links include exact lines; direct calls are static names, not a runtime trace.

## [app.py](../../app.py)

LOVISA local workspace: reusable UI, bounded jobs and human review.

#### [account_ui](../../app.py#L30)

`account_ui(auth)`

Static calls (including nested helper bodies): `st.session_state.get`, `st.sidebar.expander`, `auth.require`, `st.sidebar.caption`, `st.sidebar.success`, `st.sidebar.button`, `auth.has_users`, `st.caption`, `st.form`, `st.text_input`, `st.form_submit_button`, `auth.logout`, `clear_private_state`, `st.rerun` (additional calls in source).

#### [clear_private_state](../../app.py#L62)

`clear_private_state()`

Signing out hides every case and prevents background results reappearing.

Static calls (including nested helper bodies): `clear_patient`, `st.session_state.clear`.

#### [switch_patient](../../app.py#L68)

`switch_patient()`

Static calls (including nested helper bodies): `clear_patient`.

#### [reset_case](../../app.py#L72)

`reset_case()`

Static calls (including nested helper bodies): `reset_report_context`.

#### [main](../../app.py#L78)

`main()`

Static calls (including nested helper bodies): `st.set_page_config`, `ui.styles`, `get_services`, `account_ui`, `ui.header`, `list_patients`, `anchor`, `st.selectbox`, `ensure_patient`, `collect_task`, `st.session_state.get`, `st.sidebar.button`, `st.sidebar.caption`, `ui.sidebar_brand` (additional calls in source).

## [medical_assistant/__init__.py](../../medical_assistant/__init__.py)

Local-only educational prototype. No tracing or remote inference.

## [medical_assistant/agents.py](../../medical_assistant/agents.py)

Constrained specialist prompt templates and local inference validation.

The clinical graph uses this wrapper for reasoning only. History, medication
and safety roles run through dedicated deterministic Python components.

### [Inference](../../medical_assistant/agents.py#L60)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `model` | `str` | `required / supplied by caller` |

#### [Inference.assess](../../medical_assistant/agents.py#L63)

`assess(self, system: str, user: str, *, schema: dict \| None=None) → Assessment`

### [SpecialistAgent](../../medical_assistant/agents.py#L68)

Class contract is defined by the fields and methods below.

#### [SpecialistAgent.__init__](../../medical_assistant/agents.py#L69)

`__init__(self, role: str, inference: Inference)`

#### [SpecialistAgent.run](../../medical_assistant/agents.py#L73)

`run(self, record: PatientRecord, earlier: dict[str, dict], evidence=None) → dict`

Static calls (including nested helper bodies): `json.dumps`, `Assessment.model_json_schema`, `any`, `assessment.model_dump`, `constrain_schema`, `validate_reasoning`, `ValueError`, `earlier['safety'].get`, `record.model_dump`, `sorted`, `self.inference.assess`, `getattr`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

## [medical_assistant/auth.py](../../medical_assistant/auth.py)

Local password authentication and short-lived in-process clinician sessions.

### [LocalAuth](../../medical_assistant/auth.py#L14)

Class contract is defined by the fields and methods below.

#### [LocalAuth.__init__](../../medical_assistant/auth.py#L15)

`__init__(self, path: Path=DATABASE_PATH)`

Static calls (including nested helper bodies): `initialize`, `secrets.token_bytes`, `connect`, `db.execute`.

#### [LocalAuth.has_users](../../medical_assistant/auth.py#L25)

`has_users(self)`

Static calls (including nested helper bodies): `connect`, `bool`, `db.execute('SELECT COUNT(*) FROM clinicians').fetchone`, `db.execute`.

#### [LocalAuth.create_clinician](../../medical_assistant/auth.py#L29)

`create_clinician(self, username: str, password: str, *, local_demo=False)`

Static calls (including nested helper bodies): `secrets.token_hex`, `ValueError`, `connect`, `db.execute`, `re.fullmatch`, `len`, `hashlib.pbkdf2_hmac`, `password.encode`, `bytes.fromhex`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [LocalAuth.login](../../medical_assistant/auth.py#L47)

`login(self, username: str, password: str)`

Static calls (including nested helper bodies): `secrets.token_urlsafe`, `connect`, `PermissionError`, `hashlib.pbkdf2_hmac`, `hmac.compare_digest`, `time.monotonic`, `db.execute`, `password.encode`, `bytes.fromhex`.

Explicit raised conditions: `PermissionError`. See source for triggers; called validators may raise additional exceptions.

#### [LocalAuth.require](../../medical_assistant/auth.py#L63)

`require(self, token)`

Static calls (including nested helper bodies): `self.sessions.get`, `PermissionError`, `time.monotonic`.

Explicit raised conditions: `PermissionError`. See source for triggers; called validators may raise additional exceptions.

#### [LocalAuth.logout](../../medical_assistant/auth.py#L69)

`logout(self, token)`

Static calls (including nested helper bodies): `self.sessions.pop`.

#### [LocalAuth.audit](../../medical_assistant/auth.py#L72)

`audit(self, action, patient_id, token, payload)`

Static calls (including nested helper bodies): `self.require`, `connect`, `db.execute`, `json.dumps`.

#### [LocalAuth.receipt](../../medical_assistant/auth.py#L82)

`receipt(self, token, action, content_sha256)`

Static calls (including nested helper bodies): `self.require`, `hmac.new(self._receipt_key, message.encode(), 'sha256').hexdigest`, `hmac.new`, `message.encode`.

#### [LocalAuth.verify_receipt](../../medical_assistant/auth.py#L94)

`verify_receipt(self, receipt, action, content_sha256)`

Static calls (including nested helper bodies): `hmac.new(self._receipt_key, message.encode(), 'sha256').hexdigest`, `PermissionError`, `hmac.compare_digest`, `receipt.get`, `hmac.new`, `message.encode`.

Explicit raised conditions: `PermissionError`. See source for triggers; called validators may raise additional exceptions.

#### [LocalAuth.record_receipt](../../medical_assistant/auth.py#L107)

`record_receipt(self, receipt, patient_id, payload)`

Static calls (including nested helper bodies): `self.verify_receipt`, `connect`, `db.execute`, `json.dumps`.

## [medical_assistant/compact_reasoning.py](../../medical_assistant/compact_reasoning.py)

Compact local-model selection; Python restores exact immutable record excerpts.

No new clinical vocabulary, sources or decisions are introduced. The expanded
Assessment passes the same grounding/catalog checks as the full-output path.

### [Selected](../../medical_assistant/compact_reasoning.py#L30)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `hypothesis` | `str` | `required / supplied by caller` |
| `supporting` | `list[str]` | `Field(min_length=1, max_length=8)` |
| `against` | `list[str]` | `Field(max_length=8)` |
| `considerations` | `list[str]` | `Field(min_length=1, max_length=5)` |
| `references` | `list[str]` | `Field(max_length=3)` |

### [Selection](../../medical_assistant/compact_reasoning.py#L38)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `choices` | `list[Selected]` | `Field(min_length=1, max_length=3)` |
| `missing` | `list[str]` | `Field(max_length=3)` |
| `questions` | `list[str]` | `Field(max_length=2)` |

#### [catalog](../../medical_assistant/compact_reasoning.py#L44)

`catalog(prefix, values)`

Static calls (including nested helper bodies): `enumerate`.

#### [prepare](../../medical_assistant/compact_reasoning.py#L48)

`prepare(user)`

Static calls (including nested helper bodies): `json.loads`, `PatientRecord.model_validate`, `payload.get`, `Selection.model_json_schema`, `list`, `json.dumps`, `catalog`, `eligible_labels`.

#### [expand](../../medical_assistant/compact_reasoning.py#L81)

`expand(raw, record, refs, maps)`

Static calls (including nested helper bodies): `Selection.model_validate`, `Assessment`, `assessment.validate_sources`, `validate_reasoning`, `choose`, `labels.append`, `explanations.append`, `any`, `ValueError`, `len`, `claims`, `set`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [expand.choose](../../medical_assistant/compact_reasoning.py#L86)

`choose(ids, mapping)`

Static calls (including nested helper bodies): `any`, `ValueError`, `len`, `set`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [expand.claims](../../medical_assistant/compact_reasoning.py#L93)

`claims(ids)`

Static calls (including nested helper bodies): `choose`.

## [medical_assistant/ct_worker.py](../../medical_assistant/ct_worker.py)

Bounded local CT subprocesses. No shell, uploads, downloads or model tools.

#### [configured_ct_root](../../medical_assistant/ct_worker.py#L17)

`configured_ct_root()`

Static calls (including nested helper bodies): `Path`, `os.environ.get`, `str`.

#### [configured_ct_model](../../medical_assistant/ct_worker.py#L25)

`configured_ct_model(root=None)`

Static calls (including nested helper bodies): `Path`, `(root / 'models/luna16-full/registration.json').is_file`, `configured_ct_root`, `Path(os.environ.get('MHCRA_CT_MODEL_DIR', str(default))).expanduser`, `os.environ.get`, `str`.

### [LocalCTJob](../../medical_assistant/ct_worker.py#L37)

Class contract is defined by the fields and methods below.

#### [LocalCTJob.__init__](../../medical_assistant/ct_worker.py#L38)

`__init__(self, patient_id, *, root=None, jobs=None, timeout=MAX_JOB_SECONDS, mode='legacy', model_dir=None, device='cpu')`

Static calls (including nested helper bodies): `min`, `time.monotonic`, `Path(root or configured_ct_root()).resolve`, `self.directory.mkdir`, `threading.Lock`, `self.log_path.open`, `re.fullmatch`, `ValueError`, `Path`, `str`, `command.append`, `subprocess.Popen`, `math.isfinite`, `python.is_file` (additional calls in source).

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [LocalCTJob.bundle_path](../../medical_assistant/ct_worker.py#L146)

`bundle_path(self)`

#### [LocalCTJob._watch](../../medical_assistant/ct_worker.py#L149)

`_watch(self, timeout)`

Static calls (including nested helper bodies): `self.process.wait`, `self._log.close`, `self.cancel`, `time.monotonic`, `self.bundle_path.is_file`.

#### [LocalCTJob.cancel](../../medical_assistant/ct_worker.py#L169)

`cancel(self, *, timed_out=False)`

Static calls (including nested helper bodies): `subprocess.run`, `os.killpg`, `str`.

#### [LocalCTJob.status](../../medical_assistant/ct_worker.py#L192)

`status(self)`

#### [LocalCTJob.elapsed](../../medical_assistant/ct_worker.py#L197)

`elapsed(self)`

Static calls (including nested helper bodies): `time.monotonic`.

#### [LocalCTJob.progress](../../medical_assistant/ct_worker.py#L200)

`progress(self)`

Static calls (including nested helper bodies): `reversed`, `self.log_path.open`, `handle.seek`, `handle.read(4096).decode('utf-8', errors='replace').splitlines`, `line.startswith`, `max`, `stages.get`, `handle.read(4096).decode`, `line.split`, `self.log_path.stat`, `handle.read`.

## [medical_assistant/database.py](../../medical_assistant/database.py)

Transactional SQLite storage. Models have no access to these write functions.

#### [connect](../../medical_assistant/database.py#L17)

`connect(path: Path)`

Static calls (including nested helper bodies): `sqlite3.connect`, `connection.execute`, `connection.close`.

#### [initialize](../../medical_assistant/database.py#L28)

`initialize(path: Path=DATABASE_PATH)`

Static calls (including nested helper bodies): `path.parent.mkdir`, `connect`, `db.executescript`.

#### [attach_original](../../medical_assistant/database.py#L52)

`attach_original(record: PatientRecord, filename: str, raw: str) → PatientRecord`

Convert legacy synthetic JSON to immutable source + separately stored facts.

Static calls (including nested helper bodies): `SourceDocument`, `record.model_dump`, `PatientRecord.model_validate`, `source.model_dump`, `digest`.

#### [write_synthetic](../../medical_assistant/database.py#L69)

`write_synthetic(record: PatientRecord, path: Path, *, actor: str, action: str, approval=None)`

Internal atomic append; existing IDs are immutable and exact retries are no-ops.

Static calls (including nested helper bodies): `PatientRecord.model_validate`, `validate_record_grounding`, `record.model_dump`, `ValueError`, `connect`, `db.execute`, `Entry.model_validate_json`, `entry.model_dump_json`, `len`, `sum`, `source.date.isoformat`, `tuple`, `Entry.model_validate_json(prior[0]).model_dump`, `entry.model_dump` (additional calls in source).

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [get_history](../../medical_assistant/database.py#L170)

`get_history(patient_id: str, path: Path=DATABASE_PATH) → PatientRecord`

Static calls (including nested helper bodies): `PatientRecord`, `connect`, `LookupError`, `SourceDocument`, `Entry.model_validate_json`, `db.execute`.

Explicit raised conditions: `LookupError`. See source for triggers; called validators may raise additional exceptions.

#### [list_patients](../../medical_assistant/database.py#L206)

`list_patients(path: Path=DATABASE_PATH)`

Static calls (including nested helper bodies): `connect`, `dict`, `db.execute`.

#### [seed](../../medical_assistant/database.py#L214)

`seed(path: Path=DATABASE_PATH)`

Explicit built-in synthetic fixture creation; never imports arbitrary files.

Static calls (including nested helper bodies): `initialize`, `attach_original`, `write_synthetic`, `load_record`, `source_path.read_text`.

## [medical_assistant/endo_contracts/__init__.py](../../medical_assistant/endo_contracts/__init__.py)

ML-free, bounded RGB evidence protocol shared with LOVISA. No clinical inference.

### [Record](../../medical_assistant/endo_contracts/__init__.py#L31)

Class contract is defined by the fields and methods below.

#### [sha](../../medical_assistant/endo_contracts/__init__.py#L37)

`sha(data)`

Hash supplied bytes with SHA-256 for consistency checking.

Static calls (including nested helper bodies): `hashlib.sha256(data).hexdigest`, `hashlib.sha256`.

#### [digest](../../medical_assistant/endo_contracts/__init__.py#L42)

`digest(value)`

Hash canonical structured content without claiming producer authenticity.

Static calls (including nested helper bodies): `isinstance`, `sha`, `value.model_dump`, `json.dumps`.

### [ModelInfo](../../medical_assistant/endo_contracts/__init__.py#L53)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `name` | `Literal['synthetic-fixture', 'UNetSmall']` | `required / supplied by caller` |
| `backend` | `Literal['fixture', 'torch-cpu', 'onnx-cpu', 'openvino-cpu', 'openvino-npu']` | `required / supplied by caller` |
| `checkpoint_sha256` | `Hash` | `required / supplied by caller` |
| `recipe_sha256` | `Hash` | `required / supplied by caller` |
| `threshold` | `float` | `Field(ge=0, le=1)` |
| `min_area_px` | `int` | `Field(ge=1, le=MAX_PIXELS, strict=True)` |
| `evaluation_scope` | `Literal['software-fixture', 'synthetic-only', 'positive-images-only', 'includes-negative-images']` | `required / supplied by caller` |

#### [ModelInfo.matching](../../medical_assistant/endo_contracts/__init__.py#L68)

`matching(self)`

Keep fixture provenance and evaluation scope consistent.

Static calls (including nested helper bodies): `model_validator`, `ValueError`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

### [Candidate](../../medical_assistant/endo_contracts/__init__.py#L77)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `candidate_id` | `Id` | `required / supplied by caller` |
| `box_xyxy` | `tuple[int, int, int, int]` | `required / supplied by caller` |
| `area_px` | `int` | `Field(ge=1, le=MAX_PIXELS, strict=True)` |
| `mean_model_score` | `float` | `Field(ge=0, le=1)` |

### [Study](../../medical_assistant/endo_contracts/__init__.py#L84)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `study_id` | `Id` | `required / supplied by caller` |
| `patient_alias` | `Id` | `required / supplied by caller` |
| `input_kind` | `Literal['generated-synthetic', 'approved-public-research']` | `required / supplied by caller` |
| `source_sha256` | `Hash` | `required / supplied by caller` |
| `width` | `int` | `Field(ge=16, le=2048, strict=True)` |
| `height` | `int` | `Field(ge=16, le=2048, strict=True)` |
| `acquisition_date` | `None` | `None` |
| `model` | `ModelInfo` | `required / supplied by caller` |
| `candidates` | `list[Candidate]` | `Field(max_length=100)` |

#### [Study.bounds](../../medical_assistant/endo_contracts/__init__.py#L96)

`bounds(self)`

Check candidate identities, box bounds and fixture scope.

Static calls (including nested helper bodies): `model_validator`, `len`, `ValueError`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

### [Decision](../../medical_assistant/endo_contracts/__init__.py#L111)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `candidate_id` | `Id` | `required / supplied by caller` |
| `decision` | `Literal['accept', 'reject', 'uncertain']` | `required / supplied by caller` |

### [Review](../../medical_assistant/endo_contracts/__init__.py#L116)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `study_digest` | `Hash` | `required / supplied by caller` |
| `reviewer` | `str` | `Field(min_length=1, max_length=100, pattern='^[^\\r\\n]+$')` |
| `attested` | `Literal[True]` | `required / supplied by caller` |
| `decisions` | `list[Decision]` | `required / supplied by caller` |

#### [Review.explicit](../../medical_assistant/endo_contracts/__init__.py#L124)

`explicit(cls, value)`

Require a literal true human image-review attestation.

Static calls (including nested helper bodies): `field_validator`, `ValueError`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [Review.verify](../../medical_assistant/endo_contracts/__init__.py#L130)

`verify(self, study)`

Recheck original-source association and every derived workspace annotation.

Static calls (including nested helper bodies): `any`, `digest`, `ValueError`, `sorted`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

### [Artifact](../../medical_assistant/endo_contracts/__init__.py#L142)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `path` | `str` | `Field(min_length=1, max_length=100)` |
| `role` | `Literal['source_preview', 'probability', 'mask', 'overlay_preview']` | `required / supplied by caller` |
| `sha256` | `Hash` | `required / supplied by caller` |
| `size_bytes` | `int` | `Field(gt=0, le=16 * 1024 ** 2 + 1024, strict=True)` |
| `slice_index` | `Literal[0]` | `0` |

#### [Artifact.safe](../../medical_assistant/endo_contracts/__init__.py#L151)

`safe(cls, path)`

Reject absolute, traversal and reserved artifact paths.

Static calls (including nested helper bodies): `field_validator`, `PurePosixPath(path).is_absolute`, `any`, `ValueError`, `PurePosixPath`, `path.split`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

### [PublicResearchSource](../../medical_assistant/endo_contracts/__init__.py#L164)

Operator-declared public provenance, never a real patient-history link.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `dataset` | `str` | `Field(min_length=1, max_length=200)` |
| `source_url` | `str` | `Field(min_length=10, max_length=500, pattern='^https://')` |
| `license` | `str` | `Field(min_length=1, max_length=300)` |
| `research_subject_id` | `str` | `Field(min_length=1, max_length=100)` |
| `original_sha256` | `str` | `Field(pattern='^[a-f0-9]{64}$')` |
| `composite_case` | `Literal[True]` | `required / supplied by caller` |

#### [PublicResearchSource.explicit_composite](../../medical_assistant/endo_contracts/__init__.py#L176)

`explicit_composite(cls, value)`

Static calls (including nested helper bodies): `field_validator`, `ValueError`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

### [Bundle](../../medical_assistant/endo_contracts/__init__.py#L184)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `schema_version` | `Literal['lovisa-endo-image-v1', 'lovisa-endo-research-v2']` | `VERSION` |
| `synthetic` | `bool` | `Field(strict=True)` |
| `research` | `PublicResearchSource \| None` | `None` |
| `patient_id` | `Id` | `required / supplied by caller` |
| `study_id` | `Id` | `required / supplied by caller` |
| `job_id` | `str` | `Field(pattern='^[a-f0-9]{32}$')` |
| `acquisition_date` | `None` | `None` |
| `processed_at` | `datetime` | `required / supplied by caller` |
| `study` | `Study` | `required / supplied by caller` |
| `artifacts` | `list[Artifact]` | `Field(min_length=4, max_length=4)` |

#### [Bundle.consistent](../../medical_assistant/endo_contracts/__init__.py#L197)

`consistent(self)`

Require distinct schemas for artificial and deidentified public pixels.

Static calls (including nested helper bodies): `model_validator`, `any`, `ValueError`, `len`, `self.patient_id.startswith`, `a.path.endswith`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [regions](../../medical_assistant/endo_contracts/__init__.py#L245)

`regions(probability, threshold, min_area)`

4-connected predicted components, half-open source coordinates; no GT use.

Static calls (including nested helper bodies): `np.zeros`, `zip`, `candidates.append`, `np.where`, `deque`, `queue.popleft`, `points.append`, `len`, `np.array`, `Candidate`, `ValueError`, `queue.append`, `float`, `int` (additional calls in source).

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [overlay_pixels](../../medical_assistant/endo_contracts/__init__.py#L291)

`overlay_pixels(source, mask, candidates)`

Render deterministic amber candidate masks and boxes over source pixels.

Static calls (including nested helper bodies): `source.copy`, `source[selected].astype`, `np.array`.

#### [png](../../medical_assistant/endo_contracts/__init__.py#L305)

`png(array)`

Encode a canonical PNG artifact without external resources.

Static calls (including nested helper bodies): `io.BytesIO`, `Image.fromarray(array).save`, `buffer.getvalue`, `Image.fromarray`.

#### [array_bytes](../../medical_assistant/endo_contracts/__init__.py#L312)

`array_bytes(array)`

Encode a non-object NumPy array for bounded source verification.

Static calls (including nested helper bodies): `io.BytesIO`, `np.save`, `buffer.getvalue`.

#### [_image](../../medical_assistant/endo_contracts/__init__.py#L319)

`_image(data, mode, shape)`

Validate image dimensions and format before decoding pixel arrays.

Static calls (including nested helper bodies): `Image.open`, `np.array`, `io.BytesIO`, `ValueError`, `getattr`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [_probability](../../medical_assistant/endo_contracts/__init__.py#L332)

`_probability(data, shape)`

Bound array headers and payload before allocating a finite probability map.

Static calls (including nested helper bodies): `io.BytesIO`, `np.lib.format.read_array_header_1_0`, `np.load`, `np.lib.format.read_magic`, `ValueError`, `np.any`, `np.dtype`, `np.isfinite(value).all`, `len`, `stream.tell`, `math.prod`, `np.isfinite`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [unique](../../medical_assistant/endo_contracts/__init__.py#L353)

`unique(pairs)`

Reject duplicate JSON keys instead of silently accepting the last value.

Static calls (including nested helper bodies): `ValueError`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [read_exchange](../../medical_assistant/endo_contracts/__init__.py#L363)

`read_exchange(payload, patient_id)`

Verify all bytes and derived pixels before storing; hashes are not authenticity.

Static calls (including nested helper bodies): `ValueError`, `_image`, `_probability`, `regions`, `overlay_pixels`, `len`, `zipfile.ZipFile`, `archive.infolist`, `any`, `archive.read`, `Bundle.model_validate`, `sha`, `np.array_equal`, `io.BytesIO` (additional calls in source).

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

## [medical_assistant/endo_contracts/worker.py](../../medical_assistant/endo_contracts/worker.py)

Bounded local subprocess lifecycle shared by the endoscopy interfaces.

### [LocalJob](../../medical_assistant/endo_contracts/worker.py#L12)

Class contract is defined by the fields and methods below.

#### [LocalJob.__init__](../../medical_assistant/endo_contracts/worker.py#L13)

`__init__(self, command, *, cwd, directory, output, timeout=110, input_files=None)`

Initialise the explicit local model or bounded worker without remote fallback.

Static calls (including nested helper bodies): `min`, `time.monotonic`, `Path`, `self.directory.mkdir`, `(input_files or {}).items`, `self.log_path.open`, `threading.Lock`, `threading.Thread(target=self._watch, daemon=True).start`, `ValueError`, `(self.directory / name).write_bytes`, `subprocess.Popen`, `math.isfinite`, `self._log.close`, `threading.Thread` (additional calls in source).

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [LocalJob._watch](../../medical_assistant/endo_contracts/worker.py#L60)

`_watch(self)`

Publish completion only after successful process exit within the deadline.

Static calls (including nested helper bodies): `self.process.wait`, `self._log.close`, `self.cancel`, `max`, `self.bundle_path.is_file`.

#### [LocalJob.cancel](../../medical_assistant/endo_contracts/worker.py#L86)

`cancel(self, *, timed_out=False)`

Stop the worker process tree and prevent late result publication.

Static calls (including nested helper bodies): `subprocess.run`, `os.killpg`, `str`.

#### [LocalJob.elapsed](../../medical_assistant/endo_contracts/worker.py#L111)

`elapsed(self)`

Return local monotonic time since the job began.

Static calls (including nested helper bodies): `time.monotonic`.

#### [LocalJob.status](../../medical_assistant/endo_contracts/worker.py#L115)

`status(self)`

Read worker lifecycle state under its lock.

#### [LocalJob.progress](../../medical_assistant/endo_contracts/worker.py#L120)

`progress(self)`

Read only allowlisted stage markers from the bounded log tail.

Static calls (including nested helper bodies): `reversed`, `self.log_path.open`, `handle.seek`, `handle.read(4096).decode(errors='replace').splitlines`, `line.startswith`, `max`, `stages.get`, `handle.read(4096).decode`, `line.split`, `self.log_path.stat`, `handle.read`.

## [medical_assistant/endo_support.py](../../medical_assistant/endo_support.py)

Modality-specific candidate review binding; no clinical or safety decisions.

#### [is_endoscopy](../../medical_assistant/endo_support.py#L6)

`is_endoscopy(manifest)`

Static calls (including nested helper bodies): `manifest.get`.

#### [checked_endo_review](../../medical_assistant/endo_support.py#L10)

`checked_endo_review(manifest, review, *, reviewer=None)`

Static calls (including nested helper bodies): `Bundle.model_validate`, `Review.model_validate`, `value.verify`, `PermissionError`, `isinstance`, `review.model_dump`.

Explicit raised conditions: `PermissionError`. See source for triggers; called validators may raise additional exceptions.

#### [endo_acceptance_digest](../../medical_assistant/endo_support.py#L21)

`endo_acceptance_digest(proposal, review)`

Static calls (including nested helper bodies): `checked_endo_review`, `digest`, `value.model_dump`.

#### [verify_endo_snapshot](../../medical_assistant/endo_support.py#L31)

`verify_endo_snapshot(snapshot)`

Static calls (including nested helper bodies): `checked_endo_review`, `snapshot.get`, `endo_acceptance_digest`, `ValueError`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [summarize_endo](../../medical_assistant/endo_support.py#L42)

`summarize_endo(manifest, review=None)`

Static calls (including nested helper bodies): `Bundle.model_validate`, `checked_endo_review`, `len`, `sum`, `round`, `lookup.get`, `lookup.values`.

## [medical_assistant/endo_ui.py](../../medical_assistant/endo_ui.py)

Source-first endoscopy inspection; every candidate needs explicit human review.

#### [image_results](../../medical_assistant/endo_ui.py#L20)

`image_results(manifest, path_for, review=None)`

Static calls (including nested helper bodies): `summarize_endo`, `st.selectbox`, `str`, `st.columns`, `a.image`, `b.image`, `st.subheader`, `a.metric`, `b.metric`, `st.caption`, `path_for`, `next`, `max`, `st.dataframe` (additional calls in source).

#### [endoscopy_ui](../../medical_assistant/endo_ui.py#L79)

`endoscopy_ui(path, auth, token, user, record, *, locked=False, case_imaging=None)`

Static calls (including nested helper bodies): `st.subheader`, `st.caption`, `collect`, `image_actions`, `st.session_state.get`, `ImagingStore`, `st.info`, `st.button`, `is_endoscopy`, `store.snapshots`, `store.verify`, `st.selectbox`, `next`, `image_results` (additional calls in source).

#### [endoscopy_ui.preview](../../medical_assistant/endo_ui.py#L138)

`preview(role, index)`

Static calls (including nested helper bodies): `next`.

## [medical_assistant/endo_worker.py](../../medical_assistant/endo_worker.py)

Explicit local Endoscopy Agent adapter; bounded CV worker, no LLM or downloads.

#### [configured_endo_root](../../medical_assistant/endo_worker.py#L14)

`configured_endo_root()`

Static calls (including nested helper bodies): `Path`, `os.environ.get`, `str`.

#### [configured_endo_model](../../medical_assistant/endo_worker.py#L22)

`configured_endo_model(root=None)`

Static calls (including nested helper bodies): `Path`, `(preferred / 'registration.json').is_file`, `configured_endo_root`, `os.environ.get`, `str`.

### [LocalEndoscopyJob](../../medical_assistant/endo_worker.py#L37)

Class contract is defined by the fields and methods below.

#### [LocalEndoscopyJob.__init__](../../medical_assistant/endo_worker.py#L38)

`__init__(self, patient_id, *, root=None, jobs=None, mode='fixture', model_dir=None, backend='onnx-cpu', timeout=110, image_bytes=None, research=None)`

Static calls (including nested helper bodies): `TypeAdapter(Id).validate_python`, `Path(root or configured_endo_root()).resolve`, `super().__init__`, `PublicResearchSource.model_validate`, `ValueError`, `Path`, `str`, `TypeAdapter`, `python.is_file`, `(root / 'src/endo/cli.py').is_file`, `uuid4`, `provenance.model_dump_json().encode`, `super`, `patient_id.startswith` (additional calls in source).

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

## [medical_assistant/evidence.py](../../medical_assistant/evidence.py)

Retrieve only explicitly approved, hash-verified files in a local collection.

### [EvidenceItem](../../medical_assistant/evidence.py#L13)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `id` | `str` | `Field(min_length=1)` |
| `title` | `str` | `Field(min_length=1)` |
| `path` | `str` | `Field(min_length=1)` |
| `sha256` | `str` | `Field(pattern='^[a-f0-9]{64}$')` |
| `approved` | `bool` | `Field(strict=True)` |

### [EvidenceManifest](../../medical_assistant/evidence.py#L21)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `documents` | `list[EvidenceItem]` | `required / supplied by caller` |

### [LocalEvidenceCollection](../../medical_assistant/evidence.py#L25)

Class contract is defined by the fields and methods below.

#### [LocalEvidenceCollection.__init__](../../medical_assistant/evidence.py#L26)

`__init__(self, directory: Path)`

Static calls (including nested helper bodies): `directory.resolve`.

#### [LocalEvidenceCollection.retrieve](../../medical_assistant/evidence.py#L29)

`retrieve(self, query: str) → list[dict]`

Static calls (including nested helper bodies): `RunnableLambda(local_search).invoke`, `EvidenceManifest.model_validate_json`, `set`, `(self.directory / 'manifest.json').read_text`, `len`, `ValueError`, `re.findall`, `(self.directory / item.path).resolve`, `path.read_text`, `sorted`, `RunnableLambda`, `query.casefold`, `digest`, `results.append` (additional calls in source).

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [LocalEvidenceCollection.retrieve.local_search](../../medical_assistant/evidence.py#L30)

`local_search(query)`

Static calls (including nested helper bodies): `EvidenceManifest.model_validate_json`, `set`, `(self.directory / 'manifest.json').read_text`, `len`, `ValueError`, `re.findall`, `(self.directory / item.path).resolve`, `path.read_text`, `sorted`, `query.casefold`, `digest`, `results.append`, `path.is_relative_to`, `path.stat` (additional calls in source).

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

## [medical_assistant/grounding.py](../../medical_assistant/grounding.py)

Source grounding for JSON medical imports; no semantic facts are invented.

#### [validate_record_grounding](../../medical_assistant/grounding.py#L7)

`validate_record_grounding(record: PatientRecord)`

Static calls (including nested helper bodies): `ValueError`, `json.loads`, `originals.get(entry.source_id, {}).get`, `any`, `payload.get`, `Entry.model_validate`, `len`, `isinstance`, `originals.get`, `getattr`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

## [medical_assistant/history.py](../../medical_assistant/history.py)

Extractive history and medication agents for typed synthetic source records.

#### [chronology](../../medical_assistant/history.py#L10)

`chronology(entry)`

### [MedicalHistoryAgent](../../medical_assistant/history.py#L14)

Class contract is defined by the fields and methods below.

#### [MedicalHistoryAgent.run](../../medical_assistant/history.py#L15)

`run(self, record: PatientRecord) → Assessment`

Static calls (including nested helper bodies): `RunnableLambda(extract).invoke`, `defaultdict`, `RunnableLambda`, `by_content.values`, `Assessment`, `len`, `entry.text.casefold`, `Claim`, `sorted`, `', '.join`.

#### [MedicalHistoryAgent.run.extract](../../medical_assistant/history.py#L16)

`extract(record)`

Static calls (including nested helper bodies): `defaultdict`, `by_content.values`, `Assessment`, `len`, `entry.text.casefold`, `Claim`, `sorted`, `', '.join`.

### [MedicationAgent](../../medical_assistant/history.py#L34)

Class contract is defined by the fields and methods below.

#### [MedicationAgent.run](../../medical_assistant/history.py#L35)

`run(self, record: PatientRecord) → Assessment`

Static calls (including nested helper bodies): `RunnableLambda(extract).invoke`, `defaultdict`, `sorted`, `by_name.values`, `zip`, `missing.append`, `RunnableLambda`, `medications.append`, `len`, `Assessment`, `Medication`, `by_name[order.name.casefold()].append`, `changes.append`, `DoseChange` (additional calls in source).

#### [MedicationAgent.run.extract](../../medical_assistant/history.py#L36)

`extract(record)`

Static calls (including nested helper bodies): `defaultdict`, `sorted`, `by_name.values`, `zip`, `missing.append`, `medications.append`, `len`, `Assessment`, `Medication`, `by_name[order.name.casefold()].append`, `changes.append`, `DoseChange`, `order.name.casefold`.

## [medical_assistant/history_import.py](../../medical_assistant/history_import.py)

Separate history-management workflow: validate → extract → approve → append.

### [HistoryManagement](../../medical_assistant/history_import.py#L13)

Class contract is defined by the fields and methods below.

#### [HistoryManagement.__init__](../../medical_assistant/history_import.py#L14)

`__init__(self, path, *, auth=None)`

Static calls (including nested helper bodies): `LocalAuth`.

#### [HistoryManagement.prepare](../../medical_assistant/history_import.py#L19)

`prepare(self, raw: str, filename: str)`

Static calls (including nested helper bodies): `attach_original`, `validate_record_grounding`, `digest`, `json.dumps`, `len`, `ValueError`, `PatientRecord.model_validate_json`, `get_history`, `record.model_dump`, `MedicalHistoryAgent().run(record).model_dump`, `MedicationAgent().run(record).model_dump`, `uuid4`, `raw.encode`, `sum` (additional calls in source).

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [HistoryManagement.approve](../../medical_assistant/history_import.py#L55)

`approve(self, proposal_id, review: Review, token=None)`

Static calls (including nested helper bodies): `Review.model_validate`, `json.loads`, `PatientRecord.model_validate`, `get_history`, `review.model_dump`, `self.auth.require`, `PermissionError`, `ValueError`, `record.model_dump`, `write_synthetic`, `self.auth.audit`, `entry.model_dump`.

Explicit raised conditions: `PermissionError`, `ValueError`. See source for triggers; called validators may raise additional exceptions.

## [medical_assistant/imaging.py](../../medical_assistant/imaging.py)

Human-reviewed synthetic imaging storage, separate from clinical source facts.

### [ImagingStore](../../medical_assistant/imaging.py#L23)

Class contract is defined by the fields and methods below.

#### [ImagingStore.__init__](../../medical_assistant/imaging.py#L24)

`__init__(self, path, auth=None, trust=None)`

Static calls (including nested helper bodies): `Path`, `connect`, `db.execute`.

#### [ImagingStore.prepare](../../medical_assistant/imaging.py#L34)

`prepare(self, payload, patient_id, *, study_id=None)`

Static calls (including nested helper bodies): `get_history`, `validate_bundle`, `verify_producer`, `digest`, `directory.mkdir`, `json.dumps`, `ValueError`, `is_endoscopy`, `uuid4`, `bundle.model_dump`, `file_digest`, `signature.model_dump`, `(directory / 'bundle.json').write_bytes`, `(directory / 'source.mhcra.zip').write_bytes` (additional calls in source).

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [ImagingStore.discard](../../medical_assistant/imaging.py#L66)

`discard(self, key)`

Static calls (including nested helper bodies): `self.pending.pop`, `shutil.rmtree`.

#### [ImagingStore._directory](../../medical_assistant/imaging.py#L70)

`_directory(self, patient_id, study_id)`

#### [ImagingStore._verify_directory](../../medical_assistant/imaging.py#L74)

`_verify_directory(directory, snapshot)`

Static calls (including nested helper bodies): `archive.read_bytes`, `validate_bundle`, `{'bundle.json': raw, **artifacts}.items`, `archive.is_symlink`, `directory.is_symlink`, `ValueError`, `file_digest`, `bundle.model_dump`, `type(bundle).model_validate(snapshot['manifest']).model_dump`, `path.is_symlink`, `path.read_bytes`, `type(bundle).model_validate`, `type`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [ImagingStore.approve](../../medical_assistant/imaging.py#L95)

`approve(self, key, review, token=None, *, nodule_review=None, endo_review=None)`

Static calls (including nested helper bodies): `Review.model_validate`, `json.loads`, `imaging_acceptance_digest`, `self._verify_directory`, `self.auth.receipt`, `self._directory`, `target.parent.mkdir`, `self.pending.pop`, `directory.exists`, `review.model_dump`, `PermissionError`, `is_nodule`, `checked_nodule_review`, `is_endoscopy` (additional calls in source).

Explicit raised conditions: `PermissionError`, `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [ImagingStore.snapshots](../../medical_assistant/imaging.py#L186)

`snapshots(self, patient_id)`

Static calls (including nested helper bodies): `self.verify`, `connect`, `json.loads`, `db.execute`.

#### [ImagingStore.verify](../../medical_assistant/imaging.py#L196)

`verify(self, snapshots)`

Static calls (including nested helper bodies): `verify_nodule_snapshot`, `self._verify_directory`, `connect`, `ValueError`, `self._directory`, `json.loads`, `db.execute`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [ImagingStore.preview_path](../../medical_assistant/imaging.py#L212)

`preview_path(self, snapshot, role, index)`

Static calls (including nested helper bodies): `self.verify`, `next`, `self._directory`.

#### [ImagingStore.preview_resolver](../../medical_assistant/imaging.py#L225)

`preview_resolver(self, snapshot)`

Verify the archive once per view, then hash only requested artifacts.

Acceptance, composition, completion, export and saving still perform full
independent validation. Nothing is globally cached or shared across patients.

Static calls (including nested helper bodies): `self.verify`, `self._directory`, `path.is_symlink`, `ValueError`, `file_digest`, `path.read_bytes`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [ImagingStore.preview_resolver.resolve](../../medical_assistant/imaging.py#L239)

`resolve(role, index)`

Static calls (including nested helper bodies): `path.is_symlink`, `ValueError`, `file_digest`, `path.read_bytes`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

## [medical_assistant/imaging_actions.py](../../medical_assistant/imaging_actions.py)

Authenticated image input routing, independent of Streamlit rendering.

ZIPs contain existing predictions: Analyze validates and opens them for review.
Only a raw, permitted endoscopy image launches inference on uploaded pixels.
Nothing in this module accepts a study or approves a clinical report.

#### [job_pending](../../medical_assistant/imaging_actions.py#L19)

`job_pending(job)`

A collected result is represented by its proposal, not a stale job handle.

Static calls (including nested helper bodies): `bool`, `job.status`, `getattr`.

#### [failure_detail](../../medical_assistant/imaging_actions.py#L33)

`failure_detail(job)`

Return the bounded worker exception, without a traceback or full log dump.

Static calls (including nested helper bodies): `next`, `path.open`, `handle.seek`, `handle.read(4096).decode('utf-8', errors='replace').splitlines`, `max`, `line.strip`, `handle.read(4096).decode`, `reversed`, `line.startswith`, `path.stat`, `handle.read`.

#### [blocker](../../medical_assistant/imaging_actions.py#L56)

`blocker(state)`

Static calls (including nested helper bodies): `state.get`, `is_endoscopy`, `job.status`.

#### [analyze](../../medical_assistant/imaging_actions.py#L72)

`analyze(state, store, auth, token, patient, modality, *, upload=None, mode='auto')`

Validate input before retiring a frozen report; never silently use a demo.

``upload`` is (filename, bytes). Mode applies only when there is no upload.
An uploaded ZIP always opens its included results, regardless of example mode.
Failed input validation leaves the existing report and all approvals intact.

Static calls (including nested helper bodies): `auth.require`, `blocker`, `reset_report_context`, `state.pop`, `ValueError`, `Path(name).suffix.lower`, `store.prepare`, `completed.bundle_path.read_bytes`, `any`, `len`, `matching_endoscopy`, `LocalEndoscopyJob`, `state.get`, `completed.status` (additional calls in source).

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [collect](../../medical_assistant/imaging_actions.py#L185)

`collect(state, store, modality, patient)`

Publish one completed result without overwriting a pending/frozen review.

Static calls (including nested helper bodies): `state.get`, `getattr`, `store.prepare`, `state.pop`, `job.status`, `ValueError`, `job.bundle_path.read_bytes`, `is_endoscopy`, `store.discard`, `str`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

## [medical_assistant/imaging_contract.py](../../medical_assistant/imaging_contract.py)

Bounded synthetic imaging exchange. Model artifacts are never clinical facts.

### [Artifact](../../medical_assistant/imaging_contract.py#L31)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `path` | `str` | `required / supplied by caller` |
| `role` | `Literal['mask', 'source_preview', 'overlay_preview']` | `required / supplied by caller` |
| `sha256` | `str` | `Field(pattern='^[a-f0-9]{64}$')` |
| `size_bytes` | `int` | `Field(gt=0, le=8 * 1024 * 1024, strict=True)` |
| `slice_index` | `int \| None` | `Field(default=None, ge=0, le=63, strict=True)` |

#### [Artifact.local_relative](../../medical_assistant/imaging_contract.py#L40)

`local_relative(cls, value)`

Static calls (including nested helper bodies): `field_validator`, `value.split`, `PurePosixPath(value).is_absolute`, `any`, `ValueError`, `len`, `PurePosixPath`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

### [Geometry](../../medical_assistant/imaging_contract.py#L55)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `shape_zyx` | `tuple[int, int, int]` | `required / supplied by caller` |
| `spacing_zyx_mm` | `tuple[float, float, float]` | `required / supplied by caller` |
| `origin_lps` | `tuple[float, float, float]` | `required / supplied by caller` |
| `direction_lps` | `tuple[float, float, float, float, float, float, float, float, float]` | `required / supplied by caller` |

#### [Geometry.physical](../../medical_assistant/imaging_contract.py#L62)

`physical(self)`

Static calls (including nested helper bodies): `model_validator`, `any`, `np.array(self.direction_lps).reshape`, `ValueError`, `np.isfinite([*self.origin_lps, *self.direction_lps]).all`, `np.array`, `np.allclose`, `np.isclose`, `np.isfinite`, `np.eye`, `np.linalg.det`, `math.isfinite`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

### [ImagingBundle](../../medical_assistant/imaging_contract.py#L78)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `schema_version` | `Literal['mhcra-imaging-v1']` | `required / supplied by caller` |
| `synthetic` | `Literal[True]` | `required / supplied by caller` |
| `patient_id` | `str` | `Field(pattern='^[A-Za-z0-9_-]{1,64}$')` |
| `study_id` | `str` | `Field(pattern='^[A-Za-z0-9_-]{1,64}$')` |
| `job_id` | `str` | `Field(pattern='^[a-f0-9]{32}$')` |
| `acquisition_date` | `None` | `required / supplied by caller` |
| `processed_at` | `datetime` | `required / supplied by caller` |
| `source_series_sha256` | `str` | `Field(pattern='^[a-f0-9]{64}$')` |
| `checkpoint_sha256` | `str` | `Field(pattern='^[a-f0-9]{64}$')` |
| `onnx_sha256` | `str` | `Field(pattern='^[a-f0-9]{64}$')` |
| `model_name` | `Literal['UNetSmall']` | `required / supplied by caller` |
| `classes` | `dict[str, str]` | `required / supplied by caller` |
| `geometry` | `Geometry` | `required / supplied by caller` |
| `voxel_counts` | `tuple[int, int, int, int]` | `required / supplied by caller` |
| `candidate_volumes_mm3` | `tuple[float, float, float, float]` | `required / supplied by caller` |
| `postprocessing_enabled` | `Literal[False]` | `required / supplied by caller` |
| `onnx_parity_passed` | `Literal[True]` | `required / supplied by caller` |
| `uncertainty_mean` | `float` | `Field(ge=0, le=1, allow_inf_nan=False)` |
| `artifacts` | `list[Artifact]` | `Field(min_length=3, max_length=129)` |
| `limitations` | `str` | `Field(min_length=1, max_length=1000)` |

#### [ImagingBundle.boolean_only](../../medical_assistant/imaging_contract.py#L104)

`boolean_only(cls, value)`

Static calls (including nested helper bodies): `field_validator`, `type`, `ValueError`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [ImagingBundle.consistent](../../medical_assistant/imaging_contract.py#L110)

`consistent(self)`

Static calls (including nested helper bodies): `model_validator`, `math.prod`, `zip`, `any`, `ValueError`, `sum`, `len`, `math.isfinite`, `math.isclose`, `range`, `a.path.endswith`, `type`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [file_digest](../../medical_assistant/imaging_contract.py#L148)

`file_digest(payload)`

Static calls (including nested helper bodies): `hashlib.sha256(payload).hexdigest`, `hashlib.sha256`.

#### [validate_bundle](../../medical_assistant/imaging_contract.py#L154)

`validate_bundle(payload: bytes, patient_id: str)`

Read bounded bytes without extracting arbitrary archive paths or pickle.

Static calls (including nested helper bodies): `ValueError`, `_verify_pixels`, `len`, `zipfile.ZipFile`, `json.loads`, `z.infolist`, `any`, `z.getinfo`, `z.read`, `ImagingBundle.model_validate`, `io.BytesIO`, `archive.read`, `isinstance`, `header.get` (additional calls in source).

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [validate_bundle.unique_object](../../medical_assistant/imaging_contract.py#L207)

`unique_object(pairs)`

Static calls (including nested helper bodies): `ValueError`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [_verify_pixels](../../medical_assistant/imaging_contract.py#L249)

`_verify_pixels(bundle, artifacts)`

Static calls (including nested helper bodies): `next`, `range`, `zipfile.ZipFile`, `nested.infolist`, `np.load`, `len`, `source.copy`, `(0.55 * source[selected] + 0.45 * COLORS[labels[i][selected]]).astype`, `io.BytesIO`, `ValueError`, `np.lib.format.read_magic`, `readers[version]`, `list`, `Image.open` (additional calls in source).

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

## [medical_assistant/imaging_results.py](../../medical_assistant/imaging_results.py)

Small, deterministic CT summaries shared by the viewer and clinical summary.

#### [summarize](../../medical_assistant/imaging_results.py#L9)

`summarize(manifest, review=None)`

Static calls (including nested helper bodies): `NoduleBundle.model_validate`, `manifest.get`, `NoduleReview.model_validate`, `parsed.verify`, `decisions.get`, `rows.append`, `len`, `sum`, `round`, `bool`, `decisions.values`, `math.floor`, `math.ceil`, `d.caliper.length_mm`.

## [medical_assistant/imaging_ui.py](../../medical_assistant/imaging_ui.py)

Imaging inspection UI; acceptance is separate from final clinical approval.

#### [_viewer](../../medical_assistant/imaging_ui.py#L22)

`_viewer(manifest, path_for, key, *, review=None)`

Static calls (including nested helper bodies): `is_nodule`, `st.caption`, `st.columns`, `left.image`, `right.image`, `nodule_viewer`, `st.slider`, `str`, `path_for`.

#### [result_summary](../../medical_assistant/imaging_ui.py#L48)

`result_summary(manifest, review=None)`

Static calls (including nested helper bodies): `summarize`, `st.subheader`, `st.caption`, `st.columns`, `a.metric`, `b.metric`, `c.metric`, `st.dataframe`, `row.items`.

#### [imaging_ui](../../medical_assistant/imaging_ui.py#L81)

`imaging_ui(path, auth, token, user, record, *, locked=False, case_imaging=None)`

Static calls (including nested helper bodies): `st.subheader`, `st.caption`, `collect`, `image_actions`, `st.session_state.get`, `ImagingStore`, `is_endoscopy`, `st.info`, `st.button`, `store.snapshots`, `store.verify`, `st.selectbox`, `next`, `result_summary` (additional calls in source).

#### [imaging_ui.preview](../../medical_assistant/imaging_ui.py#L160)

`preview(role, index)`

Static calls (including nested helper bodies): `next`.

## [medical_assistant/jobs.py](../../medical_assistant/jobs.py)

Session-owned background work with a hard publication deadline; no UI in workers.

### [WorkStopped](../../medical_assistant/jobs.py#L12)

Class contract is defined by the fields and methods below.

### [Budget](../../medical_assistant/jobs.py#L16)

Class contract is defined by the fields and methods below.

#### [Budget.__init__](../../medical_assistant/jobs.py#L17)

`__init__(self, seconds=MAX_JOB_SECONDS)`

Static calls (including nested helper bodies): `min`, `time.monotonic`, `threading.Event`, `ValueError`, `math.isfinite`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [Budget.elapsed](../../medical_assistant/jobs.py#L25)

`elapsed(self)`

Static calls (including nested helper bodies): `time.monotonic`.

#### [Budget.check](../../medical_assistant/jobs.py#L28)

`check(self)`

Static calls (including nested helper bodies): `self.stopped.is_set`, `WorkStopped`.

Explicit raised conditions: `WorkStopped`. See source for triggers; called validators may raise additional exceptions.

### [WorkTask](../../medical_assistant/jobs.py#L35)

Run a callable(progress, budget) once; ignore cancelled/late results.

Threads never write Streamlit state. A timed-out Python/native operation may
finish unwinding in its daemon thread; its result cannot be published. Slots
are held until it exits so repeated retries cannot grow unbounded workers.

#### [WorkTask.__init__](../../medical_assistant/jobs.py#L43)

`__init__(self, target, *, seconds=MAX_JOB_SECONDS, title='Preparing your workspace')`

Static calls (including nested helper bodies): `Budget`, `threading.RLock`, `threading.Timer`, `threading.Thread`, `self._timer.start`, `self._thread.start`, `_SLOTS.acquire`, `WorkStopped`, `uuid4`.

Explicit raised conditions: `WorkStopped`. See source for triggers; called validators may raise additional exceptions.

#### [WorkTask._timeout](../../medical_assistant/jobs.py#L64)

`_timeout(self)`

Static calls (including nested helper bodies): `time.monotonic`, `self.budget.stopped.set`.

#### [WorkTask.progress](../../medical_assistant/jobs.py#L72)

`progress(self, message)`

Static calls (including nested helper bodies): `self.budget.check`.

#### [WorkTask._run](../../medical_assistant/jobs.py#L78)

`_run(self, target)`

Static calls (including nested helper bodies): `target`, `self.budget.check`, `self._timer.cancel`, `_SLOTS.release`, `time.monotonic`, `isinstance`, `self._timeout`, `str`.

#### [WorkTask.cancel](../../medical_assistant/jobs.py#L102)

`cancel(self)`

Static calls (including nested helper bodies): `time.monotonic`, `self.budget.stopped.set`, `self._timer.cancel`.

#### [WorkTask.snapshot](../../medical_assistant/jobs.py#L111)

`snapshot(self)`

Static calls (including nested helper bodies): `self._timeout`, `time.monotonic`.

#### [WorkTask.result](../../medical_assistant/jobs.py#L123)

`result(self)`

Static calls (including nested helper bodies): `WorkStopped`, `self.snapshot`.

Explicit raised conditions: `WorkStopped`. See source for triggers; called validators may raise additional exceptions.

### [BudgetInference](../../medical_assistant/jobs.py#L129)

Check cancellation/deadline before and after the local model call.

#### [BudgetInference.__init__](../../medical_assistant/jobs.py#L132)

`__init__(self, inference, budget)`

#### [BudgetInference.assess](../../medical_assistant/jobs.py#L136)

`assess(self, *args, **kwargs)`

Static calls (including nested helper bodies): `self.budget.check`, `self.inference.assess`.

#### [BudgetInference.close](../../medical_assistant/jobs.py#L142)

`close(self)`

Static calls (including nested helper bodies): `self.inference.close`.

## [medical_assistant/models.py](../../medical_assistant/models.py)

Validated record, specialist output, and human review contracts.

### [StrictModel](../../medical_assistant/models.py#L9)

Class contract is defined by the fields and methods below.

### [MedicationOrder](../../medical_assistant/models.py#L13)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `name` | `str` | `Field(min_length=1)` |
| `dose` | `str` | `Field(min_length=1)` |
| `frequency` | `str` | `Field(min_length=1)` |

### [BloodPressure](../../medical_assistant/models.py#L19)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `systolic` | `float` | `Field(gt=0, allow_inf_nan=False)` |
| `diastolic` | `float` | `Field(gt=0, allow_inf_nan=False)` |
| `unit` | `Literal['mmHg']` | `'mmHg'` |

### [SourceDocument](../../medical_assistant/models.py#L25)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `id` | `str` | `Field(min_length=1)` |
| `filename` | `str` | `Field(min_length=1)` |
| `date` | `Date \| None` | `None` |
| `content` | `str` | `Field(min_length=1)` |
| `sha256` | `str` | `Field(pattern='^[a-f0-9]{64}$')` |
| `verification_status` | `Literal['unverified', 'verified']` | `'unverified'` |

#### [SourceDocument.valid_digest](../../medical_assistant/models.py#L35)

`valid_digest(self)`

Static calls (including nested helper bodies): `model_validator`, `hashlib.sha256(self.content.encode()).hexdigest`, `ValueError`, `hashlib.sha256`, `self.content.encode`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

### [Entry](../../medical_assistant/models.py#L43)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `id` | `str` | `Field(min_length=1)` |
| `date` | `Date \| None` | `None` |
| `source_type` | `Literal['documented', 'patient_reported']` | `required / supplied by caller` |
| `kind` | `Literal['encounter', 'diagnosis', 'symptom', 'procedure', 'lab', 'medication']` | `required / supplied by caller` |
| `text` | `str` | `Field(min_length=1, max_length=8000)` |
| `source_id` | `str \| None` | `None` |
| `verification_status` | `Literal['unverified', 'verified']` | `'unverified'` |
| `medication` | `MedicationOrder \| None` | `None` |
| `blood_pressure` | `BloodPressure \| None` | `None` |
| `warning_screen` | `Literal['present', 'absent', 'unknown'] \| None` | `None` |

### [PatientRecord](../../medical_assistant/models.py#L56)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `fictional` | `Literal[True]` | `required / supplied by caller` |
| `patient_id` | `str` | `Field(pattern='^[a-zA-Z0-9_-]{1,64}$')` |
| `display_name` | `str` | `Field(min_length=1)` |
| `entries` | `list[Entry]` | `Field(min_length=1, max_length=100)` |
| `sources` | `list[SourceDocument]` | `Field(default_factory=list)` |

#### [PatientRecord.unique_ids](../../medical_assistant/models.py#L64)

`unique_ids(self)`

Static calls (including nested helper bodies): `model_validator`, `len`, `ValueError`, `any`, `set`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

### [Claim](../../medical_assistant/models.py#L78)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `kind` | `Literal['documented', 'patient_reported', 'hypothesis']` | `required / supplied by caller` |
| `text` | `str` | `Field(min_length=1)` |
| `evidence_ids` | `list[str]` | `Field(min_length=1)` |

### [Medication](../../medical_assistant/models.py#L84)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `name` | `str` | `Field(min_length=1)` |
| `dose` | `str \| None` | `None` |
| `frequency` | `str \| None` | `None` |
| `source_type` | `Literal['documented', 'patient_reported']` | `required / supplied by caller` |
| `evidence_ids` | `list[str]` | `Field(min_length=1)` |
| `reconciliation_question` | `str` | `Field(min_length=1)` |

### [DoseChange](../../medical_assistant/models.py#L93)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `name` | `str` | `required / supplied by caller` |
| `previous_dose` | `str` | `required / supplied by caller` |
| `documented_dose` | `str` | `required / supplied by caller` |
| `date` | `Date` | `required / supplied by caller` |
| `evidence_ids` | `list[str]` | `Field(min_length=2)` |
| `interpretation` | `Literal['documented change; current use requires reconciliation']` | `'documented change; current use requires reconciliation'` |

### [Explanation](../../medical_assistant/models.py#L104)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `status` | `Literal['hypothesis']` | `'hypothesis'` |
| `possibility` | `str` | `Field(min_length=1)` |
| `supporting` | `list[Claim]` | `Field(min_length=1)` |
| `conflicting` | `list[Claim]` | `required / supplied by caller` |
| `uncertainty` | `str` | `Field(min_length=1)` |
| `clinician_may_consider` | `list[str]` | `Field(min_length=1)` |
| `reference_ids` | `list[str]` | `Field(default_factory=list)` |

#### [Explanation.no_confirmed_diagnosis](../../medical_assistant/models.py#L115)

`no_confirmed_diagnosis(cls, value)`

Static calls (including nested helper bodies): `field_validator`, `re.search`, `ValueError`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

### [SafetyFlag](../../medical_assistant/models.py#L123)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `urgency` | `Literal['urgent', 'prompt', 'unknown']` | `required / supplied by caller` |
| `text` | `str` | `Field(min_length=1)` |
| `evidence_ids` | `list[str]` | `Field(min_length=1)` |
| `escalation` | `str` | `Field(min_length=1)` |

### [Assessment](../../medical_assistant/models.py#L130)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `findings` | `list[Claim]` | `Field(default_factory=list)` |
| `medications` | `list[Medication]` | `Field(default_factory=list)` |
| `dose_changes` | `list[DoseChange]` | `Field(default_factory=list)` |
| `known_dates` | `dict[str, Date]` | `Field(default_factory=dict)` |
| `missing_dates` | `list[str]` | `Field(default_factory=list)` |
| `explanations` | `list[Explanation]` | `Field(default_factory=list)` |
| `safety_flags` | `list[SafetyFlag]` | `Field(default_factory=list)` |
| `missing_information` | `list[str]` | `Field(default_factory=list)` |
| `clinician_questions` | `list[str]` | `Field(default_factory=list)` |

#### [Assessment.validate_sources](../../medical_assistant/models.py#L141)

`validate_sources(self, record: PatientRecord) → 'Assessment'`

Static calls (including nested helper bodies): `list`, `self.known_dates.items`, `any`, `claims.extend`, `check`, `ValueError`, `entry.medication.name.casefold`, `change.name.casefold`, `order.name.casefold`, `medication.name.casefold`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [Assessment.validate_sources.check](../../medical_assistant/models.py#L144)

`check(ids, source_type=None)`

Static calls (including nested helper bodies): `any`, `ValueError`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

### [Review](../../medical_assistant/models.py#L229)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `approved` | `bool` | `Field(strict=True)` |
| `reviewer` | `str` | `Field(min_length=2, max_length=120)` |
| `clinician_attestation` | `bool` | `Field(strict=True)` |
| `draft_sha256` | `str` | `Field(pattern='^[a-f0-9]{64}$')` |
| `notes` | `str` | `Field(default='', max_length=8000)` |

#### [Review.must_attest](../../medical_assistant/models.py#L238)

`must_attest(cls, value)`

Static calls (including nested helper bodies): `field_validator`, `ValueError`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

### [ReportNote](../../medical_assistant/models.py#L246)

An attributed reviewer comment, separate from record facts and model output.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `reviewer` | `str` | `Field(min_length=2, max_length=120)` |
| `text` | `str` | `Field(max_length=600)` |

## [medical_assistant/nodule_exchange.py](../../medical_assistant/nodule_exchange.py)

Shared, ML-free MHCRA nodule exchange v2 validation and pixel rendering.

Vendored by MHCRA with only the contracts import rewritten; CI checks equality.
Hashes bind artifacts but do not authenticate producer execution or synthetic origin.

#### [byte_digest](../../medical_assistant/nodule_exchange.py#L38)

`byte_digest(payload)`

Static calls (including nested helper bodies): `hashlib.sha256(payload).hexdigest`, `hashlib.sha256`.

### [ExchangeArtifact](../../medical_assistant/nodule_exchange.py#L42)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `path` | `str` | `required / supplied by caller` |
| `role` | `Literal['source_volume', 'source_preview', 'overlay_preview', 'producer_report']` | `required / supplied by caller` |
| `sha256` | `str` | `Field(pattern='^[a-f0-9]{64}$')` |
| `size_bytes` | `int` | `Field(gt=0, le=32 * 1024 ** 2, strict=True)` |
| `slice_index` | `int \| None` | `Field(default=None, ge=0, le=63, strict=True)` |

#### [ExchangeArtifact.safe_path](../../medical_assistant/nodule_exchange.py#L53)

`safe_path(cls, value)`

Static calls (including nested helper bodies): `field_validator`, `PurePosixPath(value).is_absolute`, `any`, `ValueError`, `len`, `PurePosixPath`, `value.split`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

### [PublicResearchSource](../../medical_assistant/nodule_exchange.py#L68)

Operator-declared public provenance, never a real patient-history link.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `dataset` | `str` | `Field(min_length=1, max_length=200)` |
| `source_url` | `str` | `Field(min_length=10, max_length=500, pattern='^https://')` |
| `license` | `str` | `Field(min_length=1, max_length=300)` |
| `research_subject_id` | `str` | `Field(min_length=1, max_length=100)` |
| `original_sha256` | `str` | `Field(pattern='^[a-f0-9]{64}$')` |
| `composite_case` | `Literal[True]` | `required / supplied by caller` |

#### [PublicResearchSource.explicit_composite](../../medical_assistant/nodule_exchange.py#L80)

`explicit_composite(cls, value)`

Static calls (including nested helper bodies): `field_validator`, `ValueError`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

### [NoduleBundle](../../medical_assistant/nodule_exchange.py#L88)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `schema_version` | `Literal['mhcra-lung-nodules-v2', 'lovisa-ct-research-v3']` | `required / supplied by caller` |
| `synthetic` | `bool` | `Field(strict=True)` |
| `research` | `PublicResearchSource \| None` | `None` |
| `original_study` | `Study \| None` | `None` |
| `crop_origin_zyx` | `tuple[int, int, int] \| None` | `None` |
| `inference_region_zyx` | `tuple[int, int, int, int, int, int] \| None` | `None` |
| `patient_id` | `Identifier` | `required / supplied by caller` |
| `study_id` | `Identifier` | `required / supplied by caller` |
| `job_id` | `str` | `Field(pattern='^[a-f0-9]{32}$')` |
| `acquisition_date` | `None` | `required / supplied by caller` |
| `processed_at` | `datetime` | `required / supplied by caller` |
| `status` | `Literal['pending_review', 'producer_reviewed']` | `required / supplied by caller` |
| `study` | `Study` | `required / supplied by caller` |
| `producer_review` | `Review \| None` | `required / supplied by caller` |
| `artifacts` | `list[ExchangeArtifact]` | `Field(min_length=6, max_length=130)` |

#### [NoduleBundle.consistent](../../medical_assistant/nodule_exchange.py#L106)

`consistent(self)`

Static calls (including nested helper bodies): `model_validator`, `self.verify_research_crop`, `ValueError`, `self.producer_review.verify`, `any`, `len`, `a.path.endswith`, `range`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [NoduleBundle.verify_research_crop](../../medical_assistant/nodule_exchange.py#L165)

`verify_research_crop(self)`

Bind a limited HU excerpt to exact original geometry and candidate coordinates.

Whole-source hashes record provenance; they do not authenticate a producer.
The consumer independently checks excerpt pixels/previews, not absent full scans.

Static calls (including nested helper bodies): `original.geometry.model_dump`, `geometry.update`, `np.array`, `ValueError`, `np.any`, `any`, `Geometry.model_validate`, `SourceSlice.model_validate`, `self.patient_id.startswith`, `min`, `tuple`, `dict`, `enumerate`, `np.all` (additional calls in source).

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [wire_pixels](../../medical_assistant/nodule_exchange.py#L240)

`wire_pixels(study, hu, index, *, calipers=())`

Portable NumPy-only source/box/caliper pixels; no font-version dependency.

Static calls (including nested helper bodies): `(np.clip((hu[index] + 1000) / 1400, 0, 1) * 255).astype`, `np.repeat`, `source.copy`, `ValueError`, `c.length_mm`, `np.array`, `np.floor(lo[1:]).astype`, `np.ceil(hi[1:]).astype`, `np.rint(np.linspace(a, b, count)).astype`, `np.clip`, `int`, `np.floor`, `np.ceil`, `math.ceil` (additional calls in source).

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [source_pixels](../../medical_assistant/nodule_exchange.py#L266)

`source_pixels(bundle, artifacts)`

Bound NPY header and exact payload before allocating source HU.

Static calls (including nested helper bodies): `next`, `io.BytesIO`, `np.lib.format.read_magic`, `readers[version]`, `np.load`, `ValueError`, `np.isfinite(hu).all`, `np.dtype`, `len`, `handle.tell`, `math.prod`, `np.isfinite`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [unique_object](../../medical_assistant/nodule_exchange.py#L294)

`unique_object(pairs)`

Static calls (including nested helper bodies): `ValueError`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [read_exchange](../../medical_assistant/nodule_exchange.py#L303)

`read_exchange(payload, patient_id)`

Validate bounded ZIP without extracting paths; all source/overlay pixels checked.

Static calls (including nested helper bodies): `ValueError`, `source_pixels`, `next`, `range`, `len`, `zipfile.ZipFile`, `z.infolist`, `any`, `z.read`, `NoduleBundle.model_validate`, `research_report`, `artifacts[report.path].decode`, `wire_pixels`, `io.BytesIO` (additional calls in source).

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

## [medical_assistant/nodule_models.py](../../medical_assistant/nodule_models.py)

Versioned immutable-by-convention records; all persisted data is revalidated.

### [Record](../../medical_assistant/nodule_models.py#L24)

Class contract is defined by the fields and methods below.

#### [digest](../../medical_assistant/nodule_models.py#L28)

`digest(value) → str`

Canonical content identity; consistency check, not source authenticity.

Static calls (including nested helper bodies): `isinstance`, `value.model_dump`, `hashlib.sha256`, `json.dumps`.

### [Geometry](../../medical_assistant/nodule_models.py#L39)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `shape_zyx` | `tuple[StrictInt, StrictInt, StrictInt]` | `required / supplied by caller` |
| `spacing_zyx_mm` | `tuple[float, float, float]` | `required / supplied by caller` |
| `origin_lps_mm` | `tuple[float, float, float]` | `required / supplied by caller` |
| `direction_lps` | `tuple[float, ...]` | `required / supplied by caller` |

#### [Geometry.valid_geometry](../../medical_assistant/nodule_models.py#L46)

`valid_geometry(self)`

Static calls (including nested helper bodies): `model_validator`, `np.array(self.direction_lps).reshape`, `ValueError`, `min`, `max`, `np.prod`, `len`, `np.array`, `np.allclose`, `np.isclose`, `np.eye`, `np.linalg.det`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [Geometry.to_lps](../../medical_assistant/nodule_models.py#L62)

`to_lps(self, points_zyx)`

Map source voxel centers to physical LPS millimetres, including obliquity.

Static calls (including nested helper bodies): `np.asarray`, `np.array(self.direction_lps).reshape`, `np.array`.

#### [Geometry.from_lps](../../medical_assistant/nodule_models.py#L69)

`from_lps(self, points_lps)`

Static calls (including nested helper bodies): `np.array(self.direction_lps).reshape`, `np.asarray`, `np.array`.

### [SourceSlice](../../medical_assistant/nodule_models.py#L76)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `index` | `Annotated[StrictInt, Field(ge=0)]` | `required / supplied by caller` |
| `sha256` | `Digest` | `required / supplied by caller` |
| `sop_uid_sha256` | `Digest` | `required / supplied by caller` |

### [Candidate](../../medical_assistant/nodule_models.py#L82)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `candidate_id` | `Identifier` | `required / supplied by caller` |
| `box_zyx` | `tuple[float, float, float, float, float, float]` | `required / supplied by caller` |
| `score` | `Annotated[float, Field(ge=0, le=1)]` | `required / supplied by caller` |
| `kind` | `Literal['model_candidate']` | `'model_candidate'` |

#### [Candidate.ordered_box](../../medical_assistant/nodule_models.py#L89)

`ordered_box(self)`

Static calls (including nested helper bodies): `model_validator`, `np.any`, `ValueError`, `np.array`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

### [ModelProvenance](../../medical_assistant/nodule_models.py#L95)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `name` | `str` | `required / supplied by caller` |
| `checkpoint_sha256` | `Digest` | `required / supplied by caller` |
| `config_sha256` | `Digest` | `required / supplied by caller` |
| `execution_device` | `str` | `required / supplied by caller` |
| `software_versions` | `dict[str, str]` | `required / supplied by caller` |
| `synthetic_fixture` | `StrictBool` | `required / supplied by caller` |
| `score_threshold` | `Annotated[float, Field(ge=0, le=1)]` | `required / supplied by caller` |

### [Study](../../medical_assistant/nodule_models.py#L105)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `schema_version` | `Literal['lung-nodule-study-v1']` | `'lung-nodule-study-v1'` |
| `study_id` | `Identifier` | `required / supplied by caller` |
| `patient_alias` | `Identifier` | `required / supplied by caller` |
| `input_kind` | `Literal['generated-synthetic', 'approved-public-research']` | `required / supplied by caller` |
| `acquisition_date` | `None` | `None` |
| `source_sha256` | `Digest` | `required / supplied by caller` |
| `geometry` | `Geometry` | `required / supplied by caller` |
| `sources` | `Annotated[list[SourceSlice], Field(min_length=2, max_length=512)]` | `required / supplied by caller` |
| `model` | `ModelProvenance` | `required / supplied by caller` |
| `candidates` | `Annotated[list[Candidate], Field(max_length=300)]` | `required / supplied by caller` |
| `protocol_attestation` | `Literal['synthetic-phantom', 'adult-noncontrast-chest-complete', 'public-chest-protocol-unverified']` | `required / supplied by caller` |

#### [Study.consistent](../../medical_assistant/nodule_models.py#L123)

`consistent(self)`

Static calls (including nested helper bodies): `model_validator`, `ValueError`, `len`, `digest`, `list`, `set`, `np.any`, `range`, `self.geometry.model_dump`, `min`, `s.model_dump`, `np.array`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

### [Caliper](../../medical_assistant/nodule_models.py#L158)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `start_zyx` | `tuple[float, float, float]` | `required / supplied by caller` |
| `end_zyx` | `tuple[float, float, float]` | `required / supplied by caller` |

#### [Caliper.length_mm](../../medical_assistant/nodule_models.py#L162)

`length_mm(self, geometry)`

Static calls (including nested helper bodies): `np.array`, `float`, `np.any`, `ValueError`, `np.linalg.norm`, `np.isclose`, `int`, `np.diff`, `geometry.to_lps`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

### [Decision](../../medical_assistant/nodule_models.py#L177)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `candidate_id` | `Identifier` | `required / supplied by caller` |
| `decision` | `Literal['accept', 'reject', 'uncertain']` | `required / supplied by caller` |
| `caliper` | `Caliper \| None` | `None` |

### [Review](../../medical_assistant/nodule_models.py#L183)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `schema_version` | `Literal['lung-nodule-review-v1']` | `'lung-nodule-review-v1'` |
| `study_digest` | `Digest` | `required / supplied by caller` |
| `reviewer` | `Annotated[str, Field(min_length=1, max_length=100, pattern='^[^\\r\\n]+$')]` | `required / supplied by caller` |
| `qualified_reviewer_attestation` | `Literal[True]` | `required / supplied by caller` |
| `decisions` | `list[Decision]` | `required / supplied by caller` |
| `approved` | `Literal[True]` | `required / supplied by caller` |

#### [Review.literal_booleans](../../medical_assistant/nodule_models.py#L193)

`literal_booleans(cls, value)`

Static calls (including nested helper bodies): `model_validator`, `isinstance`, `any`, `ValueError`, `value.get`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [Review.verify](../../medical_assistant/nodule_models.py#L203)

`verify(self, study)`

Static calls (including nested helper bodies): `any`, `digest`, `ValueError`, `sorted`, `decision.caliper.length_mm`, `next`, `np.array`, `np.any`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [research_report](../../medical_assistant/nodule_models.py#L235)

`research_report(study, review)`

Compose only approved, structured observations; no LLM or cancer inference.

Static calls (including nested helper bodies): `review.verify`, `'\n'.join`, `study.geometry.to_lps`, `range`, `np.array`, `int`, `lines.append`, `html.escape`, `len`, `np.floor`, `digest`, `np.ceil`, `decision.caliper.length_mm`.

## [medical_assistant/nodule_support.py](../../medical_assistant/nodule_support.py)

Typed nodule review binding; does not change clinical facts or safety routing.

#### [is_nodule](../../medical_assistant/nodule_support.py#L12)

`is_nodule(manifest)`

Static calls (including nested helper bodies): `manifest.get`.

#### [checked_nodule_review](../../medical_assistant/nodule_support.py#L19)

`checked_nodule_review(manifest, review, *, reviewer=None)`

Static calls (including nested helper bodies): `NoduleBundle.model_validate`, `NoduleReview.model_validate`, `value.verify`, `PermissionError`, `isinstance`, `review.model_dump`.

Explicit raised conditions: `PermissionError`. See source for triggers; called validators may raise additional exceptions.

#### [imaging_acceptance_digest](../../medical_assistant/nodule_support.py#L32)

`imaging_acceptance_digest(proposal, nodule_review=None, *, endo_review=None)`

Static calls (including nested helper bodies): `is_endoscopy`, `checked_nodule_review`, `structured_digest`, `endo_acceptance_digest`, `ValueError`, `is_nodule`, `value.model_dump`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [verify_nodule_snapshot](../../medical_assistant/nodule_support.py#L58)

`verify_nodule_snapshot(snapshot)`

Static calls (including nested helper bodies): `is_endoscopy`, `checked_nodule_review`, `verify_endo_snapshot`, `is_nodule`, `snapshot.get`, `imaging_acceptance_digest`, `ValueError`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

## [medical_assistant/nodule_ui.py](../../medical_assistant/nodule_ui.py)

Nodule source inspection and typed candidate/caliper controls; no inference.

#### [pixels_for](../../medical_assistant/nodule_ui.py#L16)

`pixels_for(manifest, path_for)`

Static calls (including nested helper bodies): `NoduleBundle.model_validate`, `next`, `source_pixels`, `path_for('source_volume', None).read_bytes`, `path_for`.

#### [nodule_viewer](../../medical_assistant/nodule_ui.py#L24)

`nodule_viewer(manifest, path_for, key, *, review=None)`

Static calls (including nested helper bodies): `NoduleBundle.model_validate`, `st.caption`, `st.selectbox`, `next`, `st.slider`, `st.columns`, `left.image`, `st.warning`, `int`, `str`, `right.image`, `pixels_for`, `NoduleReview.model_validate`, `parsed.verify` (additional calls in source).

#### [candidate_controls](../../medical_assistant/nodule_ui.py#L82)

`candidate_controls(manifest, key, *, false_positive=None)`

Return typed local choices; nothing is persisted or approved by these controls.

Static calls (including nested helper bodies): `NoduleBundle.model_validate`, `st.write`, `previous.get`, `st.radio`, `st.checkbox`, `decisions.append`, `st.caption`, `st.columns`, `columns[0].number_input`, `zip`, `Caliper`, `Decision`, `bool`, `values.append` (additional calls in source).

#### [build_nodule_review](../../medical_assistant/nodule_ui.py#L174)

`build_nodule_review(manifest, decisions, reviewer, attested)`

Static calls (including nested helper bodies): `NoduleBundle.model_validate`, `NoduleReview`, `value.verify`, `digest`.

#### [preview_calipers](../../medical_assistant/nodule_ui.py#L187)

`preview_calipers(manifest, path_for, decisions)`

Static calls (including nested helper bodies): `pixels_for`, `caliper.length_mm`, `int`, `wire_pixels`, `st.image`.

## [medical_assistant/ollama_client.py](../../medical_assistant/ollama_client.py)

Ollama HTTP adapter: fixed loopback, no proxies, redirects, or cloud models.

### [OllamaClient](../../medical_assistant/ollama_client.py#L14)

Class contract is defined by the fields and methods below.

#### [OllamaClient.__init__](../../medical_assistant/ollama_client.py#L15)

`__init__(self, model: str='gemma4:e2b', *, transport=None)`

Static calls (including nested helper bodies): `httpx.Client`, `ValueError`, `re.fullmatch`, `model.lower`, `httpx.Timeout`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [OllamaClient.close](../../medical_assistant/ollama_client.py#L35)

`close(self)`

Static calls (including nested helper bodies): `self.http.close`.

#### [OllamaClient._post](../../medical_assistant/ollama_client.py#L38)

`_post(self, path: str, body: dict) → dict`

Static calls (including nested helper bodies): `min`, `response.raise_for_status`, `response.json`, `TimeoutError`, `self.http.post`, `time.monotonic`, `httpx.Timeout`.

Explicit raised conditions: `TimeoutError`. See source for triggers; called validators may raise additional exceptions.

#### [OllamaClient.ensure_local](../../medical_assistant/ollama_client.py#L58)

`ensure_local(self)`

Static calls (including nested helper bodies): `self._post`, `any`, `details.get('details', {}).get`, `ValueError`, `details.get`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [OllamaClient.assess](../../medical_assistant/ollama_client.py#L69)

`assess(self, system: str, user: str, *, schema: dict \| None=None) → Assessment`

Static calls (including nested helper bodies): `self.ensure_local`, `self._post`, `json.loads`, `Assessment.model_json_schema`, `output_schema.get`, `prepare`, `len`, `ValueError`, `time.monotonic`, `result.get`, `expand`, `Assessment.model_validate`, `(system + user + json.dumps(output_schema)).encode`, `json.dumps`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

## [medical_assistant/producer_signature.py](../../medical_assistant/producer_signature.py)

Ed25519 producer signatures for LOVISA review ZIPs.

This file is copied byte-for-byte into the CT companion, the endoscopy companion
and LOVISA; keep it self-contained. A valid signature from a pinned key shows that
the holder of that private key exported these exact ``bundle.json`` bytes, which
in turn hash-bind every artifact. It does not prove model correctness, data
permission, clinical truth or the signer's qualifications. Research use only.

### [Record](../../medical_assistant/producer_signature.py#L30)

Class contract is defined by the fields and methods below.

### [Performance](../../medical_assistant/producer_signature.py#L34)

Producer-declared evaluation of the exact model; shown beside candidates.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `measured` | `bool` | `required / supplied by caller` |
| `metric` | `str` | `Field(min_length=1, max_length=200)` |
| `false_positive_fraction` | `float \| None` | `Field(default=None, ge=0, le=1)` |
| `test_images` | `int \| None` | `Field(default=None, ge=1, strict=True)` |
| `negative_images` | `int \| None` | `Field(default=None, ge=0, strict=True)` |
| `evaluation_sha256` | `str \| None` | `Field(default=None, pattern='^[a-f0-9]{64}$')` |
| `limitations` | `str` | `Field(min_length=1, max_length=600)` |

#### [Performance.complete](../../medical_assistant/producer_signature.py#L46)

`complete(self)`

Static calls (including nested helper bodies): `model_validator`, `any`, `ValueError`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

### [Claims](../../medical_assistant/producer_signature.py#L62)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `schema_version` | `Literal['lovisa-producer-signature-v1']` | `required / supplied by caller` |
| `producer` | `Producer` | `required / supplied by caller` |
| `bundle_sha256` | `str` | `Hex64` |
| `key_id` | `str` | `Hex64` |
| `signed_at` | `datetime` | `required / supplied by caller` |
| `performance` | `Performance` | `required / supplied by caller` |

### [Envelope](../../medical_assistant/producer_signature.py#L71)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `claims` | `Claims` | `required / supplied by caller` |
| `signature_b64` | `str` | `Field(min_length=80, max_length=100)` |

### [Check](../../medical_assistant/producer_signature.py#L76)

Result of checking an archive against locally pinned producer keys.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `status` | `Literal['verified', 'unsigned', 'untrusted-key']` | `required / supplied by caller` |
| `producer` | `Producer \| None` | `None` |
| `key_id` | `str \| None` | `None` |
| `label` | `str \| None` | `None` |
| `performance` | `Performance \| None` | `None` |

#### [canonical](../../medical_assistant/producer_signature.py#L86)

`canonical(value) → bytes`

Static calls (including nested helper bodies): `isinstance`, `value.model_dump`, `json.dumps`.

#### [key_id](../../medical_assistant/producer_signature.py#L92)

`key_id(public_raw: bytes) → str`

Static calls (including nested helper bodies): `hashlib.sha256(public_raw).hexdigest`, `hashlib.sha256`.

#### [_crypto](../../medical_assistant/producer_signature.py#L96)

`_crypto()`

Static calls (including nested helper bodies): `ValueError`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [_public_raw](../../medical_assistant/producer_signature.py#L106)

`_public_raw(public_key) → bytes`

Static calls (including nested helper bodies): `_crypto`, `public_key.public_bytes`.

#### [generate_key](../../medical_assistant/producer_signature.py#L113)

`generate_key(path) → dict`

Create a new owner-only PKCS8 private key file; never overwrite an existing one.

Static calls (including nested helper bodies): `_crypto`, `ed25519.Ed25519PrivateKey.generate`, `private.private_bytes`, `Path`, `path.parent.mkdir`, `os.open`, `public_info`, `serialization.NoEncryption`, `os.fdopen`, `handle.write`, `private.public_key`.

#### [public_info](../../medical_assistant/producer_signature.py#L130)

`public_info(public_key) → dict`

Static calls (including nested helper bodies): `_public_raw`, `key_id`, `base64.b64encode(raw).decode`, `base64.b64encode`.

#### [load_private_key](../../medical_assistant/producer_signature.py#L135)

`load_private_key(path)`

Static calls (including nested helper bodies): `_crypto`, `Path`, `serialization.load_pem_private_key`, `ValueError`, `path.read_bytes`, `isinstance`, `TypeError`, `stat.S_IMODE`, `path.stat`.

Explicit raised conditions: `TypeError`, `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [sign_archive](../../medical_assistant/producer_signature.py#L146)

`sign_archive(payload: bytes, private_key, producer, performance=NOT_MEASURED) → bytes`

Return the same archive with an added signature over bundle.json and claims.

Static calls (including nested helper bodies): `Claims`, `Envelope`, `io.BytesIO`, `stream.getvalue`, `zipfile.ZipFile`, `archive.infolist`, `dict`, `archive.writestr`, `archive.namelist`, `ValueError`, `entries.append`, `hashlib.sha256(bundle).hexdigest`, `datetime.now`, `Performance.model_validate` (additional calls in source).

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [_unique](../../medical_assistant/producer_signature.py#L175)

`_unique(pairs)`

Static calls (including nested helper bodies): `ValueError`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [check_archive](../../medical_assistant/producer_signature.py#L184)

`check_archive(payload: bytes, trusted: dict) → Check`

Check a signature against ``{key_id: {"producer", "public_key_b64", "label"}}``.

Unsigned archives and signatures from unpinned keys are reported, not trusted;
callers decide whether to accept them. A present signature that is malformed,
does not match bundle.json, names the wrong producer or fails verification
raises ValueError.

Static calls (including nested helper bodies): `_crypto`, `trusted.get`, `base64.b64decode`, `Check`, `hashlib.sha256(bundle).hexdigest`, `ValueError`, `ed25519.Ed25519PublicKey.from_public_bytes(raw).verify`, `zipfile.ZipFile`, `archive.namelist`, `archive.getinfo`, `Envelope.model_validate`, `archive.read`, `key_id`, `canonical` (additional calls in source).

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

## [medical_assistant/producer_trust.py](../../medical_assistant/producer_trust.py)

Locally pinned producer public keys and the signature acceptance policy.

The trust file is local configuration outside Git (default
``data/trust/producer_keys.json``, or ``LOVISA_TRUSTED_PRODUCER_KEYS``). Public
keys are not secret, but pinning one is a decision to trust its holder. Research
use only; a verified signature does not establish model accuracy.

### [PinnedKey](../../medical_assistant/producer_trust.py#L24)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `producer` | `Literal['lovisa-ct', 'lovisa-endo']` | `required / supplied by caller` |
| `public_key_b64` | `str` | `Field(min_length=40, max_length=60)` |
| `label` | `str` | `Field(min_length=1, max_length=80)` |

### [TrustConfig](../../medical_assistant/producer_trust.py#L31)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `require_signature` | `bool` | `False` |
| `keys` | `list[PinnedKey]` | `Field(default_factory=list, max_length=32)` |

#### [TrustConfig.trusted](../../medical_assistant/producer_trust.py#L36)

`trusted(self) → dict`

Static calls (including nested helper bodies): `base64.b64decode`, `key.model_dump`, `len`, `ValueError`, `key_id`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [trust_path](../../medical_assistant/producer_trust.py#L46)

`trust_path(path=None) → Path`

Static calls (including nested helper bodies): `Path`, `os.environ.get`.

#### [load_trust](../../medical_assistant/producer_trust.py#L50)

`load_trust(path=None) → TrustConfig`

Missing file means no pinned keys and signatures not required.

Static calls (including nested helper bodies): `trust_path`, `TrustConfig.model_validate_json`, `path.exists`, `TrustConfig`, `path.read_text`.

#### [verify_producer](../../medical_assistant/producer_trust.py#L58)

`verify_producer(payload: bytes, config: TrustConfig) → Check`

Fail closed on bad signatures; enforce ``require_signature`` when set.

Static calls (including nested helper bodies): `check_archive`, `config.trusted`, `ValueError`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [pin](../../medical_assistant/producer_trust.py#L68)

`pin(path, producer, public_key_b64, label)`

Static calls (including nested helper bodies): `trust_path`, `load_trust`, `PinnedKey`, `config.model_copy`, `updated.trusted`, `path.parent.mkdir`, `path.write_text`, `ValueError`, `updated.model_dump_json`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [main](../../medical_assistant/producer_trust.py#L81)

`main(argv=None)`

Static calls (including nested helper bodies): `argparse.ArgumentParser`, `p.add_argument`, `p.parse_args`, `pin`, `print`, `len`, `trust_path`.

## [medical_assistant/producer_ui.py](../../medical_assistant/producer_ui.py)

Show producer-signature status and declared false-positive rates beside review controls.

#### [signature_notice](../../medical_assistant/producer_ui.py#L11)

`signature_notice(proposal)`

Render the producer signature status recorded when the archive was prepared.

Static calls (including nested helper bodies): `proposal.get`, `st.success`, `st.warning`.

#### [false_positive_text](../../medical_assistant/producer_ui.py#L28)

`false_positive_text(proposal)`

Plain-language false-positive statement shown next to every candidate.

Static calls (including nested helper bodies): `proposal.get`, `check.get`.

## [medical_assistant/reasoning_constraints.py](../../medical_assistant/reasoning_constraints.py)

Limited synthetic hypothesis selection, not general clinical reasoning.

The local LLM selects from this transparent catalog. Exact record text remains
untrusted quoted evidence; these constraints do not clinically validate a cause,
identify emergencies, or establish that a selected source supports causation.

#### [eligible_labels](../../medical_assistant/reasoning_constraints.py#L36)

`eligible_labels(record: PatientRecord) → list[str]`

Static calls (including nested helper bodies): `any`, `labels.append`, `re.search`.

#### [constrain_schema](../../medical_assistant/reasoning_constraints.py#L45)

`constrain_schema(schema: dict, record: PatientRecord, reference_ids: list[str]) → dict`

Constrain both narrative vocabulary and evidence before generation.

Static calls (including nested helper bodies): `eligible_labels`, `list`, `schema['$defs'].items`.

#### [validate_reasoning](../../medical_assistant/reasoning_constraints.py#L75)

`validate_reasoning(assessment: Assessment, record: PatientRecord, reference_ids: set[str]) → None`

Reject off-catalog model text even if a transport ignores the schema.

Static calls (including nested helper bodies): `any`, `eligible_labels`, `ValueError`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

## [medical_assistant/report.py](../../medical_assistant/report.py)

Concise source-bound summaries; detailed provenance stays in the evidence package.

#### [digest](../../medical_assistant/report.py#L17)

`digest(text: str) → str`

Static calls (including nested helper bodies): `hashlib.sha256(text.encode('utf-8')).hexdigest`, `hashlib.sha256`, `text.encode`.

#### [inline_text](../../medical_assistant/report.py#L21)

`inline_text(value) → str`

Render untrusted data as one literal Markdown line, never active markup.

Original quotations remain untouched in source storage. Presentation folds
whitespace so a record cannot add headings, lists or reference definitions.
Ordinary filename underscores stay readable; intraword underscores cannot
open CommonMark emphasis. HTML, links, images and code delimiters are escaped.

Static calls (including nested helper bodies): `html.escape`, `re.sub`, `' '.join`, `str(value).split`, `str`.

#### [evidence_index](../../medical_assistant/report.py#L34)

`evidence_index(record, outputs, imaging=None)`

Keep every exact source excerpt and selected evidence link outside the short prose.

Static calls (including nested helper bodies): `Assessment.model_validate(value).validate_sources`, `outputs.items`, `is_endoscopy`, `Assessment.model_validate`, `list`, `e.date.isoformat`, `dict.fromkeys`.

#### [ct_summary](../../medical_assistant/report.py#L89)

`ct_summary(imaging)`

Short inspected result; exact source/model/coverage evidence stays bound separately.

Static calls (including nested helper bodies): `any`, `parts.append`, `' '.join`, `verify_nodule_snapshot`, `results.append`, `sum`, `len`, `summarize`, `is_endoscopy`, `review.model_dump`, `', '.join`.

#### [endoscopy_summary](../../medical_assistant/report.py#L134)

`endoscopy_summary(imaging)`

Keep the report focused on inspected regions rather than model metadata.

Static calls (including nested helper bodies): `sum`, `summarize_endo`, `is_endoscopy`, `verify_endo_snapshot(s).model_dump`, `verify_endo_snapshot`.

#### [summary_parts](../../medical_assistant/report.py#L151)

`summary_parts(record, outputs, imaging=None, clinician_note=None)`

Plain-text report blocks shared by Markdown and portable HTML presentation.

Static calls (including nested helper bodies): `list`, `' '.join`, `any`, `endoscopy_summary`, `Assessment.model_validate(value).validate_sources`, `dict.fromkeys`, `gaps.append`, `ReportNote.model_validate`, `parts.insert`, `outputs.items`, `'; '.join`, `len`, `ct_summary`, `followup.strip` (additional calls in source).

#### [compose](../../medical_assistant/report.py#L230)

`compose(record: PatientRecord, source_file: str, outputs: dict[str, dict], evidence=None, imaging=None, clinician_note=None) → str`

One concise section; full exact excerpts/citations remain in report_evidence and originals.

Static calls (including nested helper bodies): `summary_parts`, `'\n\n'.join`, `inline_text`.

## [medical_assistant/report_assets.py](../../medical_assistant/report_assets.py)

Verified representative CT images and self-contained, approval-gated HTML reports.

### [InspectionFigure](../../medical_assistant/report_assets.py#L18)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `caption` | `str` | `required / supplied by caller` |
| `source_png` | `bytes` | `required / supplied by caller` |
| `overlay_png` | `bytes` | `required / supplied by caller` |
| `source_label` | `str` | `'Source CT'` |
| `annotation_label` | `str` | `'Reviewed CT annotation'` |

#### [inspection_figures](../../medical_assistant/report_assets.py#L26)

`inspection_figures(state, store)`

Render at most three representative study slices, never omit summary counts.

Static calls (including nested helper bodies): `state.get`, `any`, `store.verify`, `enumerate`, `ValueError`, `store.preview_resolver`, `is_endoscopy`, `figures.append`, `verify_endo_snapshot`, `resolve('overlay_preview', 0).read_bytes`, `is_nodule`, `InspectionFigure`, `NoduleBundle.model_validate`, `verify_nodule_snapshot` (additional calls in source).

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [portable_html](../../medical_assistant/report_assets.py#L102)

`portable_html(payload, *, auth, safety=None)`

Final download with embedded verified CT pictures; no scripts, external assets or draft export.

Static calls (including nested helper bodies): `validate_reviewed_report`, `inspection_figures`, `summary_parts`, `''.join`, `ImagingStore`, `payload.get`, `images.append`, `len`, `html.escape`, `base64.b64encode(data).decode`, `base64.b64encode`.

## [medical_assistant/report_binding.py](../../medical_assistant/report_binding.py)

Bind approval to hidden evidence/images as well as simplified visible report text.

#### [content_digest](../../medical_assistant/report_binding.py#L8)

`content_digest(state)`

Stable clinical content only; mutable workflow/review bookkeeping is excluded.

Static calls (including nested helper bodies): `digest`, `json.dumps`, `state.get`.

#### [verify_content_binding](../../medical_assistant/report_binding.py#L36)

`verify_content_binding(state, receipt, auth, reviewer)`

Static calls (including nested helper bodies): `auth.verify_receipt`, `content_digest`, `PermissionError`.

Explicit raised conditions: `PermissionError`. See source for triggers; called validators may raise additional exceptions.

## [medical_assistant/report_notes.py](../../medical_assistant/report_notes.py)

Authenticate report-note authorship without treating commentary as clinical facts.

#### [verify_note](../../medical_assistant/report_notes.py#L7)

`verify_note(state, auth)`

Static calls (including nested helper bodies): `state.get`, `ReportNote.model_validate`, `auth.verify_receipt`, `digest`, `PermissionError`, `ValueError`, `value.model_dump_json`.

Explicit raised conditions: `PermissionError`, `ValueError`. See source for triggers; called validators may raise additional exceptions.

## [medical_assistant/research_examples.py](../../medical_assistant/research_examples.py)

Read a local, bounded public-research upload kit; never downloads or approves.

#### [_manifest](../../medical_assistant/research_examples.py#L13)

`_manifest(root=None)`

Static calls (including nested helper bodies): `json.loads`, `path.is_symlink`, `ValueError`, `path.read_text`, `isinstance`, `any`, `Path`, `data.get`, `path.stat`, `data['ct'].keys`, `len`, `os.environ.get`, `r.keys`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [_read](../../medical_assistant/research_examples.py#L43)

`_read(root, name, expected, limit)`

Static calls (including nested helper bodies): `path.read_bytes`, `ValueError`, `path.is_symlink`, `hashlib.sha256(raw).hexdigest`, `isinstance`, `Path`, `path.stat`, `hashlib.sha256`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [example_bundle](../../medical_assistant/research_examples.py#L60)

`example_bundle(modality, patient, *, root=None, index=0)`

Load only the requested modality/case; full archive verification follows at import.

Static calls (including nested helper bodies): `_manifest`, `_read`, `ValueError`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [matching_endoscopy](../../medical_assistant/research_examples.py#L69)

`matching_endoscopy(raw, patient, *, root=None)`

Recognise the exact permitted demo source bytes without guessing dataset provenance.

Static calls (including nested helper bodies): `_manifest`, `hashlib.sha256(raw).hexdigest`, `ValueError`, `len`, `hashlib.sha256`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

## [medical_assistant/runtime.py](../../medical_assistant/runtime.py)

Shared local authentication service; patient/case state stays session-scoped.

#### [get_services](../../medical_assistant/runtime.py#L9)

`get_services()`

Static calls (including nested helper bodies): `seed`, `LocalAuth`.

## [medical_assistant/safety.py](../../medical_assistant/safety.py)

Deterministic safety agent. No model response can modify this policy result.

### [SafetyPolicy](../../medical_assistant/safety.py#L17)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `version` | `str` | `Field(min_length=1)` |
| `purpose` | `str` | `Field(min_length=1)` |
| `require_current_warning_screen` | `Literal[True]` | `required / supplied by caller` |
| `require_current_blood_pressure` | `Literal[True]` | `required / supplied by caller` |
| `screen_max_age_days` | `int` | `Field(ge=0, le=1)` |
| `reported_warning_action` | `Literal['urgent_human_review_stop']` | `required / supplied by caller` |
| `missing_information_action` | `Literal['uncertain_human_review_pause']` | `required / supplied by caller` |
| `model_may_override` | `Literal[False]` | `required / supplied by caller` |

### [SafetyAgent](../../medical_assistant/safety.py#L28)

Class contract is defined by the fields and methods below.

#### [SafetyAgent.__init__](../../medical_assistant/safety.py#L29)

`__init__(self, policy_path: Path=POLICY_PATH)`

#### [SafetyAgent.evaluate](../../medical_assistant/safety.py#L32)

`evaluate(self, record: PatientRecord, *, as_of: date \| None=None)`

Static calls (including nested helper bodies): `self.policy_path.read_text`, `SafetyPolicy.model_validate_json`, `any`, `Assessment`, `digest`, `datetime.now(ZoneInfo('Europe/Amsterdam')).date`, `flags.append`, `missing.append`, `as_of.isoformat`, `assessment.model_dump`, `json.dumps`, `SafetyFlag`, `record.model_dump_json`, `datetime.now` (additional calls in source).

## [medical_assistant/storage.py](../../medical_assistant/storage.py)

Read explicitly selected local JSON records; atomically save reviewed reports.

#### [load_record](../../medical_assistant/storage.py#L17)

`load_record(path: Path) → PatientRecord`

Static calls (including nested helper bodies): `PatientRecord.model_validate_json`, `ValueError`, `path.read_text`, `sum`, `path.stat`, `len`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [validate_reviewed_report](../../medical_assistant/storage.py#L26)

`validate_reviewed_report(payload: dict, *, auth, safety=None)`

Recheck approval, sources, note authorship and CT integrity before any final export.

Static calls (including nested helper bodies): `Review.model_validate`, `validate_record_grounding`, `auth.verify_receipt`, `verify_content_binding`, `payload.get`, `verify_note`, `compose`, `(safety or SafetyAgent()).evaluate`, `ValueError`, `PatientRecord.model_validate`, `digest`, `any`, `ImagingStore(auth.path).verify`, `evidence_index` (additional calls in source).

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [save_report](../../medical_assistant/storage.py#L112)

`save_report(payload: dict, directory: Path=REPORT_DIR, *, auth=None, safety=None) → Path`

Static calls (including nested helper bodies): `validate_reviewed_report`, `directory.mkdir`, `tempfile.mkstemp`, `os.replace`, `os.path.exists`, `os.fdopen`, `json.dump`, `os.unlink`, `uuid4`.

## [medical_assistant/ui/__init__.py](../../medical_assistant/ui/__init__.py)

Local LOVISA design system and review interfaces; no inference in components.

## [medical_assistant/ui/clinical.py](../../medical_assistant/ui/clinical.py)

Responsive clinical UI; only explicit human actions issue review receipts.

#### [make_review](../../medical_assistant/ui/clinical.py#L30)

`make_review(approved, user, checked, notes, sha256)`

Static calls (including nested helper bodies): `Review`.

#### [start_task](../../medical_assistant/ui/clinical.py#L40)

`start_task(path, auth, patient_id, model, *, review=None, token=None)`

Static calls (including nested helper bodies): `WorkTask`, `ollama_client.OllamaClient`, `MedicalHistoryOrchestrator`, `BudgetInference`, `progress`, `workflow.start_patient`, `budget.check`, `workflow.acknowledge_safety`, `client.close`, `next`.

#### [start_task.run](../../medical_assistant/ui/clinical.py#L41)

`run(progress, budget)`

Static calls (including nested helper bodies): `ollama_client.OllamaClient`, `MedicalHistoryOrchestrator`, `BudgetInference`, `progress`, `workflow.start_patient`, `budget.check`, `workflow.acknowledge_safety`, `client.close`, `next`.

#### [resume_task](../../medical_assistant/ui/clinical.py#L69)

`resume_task(workflow, case, review, token)`

Static calls (including nested helper bodies): `WorkTask`, `BudgetInference`, `progress`, `workflow.acknowledge_safety`, `budget.check`, `budget.stopped.is_set`, `original.close`.

#### [resume_task.run](../../medical_assistant/ui/clinical.py#L70)

`run(progress, budget)`

Static calls (including nested helper bodies): `BudgetInference`, `progress`, `workflow.acknowledge_safety`, `budget.check`, `budget.stopped.is_set`, `original.close`.

#### [collect_task](../../medical_assistant/ui/clinical.py#L86)

`collect_task()`

Publish only a completed, in-budget result into this Streamlit session.

Static calls (including nested helper bodies): `st.session_state.get`, `task.snapshot`, `round`, `task.result`, `st.session_state.pop`, `workflow.state`.

#### [task_progress](../../medical_assistant/ui/clinical.py#L108)

`task_progress()`

Static calls (including nested helper bodies): `st.fragment`, `st.session_state.get`, `task.snapshot`, `st.info`, `st.caption`, `st.button`, `st.rerun`, `task.cancel`.

#### [background_progress](../../medical_assistant/ui/clinical.py#L125)

`background_progress()`

Keep completion responsive when the reviewer opens a different view.

Static calls (including nested helper bodies): `st.fragment`, `st.session_state.get`, `st.caption`, `st.rerun`, `task.snapshot`.

#### [generate_task](../../medical_assistant/ui/clinical.py#L136)

`generate_task(workflow, case, token)`

Static calls (including nested helper bodies): `WorkTask`, `BudgetInference`, `progress`, `workflow.continue_analysis`, `budget.check`, `budget.stopped.is_set`, `original.close`.

#### [generate_task.run](../../medical_assistant/ui/clinical.py#L137)

`run(progress, budget)`

Static calls (including nested helper bodies): `BudgetInference`, `progress`, `workflow.continue_analysis`, `budget.check`, `budget.stopped.is_set`, `original.close`.

#### [bottom_actions](../../medical_assistant/ui/clinical.py#L153)

`bottom_actions(path, auth, record, model, token, user, decision)`

Safety first, then one explicit bottom-of-page generation action.

Static calls (including nested helper bodies): `st.subheader`, `st.caption`, `st.session_state.get`, `state.get`, `bool`, `st.button`, `st.session_state.workflow.state`, `job_pending`, `task_progress`, `st.error`, `auth.require`, `generate_task`, `st.rerun`, `failure` (additional calls in source).

#### [failure](../../medical_assistant/ui/clinical.py#L311)

`failure()`

Static calls (including nested helper bodies): `st.error`, `st.session_state.get`, `st.caption`, `error_message`.

#### [new_report_with_ct](../../medical_assistant/ui/clinical.py#L323)

`new_report_with_ct()`

Static calls (including nested helper bodies): `clear_patient`, `go_to`.

#### [report_content](../../medical_assistant/ui/clinical.py#L328)

`report_content(state, workflow)`

Short summary and verified representative CT images, with optional readable evidence.

Static calls (including nested helper bodies): `st.container`, `st.markdown`, `inspection_figures`, `state.get`, `st.button`, `st.expander`, `st.caption`, `st.columns`, `left.image`, `right.image`, `len`, `st.text`, `entry['source_type'].replace`.

#### [report_panel](../../medical_assistant/ui/clinical.py#L369)

`report_panel(auth, token, user, record, *, urgent=False)`

Static calls (including nested helper bodies): `st.session_state.get`, `workflow.state`, `state.get`, `empty`, `failure`, `st.error`, `st.info`, `st.session_state.pop`, `st.subheader`, `st.caption`, `st.button`, `st.success`, `workflow._verify_report`, `report_content` (additional calls in source).

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

## [medical_assistant/ui/components.py](../../medical_assistant/ui/components.py)

Reusable presentation components. Escape every source-derived HTML value.

#### [safe](../../medical_assistant/ui/components.py#L13)

`safe(value)`

Static calls (including nested helper bodies): `html.escape(str(value), quote=True).replace`, `html.escape`, `str`.

#### [styles](../../medical_assistant/ui/components.py#L17)

`styles()`

Static calls (including nested helper bodies): `st.html`, `Path(__file__).with_name('theme.css').read_text`, `Path(__file__).with_name`, `Path`.

#### [sidebar_brand](../../medical_assistant/ui/components.py#L21)

`sidebar_brand()`

Static calls (including nested helper bodies): `st.markdown`.

#### [header](../../medical_assistant/ui/components.py#L28)

`header()`

Static calls (including nested helper bodies): `st.columns`, `st.markdown`, `st.title`.

#### [patient_header](../../medical_assistant/ui/components.py#L47)

`patient_header(record, decision, *, safety_reviewed=False)`

Static calls (including nested helper bodies): `''.join((word[0] for word in record.display_name.split()[:2])).upper`, `st.markdown`, `''.join`, `sum`, `safe`, `record.display_name.split`.

#### [timeline](../../medical_assistant/ui/components.py#L78)

`timeline(record)`

Static calls (including nested helper bodies): `st.subheader`, `st.caption`, `sorted`, `st.markdown`, `sources.get`, `cards.append`, `e.date.strftime`, `''.join`, `safe`.

#### [medications](../../medical_assistant/ui/components.py#L100)

`medications(record)`

Static calls (including nested helper bodies): `MedicationAgent().run`, `st.subheader`, `st.caption`, `sorted`, `any`, `empty`, `st.info`, `MedicationAgent`, `st.markdown`, `st.expander`, `e.date.strftime`, `st.text`, `inline_text`, `safe` (additional calls in source).

#### [original_sources](../../medical_assistant/ui/components.py#L134)

`original_sources(record)`

Static calls (including nested helper bodies): `st.subheader`, `st.caption`, `st.expander`, `sorted`, `st.download_button`, `inline_text`, `st.text`, `entry.date.strftime`.

#### [empty](../../medical_assistant/ui/components.py#L166)

`empty(title, copy)`

Static calls (including nested helper bodies): `st.markdown`, `safe`.

#### [next_action](../../medical_assistant/ui/components.py#L173)

`next_action(state=None, *, urgent=False)`

Static calls (including nested helper bodies): `st.session_state.get`, `job_pending`, `is_endoscopy`, `state.get`.

#### [guide](../../medical_assistant/ui/components.py#L201)

`guide(view, state=None, *, running=False, signed_in=False)`

Static calls (including nested helper bodies): `st.markdown`, `enumerate`, `st.button`, `st.caption`.

#### [footer](../../medical_assistant/ui/components.py#L234)

`footer()`

Static calls (including nested helper bodies): `st.markdown`.

## [medical_assistant/ui/errors.py](../../medical_assistant/ui/errors.py)

Concise literal UI errors with bounded explanations and inert markup.

#### [error_message](../../medical_assistant/ui/errors.py#L8)

`error_message(error, *, limit=600)`

Escape an actionable bounded message; omit Pydantic inputs and help URLs.

Validation errors can echo arbitrary uploaded text. Keep field locations and
explanations, while original source content stays in its dedicated view.

Static calls (including nested helper bodies): `isinstance`, `' '.join`, `inline_text`, `error.errors`, `'; '.join`, `str`, `text.split`, `len`, `messages.append`, `'.'.join`, `map`.

## [medical_assistant/ui/history.py](../../medical_assistant/ui/history.py)

Human-approved history import UI; source data is never guessed or overwritten.

#### [history_ui](../../medical_assistant/ui/history.py#L17)

`history_ui(path, auth, token, user, record)`

Static calls (including nested helper bodies): `HistoryManagement`, `st.rerun`, `st.expander`, `st.file_uploader`, `st.button`, `st.caption`, `st.subheader`, `PatientRecord.model_validate`, `timeline`, `manager.pending.pop`, `ValueError`, `st.form`, `st.text_area`, `st.checkbox` (additional calls in source).

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [history_ui.replace_proposal](../../medical_assistant/ui/history.py#L22)

`replace_proposal(result)`

Static calls (including nested helper bodies): `st.rerun`, `manager.pending.pop`, `ValueError`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

## [medical_assistant/ui/imaging_actions.py](../../medical_assistant/ui/imaging_actions.py)

Reusable Upload / Analyze controls and visible local-worker errors.

#### [image_actions](../../medical_assistant/ui/imaging_actions.py#L10)

`image_actions(modality, store, auth, token, record)`

Static calls (including nested helper bodies): `st.session_state.get`, `bool`, `modes.update`, `st.container`, `st.selectbox`, `st.columns`, `blocker`, `image_progress`, `list`, `st.button`, `st.caption`, `st.info`, `st.warning`, `st.error` (additional calls in source).

#### [image_progress](../../medical_assistant/ui/imaging_actions.py#L117)

`image_progress(job, prefix)`

Static calls (including nested helper bodies): `st.fragment`, `st.info`, `st.caption`, `st.button`, `job.status`, `st.rerun`, `job.progress`, `job.cancel`.

## [medical_assistant/ui/navigation.py](../../medical_assistant/ui/navigation.py)

Patient-scoped UI lifecycle and fixed, source-independent navigation targets.

#### [reset_report_context](../../medical_assistant/ui/navigation.py#L20)

`reset_report_context(state)`

Release only the current draft context; retain uploads and accepted studies.

Persisted reports and workflow checkpoints are never edited or approved here.
A subsequent draft must pass the safety workflow again.

Static calls (including nested helper bodies): `state.get`, `task.cancel`, `state.pop`, `task.result()[0].inference.close`, `state['workflow'].inference.close`, `task.snapshot`, `task.result`.

#### [clear_patient](../../medical_assistant/ui/navigation.py#L51)

`clear_patient(state, *, preserve_login=True, preserve_patient=True)`

Cancel abandoned work and drop every patient-specific widget/proposal.

Static calls (including nested helper bodies): `state.get`, `list`, `task.cancel`, `job.cancel`, `endo_job.cancel`, `state['workflow'].inference.close`, `task.result()[0].inference.close`, `job.status`, `endo_job.status`, `store.discard`, `task.snapshot`, `task.result`.

#### [ensure_patient](../../medical_assistant/ui/navigation.py#L88)

`ensure_patient(state, patient)`

Fail closed before rendering/collecting a mismatched patient snapshot.

Static calls (including nested helper bodies): `state.get`, `clear_patient`, `workflow.state`.

#### [destination](../../medical_assistant/ui/navigation.py#L112)

`destination(target)`

Static calls (including nested helper bodies): `ValueError`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [go_to](../../medical_assistant/ui/navigation.py#L118)

`go_to(target, *, state=None)`

Static calls (including nested helper bodies): `destination`.

#### [anchor](../../medical_assistant/ui/navigation.py#L124)

`anchor(target)`

Static calls (including nested helper bodies): `destination`, `st.html`.

#### [focus_pending](../../medical_assistant/ui/navigation.py#L129)

`focus_pending()`

Scroll only to fixed app anchors; never interpolate record/model text into JS.

Static calls (including nested helper bodies): `st.session_state.pop`, `destination`, `local_component`, `json.dumps`, `uuid4`.

## [medical_assistant/workflow.py](../../medical_assistant/workflow.py)

Clinical-review graph with deterministic safety holds and authenticated review.

### [CaseState](../../medical_assistant/workflow.py#L27)

Class contract is defined by the fields and methods below.

| Declared field | Type | Default / constraint expression |
| --- | --- | --- |
| `case_id` | `str` | `required / supplied by caller` |
| `record` | `dict` | `required / supplied by caller` |
| `source_file` | `str` | `required / supplied by caller` |
| `model` | `str` | `required / supplied by caller` |
| `assessments` | `dict` | `required / supplied by caller` |
| `evidence` | `list[dict]` | `required / supplied by caller` |
| `safety_decision` | `dict` | `required / supplied by caller` |
| `final_safety_decision` | `dict` | `required / supplied by caller` |
| `safety_ack` | `dict` | `required / supplied by caller` |
| `safety_receipt` | `dict` | `required / supplied by caller` |
| `draft` | `str` | `required / supplied by caller` |
| `generated_draft` | `str` | `required / supplied by caller` |
| `status` | `str` | `required / supplied by caller` |
| `reviewed` | `bool` | `required / supplied by caller` |
| `review` | `dict` | `required / supplied by caller` |
| `approval_receipt` | `dict` | `required / supplied by caller` |
| `review_history` | `list[dict]` | `required / supplied by caller` |
| `reviewed_at` | `str` | `required / supplied by caller` |
| `final_report` | `str` | `required / supplied by caller` |
| `imaging` | `list[dict]` | `required / supplied by caller` |
| `report_evidence` | `dict` | `required / supplied by caller` |
| `clinician_note` | `dict` | `required / supplied by caller` |
| `note_receipt` | `dict` | `required / supplied by caller` |
| `report_content_receipt` | `dict` | `required / supplied by caller` |

### [MedicalHistoryOrchestrator](../../medical_assistant/workflow.py#L54)

Class contract is defined by the fields and methods below.

#### [MedicalHistoryOrchestrator.__init__](../../medical_assistant/workflow.py#L55)

`__init__(self, inference: Inference, evidence_collection=None, *, auth=None, safety=None)`

Static calls (including nested helper bodies): `ImagingStore`, `StateGraph`, `builder.add_node`, `builder.add_edge`, `builder.add_conditional_edges`, `zip`, `builder.compile`, `LocalAuth`, `SafetyAgent`, `LocalEvidenceCollection`, `MedicalHistoryAgent`, `MedicationAgent`, `extractor.run`, `InMemorySaver` (additional calls in source).

#### [MedicalHistoryOrchestrator.__init__.extract](../../medical_assistant/workflow.py#L73)

`extract(state, role=role, extractor=extractor)`

Static calls (including nested helper bodies): `extractor.run`, `PatientRecord.model_validate`, `result.model_dump`.

#### [MedicalHistoryOrchestrator._initial_safety](../../medical_assistant/workflow.py#L123)

`_initial_safety(self, state)`

Static calls (including nested helper bodies): `self.safety.evaluate`, `PatientRecord.model_validate`.

#### [MedicalHistoryOrchestrator._checked_review](../../medical_assistant/workflow.py#L133)

`_checked_review(self, state, response, action)`

Static calls (including nested helper bodies): `Review.model_validate`, `self.auth.verify_receipt`, `digest`, `PermissionError`, `review.model_dump_json`.

Explicit raised conditions: `PermissionError`. See source for triggers; called validators may raise additional exceptions.

#### [MedicalHistoryOrchestrator._safety_review](../../medical_assistant/workflow.py#L144)

`_safety_review(self, state)`

Static calls (including nested helper bodies): `interrupt`, `self._checked_review`, `self.auth.record_receipt`, `ValueError`, `review.model_dump`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [MedicalHistoryOrchestrator._retrieve_evidence](../../medical_assistant/workflow.py#L169)

`_retrieve_evidence(self, state)`

Static calls (including nested helper bodies): `PatientRecord.model_validate`, `' '.join`, `self.evidence_collection.retrieve`.

#### [MedicalHistoryOrchestrator._reasoning](../../medical_assistant/workflow.py#L178)

`_reasoning(self, state)`

Static calls (including nested helper bodies): `self._verify_safety_ack`, `SpecialistAgent('reasoning', self.inference).run`, `PatientRecord.model_validate`, `SpecialistAgent`.

#### [MedicalHistoryOrchestrator._verify_safety_ack](../../medical_assistant/workflow.py#L187)

`_verify_safety_ack(self, state)`

Static calls (including nested helper bodies): `self.safety.evaluate`, `PatientRecord.model_validate`, `ValueError`, `Review.model_validate`, `self.auth.verify_receipt`, `state.get`, `digest`, `review.model_dump_json`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [MedicalHistoryOrchestrator._final_safety](../../medical_assistant/workflow.py#L210)

`_final_safety(self, state)`

Static calls (including nested helper bodies): `self._verify_safety_ack`.

#### [MedicalHistoryOrchestrator._verify_imaging](../../medical_assistant/workflow.py#L213)

`_verify_imaging(self, state)`

Static calls (including nested helper bodies): `state.get`, `any`, `self.imaging_store.verify`, `ValueError`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [MedicalHistoryOrchestrator._compose](../../medical_assistant/workflow.py#L222)

`_compose(self, state)`

Static calls (including nested helper bodies): `self._verify_imaging`, `compose`, `PatientRecord.model_validate`, `state.get`, `evidence_index`.

#### [MedicalHistoryOrchestrator._verify_report](../../medical_assistant/workflow.py#L242)

`_verify_report(self, state)`

Static calls (including nested helper bodies): `verify_note`, `validate_record_grounding`, `compose`, `PatientRecord.model_validate`, `state.get`, `ValueError`, `evidence_index`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [MedicalHistoryOrchestrator._review](../../medical_assistant/workflow.py#L264)

`_review(self, state)`

Static calls (including nested helper bodies): `self._verify_report`, `interrupt`, `self._checked_review`, `verify_content_binding`, `self.auth.record_receipt`, `response.get`, `digest`, `ValueError`, `review.model_dump`, `state.get`, `datetime.now(timezone.utc).isoformat`, `datetime.now`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [MedicalHistoryOrchestrator._complete](../../medical_assistant/workflow.py#L298)

`_complete(self, state)`

Static calls (including nested helper bodies): `self._verify_safety_ack`, `self._verify_imaging`, `self._verify_report`, `Review.model_validate`, `verify_content_binding`, `self.auth.verify_receipt`, `state.get`, `digest`, `ValueError`, `datetime.now(timezone.utc).isoformat`, `review.model_dump_json`, `datetime.now`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [MedicalHistoryOrchestrator.config](../../medical_assistant/workflow.py#L321)

`config(case_id)`

#### [MedicalHistoryOrchestrator.start](../../medical_assistant/workflow.py#L324)

`start(self, record: PatientRecord, source_file: str, *, imaging=None, safety_only=False)`

Static calls (including nested helper bodies): `validate_record_grounding`, `uuid4`, `self.graph.stream`, `self.config`, `record.model_dump`.

#### [MedicalHistoryOrchestrator.start_patient](../../medical_assistant/workflow.py#L351)

`start_patient(self, patient_id, path, *, safety_only=False)`

Static calls (including nested helper bodies): `get_history`, `self.start`, `Path(path).resolve`, `self.auth.path.resolve`, `ValueError`, `self.imaging_store.snapshots`, `Path`, `self.safety.evaluate`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [MedicalHistoryOrchestrator.state](../../medical_assistant/workflow.py#L368)

`state(self, case_id)`

Static calls (including nested helper bodies): `self.graph.get_state`, `self.config`.

#### [MedicalHistoryOrchestrator._response](../../medical_assistant/workflow.py#L371)

`_response(self, case_id, review, token, action)`

Static calls (including nested helper bodies): `Review.model_validate`, `self.auth.require`, `review.model_dump`, `PermissionError`, `self.auth.receipt`, `digest`, `content_digest`, `review.model_dump_json`, `self.state`.

Explicit raised conditions: `PermissionError`. See source for triggers; called validators may raise additional exceptions.

#### [MedicalHistoryOrchestrator.acknowledge_safety](../../medical_assistant/workflow.py#L393)

`acknowledge_safety(self, case_id, review: Review, token=None, *, safety_only=False)`

Static calls (including nested helper bodies): `self.state`, `self._response`, `self.graph.invoke`, `state.get`, `ValueError`, `Command`, `self.config`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [MedicalHistoryOrchestrator.ready_for_analysis](../../medical_assistant/workflow.py#L410)

`ready_for_analysis(self, case_id, token=None)`

Authenticate and recheck the exact prepared snapshot before generation.

Static calls (including nested helper bodies): `self.auth.require`, `self.graph.get_state`, `self._verify_safety_ack`, `self._verify_imaging`, `self.config`, `ValueError`, `state.get`, `tuple`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [MedicalHistoryOrchestrator.continue_analysis](../../medical_assistant/workflow.py#L423)

`continue_analysis(self, case_id, token=None)`

Static calls (including nested helper bodies): `self.ready_for_analysis`, `self.graph.invoke`, `self.config`.

#### [MedicalHistoryOrchestrator.revise](../../medical_assistant/workflow.py#L427)

`revise(self, case_id, draft: str, token=None)`

Static calls (including nested helper bodies): `self.auth.require`, `self.state`, `self.auth.audit`, `self.graph.update_state`, `ValueError`, `self.config`, `state.get`, `draft.strip`, `digest`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [MedicalHistoryOrchestrator.prepare_report_note](../../medical_assistant/workflow.py#L458)

`prepare_report_note(self, case_id, text, token=None)`

Preview a signed reviewer comment; any changed report requires fresh approval.

Static calls (including nested helper bodies): `self.auth.require`, `self.state`, `self._verify_safety_ack`, `self._verify_imaging`, `self._verify_report`, `ReportNote`, `self.auth.receipt`, `compose`, `self.auth.record_receipt`, `self.graph.update_state`, `state.get`, `ValueError`, `digest`, `PatientRecord.model_validate` (additional calls in source).

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [MedicalHistoryOrchestrator.review](../../medical_assistant/workflow.py#L498)

`review(self, case_id, review: Review, token=None)`

Static calls (including nested helper bodies): `self.state`, `self._verify_report`, `self._response`, `self.graph.invoke`, `state.get`, `ValueError`, `digest`, `Command`, `self.config`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [MedicalHistoryOrchestrator.export](../../medical_assistant/workflow.py#L508)

`export(self, case_id)`

Static calls (including nested helper bodies): `self.graph.get_state`, `self._verify_safety_ack`, `self._verify_imaging`, `self._verify_report`, `Review.model_validate`, `verify_content_binding`, `self.auth.verify_receipt`, `self.config`, `ValueError`, `state.get`, `digest`, `review.model_dump_json`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

## [scripts/check_docs.py](../../scripts/check_docs.py)

Check maintained Markdown links and heading anchors without network access.

This intentionally checks ordinary inline links, not a complete Markdown grammar.
It excludes fenced examples and never walks ignored datasets or environments.

#### [prose](../../scripts/check_docs.py#L18)

`prose(text)`

Remove fenced code so example links/headings are not treated as active.

Static calls (including nested helper bodies): `text.splitlines`, `'\n'.join`, `re.match`, `marker.group`, `output.append`, `len`.

#### [anchors](../../scripts/check_docs.py#L35)

`anchors(text)`

Approximate GitHub heading IDs, including repeated headings and Unicode.

Static calls (including nested helper bodies): `prose(text).splitlines`, `result.update`, `set`, `HEADING.match`, `re.sub`, `html.unescape(re.sub('<[^>]+>', '', label)).lower`, `''.join((c for c in label if c.isalnum() or c in '_ -')).replace`, `counts.get`, `result.add`, `re.findall`, `prose`, `match.group`, `html.unescape`, `''.join` (additional calls in source).

#### [documents](../../scripts/check_docs.py#L52)

`documents(root)`

Select maintained guides only; local runtime Markdown is not publication.

Static calls (including nested helper bodies): `Path`, `sorted`, `root.glob`, `(root / 'docs').rglob`, `(root / 'third_party').rglob`, `p.is_file`.

#### [validate](../../scripts/check_docs.py#L69)

`validate(root)`

Return broken local files/anchors; HTTPS links are deliberately not fetched.

Static calls (including nested helper bodies): `Path(root).resolve`, `documents`, `LINK.finditer`, `Path`, `prose`, `match.group(1).strip`, `urlsplit`, `file.read_text`, `(file.parent / unquote(url.path)).resolve`, `path.exists`, `errors.append`, `match.group`, `path.suffix.lower`, `anchors` (additional calls in source).

#### [main](../../scripts/check_docs.py#L91)

`main()`

Static calls (including nested helper bodies): `validate`, `print`, `ValueError`, `Path(__file__).resolve`, `'\n'.join`, `len`, `Path`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

## [scripts/check_ollama.py](../../scripts/check_ollama.py)

Short real local inference connection test without patient data.

## [scripts/generate_api_docs.py](../../scripts/generate_api_docs.py)

Regenerate source-linked class/function references without importing the app.

Run --write after intentional source changes; --check fails on stale documentation.
Annotations and docstrings describe code, not verified clinical capabilities.

#### [cell](../../scripts/generate_api_docs.py#L14)

`cell(text)`

Keep source syntax inside one Markdown table cell.

Static calls (including nested helper bodies): `' '.join(str(text).split()).replace('\|', '\\\|').replace`, `' '.join(str(text).split()).replace`, `' '.join`, `str(text).split`, `str`.

#### [source_files](../../scripts/generate_api_docs.py#L19)

`source_files(root)`

Select maintained implementation, interfaces and scripts, not tests/data.

Static calls (including nested helper bodies): `sorted`, `(root / name).rglob`, `p.is_file`.

#### [render](../../scripts/generate_api_docs.py#L35)

`render(root)`

Derive signatures, declared fields, docstrings and direct calls from AST.

Static calls (including nested helper bodies): `source_files`, `path.relative_to(root).as_posix`, `ast.parse`, `walk`, `'\n'.join(lines).rstrip`, `path.read_text`, `(root / 'docs/CODE_REFERENCE.md').is_file`, `path.relative_to`, `ast.get_docstring`, `isinstance`, `'\n'.join`, `lines.extend`, `lines.append`, `ast.walk` (additional calls in source).

#### [render.walk](../../scripts/generate_api_docs.py#L64)

`walk(nodes, prefix='')`

Static calls (including nested helper bodies): `isinstance`, `lines.extend`, `walk`, `lines.append`, `ast.get_docstring`, `ast.walk`, `sorted`, `ast.iter_child_nodes`, `ast.unparse`, `calls.append`, `cell`, `len`, `', '.join`.

#### [main](../../scripts/generate_api_docs.py#L160)

`main()`

Static calls (including nested helper bodies): `argparse.ArgumentParser`, `parser.add_mutually_exclusive_group`, `action.add_argument`, `parser.parse_args`, `render`, `target.parent.mkdir`, `target.write_text`, `print`, `Path(__file__).resolve`, `target.relative_to`, `SystemExit`, `target.is_file`, `target.read_text`, `Path`.

Explicit raised conditions: `SystemExit`. See source for triggers; called validators may raise additional exceptions.

## [scripts/prepare_research_demo.py](../../scripts/prepare_research_demo.py)

Build local upload examples from separately obtained, permitted research datasets.

No downloads, training, clinical approval or linking of real patient histories.
The real CT workspace must already have been produced by the CT companion.

#### [sha](../../scripts/prepare_research_demo.py#L20)

`sha(path)`

Static calls (including nested helper bodies): `hashlib.sha256(Path(path).read_bytes()).hexdigest`, `hashlib.sha256`, `Path(path).read_bytes`, `Path`.

#### [main](../../scripts/prepare_research_demo.py#L24)

`main()`

Static calls (including nested helper bodies): `argparse.ArgumentParser`, `p.add_argument`, `p.parse_args`, `a.output.resolve`, `a.output.mkdir`, `json.loads`, `dict`, `ct_meta.write_text`, `run`, `enumerate`, `(a.output / 'examples.json').write_text`, `(a.output / 'README.txt').write_text`, `print`, `setattr` (additional calls in source).

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [main.run](../../scripts/prepare_research_demo.py#L38)

`run(root, *args)`

Static calls (including nested helper bodies): `subprocess.run`, `str`, `map`.

## [scripts/smoke_endoscopy.py](../../scripts/smoke_endoscopy.py)

Actual bounded synthetic producer/receiver smoke; no imaging or final approvals.

#### [main](../../scripts/smoke_endoscopy.py#L15)

`main()`

Static calls (including nested helper bodies): `argparse.ArgumentParser`, `p.add_argument`, `p.parse_args`, `tempfile.TemporaryDirectory`, `LocalEndoscopyJob`, `validate_bundle`, `print`, `job.status`, `time.sleep`, `ValueError`, `job.bundle_path.read_bytes`, `Path`, `job.log_path.read_text`, `len`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

## [scripts/smoke_imaging.py](../../scripts/smoke_imaging.py)

Real local CT worker and receiver; no human or final approval is simulated.

#### [main](../../scripts/smoke_imaging.py#L17)

`main()`

Static calls (including nested helper bodies): `argparse.ArgumentParser`, `parser.add_argument`, `parser.parse_args`, `TemporaryDirectory`, `Path`, `seed`, `LocalCTJob`, `print`, `configured_ct_root`, `ImagingStore`, `store.prepare`, `store.discard`, `job.cancel`, `job.status` (additional calls in source).

Explicit raised conditions: `RuntimeError`. See source for triggers; called validators may raise additional exceptions.

## [scripts/smoke_local.py](../../scripts/smoke_local.py)

Real local model smoke: verify an uncertainty hold and a separate fully synthetic
ordinary-eligible fixture. Never approve a safety hold or final clinical report.

#### [main](../../scripts/smoke_local.py#L21)

`main()`

Static calls (including nested helper bodies): `argparse.ArgumentParser`, `parser.add_argument`, `parser.parse_args`, `OllamaClient`, `client.close`, `TemporaryDirectory`, `seed`, `LocalAuth`, `MedicalHistoryOrchestrator`, `workflow.start_patient`, `list`, `print`, `datetime.now(ZoneInfo('Europe/Amsterdam')).date().isoformat`, `json.dumps` (additional calls in source).

## [scripts/smoke_research_pair.py](../../scripts/smoke_research_pair.py)

Actual local image-pair/report smoke with SCRIPTED reviews in a TEMPORARY DB.

The approvals below test plumbing only. They are never clinical review and never
modify the demo application's database. No image pixels are sent to the LLM.

#### [main](../../scripts/smoke_research_pair.py#L32)

`main()`

Static calls (including nested helper bodies): `argparse.ArgumentParser`, `p.add_argument`, `p.parse_args`, `time.monotonic`, `OllamaClient`, `client.close`, `tempfile.TemporaryDirectory`, `seed`, `LocalAuth`, `auth.create_clinician`, `auth.login`, `ImagingStore`, `MedicalHistoryOrchestrator`, `flow.start_patient` (additional calls in source).

Explicit raised conditions: `AssertionError`. See source for triggers; called validators may raise additional exceptions.

## [scripts/smoke_uploads.py](../../scripts/smoke_uploads.py)

Exercise real local Upload/Analyze widgets in a disposable database.

Uses prepared research pixels and actual local polyp inference; no scripted model,
no LLM call, no image/safety/report approval, and no application database changes.
The local research kit and installed companion are prerequisites, not downloads.

#### [main](../../scripts/smoke_uploads.py#L26)

`main()`

Static calls (including nested helper bodies): `argparse.ArgumentParser`, `parser.add_argument`, `parser.parse_args`, `args.kit.resolve`, `print`, `tempfile.TemporaryDirectory`, `seed`, `LocalAuth`, `auth.create_clinician`, `json.dumps`, `Path(__file__).resolve`, `Path`, `patch`, `patch.dict` (additional calls in source).

Explicit raised conditions: `RuntimeError`. See source for triggers; called validators may raise additional exceptions.

## [scripts/sync_ct_contracts.py](../../scripts/sync_ct_contracts.py)

Vendor/check ML-free CT contracts; no CT model, torch or database tools imported.

#### [sync](../../scripts/sync_ct_contracts.py#L10)

`sync(ct_root, *, write=False)`

Static calls (including nested helper bodies): `print`, `(Path(ct_root) / 'src/lung_nodule' / source).read_text`, `text.replace`, `target.write_text`, `ValueError`, `target.exists`, `target.read_text`, `Path`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

#### [main](../../scripts/sync_ct_contracts.py#L32)

`main()`

Static calls (including nested helper bodies): `argparse.ArgumentParser`, `p.add_argument`, `p.parse_args`, `sync`.

## [scripts/sync_endo_contracts.py](../../scripts/sync_endo_contracts.py)

Check exact ML-free endoscopy contract/worker equality with the companion.

#### [main](../../scripts/sync_endo_contracts.py#L7)

`main()`

Static calls (including nested helper bodies): `argparse.ArgumentParser`, `p.add_argument`, `p.parse_args`, `print`, `Path`, `signature.read_bytes`, `(root / 'medical_assistant/producer_signature.py').read_bytes`, `ValueError`, `Path(__file__).resolve`, `source.read_bytes`, `target.read_bytes`.

Explicit raised conditions: `ValueError`. See source for triggers; called validators may raise additional exceptions.

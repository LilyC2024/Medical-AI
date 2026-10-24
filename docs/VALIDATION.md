# Validate LOVISA and the CT connection

[Overview](../README.md) · [Actual outcomes](../EVALUATION.md) · [Phase gates](../PLAN.md)

## Offline software checks

```bash
.venv/bin/python -m pip check
.venv/bin/python -m compileall -q medical_assistant app.py scripts tests
.venv/bin/python -m pytest -q
.venv/bin/python scripts/check_docs.py
```

See [response-budget checks](PERFORMANCE.md) and [workspace behavior](INTERFACE.md).
Timeout/cancellation/late-output, compact-ID grounding and responsive scripted UI
checks run offline. Browser screenshots and actual CT/Ollama smokes are separate.

These checks use temporary SQLite, synthetic sources and scripted model/reviewer
identities. They cover dates/orders, grounding, safety bypasses, authenticated
approvals, archive/pixel integrity, caliper UI and guarded export. Combined-report checks cover CT/no-CT snapshots,
zero candidates, note previews/stale approvals, exact evidence links, HTML pictures
and tampered-image export rejection. No CT install or
Ollama is required for this suite. Passing tests is not clinical validation.
[Eight acceptance requirements](ACCEPTANCE.md).

## Real CT interoperability

Install the companion using [Imaging](IMAGING.md). From LOVISA:

```bash
.venv/bin/python scripts/sync_ct_contracts.py --ct-root ../ai-medimg-2.5D-CT
.venv/bin/python scripts/smoke_imaging.py --mode lung-fixture
.venv/bin/python scripts/smoke_imaging.py --mode lung-pretrained --model-dir ../ai-medimg-2.5D-CT/models/luna16 --device cpu
.venv/bin/python scripts/smoke_imaging.py --mode legacy
```

The actual CT interpreter generates synthetic pixels and exports a bundle; LOVISA
validates it in a temporary database. No imaging/safety/final approval is issued.
Fixture detection is non-ML. Pretrained smoke needs verified installed weights and
never downloads during inference. Legacy mode trains its tiny model and checks
ONNX parity; its metrics are not nodule results.

Shared schema/report/rendering must match after the import-path rewrite. Maintainers
may intentionally sync with `scripts/sync_ct_contracts.py --ct-root ... --write`,
then test both projects and update the exact CI producer pin. Never hide drift by
changing only one consumer. Device selection is explicit; actual CUDA/NPU execution
must be recorded separately from unavailable-device tests.

## Real local LLM

```bash
.venv/bin/python scripts/check_ollama.py gemma4:e2b
.venv/bin/python scripts/smoke_local.py --model gemma4:e2b
```

This separate live smoke confirms the missing-data hold before reasoning, then
runs actual structured Ollama reasoning on an eligible synthetic fixture. It stops
at final review. Validation may fail closed; do not weaken grounding for a pass.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| Old nodule-v1 ZIP rejected | Re-export original workspace with current CT; do not rename schema |
| Contract drift | Inspect producer changes, intentionally sync and test both repos |
| Companion missing | Set MHCRA_CT_ROOT and install CT's separate Python 3.12 `.venv` |
| Pretrained worker fails | Inspect ignored worker.log, registration/hashes and matching torch/torchvision |
| CUDA unavailable | Configure compatible hardware/runtime or explicitly select CPU for inference |
| Uncertain candidate | Review accept/reject or discard proposal; uncertainty cannot be accepted |
| Caliper inputs absent | Enable caliper, submit measurement preview, then edit the exposed fields |
| New import missing from draft | Start a new case; snapshots are fixed |
| Source/hash/approval mismatch | Export remains blocked; inspect originals and re-import explicitly with a new study ID |
| Ollama result rejected | Inspect the local error; unsupported claims must not become reviewed output |

CI installs dependencies/weights explicitly and runs open-source models on runner
CPU; the application has no cloud inference provider. It publishes no patient
records or clinical reports. [Security](../SECURITY.md).

## Guided demonstration checks

`tests/test_guided_services.py` exercises all five fictional records and staged
safety with scripted inference. `tests/test_guided_ui.py` covers result retention,
automatic completion/empty-state replacement, case switching and session expiry.
The main UI test verifies Generate is the final main-page action and stays locked
until safety is prepared. The largest demo also exercises the actual compact
wire-size check using an HTTP mock without dropping source entries. None of those
checks are live inference or clinician verification.

## Image-first endoscopy extension

Endoscopy adds `test_endoscopy.py`, `test_endoscopy_ui.py` and `test_endo_worker.py`. Run `scripts/sync_endo_contracts.py --endo-root ../AI-MedImg-Endo` and `scripts/smoke_endoscopy.py --endo-root ../AI-MedImg-Endo` for exact contract and actual synthetic producer/receiver checks. [Details](ENDOSCOPY.md).

## Actual public-image pair

Prepare permitted data using [the research guide](RESEARCH_IMAGES.md), then run:

```bash
.venv/bin/python scripts/smoke_research_pair.py --kit data/research-demo --model gemma4:e2b --output data/research-demo/new-isolated-test
```

This uses actual research predictions and the installed local LLM. It tests image,
safety and final approval with clearly scripted submissions in a disposable DB,
never the app database. Its exported example visibly says no clinician reviewed
it. Standard `smoke_local.py` still issues no approvals. Reproduce public model
training/evaluation separately; artificial unit checks are not real-data tests.

## Upload/Analyze regressions

`tests/test_imaging_actions.py` tests authenticated routing, failed-input rollback,
frozen-report preservation, exact uploaded bytes, modality/patient checks and job
collection. `tests/test_upload_analyze_ui.py` uses actual Streamlit file-uploader
widgets with artificial pixels and scripted clinical inference. It reproduces
uploading after draft generation in both panels and verifies renewed safety gates,
visible errors/retries and pending-review navigation.

With the prepared local research kit and installed endoscopy model, run:

```bash
.venv/bin/python scripts/smoke_uploads.py --kit data/research-demo
```

This separate smoke uploads actual research ZIP/JPG files through the UI and runs
actual local polyp inference. Only persistence is redirected to a disposable
SQLite database; no image, safety or report approval is issued. It is not a
browser visual check or clinical validation.

## Expert-review and documentation checks

`tests/test_clinical_failures.py` reproduces capacity exhaustion, error rendering
and failure-cause visibility. Upload regressions cover cancellation of active
reasoning by new CT and deferred cross-modality result collection. These use
scripted models/reviewers, never a live clinical claim.

```bash
.venv/bin/python scripts/generate_api_docs.py --check
```

After intentional source/signature changes, regenerate with `--write`. The local
Markdown checker now validates heading anchors as well as file paths, including
encoded names and fenced examples. It is not a general Markdown parser and does
not contact external URLs. [Review findings](REVIEW.md).

## Reviewed integration checks

Install the pinned `quality` extra in a supported Python 3.11+ environment, then run
`python -m ruff check .`, `python -m mypy`, `python -m pytest -q --cov`, and
`python -m pip_audit -r requirements.lock.txt --strict`. Coverage is a software
regression gate (85%), not clinical validity. CycloneDX SBOMs list dependencies only.

Run `python scripts/smoke_signed_exchange.py --ct-root /path/to/ct --endo-root /path/to/endo`
for real subprocess signing and pinned receiving in disposable storage; no image
or report approval is issued. This script uses generated synthetic evidence, not
training or a clinical test. Both companions need their own installed environments.
See [reproducibility](REPRODUCIBILITY.md) for optional durable-state, tracing and key
configuration; adversarial regressions cover privacy, database isolation, audit
decision binding and hostile signed archives.

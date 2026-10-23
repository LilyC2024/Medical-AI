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
approvals, archive/pixel integrity, caliper UI and guarded export. No CT install or
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

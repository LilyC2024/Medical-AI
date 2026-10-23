# Validation and reproduction

[Overview](../README.md) · [Actual results](../EVALUATION.md) · [Phase gates](../PLAN.md)

## Offline regression

```bash
.venv/bin/python -m pip check
.venv/bin/python -m compileall -q medical_assistant app.py scripts tests
.venv/bin/python -m pytest -q
.venv/bin/python scripts/check_docs.py
```

Tests use temporary databases, synthetic sources and scripted inference/reviewers.
They include Streamlit AppTest, exact-source grounding, medication/date extraction,
safety bypass attempts, source/report escaping, account/session receipts, import
limits, imaging validation and final-approval/export integrity. Passing tests do
not establish clinical performance. Main regression needs no CT install or Ollama.

## Current CT interoperability

Install the companion as in [Imaging](IMAGING.md); then from MHCRA:

```bash
.venv/bin/python scripts/sync_ct_contracts.py --ct-root ../ai-medimg-2.5D-CT
.venv/bin/python scripts/smoke_imaging.py --mode lung-fixture
.venv/bin/python scripts/smoke_imaging.py --mode lung-pretrained --model-dir ../ai-medimg-2.5D-CT/models/luna16 --device cpu
.venv/bin/python scripts/smoke_imaging.py --mode legacy
```

Each smoke runs the actual separate CT interpreter, prepares the resulting bundle
in a temporary synthetic database and checks that no study/report is approved.
Pretrained smoke requires already-installed verified weights; no inference-time
download is allowed. Fixture is non-ML. Legacy mode performs tiny training and
ONNX parity; its results are not nodule metrics. CPU was executed locally; CUDA
selection is explicit but no actual GPU execution is claimed here.

The canonical contracts, report and NumPy wire renderer are checked byte-for-byte
against the companion after its one import-path rewrite. Intentional contract
changes must first pass producer tests (PLAN Phase 9), then consumer tests
(Phase 10), then joint validation/publication (Phase 11). Hosted integration pins
a specific CT commit instead of following an unreviewed branch tip.

## Real local language model

```bash
.venv/bin/python scripts/check_ollama.py gemma4:e2b
.venv/bin/python scripts/smoke_local.py --model gemma4:e2b
```

This is separate from mocked tests. It verifies a missing-information hold before
reasoning and uses a supplied eligible synthetic case for actual structured local
Ollama reasoning. Final approval remains pending. Model validation can legitimately
fail closed; do not remove grounding constraints to force a pass.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| Nodule-v1 ZIP rejected | Re-export the original workspace with current CT; do not relabel its schema |
| Shared contract drift | Inspect changes; intentionally sync with `--write`, test both repos and update CI pin |
| Companion missing | Set MHCRA_CT_ROOT; create CT's separate Python 3.12 `.venv` |
| Installed detector fails | Inspect local worker.log; verify model registration, recipe/weight hashes and matching torch/torchvision |
| CUDA unavailable | Select CPU explicitly or install compatible CUDA hardware/runtime; there is no silent fallback |
| Candidate uncertain | Inspect it and explicitly accept/reject, or discard the proposal; uncertainty blocks acceptance |
| Caliper controls not visible | Enable caliper and submit measurement preview, then edit newly visible form fields |
| Later imports absent from draft | Start a new case; snapshots are immutable |
| Artifact hash or approval mismatch | Stop/export stays blocked; inspect originals and rerun an explicitly reviewed import with a new study ID |
| Ollama rejects a result | Review the local validation error; unsupported source claims never become a reviewed report |

CI uploads no records/reports and calls no cloud inference. Hosted code tests are
software checks; no real clinical deployment, clinician reader study or patient
performance validation is claimed.

# Endoscopy image review

[Overview](../README.md) · [Architecture](ARCHITECTURE.md) · [Reports](REPORTS.md)

LOVISA now accepts reviewed **artificial and permitted public research colonoscopy candidates**, alongside
CT studies and medical-history evidence. This does not extend the clinical model
into general gastrointestinal diagnosis, cancer classification or treatment advice.

## Setup and operation

Clone [AI-MedImg-Endo](https://github.com/LilyC2024/AI-MedImg-Endo) as a sibling of
LOVISA. Follow its [setup](https://github.com/LilyC2024/AI-MedImg-Endo/blob/main/docs/SETUP.md)
to create its separate `.venv`. The artificial non-ML example requires no weights.
Train/register a model explicitly before selecting installed-model mode.

1. Sign in and select one artificial patient.
2. Open **Endoscopy review** (also linked in the right-hand guide).
3. **Upload** a permitted JPG/PNG or companion review ZIP, then **Analyze**.
   A JPG/PNG runs the installed local polyp model on the exact uploaded image;
   a ZIP validates and opens its included results without new inference. Raw
   public uploads must be one of the three prepared research images in the Jordan
   composite case. Without an upload, **Model / example** offers an artificial
   fixture/model input or Jordan's prepared local research example. Uploads always
   take precedence over example selection. [Files and sources](RESEARCH_IMAGES.md).
   Progress and cancellation are immediate; the worker stops after 110 seconds.
   This is a response budget, not a guarantee of success on every computer.
4. Inspect source and overlay. Areas are mask pixels and image-area fractions,
   not physical lesion size. Scores are model outputs, not cancer probability.
5. Set every region to accept/reject; uncertain blocks acceptance. An optional
   note may be blank. The green confirmation starts selected; only submission records the inspection.
6. **Include reviewed endoscopy in report**, then complete the separate safety
   check and generate a draft. Final clinician approval remains mandatory.

Accepted studies appear in the short report and its offline HTML pictures. Exact
source/model/review provenance remains in JSON evidence; it is not repeated in the
main prose. If a report already exists, successful **Analyze** opens a fresh
unreviewed context and clears the old safety decision. Saved reports stay intact;
include the images and repeat safety before generating another report.
CT and endoscopy have separate views and validators but share authenticated
storage, source verification and final content binding. Only one pending imaging
proposal is presented at a time. Patient switching cancels endoscopy work and
clears its private widgets. Urgent policy decisions pause optional imaging.

## Local configuration

| Variable | Purpose |
| --- | --- |
| `LOVISA_ENDO_ROOT` | Companion root; defaults to sibling `AI-MedImg-Endo` |
| `LOVISA_ENDO_MODEL_DIR` | Registered local model; defaults to registered `artifacts/kvasir-research-v2` when available, otherwise `artifacts/kvasir-model` |
| `LOVISA_ENDO_BACKEND` | `onnx-cpu` (default), `openvino-cpu`, or `openvino-npu` |

No runtime model download, cloud fallback, model-selected executable or LLM image
inference occurs. CPU is always an explicit choice; unavailable NPU fails.
OpenVINO starts with numerical comparison against ONNX CPU before inference.
NPU execution still needs validation on the user's Intel Windows hardware.

## Evidence format and boundaries

`lovisa-endo-image-v1` holds one generated-synthetic RGB source (16–512 pixels per
side), float32 probability map, binary predicted mask, overlay, candidate regions,
model provenance and unknown acquisition date. Every declared candidate is
recomputed from the probability map, threshold and minimum area; source and
annotation pixels are independently checked. Paths, duplicate JSON keys, ZIP
member counts, byte sizes and hashes are validated before storage. Synthetic-v1 contains exactly five files within 16 MiB. Research-v2 retains the same
five-file structure with a 64-MiB total/expanded bound and 16-MiB-plus-header
per-artifact bound, so real large source images can retain their source grid. Coordinates are half-open `xyxy` in
source pixels; connected regions are not adjudicated distinct polyp identities.

Standalone endoscopy supports explicitly permitted public research images up to
2048 pixels per side, and can use the distinct `lovisa-endo-research-v2` bundle for a `research-composite-` fictional case. Public provenance and original-byte hashes are required; Kvasir patient identity remains unknown. This does not permit real clinical records.
A synthetic flag/hash establishes internal consistency, not independent proof of
origin, inference execution or clinical correctness. Local administrators remain
trusted. No histology, anatomical segment or millimetre calibration is invented.

The Endoscopy Agent is a bounded local computer-vision adapter, implemented by
`endo_worker.LocalEndoscopyJob`. It is not another LLM persona. The four history,
medication, reasoning and safety specialists remain unchanged; only reasoning
calls Ollama. Reviewed endoscopy observations are added by Python after clinical
reasoning. Pixels and imaging notes do not enter the LLM or its hypothesis catalog.

## Reproduce checks

```bash
.venv/bin/python scripts/sync_endo_contracts.py --endo-root ../AI-MedImg-Endo
.venv/bin/python scripts/smoke_endoscopy.py --endo-root ../AI-MedImg-Endo
.venv/bin/python scripts/smoke_endoscopy.py --endo-root ../AI-MedImg-Endo --mode installed --model-dir ../AI-MedImg-Endo/artifacts/kvasir-model
```

Smokes generate artificial pixels and validate actual worker output; they issue
no imaging or clinical approvals. Tests use temporary accounts/databases and
scripted reviewers. [Actual outcomes](../EVALUATION.md).

Hosted cross-repository checks pin producer `81ff9f53a0baa9b40ff396283ef1dd9f430bf170`. Later documentation-only commits do not change this tested contract.

## Errors and retries

Errors appear beside **Analyze**, including unsupported input, wrong case/section,
missing model, invalid output and worker timeout. A malformed file does not retire
an existing report. A failed or already-collected job does not lock the other
panel. A pending candidate review must be included or discarded first; the page
links directly to the corresponding view. No upload or analysis supplies approval.

## Verified producer and failure handling

The companion now checks research sidecars and exported ZIPs against the same
original bytes, typed study and predictions. Its manifest loader rechecks decoded
related-image content and actual masks, while registration rejects ambiguous or
nonfinite parity/configuration metadata. Historical workspace compatibility is
verified; the public-v2/synthetic-v1 wire contracts are unchanged.
[Producer review](https://github.com/LilyC2024/AI-MedImg-Endo/blob/main/docs/REVIEW.md).

Changing standalone model/backend/permission clears stale work. LOVISA preserves
its own patient-scoped cancellation and immutable accepted snapshots. Bounded
literal errors explain failure without interpreting source text as markup.

# Connect the CT companion to LOVISA

[Overview](../README.md) · [Visual explanation](ILLUSTRATIONS.md) ·
[Producer guide](https://github.com/LilyC2024/ai-medimg-2.5D-CT/blob/main/docs/lung/mhcra.md)

## Responsibility and compatibility

The CT project detects candidate nodules and supports source-image/caliper review.
LOVISA organizes history and includes accepted CT evidence in a clinician-reviewed
report. Each keeps its own local environment. Pixels and imaging notes are never
sent to Ollama; imaging cannot change safety escalation or the hypothesis catalog.

| CT capability/output | LOVISA support |
| --- | --- |
| `mhcra-lung-nodules-v2` | Source HU, all-slice previews, candidates, provenance and optional CT review |
| Non-ML fixture / installed pretrained detector | Both launchable locally; explicit CPU or available CUDA for pretrained |
| `mhcra-imaging-v1` | Retained tissue-mask importer, viewer, worker and report summary |
| Incomplete nodule-v1 ZIP | Rejected; re-export the original workspace with current CT |
| Full-size/public-research CT, dataset preparation/training | Standalone CT only; LOVISA accepts bounded generated-synthetic studies |

Existing `mhcra-*`, `MHCRA_CT_*` and bridge/module names are stable interfaces.
LOVISA is the current application name. [Naming map](NAMING.md).

## Install separately

From the directory containing the LOVISA checkout, use Python 3.12 for CT:

```bash
git clone https://github.com/LilyC2024/ai-medimg-2.5D-CT.git
cd ai-medimg-2.5D-CT
python3.12 -m venv .venv
.venv/bin/python -m pip install torch==2.14.1+cpu torchvision==0.29.1+cpu --index-url https://download.pytorch.org/whl/cpu
.venv/bin/python -m pip install -e '.[ml,lung,ui,dev]'
.venv/bin/python -m pip check
```

Reuse existing environments. On Windows create the CT environment with
`py -3.12 -m venv .venv` and use `.venv\Scripts\python.exe`. CUDA needs
matching CUDA torch/torchvision builds for its driver, installed instead of CPU
wheels. Intel NPU is not supported for the new detector. Fixture mode needs no
weights. Fetch official weights explicitly during CT setup when needed:

```bash
.venv/bin/python -m lung_nodule.cli fetch-model --output models/luna16
```

LOVISA discovers a sibling `ai-medimg-2.5D-CT`; otherwise set `MHCRA_CT_ROOT`.
`MHCRA_CT_MODEL_DIR` selects installed weights. `MHCRA_CT_DEVICE` selects `cpu`
(default) or `cuda` for the installed detector; unavailable CUDA fails explicitly.
These settings are kept outside the review UI. Default discovery prefers registered
`models/luna16-full`, otherwise `models/luna16`. From LOVISA's own checkout:

```bash
export MHCRA_CT_ROOT="/absolute/path/to/ai-medimg-2.5D-CT"
export MHCRA_CT_MODEL_DIR="/absolute/path/to/ai-medimg-2.5D-CT/models/luna16"
.venv/bin/python -m streamlit run app.py
```

The worker uses CT's `.venv`, never LOVISA's interpreter. No inference-time download
or remote fallback occurs. Missing weights/unavailable CUDA fail explicitly.

## Inspect and accept in LOVISA

1. Sign in (examples are hidden until login), select the synthetic patient and open **CT review** before
   starting a case. Choose fixture, installed pretrained detector or legacy demo.
2. **Run CT analysis**. Progress refreshes automatically; cancel
   when needed. A 110-second watchdog bounds execution. Lung modes generate a 32×64×64 phantom; the legacy
   mode trains a tiny tissue model and checks ONNX parity. No review is approved.
3. Completed CT opens automatically for inspection (the manual inspection button
   remains available). Or inspect an uploaded ZIP. Patient identity
   must match; generated jobs also bind the requested study ID.
4. Scroll source/overlay slices and jump to candidates. Amber boxes are candidate
   locations. Scores are not malignancy probabilities; box spans are not diameters.
5. Explicitly accept/reject every candidate. Uncertain blocks acceptance. Optional
   calipers use one source plane and endpoints inside the candidate box. Enable a
   caliper, submit **Preview nodule measurements** to expose its form inputs, then
   edit and preview again. Cyan lines are unapproved previews at this stage.
6. Add imaging notes, attest association/geometry review and accept. The authenticated
   account and exact decisions/calipers are bound to the acceptance hash.
7. Complete safety preparation after accepting CT. The short clinical summary
   includes the accepted inspection and reviewed calipers, with representative
   source/annotation pictures. Preview the clinician note, then approve the exact
   combined report separately. The HTML download embeds those pictures.
   A report prepared before CT acceptance needs a new review to include the study.
   [Report rules](REPORTS.md).

CT analysis results show counts, review state, source-slice ranges, scores and
reviewed calipers. Pending and accepted results appear in CT review; accepted
studies remain inspectable in an active clinical snapshot. Empty states explain
when no CT has been attached.

Pending imaging blocks safety preparation and draft generation. Active cases lock new imaging; later
imports need a new case. Urgent warnings take priority over optional image checks.
Acquisition date remains unknown. Rejected/zero candidates never establish normality.

## Export from CT

The dedicated bridge creates a pending synthetic bundle with matching aliases:

```bash
# Run in CT; this prepares input and supplies no human approval.
.venv/bin/python -m deploy.mhcra_lung_bridge --patient-id synthetic-checklist --study-id synthetic-example --output-dir artifacts/lovisa-lung --mode fixture --device cpu
```

Output: `artifacts/lovisa-lung/exchange/bundle.mhcra.zip`. For installed weights,
use `--mode pretrained --model-dir models/luna16 --device cpu` (or available CUDA).
Use a new study ID/output directory each run.

Default standalone export requires completed CT review:

```bash
.venv/bin/python -m lung_nodule.cli export --workspace artifacts/pretrained-demo --output artifacts/nodules.zip
```

Its study `patient_alias` must match LOVISA's synthetic patient ID. The default
standalone demo uses `synthetic`; use `detect --patient-alias ... --study-id ...`
or the dedicated bridge for an appropriate association. CT review can seed LOVISA
controls but never replaces authenticated imaging acceptance or final approval.

## Contract and trust details

| Artifact | Required check |
| --- | --- |
| bundle.json | Version, literal synthetic flag, matching patient/study, job identity, processing time, unknown acquisition date and typed study/review |
| source.npy | Finite float32 HU; bound header/shape/payload before allocation |
| All source/overlay PNGs | Exact dimensions and pixels recomputed from HU, boxes and producer calipers |
| producer/report.md | Exact canonical report or fixed pending text; no arbitrary producer conclusions |
| Manifest | Safe paths, role/index, byte sizes and SHA-256; reject duplicates/unlisted/encrypted/symlink entries |
| LOVISA acceptance | Fully resolved candidate review, valid calipers, matching reviewer/study and content hash |

Bounds: **64 slices ×256×256**, 64 MiB compressed, 128 MiB expanded, 131 members,
400 KB manifest. Exchange uses the full bounded source snapshot, not truncation.
Wire previews use −1000 to 400 HU and a font-independent NumPy renderer.

Shared ML-free contracts/report/renderer are vendored from CT with one import-path
rewrite. [Sync/check commands](VALIDATION.md) detect drift. CI pins producer
`5ba347cf6cd66b1931eaad3cd7d8cb27d4136606`; later documentation commits leave that
contract unchanged. [Workflow](../.github/workflows/tests.yml).

Ignored `data/imaging/` holds originals/HU/previews/jobs. SQLite stores accepted
snapshots/audit separately from clinical facts. Snapshot loading verifies accepted studies; the selected viewer then performs
one resolver validation and checks each requested preview individually. Composition, completion, saving
and export recheck artifacts and review bindings. Hashes prove internal consistency,
not independent synthetic origin/model execution or clinical truth. Local admins
remain trusted. Interrupted jobs/proposals are not resumable; a completed bundle
can be re-imported. Accepted files must remain available for verification.

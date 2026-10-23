# Local lung CT integration

[Overview](../README.md) · [Architecture](ARCHITECTURE.md) ·
[Companion guide](https://github.com/LilyC2024/ai-medimg-2.5D-CT/blob/main/docs/lung/mhcra.md)

## Compatibility and scope

MHCRA v0.2 supports the current lung workflow through **mhcra-lung-nodules-v2**.
It also retains the old **mhcra-imaging-v1** tissue-mask bridge. These are separate
contracts: nodule boxes never become tissue labels. Incomplete nodule-v1 archives
are rejected; re-export their original CT workspace using the current producer.

Only generated synthetic inputs enter MHCRA. Public-research approval, real DICOM
loading, large-volume review, dataset preparation, CUDA training and FROC evaluation
remain standalone CT features. They are not implemented inside MHCRA. This is not
cancer diagnosis or a validated lesion detector. No image-derived facts or review
notes enter Ollama or expand the clinical hypothesis catalog.

## Install the companion

Keep MHCRA's existing `.venv`. From the parent directory, install CT separately
with Python 3.12 (Windows substitutes `.venv\Scripts\python.exe`):

```bash
git clone https://github.com/LilyC2024/ai-medimg-2.5D-CT.git
cd ai-medimg-2.5D-CT
python3.12 -m venv .venv
.venv/bin/python -m pip install torch==2.14.1+cpu torchvision==0.29.1+cpu --index-url https://download.pytorch.org/whl/cpu
.venv/bin/python -m pip install -e '.[ml,lung,ui,dev]'
.venv/bin/python -m pip check
.venv/bin/python -m pytest -q
```

For CUDA use matching CUDA torch/torchvision wheels for the installed driver,
following the companion's deployment guide. Do not install CPU wheels first.
Intel NPU is not CUDA and is not supported for the new detector in this release.
The fixture path needs no pretrained weights. For actual pretrained inference,
explicitly fetch the pinned official model during setup, from the CT checkout:

```bash
.venv/bin/python -m lung_nodule.cli fetch-model --output models/luna16
```

MHCRA finds the sibling CT checkout automatically. Override before starting MHCRA
if necessary (run Streamlit from MHCRA using MHCRA's environment):

```bash
export MHCRA_CT_ROOT="/absolute/path/to/ai-medimg-2.5D-CT"
export MHCRA_CT_MODEL_DIR="/absolute/path/to/ai-medimg-2.5D-CT/models/luna16"
.venv/bin/python -m streamlit run app.py
```

The worker uses the companion's own `.venv/bin/python` (or Windows equivalent).
It never downloads weights/data or falls back to remote inference. An unavailable
requested accelerator or absent model fails explicitly. Default model discovery
prefers `models/luna16-full` when registered, otherwise `models/luna16`.

## MHCRA workflow

1. Sign in, select the synthetic patient and open **Imaging workbench** before
   starting a clinical case. Choose **Lung nodule fixture (non-ML)**,
   **Installed pretrained lung detector**, or the retained **Legacy tissue-mask
   demonstration**. Fixture is default and clearly labeled; pretrained requires
   verified installed weights and an explicit CPU/CUDA selection.
2. Click **Generate synthetic CT demonstration**; refresh or cancel as needed.
   A three-minute watchdog terminates jobs. Lung modes generate a 32×64×64 chest
   phantom; legacy mode trains its tiny tissue model and checks ONNX parity.
   Neither path approves anything.
3. **Inspect completed CT bundle**, or upload and inspect a synthetic v2 ZIP.
   Patient alias must match the selected patient; jobs also bind the requested
   study ID. All source/overlay bytes, geometry and report consistency are checked.
4. Jump to each candidate or scroll the source slices. Amber rectangles show
   source-grid boxes. Scores are detector outputs, not cancer risk; box extents
   are not lesion diameters or volume. Review source/model hashes and limitations.
5. Give every nodule an **accept** or **reject** decision; **uncertain** keeps
   acceptance blocked. Optionally enable a same-plane caliper, set source slice,
   start/end row/column and click **Preview nodule measurements**. Controls are in a
   form: after enabling a caliper, preview once to expose its coordinates, then
   edit and preview again. Cyan previews are unapproved until submission.
6. Supply imaging notes and the association/geometry attestation; accept for the
   research appendix. The authenticated account must match the nodule reviewer.
   The acceptance hash covers the bundle **and exact decisions/calipers**.
   Upstream CT review can seed controls, but cannot bypass this MHCRA review.
7. Start a new clinical case. Existing urgent/uncertain safety holds apply before
   reasoning. Review the seven-section draft and its nodule research appendix;
   explicit **final clinician approval** is still required for reviewed export.

Acquisition date is unavailable rather than inferred from processing time.
Rejected candidates remain in the audit/report context; accepted annotations do
not establish disease. Zero-candidate output does not exclude disease.

Pending imaging and running/completed uninspected jobs block draft generation.
Accept/discard/dismiss first. Active cases lock new imaging actions. A newly
accepted study requires a new case; active snapshots never update silently.
Urgent structured warnings take priority over optional imaging and block stale
review/download until a new case starts. Imaging cannot lower escalation.

## Export from the standalone CT application

Default standalone export still requires its explicit local reviewer attestation:

```bash
# From CT, after completing the review in its UI/CLI:
.venv/bin/python -m lung_nodule.cli export --workspace artifacts/lung-demo/workspace --output artifacts/lung-reviewed.zip
```

Use a workspace whose `patient_alias` equals MHCRA's selected synthetic patient
ID. The default standalone `demo` uses alias `synthetic`; for a matching study,
run `detect` with the appropriate `--patient-alias` and `--study-id`, or use the
MHCRA worker. The dedicated bridge creates an unreviewed bundle without forging
standalone approval:

```bash
# From CT; this command prepares input, not human approval.
.venv/bin/python -m deploy.mhcra_lung_bridge --patient-id synthetic-checklist --study-id synthetic-example --output-dir artifacts/mhcra-lung --mode fixture --device cpu
```

Output: `artifacts/mhcra-lung/exchange/bundle.mhcra.zip`. Pretrained uses
`--mode pretrained --model-dir models/luna16 --device cpu` (or available CUDA).
Use a new output directory and immutable study ID for each run.

## Wire contract and validation

| Content | Validation |
| --- | --- |
| `bundle.json` | Version, literal synthetic flag, patient/study/job identity, unknown acquisition date, processing timestamp, typed Study and optional producer Review |
| `source.npy` | Float32 finite HU, declared shape; inspect NPY header and exact payload length before allocation |
| Every source and overlay PNG | Dimensions plus exact pixels recomputed from HU, candidate boxes and producer calipers |
| `producer/report.md` | Recomputed shared deterministic report, or exact pending-review text; arbitrary prose rejected |
| Artifact manifest | Role/index/path, bytes and SHA-256; no unlisted, duplicate, encrypted or symlink members |
| MHCRA candidate review | Exactly one explicit decision per candidate, no uncertainty, valid accepted-candidate calipers and matching study digest/reviewer |

Limits: 64 MiB compressed, 128 MiB expanded, at most 131 ZIP members, 400 KB
manifest, 64 source slices and 256×256 pixels per plane. Full HU is required for
independent preview/measurement checks. Source previews use lung window −1000 to
400 HU. The shared NumPy renderer uses no fonts, ensuring exact parity across
Pillow versions. Untrusted values are escaped in final report text.

The ML-free schemas, renderer and canonical report are vendored from CT, with
only the import path rewritten. Check drift with:

```bash
.venv/bin/python scripts/sync_ct_contracts.py --ct-root ../ai-medimg-2.5D-CT
# Maintainer only, after intentionally changing and testing the contract:
.venv/bin/python scripts/sync_ct_contracts.py --ct-root ../ai-medimg-2.5D-CT --write
```

This release pins CT `e0704b22177a23b323e4d3aff455c447d0579542`.
Hosted integration CI pins the exact companion commit in
[tests.yml](../.github/workflows/tests.yml); update it with coordinated releases.

## Persistence and trust

Ignored `data/imaging/` holds jobs, pending proposals, immutable original ZIPs,
source HU and previews. SQLite keeps accepted snapshots/audit separately from
clinical source facts. Imaging acceptance is transactional; composition,
completion, export and report saving recheck accepted bytes and choices.
The final report hash covers the appendix. Original DICOM/weights are not embedded
in clinical exports. Source hashes, detector execution/version metadata and
synthetic-origin markers are producer declarations: consistency does not establish
independent authenticity or clinical truth. Local code/database administrators
remain trusted. Neither upstream attestation nor MHCRA authentication verifies
professional credentials.

A crash can leave ignored jobs/proposals. Pending UI work is not resumable job
management; import a completed bundle to resume inspection. Interrupted promotion
can be retried with the same bytes; conflicting orphaned data fail closed and
need inspection. Accepted artifacts must stay in place for integrity checks.
There is no deletion/reopening UI. [Validation](VALIDATION.md) · [Actual results](../EVALUATION.md).

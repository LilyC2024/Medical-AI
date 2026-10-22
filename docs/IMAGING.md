# Shared local CT workbench

The **Imaging workbench** tab places synthetic CT source slices, candidate
overlays, geometry and source-grid measurements beside MHCRA's longitudinal
history. CT processing runs in a separate local Python worker. The four clinical
specialists and their safety/approval rules remain unchanged; images and imaging
notes are excluded from the LLM. Accepted imaging is a research appendix in the
same draft covered by final clinician approval.

## Setup

Keep MHCRA's existing `.venv`. Install the companion separately (Python 3.12):

```bash
# From the parent directory of your Medical-AI checkout:
git clone https://github.com/LilyC2024/ai-medimg-2.5D-CT.git
cd ai-medimg-2.5D-CT
python3.12 -m venv .venv
.venv/bin/python -m pip install torch==2.14.1+cpu --index-url https://download.pytorch.org/whl/cpu
.venv/bin/python -m pip install -e '.[ml,dev]'
.venv/bin/python -m unittest discover -s tests -v
```

MHCRA finds a sibling folder named `ai-medimg-2.5D-CT`. For another location,
set `MHCRA_CT_ROOT` to its absolute path before starting Streamlit:

```bash
export MHCRA_CT_ROOT="/absolute/path/to/ai-medimg-2.5D-CT"
.venv/bin/python -m streamlit run app.py
```

Run that last command from MHCRA's checkout, using MHCRA's `.venv`, not the CT
environment. The CT interpreter is taken from its own `.venv/bin/python`
(`.venv\Scripts\python.exe` on Windows). Setup downloads packages; the workbench
does not download data/models or call cloud inference. Its demo generates its
own synthetic CT and trains a small model locally.

## Use

1. Sign in to a local reviewer account, select the synthetic patient, and open
   **Imaging workbench** before starting a clinical case.
2. Click **Generate synthetic CT demonstration**. The worker creates 20 synthetic
   48×48 slices, trains a tiny 32×32/base-width-4 model for 12 epochs, validates
   ONNX parity and exports a review bundle. Click **Refresh CT job** to check
   progress, or **Cancel CT job**. A watchdog terminates jobs after three minutes.
3. Click **Inspect completed CT bundle**. Alternatively upload a bundle generated
   by the [companion bridge](https://github.com/LilyC2024/ai-medimg-2.5D-CT/blob/main/docs/mhcra-workbench.md)
   and click **Inspect uploaded CT bundle**. Patient identity must match the
   selected patient; generated jobs must also match the requested study ID.
4. Move the source-grid slice slider and compare source and overlay. Teal is
   heuristic class 1, amber class 2 and purple class 3. Class 0 is transparent;
   it is not a normality assessment. Review geometry, candidate counts/volumes,
   hashes and limitations. Acquisition date is explicitly unavailable.
5. Supply **Imaging review notes**, tick the association/geometry attestation and
   click **Accept imaging for research appendix**. This requires authentication,
   notes and a matching proposal hash. Discarding writes no accepted study.
6. Start a new clinical case from **History and clinical review**. Existing safety
   holds still apply before LLM reasoning. The draft includes accepted imaging
   as a source-linked research appendix. Inspect it and use the existing final
   clinician-review form. Imaging acceptance alone cannot enable final export.

Pending imaging and running/completed uninspected jobs block draft generation.
Accept, discard or explicitly dismiss them first. Active clinical cases lock new
imaging actions. Later accepted studies do not change an existing case snapshot;
start a new case to include them. Study IDs are immutable; reruns use a new ID.
The UI checks structured warnings before inspecting optional images. If a warning
arrives outside an active case's snapshot, the UI blocks its review/download and
requires a new case; the snapshot itself remains immutable.

## Data and trust boundaries

`data/imaging/` contains ignored local job logs/artifacts, pending proposals,
immutable original ZIPs and extracted accepted previews/masks. SQLite stores
accepted study snapshots and audit records separately from clinical source facts.
Human acceptance is bound to the manifest and archive hashes. Composition,
completion, export and report persistence recheck the accepted artifacts.
Image files are viewed locally; exported reports contain provenance and research
measurements, not embedded DICOM, model weights or external image links.

ZIP input is bounded to 64 MiB compressed/128 MiB expanded. Paths, duplicate
entries, file hashes, PNG dimensions, mask classes, source-grid counts, geometry
and overlay pixels are checked. NPY headers are checked before allocating arrays.
The contract supports at most 64 slices and 256 pixels per in-plane dimension;
clinical JSON retains its separate 100 KB limit. Generated series require the
companion's unchanged synthetic-source hash marker.

Hashes establish internal identity/consistency, not independent authenticity of
synthetic origin or model execution. Uploaded model/source hashes, entropy and
ONNX parity are producer declarations. The trusted companion really runs parity
validation; MHCRA does not receive weights/original DICOM to recompute it. A
local operator who modifies code, source markers or database is trusted.

The candidate classes are heuristic and the small demo has weak agreement with
its teacher. Volumes describe candidate voxels, not validated anatomy, lesions
or progression. The bridge uses raw predictions explicitly; baseline
postprocessing previously worsened teacher agreement. Entropy is model behavior,
not clinical confidence. No imaging output can lower safety escalation or add
new diagnostic hypotheses. The integration supports generated synthetic input
only; the companion's broader research-DICOM mode remains outside MHCRA.

The watchdog handles worker timeout and explicit cancellation. A process/server
crash may leave local job or pending directories; these are ignored artifacts,
not accepted studies. An interrupted file promotion can be retried by importing
and reviewing the same original bundle; conflicting orphaned bytes fail closed
and need local inspection. Pending proposals and job handles live in the UI session;
resetting a session does not provide resumable job management. Import an already
completed bundle to resume inspection. Accepted study files must remain in place
for integrity-checked reports; there is no archive-reopening or deletion UI.

## Reproduce the integration check

```bash
.venv/bin/python -m pytest -q
.venv/bin/python scripts/smoke_imaging.py
.venv/bin/python scripts/smoke_local.py --model gemma4:e2b
```

The imaging smoke runs the real CT worker and receiver against a temporary
synthetic database. It prepares and verifies an import, but issues no imaging,
safety or final approval. Automated workflow/UI tests separately use scripted
reviewers and model responses. The Ollama smoke exercises real local inference
separately. See [EVALUATION.md](../EVALUATION.md) for actual results.
Hosted MHCRA CI also runs the synthetic producer/consumer smoke against CT commit
`6d24dc952bc2012123fc4343e5079c66788ec18f`. Update that pin deliberately when
changing the versioned exchange contract; the four clinical specialists continue
to use their existing offline regression tests.

# LOVISA release and migration record

[Overview](../README.md) · [Evaluation](../EVALUATION.md) · [Naming](NAMING.md)

## v0.2.1 — LOVISA name and documentation

- Renamed the visible application to **LOVISA**, retaining **Medical History &
  Clinical Reasoning Assistant** as the functional description.
- Rewrote both projects' guides around their distinct inputs, models, outputs and
  human-review responsibilities. Reused prior pictures with explicit captions.
- Kept the repository address, Python package, environment settings and versioned
  exchange identifiers stable. Existing integrations use the same commands.
- Separated concise overview guides from technical references and historical
  evidence. Corrected stale links and outdated legacy commands.
- Updated UI/report branding and its existing regression assertion. No clinical
  policy, hypothesis catalog, detector weights or exchange schema changed.

## v0.2.0 — current lung CT compatibility

Added `mhcra-lung-nodules-v2`: bounded source HU, every-slice previews, typed study,
model/source hashes and optional producer review. Shared ML-free schemas/report/
renderer support independent validation and drift checking.

LOVISA gained candidate navigation, source-plane caliper preview and authenticated
imaging acceptance bound to exact decisions. Fixture/pretrained workers complement
the retained legacy tissue-mask worker. An escaped, evidence-linked appendix is
covered by final clinical approval; images/notes remain outside reasoning.

The release passed 146 LOVISA and 81 CT tests, actual local fixture/pretrained/
legacy transfers, local Ollama smoke and hosted checks. Exact commits/runs are in
[Evaluation](../EVALUATION.md).

## Compatibility rules

| Existing input/interface | Action |
| --- | --- |
| nodule-v2 | Use current candidate/caliper import and review |
| tissue-mask `mhcra-imaging-v1` | Retained as a distinct legacy path |
| incomplete `mhcra-lung-nodules-v1` | Re-export original workspace with current CT; do not relabel |
| Existing package/environment/bridge names | Continue using them; the LOVISA rename is presentation-level |
| Public research/full-size CT | Keep in standalone CT; LOVISA accepts bounded synthetic studies only |

Standalone CT export requires its local review by default. Its dedicated LOVISA
bridge exports pending review and never forges approval. LOVISA always requires
its own authenticated imaging acceptance and separate final clinical approval.

## 0.3.0 — local workspace and response budget

Reusable light UI, three lazy views, readable source/medication cards and right-hand
operating guide. Clinical generation/resumption now runs in bounded background
tasks with progress, cancellation and late-result rejection. CT has a 110-second
watchdog, real-stage progress and automatic pending inspection. Verified-view
preview access removes repeated full-archive work. Compact local reasoning selects
IDs and restores exact source text in Python. Clinical/import/imaging approvals,
source integrity, local-only inference and both CT exchange formats are preserved.
No dependency or model upgrade. [Details](PERFORMANCE.md) · [Evaluation](../EVALUATION.md).

## 0.4.0 — guided signed-in demonstrations

Five new authored fictional cases; login-gated examples; explicit safety preparation
with no model call; bottom generation enabled only after required checks. CT result
summaries remain visible after clinical analysis. Reports quote each source once,
use compact evidence keys and retain a brief CT appendix with full JSON provenance.
An explicit demo-only account setup leaves normal password rules unchanged.
The local hypothesis catalog, CT format and clinical review boundary are unchanged.
[Operation](WORKFLOWS.md) · [Cases](DEMO_CASES.md) · [Evaluation](../EVALUATION.md).

## 0.5.0 — focused patient navigation

- Made patient selection explicit and placed it above the workspace. Removed the
  multi-case body table; only the selected person's data is rendered.
- Added a dedicated Safety check view. Pending imports/CT have a direct resolution
  link; generation stays locked until required checks and remains below the form.
- Replaced static instructions with clickable guide steps and a contextual Next
  action. Links open and scroll to fixed app destinations without approving work.
- Removed raw extraction/manifest JSON, hashes, model paths and internal IDs from
  the review page. Readable source excerpts and original-input downloads remain
  in Source records; evidence validation and export provenance are preserved.
- Clear patient-specific widgets/proposals and cancel abandoned jobs on switching;
  check snapshot identity before rendering results. Clear previous final-review
  choices when starting another review. Background completion is polled even when
  the reviewer opens a different view.
- Corrected a recovery-test fixture that regenerated a ZIP on retry: its timestamp
  could change the archive identity. The test now retries the exact same bytes;
  production archive checks remain strict.

No dependency, model, safety policy, hypothesis catalog or CT contract upgrade.
The CT producer is unchanged. [Operation](WORKFLOWS.md) · [Evaluation](../EVALUATION.md).

## 0.6.0 — concise combined clinical and CT report

- Replaced the seven-section presentation with one short Clinical summary:
  local-model history hypotheses, accepted CT inspection, essential gaps and an
  attributed clinician note. No full timeline or technical source-key list in prose.
- Preserved every original excerpt and model evidence link in a separate evidence
  index and JSON package; optional readable evidence remains available in the UI.
- Included CT candidate decisions, reviewed calipers and representative source/
  annotation images. No-CT is explicit, with a direct new-report route; a later CT
  acceptance requires a fresh report snapshot.
- Added authenticated note preview (600 characters), signed authorship and fresh
  content-bound approval after edits. Notes do not become record facts or trigger
  another model call.
- Added approval-gated HTML downloads with embedded verified CT pictures alongside
  concise Markdown and full JSON. Export/save recompute and verify report text,
  evidence links, notes, approvals and imaging integrity.
- Updated operating, architectural and function guides and a labelled scripted
  example. Existing saved reports retain their historical format and approval.

No dependency, model, hypothesis catalog, safety policy or CT producer/contract
change. The CT project remains compatible. [Reports](REPORTS.md) · [Evaluation](../EVALUATION.md).

## 0.7.0 — Image-first endoscopy

Adds a separate polyp image companion, source/mask/probability/overlay verification, candidate decisions, bounded local processing, patient-isolated UI and accepted endoscopy findings/pictures in the single-section report. The CV adapter is not an LLM; history reasoning remains local and catalog-bounded. Final approval binds both CT and endoscopy snapshots. [Guide](ENDOSCOPY.md).

## Public research-image composite and simpler review

Separate CT-v3/endoscopy-v2 research contracts support real deidentified images
with distinct subject provenance and bounded CT coverage. Earlier synthetic
formats/stored manifests remain verifiable. A signed-in composite example and
local preparation scripts provide real upload files. Imaging prose is shorter;
notes are optional; confirmations start selected; colour and larger decisions
make pauses/approval clearer. Explicit submission, uncertain-candidate blocks,
safety routing and final content binding remain. [Experiment details](RESEARCH_IMAGES.md).

## Upload/Analyze repair — 23 October 2026

Both image views use Upload/Analyze and optional model/example selection. Uploads
never silently launch generated-demo inference. CT/endoscopy review ZIPs open
existing results; permitted raw endoscopy images run the local model. A successful
Analyze after case creation opens a fresh unreviewed context, clearing old safety
and final-review choices while preserving stored reports. Invalid uploads leave
the old context intact. Pending reviews and running jobs have visible blockers;
completed/failed job handles no longer disable the other panel. Runtime and
validation errors are displayed beside Analyze, with retry available.

Reused environments/models and unchanged producer contracts. Source validation,
urgent routing, explicit image/safety/final approvals and immutable accepted
studies remain enforced. [Operation](INTERFACE.md) · [Actual checks](../EVALUATION.md).

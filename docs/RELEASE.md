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

# v0.2.0 — current lung CT interoperability

23 October 2026. [Overview](../README.md) · [Actual checks](../EVALUATION.md)

Previously MHCRA launched only the legacy tissue-mask demo and consumed only
`mhcra-imaging-v1`. The CT project's current nodule workflow was not importable.
This coordinated update adds a separate nodule path without changing clinical
safety routing, the hypothesis catalog or final approval requirements.

## Changes

- Added **mhcra-lung-nodules-v2** with source HU, every-slice previews, typed study,
  model/source provenance, hashed artifact manifest and explicit producer status.
- Added shared ML-free schemas, canonical report and portable NumPy renderer;
  drift checking avoids accidental producer/consumer divergence.
- Added bounded nodule import with exact source/annotation/report checks and
  authenticated candidate/caliper review. Acceptance binds the exact decisions.
- Added source/overlay viewer, candidate navigation and caliper preview in MHCRA.
  Upstream CT attestation seeds controls but cannot approve MHCRA imaging.
- Added fixture and installed-pretrained workers with explicit CPU/CUDA selection;
  retained legacy tissue worker/importer/viewer/report support.
- Added source-linked nodule appendix inside the existing seven-section draft.
  Images and review notes remain excluded from LLM reasoning. Final report
  approval is separate; saved/exported reports recheck accepted artifact integrity.
- Reorganized root README around a concise overview, current figure, agent table,
  setup and compatibility matrix; moved detailed instructions to linked guides.
  Preserved earlier clinical/technical pictures with their explanatory text.
- Extended adversarial, worker and UI tests; added real fixture/pretrained/legacy
  cross-project smoke and pinned CI contract checks. No dependency upgrade needed.

## Migration

Existing `mhcra-imaging-v1` accepted studies and default programmatic legacy jobs
remain supported. The UI now defaults to the explicitly non-ML nodule fixture.
Old incomplete `mhcra-lung-nodules-v1` ZIPs require re-export from the original
workspace; they cannot be safely upgraded by renaming a field. Standalone export
still requires local CT review by default; the dedicated MHCRA bridge exports
**pending** review so MHCRA can perform its own authenticated acceptance.

The synthetic workbench has bounded volume dimensions. Public research DICOM,
large-volume review, GPU training and evaluation stay in CT. No full clinical CT
or cancer-diagnosis support is claimed. [Wire contract/use](IMAGING.md).

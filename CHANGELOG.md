# Changelog

All notable changes to LOVISA are recorded here. Dated test outcomes live in
[EVALUATION.md](EVALUATION.md). LOVISA is educational/research software, not a
diagnostic device.

## Unreleased

### Added
- Producer-signature verification for CT and endoscopy review ZIPs (Ed25519,
  public keys pinned locally via `python -m medical_assistant.producer_trust`).
  Bad signatures fail closed; unsigned or unpinned archives show a warning and
  are accepted unless `require_signature` is set.
- The review screen shows the verified producer's false-positive rate beside every
  candidate ("not measured" for CT; "not available" without a verified claim).
- New dependency `cryptography` (lockfile: cryptography 50.0.2, cffi 2.1.1,
  pycparser 3.11).

### Changed
- Vendored CT and endoscopy readers accept one optional `signature.json`; CI pins
  the producer commits that add signing.

## 0.7.0 — 24 October 2026

Baseline before this changelog was introduced; see [EVALUATION.md](EVALUATION.md)
for the history of earlier releases.

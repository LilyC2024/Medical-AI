# Changelog

All notable changes to LOVISA are recorded here. Dated test outcomes live in
[EVALUATION.md](EVALUATION.md). LOVISA is educational/research software, not a
diagnostic device.

## Unreleased

### Added
- Opt-in redacted local traces: with `LOVISA_TRACE_FILE`, each workflow step
  writes an OpenTelemetry span (step, hashed case reference, outcome, timing,
  exception type) to a local JSON-lines file. No network exporter. New dependency
  `opentelemetry-sdk` (lockfile: 1.45.1, semantic conventions 0.66b1).
- Read-only **Audit trail** expander on Clinical report: chronological audit rows
  for the selected patient with receipt verification status.

## 0.7.0 — 24 October 2026

Baseline before this changelog was introduced; see [EVALUATION.md](EVALUATION.md)
for the history of earlier releases.

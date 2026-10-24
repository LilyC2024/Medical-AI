# Changelog

## Reviewed branch integration — 24 October 2026

- Added report-bound model, prompt and policy provenance, optional durable pending
  reviews, redacted local traces and selected-patient audit replay.
- Added coordinated Ed25519 imaging exchange and pinned exporter trust, repairing
  archive bounds, ambiguous metadata and unknown-key acceptance.
- Fixed database isolation, exception-trace leakage and misleading audit decisions;
  changed keys/policies/images are rejected before advancing durable final reviews.
- Preserved optional notes/checked confirmations; CT candidate choices start paused.
- Integrated MIT source/data terms, reporting checklists and quality/security CI.
- Raised supported Python minimum to 3.11 for Pillow 13; preserved the old local
  environment. See EVALUATION.md for actual checks and docs/BRANCH_REVIEW.md for
  every branch decision. Container deployment and human-factors trials are deferred.

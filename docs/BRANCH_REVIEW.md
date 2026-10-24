# Reviewed branch integration — 24 October 2026

Every fetched remote branch and local non-main branch was compared against the
previous main. Changes were selectively integrated and repaired, rather than
blindly merging entire tips. The original branches remain available. Branch
commit messages and claimed test counts were not accepted as validation evidence.

| Reviewed branch | Tip | Decision |
| --- | --- | --- |
| `codex/ci-evaluation` | `c3a3d04e40f0` | Superseded/previous release; no historical code restored. |
| `codex/mhcra-ai` | `6b0d23863f4d` | Superseded/previous release; no historical code restored. |
| `origin/chore/mit-license` | `7ff29ed46c8d` | Integrated MIT source license/data terms; datasets, weights and third-party code retain separate terms. |
| `origin/ci/hardening` | `a9563840a921` | Adapted lint/type/coverage, audits, SBOM, secret scanning and CodeQL. Run results recorded separately; CI configuration alone is not a passed check. |
| `origin/docs/honest-process-wording` | `a30e74b0e3d2` | Adapted qualification of AI-assisted source review; preserved actual coding-agent review history. No independent clinician/security certification claimed. |
| `origin/docs/status-checklists-human-factors` | `8e2c183a55ad` | Integrated reporting-checklist mapping and proposed human-factors protocol, explicitly not executed. |
| `origin/feat/durable-workflow-state` | `37c7c8b75818` | Adapted: optional durable receipt key, database-scoped keys/checkpoints, only interrupted human-review states offered for resume. |
| `origin/feat/inference-provenance` | `8f7af02fb28e` | Integrated report-bound model/prompt/policy identity. Compose/Docker proposal deferred: no validated container run or companion runtime in this release. |
| `origin/feat/local-traces-audit-replay` | `3a0e8227ec5e` | Adapted: opt-in local spans without exception text/resource detectors; replay verifies displayed decisions against receipts. |
| `origin/feat/verify-producer-signatures` | `e4fda59b1e9c` | Adapted coordinated Ed25519 exchange, strict bounded archive/envelope validation, pinned-key receiver policy and accurately labelled producer declarations. |
| `origin/fix/pillow-13-security` | `310a2c4a722f` | Integrated fixed Pillow 13 after verifying Python >=3.11 requirement; supported release minimum raised, old environment preserved. |
| `origin/fix/review-gate-active-choices` | `a98a08c06343` | Adapted only independent CT candidate decisions. Retained requested checked confirmations, optional notes and exact-content explicit submission. |

## Cross-project result

The original schema versions and unsigned fictional/public-research examples stay
compatible. Optional signatures identify an exporter and bind exact manifest and
artifact bytes. A pinned key is a local trust decision, not clinical validation;
unknown signed keys are rejected by LOVISA. Producer-declared unmatched-candidate
fractions are exploratory precision proxies, not specificity or cancer risk.

The shared attestation module is identical in all three repositories. It bounds
ZIP sizes before decompression, rejects duplicate/unsafe members and JSON keys,
reconstructs artifact hashes, validates strict claims and verifies Ed25519 proofs.
Code source licensing is MIT; data/model terms remain separate.

## Validation and limitations

See [EVALUATION.md](../EVALUATION.md) for checks actually executed on the integrated
source. Offline tests use generated data/scripted reviews; live model smokes are
identified separately. Existing trained models are reused; no new clinical
validation, GPU training, NPU execution or clinician qualification is claimed.

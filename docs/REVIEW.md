# Three-project expert code review — 24 October 2026

[Overview](../README.md) · [Checks](VALIDATION.md) · [Evidence](../EVALUATION.md)

Three independent reviewers inspected LOVISA, CT and endoscopy source, tests and
runtime boundaries. The primary agent checked integrations, documentation and
publication. Each material defect received a regression or rejected-input test.
This is a software audit, not clinician review or exhaustive security assurance.

## LOVISA findings

| Priority | Reproduction and repair |
| --- | --- |
| P2: saturated clinical workers crashed controls | Exhaust available workers, then save safety/prepare/generate. `WorkStopped` now produces a recoverable explanation and preserves eligible safety state. |
| P2: import-validation errors rendered uploaded Markdown | A malformed fictional field containing an external-image Markdown expression was echoed by `st.error`. Dynamic errors now use a bounded literal formatter, with no Pydantic input dump or help URL. |
| P3: stopped analyses hid their cause | The failure panel now shows a bounded escaped reason instead of only a generic stop message. |

Eight new regressions cover baseline failures, retries, safe rendering, cancellation
when a CT upload starts a fresh context, late-result rejection and deferred
cross-modality result collection. Existing adversarial source, policy, actor,
content-binding, image and isolation suites remain intact. No additional bypass
was found in those reviewed paths; that is not proof that all bugs are absent.

## Companion findings

CT repairs upload cleanup ownership, duplicate/encrypted ZIP handling, label
validation before integer conversion, finite real training HU and workspace
preflight before output reservation. [Detailed CT review](https://github.com/LilyC2024/ai-medimg-2.5D-CT/blob/main/docs/review.md).

Endoscopy repairs provenance/ZIP association, decoded-content split checks, strict
model-registration evidence and stale settings/results. Historical workspaces and
the original frozen split remain compatible after verification. [Detailed endoscopy
review](https://github.com/LilyC2024/AI-MedImg-Endo/blob/main/docs/REVIEW.md).

## Validation and residual assumptions

The source-repair phase passed LOVISA 279 tests, CT 101 runtime tests plus four
shared documentation checks, and endoscopy 72 tests. Final combined checks and
actual inference are recorded in [Evaluation](../EVALUATION.md). No shared protocol,
installed model, dependency, actual-app approval or hypothesis catalog changed.

Local administrators, permission declarations and model installers remain trusted.
Unsigned hashes establish consistency, not authenticity. Histories remain fictional;
public imaging subjects are separate. GPU training, NPU execution and independent
clinical validity are not established. Browser visual QA is separate from Streamlit
AppTest; the current review does not claim new manual browser verification.

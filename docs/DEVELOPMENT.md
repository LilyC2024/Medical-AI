# Development method and agent implementation

[Overview](../README.md) · [Architecture](ARCHITECTURE.md) · [Contributing](../CONTRIBUTING.md)

## Runtime implementation

`MedicalHistoryOrchestrator` builds one LangGraph state machine with fixed stages
and in-memory checkpoints. History and medication extraction and the safety policy
are Python. Clinical reasoning uses one local Ollama model with constrained JSON/
ID output. LangChain runnables wrap local extraction/retrieval. No specialist has
arbitrary tools, a database connection or authority to approve output.

The CT and endoscopy adapters launch separate bounded local processes. RetinaNet
and U-Net are computer-vision models, not LLM agents. Python composes accepted
observations after history reasoning; image pixels/notes never enter the LLM.
[Schema/module contracts](CODE_REFERENCE.md).

## AI coding-agent review

The 24 October 2026 review used a primary integration/documentation agent and
three AI coding-agent reviewers, each in a separate session:

| Reviewer scope | Inspection and result |
| --- | --- |
| LOVISA | Safety/auth/source/content binding, UI jobs and errors; repaired saturation crashes, hidden failure reasons and Markdown injection |
| CT | Geometry, training sources/labels, workspaces and legacy upload API; repaired cleanup ownership, ambiguous archives and invalid numeric data |
| Endoscopy | Workspaces, provenance, frozen datasets, registrations and stale UI; repaired evidence mismatch, leakage checks and invalid metadata |
| Primary agent | Cross-project protocol compatibility, documentation/commands, reusable figures, final regressions/smokes and publication |

Coding agents are development collaborators, not deployed runtime subagents or
clinical experts. Because the agents and the single human author share the same
project context, this is a self-audit, not independent review; no independent
human code, security or clinician review has taken place. Tests used temporary databases, manufactured inputs and scripted
reviewers; actual model smokes were run separately. [Findings](REVIEW.md) ·
[Evidence](../EVALUATION.md). Earlier historical passes used different review
arrangements; no past use of agents is inferred from this one.

## Phase discipline

1. Read [AGENTS.md](../AGENTS.md), the current [PLAN](../PLAN.md) phase and contracts.
2. Inspect/reuse installed environments; avoid gratuitous dependencies or rewrites.
3. Reproduce material defects and test source repairs before changing docs/UI phases.
4. Test source identity, rejected paths, cancellation and explicit review boundaries.
5. Refresh concise overview plus linked implementation/operation guides.
6. Run full suites, actual local model/interoperability checks and documentation
   validation; distinguish mock, actual CPU and unexecuted accelerator evidence.
7. Inspect all staged files, publish compatible producers, then update the receiver's
   pinned producer commits and verify hosted results.

## Coordinated contracts and publication

CT's lightweight contracts/renderer are vendored with a controlled import rewrite;
endoscopy's ML-free contract/worker are copied exactly. Sync checks detect drift.
Do not fix only one side, change a schema label to bypass a check or add torch to
LOVISA's lightweight environment. Preserve old supported evidence and explicit
migration rules. UI simplification cannot remove approval/content verification.

Only source, fictional fixtures and permitted aggregate metadata belong in Git.
Datasets, weights, local accounts, approvals, runtime image stores and generated
reports remain ignored. Publishing code does not deploy a clinical service.
[Validation](VALIDATION.md) · [Security](../SECURITY.md) · [Release record](RELEASE.md).

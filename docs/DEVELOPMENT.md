# Development and review approach

[Overview](../README.md) · [Architecture](ARCHITECTURE.md) · [Contributing](../CONTRIBUTING.md)

## Runtime design

LOVISA implements one LangGraph orchestrator and four specialist roles. History,
medications and safety use Python; only clinical reasoning calls local Ollama.
LangChain `RunnableLambda` wraps deterministic extraction/retrieval. Graph
interrupts enforce authenticated human review. [Exact implementation](ARCHITECTURE.md).

The CT companion is a separate computer-vision application: pretrained MONAI
RetinaNet plus Python geometry, measurements and deterministic reporting. It has
no autonomous LLM agents and is not a fifth LOVISA specialist.

## Development agents and subagents

Earlier development used a primary coding agent and review subagents assigned to
records/UI, safety/workflow and documentation/release. Their code inspections and
adversarial tests found source-binding, approval-integrity, medication, import-limit,
archive-allocation and rendering defects. These were software reviews, not clinical
verification. Development subagents are not shipped in either runtime.

The lung compatibility pass traced worker commands, wire contracts, candidate
review, persistence and report/export guards. Implementation followed producer
checks, consumer checks and joint validation. The LOVISA documentation/branding
pass uses source review and regression checks; it adds no new runtime agents.

## Workspace release

The response-budget/UI work followed three separately tested phases: background
workers and integrity-preserving preview access; reusable/lazy UI and right guide;
actual browser/CT/Ollama verification and documentation. No development subagents
were run for this release. Compact ID selection keeps runtime specialist roles
unchanged while Python restores source excerpts. [Details](PERFORMANCE.md).

## Working method

1. Read [AGENTS.md](../AGENTS.md) and the relevant contract/guide.
2. Reuse `.venv`; inspect versions before changing dependencies.
3. Complete/test the current [PLAN phase](../PLAN.md) before beginning another.
4. Test with temporary databases, scripted models and deliberately synthetic data.
5. Run live Ollama/CT smokes separately when behavior changes; never label mocks live.
6. Record actual results and unexecuted checks in [Evaluation](../EVALUATION.md).

Keep UI, schemas, storage, extraction, retrieval, policy and coordination separate.
A passing test cannot justify weakening source grounding, safety routing or human
approval. Coordinated CT changes start in the producer contract; intentionally
sync the consumer, run both suites and update its tested producer CI pin.

## Publication

LOVISA is published at `LilyC2024/Medical-AI`; CT at
`LilyC2024/ai-medimg-2.5D-CT`. Publishing source does not deploy a clinical service.
Inspect the full staged diff and existing history. Commit code, documentation,
config and deliberately fictional fixtures only. Keep credentials, databases,
exports, local approvals, logs, data and weights ignored.

[Validation commands](VALIDATION.md) · [Security](../SECURITY.md) · [Naming](NAMING.md).

## Guided demonstration release

The next pass separates safety preparation from model execution. Five explicitly
authored fictional cases extend software coverage; they do not expand the medical
hypothesis catalog. CT completion is prepared before empty-state rendering and
results precede controls. The concise report quotes each source once and keeps
full provenance in JSON. All development/review in this pass used the primary
coding agent and automated tests; no additional runtime or coding subagents were
introduced. [Operation](WORKFLOWS.md) · [Case expectations](DEMO_CASES.md).

## Focused navigation release

Patient-scope cleanup and fixed navigation targets were tested before UI
integration. The interface then gained explicit selection, a dedicated Safety
check view, actionable guide buttons and separate readable sources. Regression
checks include switching during blocked scripted inference and discarding the
previous patient's pending CT. Browser checks verify actual scrolling separately
from scripted AppTest assertions. This pass uses the primary coding agent and
automated tests; it introduces no subagents or runtime model changes.

## Combined report release

The primary coding agent implemented/tested summary services and signed note
previews first, then report pictures/HTML and UI actions, followed by regression,
actual local smokes and documentation. No coding subagents or additional runtime
LLMs were introduced. History/medication/safety remain Python specialists; Ollama
selects constrained history hypotheses. CT inspection/measurements are composed
in Python and remain outside LLM inference. [Report contracts](REPORTS.md).

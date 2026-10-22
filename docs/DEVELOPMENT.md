# Development and publication

## How the prototype was implemented

The specification separates a Medical History Orchestrator from four specialist
responsibilities. LangGraph encodes that coordination as explicit transitions
and review interrupts. Python performs repeatable extraction and safety routing;
the installed `gemma4:e2b` model provides constrained, uncertain synthetic
hypothesis selection through Ollama's structured JSON API. LangChain Core
`RunnableLambda` wraps deterministic extraction and local evidence retrieval;
those operations do not call an LLM.

[PLAN.md](../PLAN.md) progresses through foundation, history management,
orchestration, safety/approval and interface/evaluation. Records were deliberately
constructed as synthetic JSON fixtures. SQLite source/fact separation supports
traceability without allowing a model to mutate history. Human approval applies
to imported records, uncertain safety holds and final clinical reports.

Development review agents and subagents are coding assistants used to inspect
implementation, tests, documentation and publication readiness. They are separate
from the four runtime specialists. They do not run inside the published app or
replace a clinical reviewer. Their reviews and tests verify software behavior,
not clinical validity. Normal operation does not call a hosted coding model.

The implementation/review process used a primary coding agent for integration
and separate subagents for records/UI, safety/workflow, and documentation/release
readiness. On the illustrated README pass, these three reviewers independently
checked source behavior while the primary agent rewrote the guide and prepared
the publication. Their findings clarified startup seeding, fixed case snapshots,
historical warning holds and automatic report persistence. Development-agent
labels describe review assignments; they are not application classes or installed
runtime services.

At runtime, `MedicalHistoryOrchestrator` creates one `StateGraph(CaseState)`.
History and medication classes return `Assessment` objects through
`RunnableLambda`; `SafetyAgent.evaluate()` returns a Python policy decision.
`SpecialistAgent("reasoning", inference)` alone calls the Ollama adapter, which
returns schema-constrained JSON and is followed by Python validation. These
specialists run sequentially and share typed graph state. Human review uses
LangGraph interrupts/resume commands and authenticated, content-bound receipts.
The source retains generic prompts for all four roles, but the graph uses
inference only for reasoning.

The two illustrations in [the README](../README.md#how-it-works-in-pictures)
were generated using the built-in image tool and checked against the source.
PNG files, generation prompts and an editable technical Mermaid diagram are in
`docs/images/`. They document the application; they do not add cloud inference
to its runtime.

## Work on the code

Read [AGENTS.md](../AGENTS.md) before changes. Reuse the environment and inspect
versions before changing dependencies:

```bash
.venv/bin/python -m pip show langgraph langchain-core pydantic httpx streamlit pytest
.venv/bin/python -m pytest -q
```

Keep UI, schemas, persistence, extraction, retrieval, policy and coordination
separate. SQLite writes remain parameterized and transactional. Models must not
receive persistence tools or replace deterministic safety decisions. Do not
weaken human approval to satisfy a test.

Use temporary databases and scripted inference for regression tests. Cover source
mismatches, stale hashes, unauthenticated actions, missing dates, ambiguous orders
and attempted safety bypasses. Run the real model smoke separately:

```bash
.venv/bin/python scripts/smoke_local.py --model gemma4:e2b
```

Record exact commands, results and limitations in [EVALUATION.md](../EVALUATION.md).
Do not describe mocked inference as a live test. Passing software tests does not
establish diagnostic accuracy, triage sensitivity or clinical safety.

## Acceptance checklist

The eight requested checks cover SQLite encounter integrity, documented dose
changes, missing dates, hypothesis labels, unavailable blood pressure and history,
deterministic escalation, real source linkage, and mandatory clinician approval.
Tests and evaluation results should map to these requirements. For model, prompt,
policy, schema or workflow changes, rerun affected checks. Policy changes require
an explicit version update and fresh review.

## Public GitHub publication

The publication repository is `LilyC2024/Medical-AI`; the application is named **MHCRA AI**. GitHub
hosts source code; publishing it does not deploy a clinical service or move
inference to GitHub.

Before committing, inspect the entire staged diff and confirm it contains only
source, tests, configuration, documentation and deliberately synthetic fixtures.
Exclude SQLite databases, account hashes, report exports, temporary records,
`.venv`, caches, logs, credentials and tokens. Inspect existing history too;
ignoring a previously tracked file does not remove it from history.

```bash
git status --short
git diff --check
git diff --cached --stat
git diff --cached
```

Review the outcomes in `EVALUATION.md` and precautions in [SECURITY.md](../SECURITY.md).
Do not imply an open-source redistribution license unless one has deliberately
been selected. The repository does not bundle model weights; users obtain them
separately and must comply with their applicable license.

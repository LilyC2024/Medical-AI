# MHCRA AI

**Medical History & Clinical Reasoning Assistant** is a local Python prototype for
organizing **synthetic patient records** and preparing a source-linked report for
human clinician review. It uses SQLite, LangGraph, Streamlit and an installed
Ollama model. It uses no paid APIs, cloud inference or remote tracing.

Educational and experimental. Not a diagnostic device. It does not establish
diagnoses, prescribe treatment, or make automatic medical decisions. All clinical
conclusions require clinician verification. Do not enter real patient data.

**Start here:** [visual walkthrough](#how-it-works-in-pictures) ·
[agents and orchestration](#how-the-agents-are-implemented) ·
[local setup](#run-locally) · [first demonstration](#try-the-bundled-demonstration) ·
[adapt the prototype](#adapt-the-prototype) · [validation](#test-and-evaluate).

## How it works in pictures

### Clinical workflow

![MHCRA AI workflow: synthetic records, safety routing, four specialists and clinician approval](docs/images/mhcra-ai-workflow-v1.png)

Read this illustration from left to right. SQLite supplies the synthetic source
history, and the orchestrator applies the Safety Agent before reasoning. An
explicit warning stops the case for human assessment. Missing information pauses
it for authenticated review; an approved uncertainty assessment allows the
workflow to continue. History and medication extraction then precede constrained
reasoning, a safety recheck and an unverified draft. A clinician must approve the
exact draft before it becomes a reviewed report. Requested corrections keep it
pending. The separate strip shows human approval before source imports are saved.

### Technical flow

![MHCRA AI technical architecture: Streamlit, SQLite, sequential LangGraph nodes, local Ollama and authenticated review](docs/images/mhcra-ai-technical-flow-v1.png)

The interface is Streamlit (`app.py`). Python validates a SQLite source snapshot,
then LangGraph passes it through the numbered specialist and validation nodes.
Only the Clinical Reasoning Agent sends a prompt and JSON Schema to Ollama at
`127.0.0.1:11434`; the default installed model is `gemma4:e2b`. Python validates
the returned JSON, source IDs, excerpts and attribution before composing a draft.
An authenticated review interrupt blocks completion until a matching approval
receipt exists. Completion and export recheck safety and approval integrity.

The bottom cards distinguish in-memory graph state from persistent SQLite data
and describe the supporting authentication, audit and source-traceability
components. Both urgent and uncertain cases reach the safety-review interrupt;
an urgent case can only stop. The illustrations summarize the flow; the precise
graph and module contracts are in [ARCHITECTURE.md](docs/ARCHITECTURE.md).

The PNG illustrations were generated with the built-in image tool and checked
against the implementation. Their [workflow prompt](docs/images/mhcra-ai-workflow-v1.prompt.txt),
[technical prompt](docs/images/mhcra-ai-technical-flow-v1.prompt.txt) and
[editable technical Mermaid source](docs/images/mhcra-ai-technical-flow-v1.mmd)
are included. Image generation was a documentation step; it is not an application
runtime dependency.

## How the agents are implemented

The Medical History Orchestrator coordinates four specialist roles:

| Runtime specialist | Implementation | Responsibility | Source |
| --- | --- | --- | --- |
| Medical History | `MedicalHistoryAgent.run()`; Python wrapped in LangChain `RunnableLambda` | Preserve documented versus patient-reported facts, sort known dates and identify undated entries | [history.py](medical_assistant/history.py) |
| Medication | `MedicationAgent.run()`; Python wrapped in `RunnableLambda` | Extract supplied structured orders and dated documented dose changes; request reconciliation | [history.py](medical_assistant/history.py) |
| Clinical Reasoning | `SpecialistAgent("reasoning", inference)`; Ollama structured JSON and Python validation | Select eligible synthetic hypotheses with exact source excerpts from a bounded catalog | [agents.py](medical_assistant/agents.py), [reasoning_constraints.py](medical_assistant/reasoning_constraints.py) |
| Safety | `SafetyAgent.evaluate()`; Python and a versioned JSON policy | Route cases to an urgent stop, uncertainty review hold, or ordinary workflow eligibility | [safety.py](medical_assistant/safety.py), [policy](config/safety_policy.json) |

Only the Clinical Reasoning specialist uses an LLM in the runtime workflow. The
other roles use code so models cannot invent dates or orders, change safety
routing, approve imports, or approve their own reports. LangGraph coordinates the
steps. Python composes the seven-section report.

`MedicalHistoryOrchestrator` builds a LangGraph `StateGraph(CaseState)` in
[workflow.py](medical_assistant/workflow.py). The specialists run **sequentially**
as bounded role components. Each returns structured assessments into shared case
state; the model receives grounded record entries and a compact safety context.
Original JSON stays in SQLite. Approved local evidence is retrieved before
reasoning. The graph uses `InMemorySaver`, `interrupt()` and
`Command(resume=...)` for human pauses. Hashes bind safety decisions, import
proposals and reviews to their specific contents. No model call follows final
approval, and the model receives no database, filesystem or shell tools.

The generic prompt module retains definitions for all four roles; the clinical
graph invokes its inference wrapper for reasoning only. The other three runtime
specialists use their dedicated Python implementations shown above.

### Development agents and subagents

During implementation, a primary coding agent coordinated changes and integrated
independent review subagents. These coding assistants inspected records and UI,
safety and workflow constraints, and documentation and release readiness. Their
tests and reviews helped resolve source-binding, approval-integrity, medication,
import-limit and report-rendering issues. In this documentation pass, three
review subagents checked those areas again while the primary agent updated the
README and prepared publication.

These **development subagents** are separate from the four **runtime specialist
roles**. The published app implements specialists as Python classes and graph
nodes; it does not launch the development assistants or spawn autonomous LLM
subagents. All runtime inference uses the local Ollama model. Development review
is software review, not clinician verification. See
[DEVELOPMENT.md](docs/DEVELOPMENT.md) and [EVALUATION.md](EVALUATION.md) for the
implementation process, fixes and test evidence.

## Bundled example

The bundled checklist fixture contains two encounters, a documented amlodipine
change from 5 mg to 10 mg, an undated patient symptom report and unavailable
blood-pressure measurements. These are deliberately fictional test inputs.

## Run locally

The package requires Python 3.10 or newer; CI exercises Python 3.10 and 3.12.
Use an installed Ollama server and enough local memory for the model and its
requested 16,384-token context. Performance depends on your hardware. The commands
below use a Linux/macOS shell; this release's hosted tests run on Linux. In an
existing checkout, reuse `.venv`. For a fresh checkout:

```bash
git clone https://github.com/LilyC2024/Medical-AI.git
cd Medical-AI
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
.venv/bin/python -m pip check
```

Start Ollama in another terminal if it is not already running:

```bash
OLLAMA_NO_CLOUD=1 OLLAMA_HOST=127.0.0.1:11434 ollama serve
```

For service-managed Ollama, configure these variables on the service instead.
Check that the development model is installed:

```bash
ollama list
```

The default model is `gemma4:e2b`. If its weights are absent, install them explicitly:

```bash
ollama pull gemma4:e2b
```

Dependency installation and the initial model download need internet access.
Inference and application operation use local resources after installation.

Optionally initialize the built-in synthetic records explicitly, then create a
local reviewer account. The UI also seeds these fixtures idempotently at startup:

```bash
.venv/bin/python -m medical_assistant.database
.venv/bin/python -m medical_assistant.auth
```

Seeding is idempotent: exact repeats do not duplicate encounters; conflicts roll
back. The account command prompts for a 3–80 character username using letters,
digits, `_`, `.` or `-`, and a password of at least 12
characters. Passwords are stored as salted PBKDF2 hashes. This authenticates a local
account; it does not verify professional clinical credentials.

Start the interface:

```bash
.venv/bin/python -m streamlit run app.py
```

Open [the local interface](http://127.0.0.1:8501). The checked-in Streamlit
configuration binds to loopback and disables usage telemetry. Keep the app local.

## Try the bundled demonstration

1. In the sidebar, sign in using the local account created above and select
   **Taylor Synthetic — checklist case** (`synthetic-checklist`). Leave the
   installed model as `gemma4:e2b`, or select another compatible installed local
   model. Other models have not been evaluated by this release.
2. Inspect **Longitudinal timeline and original sources** and **Medication
   reconciliation overview**. The five source facts include two encounters, the
   documented 5 mg to 10 mg dose change, and an explicitly undated symptom report.
3. Click **Generate draft for clinician review**. This fixture intentionally lacks
   current screening and blood pressure, so it pauses at **Human safety assessment
   required before reasoning**, before calling the model. This is expected.
4. Inspect the decision. A qualified reviewer can stop, or assess the synthetic
   uncertainty, provide nonempty **Safety review notes**, tick the attestation,
   choose **Continue after clinician assessment of uncertainty**, and submit.
   Do not invent observations to make the hold disappear. An urgent case cannot
   use this continuation path.
5. Inspect every section of the unverified draft and its source citations. Add
   **Review notes and required corrections**, tick the verification attestation,
   choose **Approve report** only after review, and click **Submit clinician
   review**. The default decision requests corrections and leaves it pending.
6. Approval automatically saves reviewed JSON in `data/reports/`. The interface
   offers separate JSON and Markdown downloads. Click **Start a new case** to
   unlock patient/model selection and imports for another assessment.

Review actions require a signed-in account, nonempty notes and the applicable
attestation. Local sessions expire after one hour. Record inspection and initial
generation are available without sign-in; approvals are authenticated. The live
model may fail output validation; a failed run produces no reviewed report.

## Use the two workflows

**History management:** inspect a synthetic JSON import proposal, its original
sources, extracted history and medications. An authenticated reviewer must
explicitly approve the matching proposal before it is appended to SQLite. In the
interface, expand **Import a synthetic medical record / add observations**, select
a JSON file and click **Preview JSON import**. Inspect the proposal, supply
**Import review notes**, tick the source-verification attestation and click
**Approve history import**. For an observation, use **Prepare observation
proposal** first; date and blood-pressure inputs are stored only when their
respective checkboxes are selected. Pending proposals can be discarded.
Conflicting facts or dates require manual reconciliation; the program does not
overwrite an existing original source. Built-in fixture seeding is an idempotent
development bootstrap, separate from the user import-approval workflow.

**Clinical review:** select a patient from SQLite and inspect the source record.
Current observations supplied through the interface become a synthetic import
proposal and require approval before use. Start the assessment. The deterministic
safety policy runs before clinical reasoning:

- Any structured `warning_screen="present"` in the supplied snapshot stops the
  case, including historical entries. A newer absent screen cannot clear it, and
  a reviewer cannot continue automated reasoning within that urgent case.
- Missing or uncertain current warning screening or blood pressure pauses for an
  authenticated clinician's assessment. A matching explicit decision is required
  before reasoning can begin.
- Ordinary eligibility permits reasoning; it is not a statement of clinical safety.

Inspect the generated hypotheses, evidence, missing information and safety
findings. Approve the exact report or reject it with review notes. Corrections to
facts require an explicitly approved new source import and a new assessment;
existing source/fact IDs are immutable. Unrestricted editing of generated report
text is unsupported so an approval cannot introduce uncited clinical claims.
Explicit authenticated approval is required to mark a report reviewed and enable
final export. Safety and approval integrity are checked again before completion
and export. Each case uses the SQLite snapshot captured when it starts. The
checks detect changes to that in-case snapshot, policy or assessment date; they
do not reload later database imports. Start a new case after adding facts,
including facts approved in another session.

The report contains:

1. Medical history timeline
2. Current clinical summary
3. Medication overview
4. Possible diagnostic explanations and evidence
5. Missing information
6. Safety flags
7. Questions for clinician review

## Records, sources and local references

SQLite lives at `data/medical_history.sqlite3`. Original JSON content and its
SHA-256 digest are stored separately from extracted facts. Each fact links to an
original source ID. Report citations include the original filename, known entry
date (or an explicit missing-date label), and entry ID.

See [the checklist fixture](data/patients/checklist_patient.json) for the supported
record format. Records require `"fictional": true`, a synthetic patient identifier,
and unique entry IDs. Dates may be `null`; the program never guesses them.
Structured medication and observation fields must appear in the original JSON,
not only in extracted facts. See [the schema](medical_assistant/models.py).
Imports support this JSON format, not arbitrary PDFs, OCR or EHR records.

The approved reference collection at `data/evidence/` is **empty by default**.
The app does not search the web or download medical references. Optional local
`.txt` or `.md` references need explicit manifest approval and matching file
hashes. Retrieval uses word overlap and returns at most three documents; it is
not a medical literature search. See [local evidence instructions](data/evidence/README.md).
An empty collection is disclosed in the report. It provides no verified reference
support for hypotheses.

Factual model claims must copy exact excerpts from cited record entries and
preserve documented/patient-reported attribution. Hypotheses and clinician
questions are deliberately bounded to a synthetic evaluation catalog. Unknown
sources, unsupported excerpts, invented references and out-of-contract outputs
fail closed. These engineering checks cannot establish medical correctness,
completeness or appropriateness for an actual patient.

## Adapt the prototype

Start with the bundled fixtures and tests, then make one bounded change at a time.
Copy [checklist_patient.json](data/patients/checklist_patient.json) as your format
template, keeping `fictional: true`. Use a new synthetic patient ID for a separate
case and unique entry IDs for new facts. Retain actual supplied dates or `null`;
structured medication and observation values must also exist in the original
source. Import your JSON through the approval workflow above. Histories are
limited to 100 facts and 24,000 text characters; individual JSON inputs are limited
to 100 KB. The model has a stricter combined prompt/schema budget and may reject
an otherwise valid long history.

| Intended change | Start here | Check before using it |
| --- | --- | --- |
| Add synthetic histories | `data/patients/`, `models.py`, import UI | Unique IDs, original-source grounding and explicit import approval |
| Add approved local references | `data/evidence/manifest.json` and its [instructions](data/evidence/README.md) | Human approval and exact UTF-8 content hash |
| Modify demonstration hypotheses | `reasoning_constraints.py`, `agents.py` | Eligibility, fixed vocabulary, source/attribution validation and regression tests |
| Change workflow routing | `workflow.py`, `safety.py`, `config/safety_policy.json` | Versioned policy, approval guards and attempted-bypass tests |
| Change presentation | `app.py`, `report.py` | Source escaping, uncertainty labels and authenticated review/export behavior |

The hypothesis catalog uses simple demonstration eligibility rules: a medication
entry or structured order allows a medication-related possibility, and a
whole-word mention of sleep allows a sleep-related possibility, even in negated
text. These rules do not demonstrate clinical relevance or causation. Changes
need appropriate clinician review and evaluation before any broader use.

The repository has **no selected redistribution license**. Review that status and
the dependency/model licenses before copying, distributing or incorporating it
into another project. Model weights are obtained separately. GitHub publication
shares source; it does not deploy or clinically validate this application.

## Test and evaluate

```bash
.venv/bin/python -m pytest -q
.venv/bin/python scripts/check_ollama.py gemma4:e2b
.venv/bin/python scripts/smoke_local.py --model gemma4:e2b
```

Automated tests use temporary SQLite databases, scripted models and mocked HTTP;
they do not demonstrate real model performance or clinical validity. The smoke
script separately exercises the real local model without approving a final
clinical report. Consult [EVALUATION.md](EVALUATION.md) for actual outcomes and
limitations from this checkout, including the eight acceptance checklist items.

See [architecture](docs/ARCHITECTURE.md) for the graph and module boundaries,
[development](docs/DEVELOPMENT.md) for how agents and the LLM were used, and
[security](SECURITY.md) for the local threat model and publication precautions.
The complete source/test/documentation inventory is in [FILE_INVENTORY.md](docs/FILE_INVENTORY.md).

## Limits

This is a single-machine demonstration, not a production clinical service.
Pending graph checkpoints, reviewer sessions and import proposals are in memory;
restarting or resetting the session loses pending work. SQLite originals,
accounts and audit events persist. Exported reports persist if saved locally.
The database and exports are not encrypted by the application.

The policy checks explicit structured warning fields and current-day observations
in the Europe/Amsterdam timezone. It cannot recognize every emergency from free
text and is not a validated clinical triage protocol. Missing information is
uncertainty. If urgent help is needed, do not wait for this prototype.

Small models can omit or misinterpret information. Oversized model requests fail
rather than silently truncate sources. There is no cloud fallback. Local accounts
and approval receipts protect the normal application workflow; anyone controlling
the Python process, database or source can alter it. Do not expose Streamlit or
Ollama to the public internet.

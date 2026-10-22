# MHCRA AI

**Medical History & Clinical Reasoning Assistant** is a local Python prototype for
organizing **synthetic patient records** and preparing a source-linked report for
human clinician review. It uses SQLite, LangGraph, Streamlit and an installed
Ollama model. It uses no paid APIs, cloud inference or remote tracing.

Educational and experimental. Not a diagnostic device. It does not establish
diagnoses, prescribe treatment, or make automatic medical decisions. All clinical
conclusions require clinician verification. Do not enter real patient data.

## What the program does

The Medical History Orchestrator coordinates four specialist roles:

| Runtime specialist | Implementation | Responsibility |
| --- | --- | --- |
| Medical History | Deterministic Python with LangChain `RunnableLambda` | Preserve documented versus patient-reported facts, sort known dates and identify undated entries |
| Medication | Deterministic Python with `RunnableLambda` | Extract supplied structured orders and dated documented dose changes; request reconciliation |
| Clinical Reasoning | Ollama structured JSON inference and Python validation | Select eligible synthetic hypotheses with exact source excerpts from a bounded catalog |
| Safety | Deterministic Python and a versioned JSON policy | Route cases to an urgent stop, uncertainty review hold, or ordinary workflow eligibility |

Only the Clinical Reasoning specialist uses an LLM in the runtime workflow. The
other roles use code so models cannot invent dates or orders, change safety
routing, approve imports, or approve their own reports. LangGraph coordinates the
steps. Python composes the seven-section report.

The bundled checklist fixture contains two encounters, a documented amlodipine
change from 5 mg to 10 mg, an undated patient symptom report and unavailable
blood-pressure measurements. These are deliberately fictional test inputs.

## Run locally

Use Python 3.10 or newer and an installed Ollama server. In an existing checkout,
reuse `.venv`. For a fresh checkout:

```bash
git clone https://github.com/LilyC2024/Medical-AI.git
cd Medical-AI
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
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

Initialize the built-in synthetic records and create a local reviewer account:

```bash
.venv/bin/python -m medical_assistant.database
.venv/bin/python -m medical_assistant.auth
```

Seeding is idempotent: exact repeats do not duplicate encounters; conflicts roll
back. The account command prompts for a username and password of at least 12
characters. Passwords are stored as salted PBKDF2 hashes. This authenticates a local
account; it does not verify professional clinical credentials.

Start the interface:

```bash
.venv/bin/python -m streamlit run app.py
```

Open [the local interface](http://127.0.0.1:8501). The checked-in Streamlit
configuration binds to loopback and disables usage telemetry. Keep the app local.

## Use the two workflows

**History management:** inspect a synthetic JSON import proposal, its original
sources, extracted history and medications. An authenticated reviewer must
explicitly approve the matching proposal before it is appended to SQLite.
Conflicting facts or dates require manual reconciliation; the program does not
overwrite an existing original source. Built-in fixture seeding is a separate,
explicit development initialization action.

**Clinical review:** select a patient from SQLite and inspect the source record.
Current observations supplied through the interface become a synthetic import
proposal and require approval before use. Start the assessment. The deterministic
safety policy runs before clinical reasoning:

- An explicit warning-sign report stops the case. A reviewer cannot continue
  automated reasoning within that urgent case.
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
and export. A changed policy, date or record requires restarting review.

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

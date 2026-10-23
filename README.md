# LOVISA

**Medical History & Clinical Reasoning Assistant**

LOVISA is a local research prototype that turns **synthetic patient records** into
a chronological, source-linked report for clinician review. It combines SQLite,
LangGraph, Streamlit and local Ollama inference. The former project name was
**MHCRA AI**. LOVISA is the project name; its medical-history and clinical-reasoning
function remains the same.

## Two projects, one reviewed workflow

| Project | Input → output | Responsibility |
| --- | --- | --- |
| **LOVISA** — this repository | Synthetic history → seven-section clinical draft | Organize facts, identify gaps, propose constrained hypotheses and require clinician approval |
| **[Lung CT Research Assistant](https://github.com/LilyC2024/ai-medimg-2.5D-CT)** | Supported CT → nodule candidates, annotations, calipers and research summary | Support source-image inspection and measurement in a separate local environment |

The CT companion can send a validated **synthetic** study to LOVISA. A reviewer
checks its candidates and measurements before accepting it as a research appendix.
The combined clinical draft then requires separate final approval. Images and
imaging notes stay outside the language model. [Integration guide](docs/IMAGING.md).

**Research and education only.** Neither project diagnoses cancer, excludes
disease, prescribes treatment or makes automatic medical decisions. LOVISA accepts
fictional records only. Local login does not verify clinical qualifications.

## Understand the workflow

![LOVISA clinical workflow, illustrated under its former MHCRA AI name](docs/images/mhcra-ai-workflow-v1.png)

Read left to right: local records → safety check → history and medication
extraction → source-grounded hypotheses → safety recheck → clinician review.
An urgent warning stops reasoning. Missing safety information pauses for human
assessment. A draft becomes reviewed only after explicit approval of its exact
contents. The retained picture uses the previous **MHCRA AI** name.

![Synthetic CT source, candidate box and demonstration caliper](docs/images/lung-research-workflow.png)

The companion adds image evidence: source slice → candidate annotation → physical
caliper. This picture uses generated pixels and a **non-ML fixture finder**. Its
8 mm caliper illustrates software behavior; it is not a clinical finding or a
pretrained-detector accuracy result.

## Agents and models

One `MedicalHistoryOrchestrator` runs four sequential specialist roles:

| Specialist | Implementation | Purpose |
| --- | --- | --- |
| History | Python `MedicalHistoryAgent` | Preserve dates, attribution and missing chronology |
| Medication | Python `MedicationAgent` | Extract supplied orders and documented dose changes |
| Clinical reasoning | `SpecialistAgent("reasoning", inference)` + local Ollama | Select eligible hypotheses with exact source excerpts |
| Safety | Python `SafetyAgent` + versioned policy | Enforce urgent stops and uncertainty-review holds |

Only clinical reasoning calls the installed `gemma4:e2b` LLM. Python validates its
JSON and citations, calculates measurements and composes the report. The CT
companion uses pretrained MONAI 3D RetinaNet; it has no LLM agents. Development
coding subagents helped earlier reviews but are not part of either app's runtime.
[Architecture and agent implementation](docs/ARCHITECTURE.md).

![LOVISA technical architecture, illustrated under its former MHCRA AI name](docs/images/mhcra-ai-technical-flow-v1.png)

Streamlit supplies the interface; SQLite preserves original sources separately
from extracted facts; LangGraph coordinates specialist steps and human interrupts.
Ollama runs on loopback. Completion/export recheck safety, source integrity and
approval. The detailed [picture guide](docs/ILLUSTRATIONS.md) explains the diagrams
and the CT connection.

## Run LOVISA

Use Python **3.10+** and an installed local Ollama service with `gemma4:e2b`.
Reuse `.venv` if present. For a fresh Linux/macOS checkout:

```bash
git clone https://github.com/LilyC2024/Medical-AI.git
cd Medical-AI
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
.venv/bin/python -m medical_assistant.auth
.venv/bin/python -m streamlit run app.py
```

Open [localhost:8501](http://127.0.0.1:8501) and select **Taylor Synthetic — checklist
case**. The app seeds fictional examples automatically. Its missing blood pressure
and warning screening intentionally trigger review. [Complete setup](docs/SETUP.md)
includes local Ollama configuration and Windows paths;
[first-case instructions](docs/WORKFLOWS.md) explain every approval.

Install CT separately with Python **3.12**. The integration supports nodule-v2 and
legacy tissue-mask bundles within a synthetic limit of **64 slices ×256×256**.
Full-size/public-research CT and training remain standalone companion features.
Existing `mhcra-*` formats and `MHCRA_CT_*` settings are stable integration names.
[Naming and compatibility](docs/NAMING.md) · [CT setup](docs/IMAGING.md).

## Documentation and evidence

| Read next | Purpose |
| --- | --- |
| [Documentation index](docs/README.md) | Choose a guide by task |
| [Architecture](docs/ARCHITECTURE.md) | Specialists, storage, models and trust boundaries |
| [Records](docs/RECORDS.md) | Synthetic JSON, sources and local references |
| [Imaging](docs/IMAGING.md) | Connect, inspect, measure and accept CT results |
| [Code reference](docs/CODE_REFERENCE.md) | Modules, functions and folders |
| [Validation](docs/VALIDATION.md) / [Evaluation](EVALUATION.md) | Reproduce checks; distinguish tests from actual inference |
| [Release history](docs/RELEASE.md) | Changes, naming and migration |

The last compatibility release passed **146 LOVISA tests and 81 CT tests**, real
local CT/Ollama smokes and hosted checks. Current documentation/branding validation
is recorded separately in [EVALUATION.md](EVALUATION.md).

Operation uses no paid APIs, cloud inference or remote tracing. Setup may download
packages and weights explicitly. Keep both apps local; pending work is in memory
and disk storage is not encrypted. [Security](SECURITY.md) ·
[Contributing](CONTRIBUTING.md). LOVISA has no selected project-wide redistribution
license; [vendored CT components retain MIT terms](third_party/README.md).

# Records, references and extension rules

[Overview](../README.md) · [Architecture](ARCHITECTURE.md)

SQLite lives at `data/medical_history.sqlite3`. Original JSON content and its
SHA-256 digest are stored separately from extracted facts. Each fact links to an
original source ID. Report citations include the original filename, known entry
date (or an explicit missing-date label), and entry ID.

See [the checklist fixture](../data/patients/checklist_patient.json) for the supported
record format. Records require `"fictional": true`, a synthetic patient identifier,
and unique entry IDs. Dates may be `null`; the program never guesses them.
Structured medication and observation fields must appear in the original JSON,
not only in extracted facts. See [the schema](../medical_assistant/models.py).
Imports support this JSON format, not arbitrary PDFs, OCR or EHR records.

The approved reference collection at `data/evidence/` is **empty by default**.
The app does not search the web or download medical references. Optional local
`.txt` or `.md` references need explicit manifest approval and matching file
hashes. Retrieval uses word overlap and returns at most three documents; it is
not a medical literature search. See [local evidence instructions](../data/evidence/README.md).
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
Copy [checklist_patient.json](../data/patients/checklist_patient.json) as your format
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
| Add approved local references | `data/evidence/manifest.json` and its [instructions](../data/evidence/README.md) | Human approval and exact UTF-8 content hash |
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

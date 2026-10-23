# Synthetic records and local references

[Overview](../README.md) · [Import workflow](WORKFLOWS.md) · [Schemas](../medical_assistant/models.py)

## Supported history input

Use [checklist_patient.json](../data/patients/checklist_patient.json) as the template.
Records require `fictional: true`, a synthetic patient ID and unique entry IDs.
Supported input is structured JSON, not PDF, OCR or EHR import. A fictional flag
is not proof of privacy: manually inspect every source.

| Field or content | Rule |
| --- | --- |
| Dates | Preserve supplied values or `null`; never estimate |
| Attribution | Keep documented and patient-reported entries distinct |
| Medication orders | Dose/frequency must exist in original structured JSON |
| Observations | Include only supplied measurements and selected date fields |
| Identity | Exact repeats are idempotent; changed immutable IDs fail |
| Limits | 100 KB per JSON input; cumulative 100 facts and 24,000 text characters |

SQLite at `data/medical_history.sqlite3` separates immutable original JSON/SHA-256
from extracted facts. Each fact links to a source ID. Reports cite filename,
known date or missing-date label, and entry ID. Writes are parameterized and
transactional; the model has no persistence tools. [Approval procedure](WORKFLOWS.md).

## Local reference evidence

The reference collection at `data/evidence/` is empty by default. LOVISA discloses
that no approved reference support was retrieved. It performs no web search or
automatic literature download.

A human may add permitted `.txt`/`.md` excerpts and explicitly approve their IDs,
titles, relative paths and SHA-256 in the manifest. Retrieval checks the hash,
uses word overlap and returns at most three items. This is a small local lookup,
not a clinical literature search. [Manifest instructions](../data/evidence/README.md).

## Grounding and extension

Model facts need actual source IDs, exact excerpts and correct attribution.
Unknown labels, invented references or unsupported statements block the draft.
The synthetic hypothesis catalog is deliberately small: medication and whole-word
sleep mentions permit corresponding possibilities, even when sleep is negated.
These are demonstration eligibility rules, not diagnostic evidence.

| Change | Start with | Preserve |
| --- | --- | --- |
| Add fictional histories | `data/patients`, import UI, models | Original source and authenticated approval |
| Add local references | Evidence manifest | Permissions, approval and exact content hash |
| Extend hypotheses | reasoning_constraints.py, agents.py | Eligibility/source checks and clinician review |
| Change safety | Versioned policy, safety.py | Python routing and attempted-bypass tests |
| Extend CT | Shared contract, imaging services | Synthetic boundary and separate final approval |

Keep source corrections explicit and start a new case after importing. The model
has a stricter prompt/schema budget than history storage and may reject a long
valid record. Tests establish consistency, not clinical correctness. LOVISA has
no selected project-wide redistribution license; CT-vendored files have separate
[MIT terms](../third_party/README.md).

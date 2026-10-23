# Five complex artificial demonstrations

[Overview](../README.md) · [Operation](WORKFLOWS.md) · [Evaluation](../EVALUATION.md)

These are deliberately authored fictional software fixtures, not patient records.
They appear in the signed-in patient selector and **Five complex artificial demo
cases** list. The original Alex and Taylor fixtures remain available too.

| Case / ID | Complexity and intended check | Source |
| --- | --- | --- |
| Morgan / demo-01 | Two medicines, 5→10 mg change, historical seated BP, undated OTC/sleep-tablet report and standing lightheadedness | [demo_morgan.json](../data/patients/demo_morgan.json), 2 Aug–12 Sep 2026 plus undated report |
| Riley / demo-02 | Cough documented before the prescription change, missing smoking detail and a separate optional CT demonstration | [demo_riley.json](../data/patients/demo_riley.json), 8 Jul–1 Oct 2026 plus undated report |
| Sam / demo-03 | Fatigue, sleep/shift history with contrary follow-up, fictional laboratory values and an unidentified supplement | [demo_sam.json](../data/patients/demo_sam.json), 11 Jun–17 Sep 2026 plus undated entry |
| Casey / demo-04 | Past history/procedure, breathlessness/chest discomfort and an explicit structured warning flag | [demo_casey.json](../data/patients/demo_casey.json), 13 Aug–2 Oct 2026 plus undated reports |
| Avery / demo-05 | 5→10→5 mg orders versus reported 10 mg use, fictional renal laboratory result, swelling and incomplete follow-up | [demo_avery.json](../data/patients/demo_avery.json), 1 Jul–5 Sep 2026 plus undated report |

Morgan, Riley, Sam and Avery intentionally lack required current safety data:
review the listed gaps before enabling draft generation. Casey must stop; the
model is never called. Exact dates remain exact and undated entries stay undated.
A CT generated for any case is a separate phantom, not an illustration of the
symptoms or laboratory results in that fictional history.

Automated tests load all five from temporary SQLite twice to check idempotence,
validate original sources/unknown dates/dose changes, exercise staged safety and
check concise source-linked drafts. They use **scripted inference/reviewers** and
never establish clinical correctness. Tests for Casey verify the mandatory stop.
The actual local Ollama smoke is separate and does not issue clinician approval.

The hypothesis catalog remains deliberately small: medication contribution,
sleep contribution or insufficient information. These examples do not add cancer,
anemia or other diagnostic capabilities. CT scores are not malignancy estimates;
measurements require review. [Architecture](ARCHITECTURE.md).

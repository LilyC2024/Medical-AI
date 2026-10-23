# Artificial combined-report example

[Report guide](../REPORTS.md) · [Project overview](../../README.md)

**Software demonstration only: inference, safety acknowledgement, image acceptance
and final approval are scripted in a temporary test database. No clinician
reviewed this example.**

[Open the self-contained HTML](clinical-summary.html) to see the short text,
source CT and reviewed annotation together. [Markdown](clinical-summary.md) has
the same report text without embedded images. Both use one Clinical summary
heading; the example is under 200 whitespace-separated words.

The local non-ML fixture worker generated a 32×64×64 artificial phantom. A scripted
reviewer placed an 8.00 mm caliper inside its candidate box. The value demonstrates
geometry/software behavior, not an observed lesion or detector accuracy. The
history is Taylor's authored fictional fixture. The model output is scripted,
separate from the actual Ollama smoke recorded in [Evaluation](../../EVALUATION.md).

The example was composed/exported through the same verified workflow as the app.
Regression coverage lives in [combined report tests](../../tests/test_combined_report.py),
[image/export tests](../../tests/test_report_assets.py) and
[combined UI tests](../../tests/test_combined_report_ui.py). The temporary account,
password, database and approval receipts are not distributed.

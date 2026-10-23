# First case and review workflows

[Overview](../README.md) · [Setup](SETUP.md) · [Imaging](IMAGING.md)

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

## History and clinical review

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
The UI gives newly supplied structured warnings priority over optional image
inspection and blocks review/download of an older case until a new case starts.

The report contains:

1. Medical history timeline
2. Current clinical summary
3. Medication overview
4. Possible diagnostic explanations and evidence
5. Missing information
6. Safety flags
7. Questions for clinician review

Accepted research imaging appears as an appendix within the seven-section draft.
Its source bundle, model/source hashes, unknown acquisition date, candidate decisions, caliper/source-plane measurements
and review attribution are included in the exact text covered by final approval.

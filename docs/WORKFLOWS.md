# Use LOVISA: records, CT and final review

[Overview](../README.md) · [Setup](SETUP.md) · [Imaging details](IMAGING.md)

## First synthetic case

1. Sign in and select **Taylor Synthetic — checklist case** (`synthetic-checklist`).
   Keep the installed model `gemma4:e2b`.
2. Open **Patient overview**. Inspect the timeline, original sources and medication overview. The fixture has
   five facts, two encounters, an amlodipine 5 mg → 10 mg documented change and an
   undated patient report. These are fictional software-test inputs.
3. Click **Generate draft for clinician review**. Progress/cancel appears immediately;
   completion opens **Clinical report**. Missing current screening/blood
   pressure triggers **Human safety assessment required before reasoning**.
4. Review the uncertainty. To continue, an authorized reviewer supplies safety
   notes, the attestation and **Continue after clinician assessment of uncertainty**.
   Choosing stop ends the case. An urgent case cannot use this continuation path.
5. Inspect the draft, exact source citations, hypotheses and missing information.
   Enter review notes, attest verification, select **Approve report** and submit
   only after review. The default requests corrections and keeps the draft pending.
6. Valid approval saves JSON under ignored `data/reports/` and enables JSON/Markdown
   downloads. **Start a new case** before changing patient, sources or accepted CT.

Approvals require login, nonempty notes, attestation and matching content hashes.
Sessions expire after one hour. Inspection/initial generation can run without login;
approvals cannot. Invalid model output produces no reviewed report.

## Import a new synthetic source

Open **Import a synthetic medical record / add observations**. Upload supported
JSON and select **Preview JSON import**. Inspect original sources, extracted facts
and discrepancies. Enter import notes, attest source verification and approve the
matching proposal. Pending proposals can be discarded without importing.

Observation controls create proposals too. Date/blood-pressure values are included
only when their checkboxes are selected. Defaults are not observations. IDs and
originals are immutable; conflicts need reconciliation, not overwriting. Bundled
fixture seeding is a separate development bootstrap. [Record format](RECORDS.md).

## Add CT research evidence

Before starting a clinical case, open **CT review**. Generate a synthetic
fixture/pretrained study or inspect an uploaded synthetic bundle. Review source
slices, every candidate and optional calipers, then explicitly accept it for the
research appendix. Pending imaging blocks draft generation. CT attestation,
LOVISA imaging acceptance and final report approval remain separate.

Start a new clinical case to include the accepted study. Pixels/notes are excluded
from language-model reasoning. [Full CT procedure](IMAGING.md).

## Safety and snapshot rules

| Situation | Required behavior |
| --- | --- |
| Any supplied structured warning is present | Urgent human assessment; no reasoning continuation in that case |
| Current screening/BP is missing or uncertain | Authenticated uncertainty assessment before reasoning |
| Ordinary workflow eligibility | Reasoning may proceed; this is not proof of safety |
| New source or CT accepted after case start | Start a new case; existing snapshot remains fixed |
| Newly supplied warning outside an active snapshot | Old review/download is blocked; start a new case |
| Report corrections requested | Draft remains pending; factual corrections go through a new approved source |

The seven report sections are timeline, current summary, medications, possible
explanations/evidence, missing information, safety flags and clinician questions.
Accepted CT appears as a research appendix within those sections. Final approval
covers its source IDs/hashes, decisions, measurements and reviewer attribution.

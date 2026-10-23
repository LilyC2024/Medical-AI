# Use LOVISA: review first, generate second

[Overview](../README.md) · [Setup](SETUP.md) · [Five complex cases](DEMO_CASES.md)

## First synthetic case

1. **Sign in.** All patient examples, CT and report controls stay hidden until
   authenticated. Select Taylor or one of the five complex fictional cases.
2. Read **Patient overview**. Check dates, attribution, medicines and original
   sources in **Source records**. Import/approve any synthetic corrections there
   before preparing the case.
3. Optionally open **CT review** and **Run CT analysis**. The completed result
   opens automatically: candidate count, review status, source slices, annotations
   and optional calipers. Inspect and accept it, or discard it. A pending study
   blocks the safety preparation so it cannot be silently omitted from the draft.
4. Open **Safety check** using its tab, **Next action**, or guide step 4. For
   missing current information, add assessment notes, tick the review checkbox,
   choose **Allow draft generation after my safety assessment**, and **Save safety
   assessment**. This saves the decision and freezes the snapshot; **no model
   runs yet**. Choosing **Keep analysis paused** ends this case for human review.
   When the required current structured observations are supplied, use **Confirm
   required safety checks** instead. An urgent warning blocks generation outright.
5. Only after these checks does **Generate draft for clinician review**, at the
   bottom of Safety check, become enabled. Click it to run local reasoning.
   Progress/cancel stays in that view; completion opens **Clinical report**.
6. Read the single **Clinical summary** section. It combines the local model's
   history hypotheses, accepted CT inspection, essential gaps and clinician note.
   Source/annotation pictures appear beneath it. Detailed citations are in the
   collapsed evidence view and JSON package, not repeated through the prose.
7. Enter a brief clinician note (up to 600 characters) and **Preview note in report**.
   Read the changed draft, tick the review checkbox again, choose **Approve report**
   and submit. The default requests corrections and keeps the draft pending.
   Approval saves ignored local JSON and enables HTML, Markdown and JSON downloads.
   HTML embeds CT pictures for offline use; Markdown contains the concise text.

If the report has no CT, **Start a new report with CT** opens CT review for the
same patient. Accept the study before safety preparation; a study added later
requires a new report snapshot.

Use **Start a new review** to reassess the same patient after a source change.
You can choose another patient at any time: unfinished work is cancelled and all
notes/proposals/report controls are cleared. Stored accepted records remain
patient-specific. Sign-out or session expiry hides all patient content.

Every button in **Your review steps** opens and scrolls to the relevant section.
If safety is blocked by pending CT/history, use **Open pending changes**, then
accept or discard that proposal. Navigation never approves anything.

## Safety is a workflow boundary

| Situation | What the page does |
| --- | --- |
| Any supplied structured warning is present | Blocks generation and optional CT work; requires human assessment |
| Current screening/BP missing or uncertain | Lists the gaps; requires an authenticated, attested assessment before generation |
| Required current structured observations supplied | Allows snapshot confirmation; this is not a clinical safety finding |
| Source/policy/date changes after preparation | Blocks the old case; start a new one |
| Safety saved but Generate not clicked | No clinical model call |
| Draft generated but final review incomplete | No reviewed export |

These rules are local prototype safeguards, not regulatory certification or a
claim of medical-device compliance. The model cannot lower escalation.

## Import a source

Open **Source records**, then **Import a synthetic medical record / add observations**. Preview supported
JSON or observation controls; inspect the proposal, add notes/attestation and
approve the exact import. Dates/measurements are included only when explicitly
supplied. Defaults are not observations. Originals and IDs are immutable.
[Record format](RECORDS.md) · [Detailed CT review](IMAGING.md).

## Image-first endoscopy extension

Before safety preparation, optionally inspect and accept an endoscopy study in **Endoscopy review**. Resolve every region, add a note and attest inspection; final report approval remains separate. [Image workflow](ENDOSCOPY.md).

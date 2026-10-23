# Use LOVISA: review first, generate second

[Overview](../README.md) · [Setup](SETUP.md) · [Five complex cases](DEMO_CASES.md)

## First synthetic case

1. **Sign in.** All patient examples, CT and report controls stay hidden until
   authenticated. Select Taylor or one of the five complex fictional cases.
2. Read **Patient overview**. Check dates, attribution, medicines and original
   sources. Import/approve any synthetic corrections before preparing the case.
3. Optionally open **CT review** and **Run CT analysis**. The completed result
   opens automatically: candidate count, review status, source slices, annotations
   and optional calipers. Inspect and accept it, or discard it. A pending study
   blocks the safety preparation so it cannot be silently omitted from the draft.
4. At the **bottom of the page**, read **Before you generate the draft**. For
   missing current information, add assessment notes, tick the review checkbox,
   choose **Allow draft generation after my safety assessment**, and **Save safety
   assessment**. This saves the decision and freezes the snapshot; **no model
   runs yet**. Choosing **Keep analysis paused** ends this case for human review.
   When the required current structured observations are supplied, use **Confirm
   required safety checks** instead. An urgent warning blocks generation outright.
5. Only after these checks does the bottom **Generate draft for clinician review**
   button become enabled. Click it to run local reasoning. Progress/cancel remains
   at the bottom; completion opens **Clinical report**.
6. Read the concise seven-section draft. Source text appears once in the timeline;
   `[S1]` evidence keys refer to filename/date/entry IDs in **Source key**. CT is a
   short research appendix. The JSON export retains full provenance and decisions.
7. Enter final review notes and attestation; choose **Approve report** and submit
   only after review. The default requests corrections and keeps the draft pending.
   Approval saves ignored local JSON and enables JSON/Markdown downloads.

**Start a new case** before changing a prepared patient/source/CT snapshot.
Signing out or session expiry hides all case controls and cancels session work.
Unsubmitted safety choices are cleared when the patient changes.

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

Open **Import a synthetic medical record / add observations**. Preview supported
JSON or observation controls; inspect the proposal, add notes/attestation and
approve the exact import. Dates/measurements are included only when explicitly
supplied. Defaults are not observations. Originals and IDs are immutable.
[Record format](RECORDS.md) · [Detailed CT review](IMAGING.md).

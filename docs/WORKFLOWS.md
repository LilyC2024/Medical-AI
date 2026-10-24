# Operate LOVISA: one case, explicit review

[Overview](../README.md) · [Setup](SETUP.md) · [Interface](INTERFACE.md)

## 1. Sign in and select a fictional case

No case opens automatically. Sign in, choose one patient and read **Patient
overview**: dated/undated entries, documented versus reported statements and
historical medication orders. **Source records** shows original wording and input
downloads. Correct facts through an explicitly approved synthetic import, never
by editing a generated note. [Fixtures and intended behavior](DEMO_CASES.md).

## 2. Add optional image evidence

Open **CT review** or **Endoscopy review**, then **Upload → Analyze**.

| Input | What Analyze does |
| --- | --- |
| CT companion review ZIP | Validate and open existing source/candidate results; no full-volume model rerun |
| Endoscopy review ZIP | Validate and open included source/probability/region evidence |
| Exact permitted research-kit endoscopy JPG/PNG | Run the installed local polyp model on those bytes |
| Model/example choice without an upload | Generate the explicit artificial example or open Jordan's prepared research result |

An upload takes precedence over example selection. Remove it to use an example.
Full DICOM inference and arbitrary research-image preparation remain companion
work. For public files select **Jordan — real-image research composite**; its
CT and endoscopy subjects are unrelated to each other and the fictional history.
[Research files and permissions](RESEARCH_IMAGES.md).

Inspect source and annotations, resolve every candidate, optionally add a note,
and explicitly include the study. Uncertain blocks inclusion. A checked default
confirmation submits nothing. Alternatively discard the pending proposal.
Only one pending image review is shown at a time; the page links to it directly.
[CT/calipers](IMAGING.md) · [Endoscopy](ENDOSCOPY.md).

## 3. Complete the safety assessment

Use **Safety check**, **Next action**, or its right-hand guide link. Pending record
or image proposals must be resolved first; **Open pending changes** goes to the
correct view. Urgent structured warnings block reasoning and optional imaging.

For missing current information, review the actual listed gaps, optionally add
notes, keep the attestation selected, choose **Allow draft generation after my
safety assessment**, and **Save safety assessment**. Choosing **Keep analysis
paused** stops the case for human assessment. With required observations supplied,
use **Confirm required safety checks** instead. Neither path establishes medical
safety or calls the LLM yet; it freezes a workflow snapshot.

## 4. Generate and inspect the draft

Only then does **Generate draft for clinician review**, at the bottom of Safety
check, become eligible. Progress/cancellation is immediate; completion opens
**Clinical report**. A missing model, capacity limit, timeout or validation failure
shows an escaped bounded reason; no fallback invents findings or approves output.

The report has one **Clinical summary** section: constrained history hypotheses,
accepted CT/endoscopy observations, essential uncertainty and optional clinician
commentary. Verified source/annotation pictures appear below. Exact excerpts and
IDs remain in the evidence package and optional readable view, not throughout
the short prose. [Format](REPORTS.md).

## Audit replay

**Clinical report** ends with an **Audit trail** expander: each import, safety
decision, note preview, imaging acceptance and final decision for the selected
patient, with who did it and whether its receipt verifies under the current key.
It is read-only. Set `LOVISA_TRACE_FILE=/path/traces.jsonl` before launch for
redacted local step timings.

## 5. Review, approve and export

An initially blank, unchanged final note needs no preview. Preview every changed
note, including clearing a previously previewed comment: select **Preview note
in report** and read the revised content first. Retain attestation,
choose **Approve report** and explicitly submit. The default requests corrections.
No viewed image, checked box, navigation action or LLM response counts as approval.

Approval enables HTML, Markdown and JSON downloads. HTML embeds verified pictures
for offline use; Markdown is the concise prose; JSON retains exact source/model/
image/review evidence. Saving/export recheck content, safety and artifacts.

## Change, retry or leave a case

- Valid Upload/Analyze after preparation starts a fresh unreviewed context and
  requires image inclusion/safety again; saved reports and the old snapshot stay intact.
- Invalid input leaves the old context intact and displays a retryable error.
- Worker saturation preserves safety state; retry after a slot is free. A failed
  analysis cannot publish a late draft or enable export.
- Changing patient cancels unfinished work and clears its notes/proposals.
- Sign-out/session expiry hides all case controls; restart loses pending sessions.
- New source/policy/date requires a new review; an old approval cannot authorize it.

These gates are prototype safeguards, not regulatory certification or a comprehensive
clinical triage protocol. [Security](../SECURITY.md) · [Troubleshooting](VALIDATION.md).

# Concise clinical summary with reviewed imaging

[Overview](../README.md) · [Operation](WORKFLOWS.md) · [Endoscopy](ENDOSCOPY.md)

One **Clinical summary** section contains short labelled paragraphs. Full timelines,
filenames, source IDs and hashes stay in the evidence package.

| Content | Source |
| --- | --- |
| AI history analysis | Local Ollama selects bounded hypotheses/evidence; Python validates them |
| CT inspection | Accepted CT candidates and reviewer-placed calipers |
| Endoscopy inspection, when included | Accepted artificial RGB studies, region decisions and predicted mask areas in pixels |
| Essential gaps | Versioned safety rules and source-bound missing information |
| Clinician note | Authenticated, previewed reviewer comment; up to 600 characters |
| Representative pictures | Verified source and annotation pairs from up to three studies |

The LLM analyzes history, not imaging pixels. Imaging paragraphs are composed in
Python from accepted structured observations. No model score becomes a cancer
probability, physical endoscopy measurement, symptom explanation or diagnosis.

## Include imaging before safety preparation

Inspect and explicitly accept CT/endoscopy **before** preparing safety. Preparation
freezes accepted studies into the report. Pending/discarded studies are not included;
new imaging requires a new review. CT review retains all source slices; Endoscopy
review retains its source image and overlay. The prose covers every accepted study;
representative pictures and short measurement lists are bounded. Exact artifacts
and full decisions remain available in the local store/evidence package.

## Note and final approval

Enter a brief note and choose **Preview note in report**. The draft updates and the
confirmation returns to its selected default; no LLM call or approval occurs. Read the new text/images,
confirm review and explicitly approve. Notes have signed, case-bound authorship;
new source facts require an approved import, not a note. An old approval cannot
approve changed content.

## Downloads and provenance

- **HTML:** concise text and embedded source/annotation pictures; opens offline.
- **Markdown:** the same concise text, including reviewed imaging findings.
- **JSON:** original record excerpts, source links, model evidence, imaging
  provenance/decisions and approval receipts. Original imaging archives remain
  in the local store.

Every final export/save rechecks source artifacts, image acceptance, note authorship,
evidence and approval of the full content manifest. Images cannot be substituted
even when the short prose stays identical. HTML uses no external assets/scripts.
Visible citations remain simple; exact evidence is preserved and validated.

## Existing illustration

![Earlier CT/history summary example](images/lovisa-combined-summary.jpg)

This earlier example uses artificial pixels, scripted model output and a scripted
reviewer. It demonstrates layout, not clinical accuracy or actual clinician review.
[Offline example](examples/clinical-summary.html). Endoscopy adds a short inspection
paragraph and its image pair when an accepted study exists. Existing saved reports
retain their original content/approval and are not rewritten.

## Short imaging results

The CT line gives proposed/accepted counts, any accepted reviewed calipers and
limited public-excerpt coverage. Endoscopy gives proposed/accepted regions, with
no invented physical size or histology. Model metadata and raw source identifiers
remain in bound evidence. A composite notice prevents cross-subject interpretation.
Notes may be blank; blank final notes need no preview. A changed nonempty note
still requires preview before explicit approval. [Real-image case](RESEARCH_IMAGES.md).

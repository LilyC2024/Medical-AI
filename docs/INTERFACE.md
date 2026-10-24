# Patient workspace and design system

[Overview](../README.md) · [Walkthrough](WORKFLOWS.md) · [Budgets](PERFORMANCE.md)

## Six focused views

Sign in and explicitly choose one fictional patient. The menu lists examples;
the body displays only the selected case. The right-hand **Your review steps**
links open and scroll to the relevant action. **Next action** prioritizes pending
record/image changes, safety and report review. Navigation never supplies approval.

| View | Purpose |
| --- | --- |
| Patient overview | Dated/undated history, attribution and historical medicines |
| CT review | Upload/Analyze a review ZIP or example; inspect candidates and optional physical calipers |
| Endoscopy review | Upload/Analyze a permitted image or ZIP; inspect source/overlay and decide each region |
| Safety check | Review policy gaps, save an assessment, then generate a draft |
| Clinical report | One concise summary with accepted pictures, brief note and final approval |
| Source records | Original wording/downloads and explicitly approved synthetic imports |

On narrow screens the guide stacks below the workspace; Next action remains near
the top. Patient changes/logout cancel jobs and clear private widgets. Accepted
records remain associated with their own patient.

## Consistent image actions

Both panels show **Upload** and **Analyze** above their results. Upload opens one
picker; the selected filename stays visible. The model/example selector applies
when no file is selected. ZIPs open included results; raw permitted endoscopy
images run local inference. Full CT preparation remains offline companion work.

Pending reviews and running jobs have explicit explanations and navigation.
Terminal/invalid job handles do not silently disable the other view. Correct a
bad input or missing local model and retry; the actual bounded reason remains
visible. A valid new image after report preparation opens a fresh context, while
invalid input preserves the previous case. [Image guide](IMAGING.md).

## Decisions and reports

Confirmations start unselected; selecting one submits nothing. Pause/corrections
choices are yellow; allow/approve choices are green. Colour describes the
selection, never completed approval. Candidate choices start empty (a producer's
earlier choice is shown only as a caption) and each must be actively set to
include or exclude. Notes can be blank, but every final report must be previewed
before approval, and every changed note, including clearing one, previewed again.

Safety preparation and generation are separate. The Generate button sits below
the safety controls and remains gated. Final review is another explicit form.
The report stays short; source excerpts remain accessible without raw JSON,
checkpoint hashes or model paths in the main workflow. [Report details](REPORTS.md).

## Reusable components

| Module | Responsibility |
| --- | --- |
| `ui/theme.css` | Local tokens, cards, typography, responsive layout and selected decision colours |
| `ui/components.py` | Escaped patient/history/medication presentation and guide |
| `ui/navigation.py` | Fixed destinations, scrolling and patient/report-context cleanup |
| `ui/imaging_actions.py` | Shared Upload/Analyze, visible blockers and worker progress |
| `imaging_actions.py` | Authenticated input routing, source validation and result collection |
| `ui/errors.py` | Literal bounded errors without echoed Pydantic input/help URLs |
| `ui/history.py`, `ui/clinical.py` | Explicit import, safety, note and clinical review actions |

Streamlit native controls retain keyboard operation. No remote fonts/templates or
frontend service are loaded. Fixed-anchor JavaScript never interpolates source or
model data. The retained scrolling component has an installed-Streamlit deprecation
warning; changing that browser-focus path requires separate visual verification.

## Pictures and current scope

![Earlier selected-patient workspace and guide](images/lovisa-workspace-overview.jpg)

This earlier screenshot predates the current Endoscopy and two-action upload
controls. It documents the layout, not the latest button labels. [Current diagram
and historical figures](ILLUSTRATIONS.md) distinguish generated, actual model and
scripted examples. This release remains on [localhost:8501](http://127.0.0.1:8501).

# LOVISA workspace

[Overview](../README.md) · [First case](WORKFLOWS.md) · [Response budgets](PERFORMANCE.md)

## Three focused views

| View | Use it for |
| --- | --- |
| Patient overview | Read dated/undated source cards, attribution and medication history; open originals when needed |
| CT review | Generate or upload a synthetic study, inspect source/annotation slices and review candidates/calipers |
| Clinical report | Handle the safety pause, read the draft and explicitly approve or request corrections |

Sign in first; patient examples and controls remain hidden until authentication.
Select a fictional patient in the left sidebar. The patient header shows actual
source counts and the Python safety-policy state. The right-hand **How to use
LOVISA** guide lists five steps and the next action. On narrow screens the guide
stacks below the workspace and the sidebar can be opened with the native control.

At the bottom, **Before you generate the draft** lists the safety gaps. Saving an
attested safety assessment freezes the snapshot without calling the model. Only
then is **Generate draft for clinician review** enabled; clicking starts background
reasoning.
Progress shows real workflow stages, elapsed time and cancellation. CT completion
opens its pending inspection automatically with a prominent result summary: counts,
review state, source-slice range, scores and any reviewed calipers. Accepted results
remain visible after clinical analysis. An empty CT panel explains that no study
is attached. CT generation never accepts a study for you.
Pending imports/CT must be resolved before a draft. Start a new case to change an
active snapshot. Sign-out/session expiry hides all patient content and cancels session work.

Raw JSON, hashes, connection settings and original sources are available in
labeled expanders. Missing structured orders stay missing; narrative medication
quotes are displayed without inventing doses. Dates, attribution and source IDs
remain visible in the readable view.

## Local design system

`medical_assistant/ui/theme.css` defines shared ink, muted text, teal, navy,
borders, cards and responsive layout. `components.py` renders escaped timeline,
medication, status, metric, empty-state and guide components. `clinical.py` owns
clinical actions and `history.py` owns approved import forms. `app.py` selects
and lazily renders one view. Imaging-specific components remain in the imaging
modules. Native Streamlit forms, buttons and radios retain keyboard interaction.
No frontend build service, external template CDN or remote font is needed.

![LOVISA patient workspace with right-hand operating guide](images/lovisa-workspace-overview.jpg)

The screenshot shows supplied fictional data. Its safety-review state is not a
clinical conclusion. Existing workflow/architecture pictures remain in the
[illustration guide](ILLUSTRATIONS.md).

## Native local connections

SQLite supplies history; Ollama supplies constrained reasoning; the separate CT
Python environment supplies image candidates. There is no cloud inference,
automatic clinical approval, public deployment or custom domain in this version.
The server remains on [localhost:8501](http://127.0.0.1:8501).

![LOVISA pending CT source and verified candidate overlay](images/lovisa-ct-review.jpg)

This generated fixture remains unapproved. The amber box is a non-ML demonstration
candidate; it is not evidence of lesion-detection accuracy.

## Safety before generation

![Bottom safety assessment and locked generation button](images/lovisa-safety-first.jpg)

The grey button is disabled until the required checks are completed. Saving the
assessment does not call the model. Final report approval remains separate.

## Actual installed detector

![Installed pretrained detector result on a generated phantom](images/lovisa-ct-pretrained-results.jpg)

This screenshot is an actual local pretrained CPU run on generated 32×64×64 data,
not a patient CT or a diagnostic accuracy result. One candidate is still pending
human review; its score is not malignancy probability. Both source/overlay images
loaded successfully in the browser.

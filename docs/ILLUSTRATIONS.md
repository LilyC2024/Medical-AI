# LOVISA and its imaging companions in pictures

[Overview](../README.md) · [Architecture](ARCHITECTURE.md) · [CT](IMAGING.md) · [Endoscopy](ENDOSCOPY.md)

## Current three-project sketch

![Current sources, local engines, evidence review and clinician approval](images/lovisa-system.svg)

Read each row from source to local processing and reviewable evidence. Fictional
JSON history passes Python safety and extraction, then constrained local Ollama
reasoning. CT uses MONAI RetinaNet with source-grid candidates/calipers. Endoscopy
uses U-Net with probability-derived regions. Human image inclusion is independent
of safety assessment and final clinician approval. Python composes accepted
observations and pictures after reasoning; image pixels/notes never enter the LLM.

The SVG is an editable source diagram copied consistently into all three repos.
It contains no patient images, inference results or accuracy claims. Its rendered
layout was inspected locally. Separate environments and research/composite-source
boundaries are deliberate architecture, not a unified general-disease classifier.

## Original history workflow

![Original history workflow under the former MHCRA AI name](images/mhcra-ai-workflow-v1.png)

This retained AI-generated illustration explains records, specialist roles and
human approval, using the old MHCRA AI name and an earlier longer report layout.
The current report has one Clinical summary section. “Eligible” is workflow
permission, never a finding of medical safety.

## Original technical illustration

![Earlier Streamlit, SQLite, LangGraph and Ollama architecture](images/mhcra-ai-technical-flow-v1.png)

Streamlit supplies UI; SQLite separates originals/facts; LangGraph coordinates
Python roles and human interrupts; local Ollama selects bounded hypotheses.
The old picture does not depict the later endoscopy or Upload/Analyze extensions.
[Editable historical Mermaid](images/mhcra-ai-technical-flow-v1.mmd),
[workflow prompt](images/mhcra-ai-workflow-v1.prompt.txt) and
[technical prompt](images/mhcra-ai-technical-flow-v1.prompt.txt) preserve provenance.
Image generation was documentation work, not runtime clinical inference.

## Candidate and measurement example

![Artificial CT source, candidate and manual measurement](images/lung-research-workflow.png)

Left is manufactured CT-like source; amber is a candidate box; cyan is a manually
placed 8 mm fixture caliper. This uses the non-ML finder, not pretrained detection
or clinical ground truth. It illustrates geometry and review interaction only.
Actual pretrained model smokes and public ROI limits are recorded separately in
[Evaluation](../EVALUATION.md).

## Historical interface and legacy path

![Earlier selected-patient workspace and operating guide](images/lovisa-workspace-overview.jpg)

The light UI/right-hand guide persist, while button labels and view count have
changed. Current operation uses [six views and Upload/Analyze](INTERFACE.md).
Do not use this screenshot as a precise map of current buttons.

![Legacy manufactured tissue-mask workbench](images/mhcra-synthetic-workbench.png)

The retained four-class 2.5D teacher/mask pipeline is separate from nodule detection.
Its counts, segmentation metrics and historical NPU timing cannot establish lung
or endoscopy performance. [Current CT integration](IMAGING.md).

[Report layout example](REPORTS.md) contains fictional/scripted content and is
labelled accordingly. No illustration is clinician verification or an actual
review of the app's current patient data.

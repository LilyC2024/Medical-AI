# LOVISA documentation

**LOVISA** is the project name; **Medical History & Clinical Reasoning Assistant**
is its function. [Root overview](../README.md).

## Choose a route

| Goal | Guide |
| --- | --- |
| Install and run the local application | [Setup](SETUP.md) |
| Operate a case and each explicit review gate | [Workflow](WORKFLOWS.md) / [Interface](INTERFACE.md) |
| Try fictional cases or the public-image composite | [Demo cases](DEMO_CASES.md) / [Research images](RESEARCH_IMAGES.md) |
| Connect CT or endoscopy | [CT integration](IMAGING.md) / [Endoscopy integration](ENDOSCOPY.md) |
| Understand agents, LLMs, schemas and trust | [Architecture](ARCHITECTURE.md) |
| Understand source JSON, medication fields and local references | [Records](RECORDS.md) |
| Understand the short report and image export | [Reports](REPORTS.md) |
| Understand timings and cancellation | [Performance](PERFORMANCE.md) |
| Find folders/functions/subfunctions | [Code reference](CODE_REFERENCE.md) / [File inventory](FILE_INVENTORY.md) |
| Reproduce checks or inspect bugs | [Validation](VALIDATION.md) / [Expert review](REVIEW.md) |
| Inspect executed outcomes or the original checklist | [Evaluation](../EVALUATION.md) / [Acceptance](ACCEPTANCE.md) |
| Understand retained diagrams and names | [Illustrations](ILLUSTRATIONS.md) / [Naming](NAMING.md) |
| Develop and publish changes | [Development](DEVELOPMENT.md) / [Contributing](../CONTRIBUTING.md) |

The clinical model reasons over fictional history, not image pixels. Both
companions produce reviewable observations through separate environments and
schemas. [CT docs](https://github.com/LilyC2024/ai-medimg-2.5D-CT/blob/main/docs/README.md)
· [Endoscopy docs](https://github.com/LilyC2024/AI-MedImg-Endo/blob/main/docs/README.md).

[Security](../SECURITY.md) · [Phase gates](../PLAN.md) · [Release record](RELEASE.md).
Earlier pictures and experiments remain explicitly historical; use the current
workflow/API guides for operation. A scripted demonstration is not clinician review.

## Reviewed integration

- [Branch decisions](BRANCH_REVIEW.md)
- [Provenance, trust and restart recovery](REPRODUCIBILITY.md)
- [Reporting-checklist mapping](REPORTING_CHECKLISTS.md)
- [Proposed human-factors study](HUMAN_FACTORS.md)

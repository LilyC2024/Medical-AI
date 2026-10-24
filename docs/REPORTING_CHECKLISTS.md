# Reporting checklists: where LOVISA stands

[Overview](../README.md) · [Evaluation](../EVALUATION.md) · [Human factors](HUMAN_FACTORS.md)

LOVISA and its companions are educational research software, **not a diagnostic
device**, and have no clinical evaluation. This page maps the project to three
published reporting guidelines at the level of their main domains, so readers can
see what a credible future report would need. It is a self-assessment by the
author and AI coding agents, not an independent audit, and it paraphrases the
guidelines rather than reproducing their item lists. Use the official checklists
when writing any study.

| Guideline | Scope | Applies to |
| --- | --- | --- |
| CLAIM (Checklist for Artificial Intelligence in Medical Imaging) | Reporting imaging AI studies | CT RetinaNet and endoscopy U-Net |
| TRIPOD+AI | Reporting prediction-model development or validation | Any future claim about LLM hypothesis selection or imaging performance |
| DECIDE-AI | Early-stage live clinical evaluation of decision support, including human factors | Any future study of reviewers using LOVISA |

Status values: **met** (documented and reproducible here), **partial**, **not met**.

## CLAIM (imaging models)

| Domain | CT | Endoscopy | Evidence / gap |
| --- | --- | --- | --- |
| Data sources, terms and selection | partial | partial | [Sources and permission](RESEARCH_IMAGES.md#sources-and-permission); single LIDC-IDRI subject; Kvasir positive-only |
| Patient-level partitioning, untouched test set | not met | not met | CT region chosen from a reader contour; Kvasir test split inspected before retraining, patient independence unknown |
| Reference standard | partial | partial | LIDC reader annotations / Kvasir masks; no adjudication |
| Model description and training | partial | met | Pretrained MONAI bundle (LUNA16 overlap possible) / documented U-Net recipe |
| Evaluation metrics with uncertainty | not met | partial | No FROC or full-scan result / Dice, IoU, region proxies without confidence intervals |
| Negative cases and false-alarm rate | not met | not met | No normal examinations evaluated |
| External validation | not met | not met | None (e.g. CVC-ClinicDB, ETIS-Larib, a non-LUNA CT cohort) |
| Failure analysis and limitations | partial | partial | Candid limitation sections; no systematic error analysis |
| Code and model availability | met | met | MIT code; weights excluded with documented terms |

## TRIPOD+AI (LLM hypothesis selection and any performance claim)

| Domain | Status | Evidence / gap |
| --- | --- | --- |
| Intended use and target population | met | Fictional histories, research only |
| Data and outcome definition | not met | No gold hypothesis labels or synthetic benchmark |
| Model specification | partial | Fixed local model, temperature 0, closed catalog and versioned policy; observed model digest/prompt/policy versions bound into reports |
| Performance (precision, recall, faithfulness, repeat variance) | not met | Only scripted and smoke tests; no pass^k or baseline comparison |
| Comparison with a rule-only baseline | not met | Not run |
| Open science (code, prompts, protocol) | partial | Code/prompts public; no preregistered evaluation protocol |

## DECIDE-AI (early human-in-the-loop evaluation)

| Domain | Status | Evidence / gap |
| --- | --- | --- |
| Human-AI interaction design | partial | Explicit submit and content-bound approval on main; paused candidate choices and pinned exporter signatures; checked confirmation defaults/optional notes retained |
| User characteristics and training | not met | Local accounts do not verify qualifications |
| Human factors and error detection | not met | Seeded-error protocol written ([HUMAN_FACTORS](HUMAN_FACTORS.md)), not run |
| Safety monitoring and adverse events | partial | Deterministic safety routing; no live use, so no events |
| Independent review | not met | Development reviews were AI-assisted coding-agent reviews; no clinician or human security review |

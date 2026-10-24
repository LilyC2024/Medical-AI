# Project naming and stable identifiers

[Overview](../README.md) · [Integration](IMAGING.md)

The project is named **LOVISA**. Its functional description is **Medical History &
Clinical Reasoning Assistant**. LOVISA is a memorable name, not a newly defined
clinical acronym. Earlier documentation, figures and releases used **MHCRA AI**.

| Name or identifier | Meaning |
| --- | --- |
| LOVISA | Current application/project name, used in the UI and documentation |
| Medical History & Clinical Reasoning Assistant | Functional description beneath the name |
| `LilyC2024/Medical-AI` | Existing GitHub repository address |
| `medical_assistant` / `MedicalHistoryOrchestrator` | Existing Python package and orchestrator class |
| `MHCRA_CT_ROOT` / `MHCRA_CT_MODEL_DIR` / `MHCRA_CT_DEVICE` | Existing CT checkout and weight-location settings |
| `mhcra-lung-nodules-v2` | Current synthetic nodule exchange contract |
| `mhcra-imaging-v1` | Retained legacy tissue-mask exchange contract |
| `lovisa-ct-research-v3` | Bounded public CT excerpt with separate provenance |
| `lovisa-endo-image-v1` / `lovisa-endo-research-v2` | Separate artificial/public RGB exchanges |
| `LOVISA_ENDO_*` | Existing endoscopy checkout, model and backend settings |
| `deploy.mhcra_lung_bridge` / `deploy.mhcra_bridge` | Current nodule and legacy producer entry points |
| `docs/lung/mhcra.md` in CT | Existing integration guide URL |

The rename changes the visible identity, not these interfaces or existing data.
Use existing repository URLs and commands in setup instructions. Do not rename existing archive schema values, environment variables or package
imports merely to match branding. The later public/endo `lovisa-*` schemas above
are separately implemented formats, not renamed versions of old bundles.

The original workflow and technical PNGs are reused with their historical labels
explained in the captions. Their prompts preserve generation history. Editable
text diagrams use the current name. [Illustrations](ILLUSTRATIONS.md).

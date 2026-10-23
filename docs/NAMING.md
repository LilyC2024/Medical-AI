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
| `MHCRA_CT_ROOT` / `MHCRA_CT_MODEL_DIR` | Existing CT checkout and weight-location settings |
| `mhcra-lung-nodules-v2` | Current synthetic nodule exchange contract |
| `mhcra-imaging-v1` | Retained legacy tissue-mask exchange contract |
| `deploy.mhcra_lung_bridge` / `deploy.mhcra_bridge` | Current nodule and legacy producer entry points |
| `docs/lung/mhcra.md` in CT | Existing integration guide URL |

The rename changes the visible identity, not these interfaces or existing data.
Use existing repository URLs and commands in setup instructions. Do not rename
archive schema values, environment variables or package imports to `lovisa-*`;
that would require a separate compatibility migration.

The original workflow and technical PNGs are reused with their historical labels
explained in the captions. Their prompts preserve generation history. Editable
text diagrams use the current name. [Illustrations](ILLUSTRATIONS.md).

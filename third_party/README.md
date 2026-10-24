# Vendored CT components in LOVISA

`medical_assistant/nodule_models.py` and `nodule_exchange.py` come from
`LilyC2024/ai-medimg-2.5D-CT` (`contracts.py`, `exchange_contract.py`), with one
import-path rewrite. Their [MIT notice](CT-MIT-LICENSE.txt) is retained verbatim;
it does not select a license for the rest of LOVISA.

[Integration](../docs/IMAGING.md) explains synchronization. The exact tested CT
revision is pinned in [CI](../.github/workflows/tests.yml). Existing `mhcra-*`
identifiers are documented in [Naming](../docs/NAMING.md).

## Shared endoscopy interface

`medical_assistant/endo_contracts/` is copied exactly from the new, same-owner
[AI-MedImg-Endo](https://github.com/LilyC2024/AI-MedImg-Endo) companion's
`src/endo_contracts/`. This includes schemas/pixel validation and the bounded worker
lifecycle. It is not covered by the CT MIT notice; neither project currently
selects a project-wide redistribution license for this new code. No model weights,
research images or third-party training code are vendored with it.
[Endoscopy synchronization](../docs/ENDOSCOPY.md) and the CI producer pin identify
the tested source. Dependency and dataset rights remain separate.

## Shared producer-signature module

`medical_assistant/producer_signature.py` is byte-identical to
`src/lung_nodule/producer_signature.py` (CT) and
`src/endo_contracts/producer_signature.py` (endoscopy). Both sync scripts check it.

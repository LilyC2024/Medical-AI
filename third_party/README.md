# Vendored CT components in LOVISA

`medical_assistant/nodule_models.py` and `nodule_exchange.py` come from
`LilyC2024/ai-medimg-2.5D-CT` (`contracts.py`, `exchange_contract.py`), with one
import-path rewrite. Their [MIT notice](CT-MIT-LICENSE.txt) is retained verbatim;
it does not select a license for the rest of LOVISA.

[Integration](../docs/IMAGING.md) explains synchronization. The exact tested CT
revision is pinned in [CI](../.github/workflows/tests.yml). Existing `mhcra-*`
identifiers are documented in [Naming](../docs/NAMING.md).

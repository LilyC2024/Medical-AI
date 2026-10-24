"""Vendor/check ML-free CT contracts; no CT model, torch or database tools imported."""

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def sync(ct_root, *, write=False):
    pairs = (
        ("contracts.py", "nodule_models.py"),
        ("exchange_contract.py", "nodule_exchange.py"),
        ("producer_signature.py", "producer_signature.py"),
    )
    for source, destination in pairs:
        text = (Path(ct_root) / "src/lung_nodule" / source).read_text(encoding="utf-8")
        text = text.replace(
            "from lung_nodule.contracts import",
            "from medical_assistant.nodule_models import",
        )
        text = text.replace(
            "from lung_nodule.producer_signature import",
            "from medical_assistant.producer_signature import",
        )
        target = ROOT / "medical_assistant" / destination
        if write:
            target.write_text(text, encoding="utf-8")
        elif not target.exists() or target.read_text(encoding="utf-8") != text:
            raise ValueError(
                f"Contract drift: {destination}; inspect upstream and synchronize intentionally"
            )
    print("CT/LOVISA lightweight contract and rendering sources match")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ct-root", type=Path, default=ROOT.parent / "ai-medimg-2.5D-CT")
    p.add_argument("--write", action="store_true")
    a = p.parse_args()
    sync(a.ct_root, write=a.write)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as error:
        sys.exit(str(error))

"""Check exact ML-free endoscopy contract/worker equality with the companion."""

import argparse
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--endo-root", required=True)
    args = p.parse_args()
    root = Path(__file__).resolve().parents[1]
    for name in ("__init__.py", "worker.py", "producer_signature.py"):
        source = Path(args.endo_root) / "src/endo_contracts" / name
        target = root / "medical_assistant/endo_contracts" / name
        if source.read_bytes() != target.read_bytes():
            raise ValueError("Endoscopy contract drift: " + name)
    signature = Path(args.endo_root) / "src/endo_contracts/producer_signature.py"
    if signature.read_bytes() != (root / "medical_assistant/producer_signature.py").read_bytes():
        raise ValueError("Endoscopy contract drift: producer_signature.py")
    print("Endoscopy contracts and worker match exactly")


if __name__ == "__main__":
    main()

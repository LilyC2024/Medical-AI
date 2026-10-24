"""Actual signed companion CLI transfers into LOVISA; no image/report approval."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from medical_assistant.database import seed
from medical_assistant.imaging import ImagingStore
from medical_assistant.producer_signature import generate_key
from medical_assistant.producer_trust import TrustConfig


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ct-root", type=Path, required=True)
    parser.add_argument("--endo-root", type=Path, required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="lovisa-signed-smoke-") as temp:
        directory = Path(temp)
        database = directory / "synthetic.sqlite3"
        seed(database)
        for name, repository in (("ct", args.ct_root), ("endo", args.endo_root)):
            repository = repository.resolve()
            start = time.monotonic()
            key = directory / (name + ".key")
            public = generate_key(key)
            output = directory / name
            executable = repository / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            if name == "ct":
                command = [str(executable), "-m", "deploy.mhcra_lung_bridge", "--patient-id", "synthetic-checklist", "--study-id", "signed-smoke-ct", "--output-dir", str(output), "--mode", "fixture", "--device", "cpu"]
            else:
                command = [str(executable), "-m", "endo.cli", "demo", "--patient-id", "synthetic-checklist", "--study-id", "signed-smoke-endo", "--output", str(output), "--signing-key", str(key)]
            environment = {**os.environ, "LOVISA_SIGNING_KEY_FILE": str(key), "OLLAMA_NO_CLOUD": "1", "LANGSMITH_TRACING": "false", "LANGCHAIN_TRACING_V2": "false"}
            result = subprocess.run(command, cwd=repository, env=environment, capture_output=True, text=True, timeout=110)
            if result.returncode:
                raise RuntimeError(f"{name} producer failed: {result.stderr[-1000:]}")
            archives = list(output.rglob("*.zip"))
            if len(archives) != 1:
                raise ValueError("Expected exactly one generated review ZIP")
            config = TrustConfig(require_signature=True, keys=[{"producer": "lovisa-" + name, "public_key_b64": public["public_key_b64"], "label": "Temporary smoke key"}])
            store = ImagingStore(database, trust=config)
            identifier, proposal = store.prepare(archives[0].read_bytes(), "synthetic-checklist")
            assert proposal["producer_signature"]["status"] == "verified"
            assert not store.snapshots("synthetic-checklist")
            print(json.dumps({"status": "PASS", "producer": name, "seconds": round(time.monotonic()-start, 2), "signature": "verified", "artifacts": len(proposal["manifest"]["artifacts"]), "approvals_issued": False}), flush=True)
            store.discard(identifier)


if __name__ == "__main__":
    main()

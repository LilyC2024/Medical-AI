"""Read a local, bounded public-research upload kit; never downloads or approves."""

import hashlib
import json
import os
from pathlib import Path

from medical_assistant.storage import ROOT

PATIENT = "research-composite-demo"


def _manifest(root=None):
    root = Path(
        root or os.environ.get("LOVISA_RESEARCH_DEMO_DIR", ROOT / "data/research-demo")
    ).resolve()
    path = root / "examples.json"
    if path.is_symlink() or path.stat().st_size > 50_000:
        raise ValueError("Research examples manifest is invalid")
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError("Research examples manifest must be an object")
    if (
        data.get("schema_version") != "lovisa-research-demo-v1"
        or data.get("patient_id") != PATIENT
    ):
        raise ValueError("Research composite identity mismatch")
    if (
        not isinstance(data.get("ct"), dict)
        or not {"file", "sha256"} <= data["ct"].keys()
        or not isinstance(data.get("endoscopy"), list)
        or not 1 <= len(data["endoscopy"]) <= 3
        or any(
            not isinstance(r, dict)
            or not {"file", "sha256", "raw_sha256", "provenance"} <= r.keys()
            for r in data["endoscopy"]
        )
    ):
        raise ValueError("Research examples manifest is incomplete")
    return root, data


def _read(root, name, expected, limit):
    if (
        not isinstance(name, str)
        or Path(name).name != name
        or "\\" in name
        or ":" in name
    ):
        raise ValueError("Research example path must be a basename")
    path = root / name
    if path.is_symlink() or path.stat().st_size > limit:
        raise ValueError("Research example exceeds bounds")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("Research example changed; rebuild its local kit")
    return raw


def example_bundle(modality, patient, *, root=None, index=0):
    """Load only the requested modality/case; full archive verification follows at import."""
    if patient != PATIENT or modality not in ("ct", "endoscopy"):
        raise ValueError("Public examples belong only to the research composite case")
    directory, data = _manifest(root)
    row = data["ct"] if modality == "ct" else data["endoscopy"][index]
    return _read(directory, row["file"], row["sha256"], 64 * 1024**2)


def matching_endoscopy(raw, patient, *, root=None):
    """Recognise the exact permitted demo source bytes without guessing dataset provenance."""
    if patient != PATIENT or not raw or len(raw) > 16 * 1024**2:
        raise ValueError(
            "Select the research composite and use a prepared research image"
        )
    _, data = _manifest(root)
    sha = hashlib.sha256(raw).hexdigest()
    matches = [r for r in data["endoscopy"] if r["raw_sha256"] == sha]
    if len(matches) != 1:
        raise ValueError(
            "Use endoscopy-01.jpg, endoscopy-02.jpg or endoscopy-03.jpg from the research kit"
        )
    return matches[0]["provenance"]

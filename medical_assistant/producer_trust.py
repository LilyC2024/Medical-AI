"""Locally pinned producer public keys and the signature acceptance policy.

The trust file is local configuration outside Git (default
``data/trust/producer_keys.json``, or ``LOVISA_TRUSTED_PRODUCER_KEYS``). Public
keys are not secret, but pinning one is a decision to trust its holder. Research
use only; a verified signature does not establish model accuracy.
"""

import argparse
import base64
import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from medical_assistant.producer_signature import Check, check_archive, key_id

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATH = ROOT / "data/trust/producer_keys.json"
ENV = "LOVISA_TRUSTED_PRODUCER_KEYS"


class PinnedKey(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    producer: Literal["lovisa-ct", "lovisa-endo"]
    public_key_b64: str = Field(min_length=40, max_length=60)
    label: str = Field(min_length=1, max_length=80)


class TrustConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    require_signature: bool = False
    keys: list[PinnedKey] = Field(default_factory=list, max_length=32)

    def trusted(self) -> dict:
        pinned = {}
        for key in self.keys:
            raw = base64.b64decode(key.public_key_b64, validate=True)
            if len(raw) != 32:
                raise ValueError("Pinned Ed25519 public keys are 32 bytes")
            pinned[key_id(raw)] = key.model_dump()
        return pinned


def trust_path(path=None) -> Path:
    return Path(path or os.environ.get(ENV) or DEFAULT_PATH)


def load_trust(path=None) -> TrustConfig:
    """Missing file means no pinned keys and signatures not required."""
    path = trust_path(path)
    if not path.exists():
        return TrustConfig()
    return TrustConfig.model_validate_json(path.read_text(encoding="utf-8"))


def verify_producer(payload: bytes, config: TrustConfig) -> Check:
    """Fail closed on bad signatures; enforce ``require_signature`` when set."""
    check = check_archive(payload, config.trusted())
    if config.require_signature and check.status != "verified":
        raise ValueError(
            "A verified producer signature is required by local trust settings"
        )
    return check


def pin(path, producer, public_key_b64, label):
    path = trust_path(path)
    config = load_trust(path)
    key = PinnedKey(producer=producer, public_key_b64=public_key_b64, label=label)
    if key.public_key_b64 in {k.public_key_b64 for k in config.keys}:
        raise ValueError("Key already pinned")
    updated = config.model_copy(update={"keys": [*config.keys, key]})
    updated.trusted()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(updated.model_dump_json(indent=2), encoding="utf-8")
    return updated


def main(argv=None):
    p = argparse.ArgumentParser(description="Pin a producer's Ed25519 public key")
    p.add_argument("--producer", choices=["lovisa-ct", "lovisa-endo"], required=True)
    p.add_argument("--public-key", required=True, help="public_key_b64 from keygen")
    p.add_argument("--label", required=True)
    p.add_argument("--trust-file", help=f"Defaults to ${ENV} or {DEFAULT_PATH}")
    a = p.parse_args(argv)
    config = pin(a.trust_file, a.producer, a.public_key, a.label)
    print(f"{len(config.keys)} pinned key(s) in {trust_path(a.trust_file)}")


if __name__ == "__main__":
    main()

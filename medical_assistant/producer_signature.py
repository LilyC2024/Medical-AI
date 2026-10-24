"""Ed25519 producer signatures for LOVISA review ZIPs.

This file is copied byte-for-byte into the CT companion, the endoscopy companion
and LOVISA; keep it self-contained. A valid signature from a pinned key shows that
the holder of that private key exported these exact ``bundle.json`` bytes, which
in turn hash-bind every artifact. It does not prove model correctness, data
permission, clinical truth or the signer's qualifications. Research use only.
"""

import base64
import hashlib
import io
import json
import os
import stat
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

SIGNATURE_ENTRY = "signature.json"
SCHEMA = "lovisa-producer-signature-v1"
MAX_SIGNATURE_BYTES = 16_000
Producer = Literal["lovisa-ct", "lovisa-endo"]
Hex64 = Field(pattern=r"^[a-f0-9]{64}$")


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class Performance(Record):
    """Producer-declared evaluation of the exact model; shown beside candidates."""

    measured: bool
    metric: str = Field(min_length=1, max_length=200)
    false_positive_fraction: float | None = Field(default=None, ge=0, le=1)
    test_images: int | None = Field(default=None, ge=1, strict=True)
    negative_images: int | None = Field(default=None, ge=0, strict=True)
    evaluation_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    limitations: str = Field(min_length=1, max_length=600)

    @model_validator(mode="after")
    def complete(self):
        values = (self.false_positive_fraction, self.test_images, self.evaluation_sha256)
        if self.measured and any(v is None for v in values):
            raise ValueError("Measured performance needs a rate, test size and evaluation hash")
        if not self.measured and any(v is not None for v in values):
            raise ValueError("Unmeasured performance cannot carry a rate")
        return self


NOT_MEASURED = Performance(
    measured=False,
    metric="false-positive rate per candidate",
    limitations="No false-positive evaluation exists for this exact model.",
)


class Claims(Record):
    schema_version: Literal["lovisa-producer-signature-v1"]
    producer: Producer
    bundle_sha256: str = Hex64
    key_id: str = Hex64
    signed_at: datetime
    performance: Performance


class Envelope(Record):
    claims: Claims
    signature_b64: str = Field(min_length=80, max_length=100)


class Check(Record):
    """Result of checking an archive against locally pinned producer keys."""

    status: Literal["verified", "unsigned", "untrusted-key"]
    producer: Producer | None = None
    key_id: str | None = None
    label: str | None = None
    performance: Performance | None = None


def canonical(value) -> bytes:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def key_id(public_raw: bytes) -> str:
    return hashlib.sha256(public_raw).hexdigest()


def _crypto():
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ed25519
    except ImportError as error:
        raise ValueError("The 'cryptography' package is required for signatures") from error
    return InvalidSignature, serialization, ed25519


def _public_raw(public_key) -> bytes:
    _, serialization, _ = _crypto()
    return public_key.public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )


def generate_key(path) -> dict:
    """Create a new owner-only PKCS8 private key file; never overwrite an existing one."""
    _, serialization, ed25519 = _crypto()
    private = ed25519.Ed25519PrivateKey.generate()
    pem = private.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(pem)
    return public_info(private.public_key())


def public_info(public_key) -> dict:
    raw = _public_raw(public_key)
    return {"key_id": key_id(raw), "public_key_b64": base64.b64encode(raw).decode()}


def load_private_key(path):
    _, serialization, ed25519 = _crypto()
    path = Path(path)
    if os.name == "posix" and stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise ValueError("Signing key must be readable only by its owner (chmod 600)")
    key = serialization.load_pem_private_key(path.read_bytes(), password=None)
    if not isinstance(key, ed25519.Ed25519PrivateKey):
        raise TypeError("Signing key must be Ed25519")
    return key


def sign_archive(payload: bytes, private_key, producer, performance=NOT_MEASURED) -> bytes:
    """Return the same archive with an added signature over bundle.json and claims."""
    entries = []
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        if SIGNATURE_ENTRY in archive.namelist():
            raise ValueError("Archive is already signed")
        for info in archive.infolist():
            entries.append((info.filename, archive.read(info)))
    bundle = dict(entries)["bundle.json"]
    claims = Claims(
        schema_version=SCHEMA,
        producer=producer,
        bundle_sha256=hashlib.sha256(bundle).hexdigest(),
        key_id=public_info(private_key.public_key())["key_id"],
        signed_at=datetime.now(timezone.utc),
        performance=Performance.model_validate(performance),
    )
    envelope = Envelope(
        claims=claims,
        signature_b64=base64.b64encode(private_key.sign(canonical(claims))).decode(),
    )
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries:
            archive.writestr(name, data)
        archive.writestr(SIGNATURE_ENTRY, canonical(envelope))
    return stream.getvalue()


def _unique(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("Duplicate signature JSON key")
        value[key] = item
    return value


def check_archive(payload: bytes, trusted: dict) -> Check:
    """Check a signature against ``{key_id: {"producer", "public_key_b64", "label"}}``.

    Unsigned archives and signatures from unpinned keys are reported, not trusted;
    callers decide whether to accept them. A present signature that is malformed,
    does not match bundle.json, names the wrong producer or fails verification
    raises ValueError.
    """
    InvalidSignature, _, ed25519 = _crypto()
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            names = archive.namelist()
            if SIGNATURE_ENTRY not in names:
                return Check(status="unsigned")
            if names.count(SIGNATURE_ENTRY) != 1:
                raise ValueError("Duplicate signature entry")
            info = archive.getinfo(SIGNATURE_ENTRY)
            if info.file_size > MAX_SIGNATURE_BYTES or info.flag_bits & 1:
                raise ValueError("Signature entry is oversized or encrypted")
            envelope = Envelope.model_validate(
                json.loads(archive.read(info), object_pairs_hook=_unique)
            )
            bundle = archive.read("bundle.json")
    except (zipfile.BadZipFile, KeyError, OSError, EOFError, TypeError) as error:
        raise ValueError("Invalid signed archive") from error
    claims = envelope.claims
    if claims.bundle_sha256 != hashlib.sha256(bundle).hexdigest():
        raise ValueError("Signature does not match this bundle")
    pinned = trusted.get(claims.key_id)
    if pinned is None:
        return Check(status="untrusted-key", producer=claims.producer, key_id=claims.key_id)
    raw = base64.b64decode(pinned["public_key_b64"], validate=True)
    if key_id(raw) != claims.key_id or pinned["producer"] != claims.producer:
        raise ValueError("Pinned key does not match the signing producer")
    try:
        ed25519.Ed25519PublicKey.from_public_bytes(raw).verify(
            base64.b64decode(envelope.signature_b64, validate=True), canonical(claims)
        )
    except (InvalidSignature, ValueError) as error:
        raise ValueError("Producer signature verification failed") from error
    return Check(
        status="verified",
        producer=claims.producer,
        key_id=claims.key_id,
        label=pinned.get("label"),
        performance=claims.performance,
    )

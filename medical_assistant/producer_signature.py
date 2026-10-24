"""Bounded Ed25519 producer attestations, shared byte-for-byte across LOVISA projects.

A pinned signature identifies an exporting key and exact manifest/artifact bytes.
It does not establish evaluation validity, data permission or clinical truth.
Unsigned legacy evidence remains structurally valid; consumers choose a trust policy.
"""

import base64
import binascii
import hashlib
import io
import json
import os
import re
import stat
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

SIGNATURE_ENTRY: Final = "signature.json"
SCHEMA: Final = "lovisa-producer-signature-v1"
MAX_SIGNATURE_BYTES: Final = 16_000
MAX_ARCHIVE_BYTES: Final = 64 * 1024**2
MAX_EXPANDED_BYTES: Final = 128 * 1024**2
MAX_MEMBER_BYTES: Final = 32 * 1024**2
MAX_MANIFEST_BYTES: Final = 400_000
MAX_MEMBERS: Final = 132
MAX_KEY_BYTES: Final = 16_384
Producer = Literal["lovisa-ct", "lovisa-endo"]
Hex64 = Field(pattern=r"^[a-f0-9]{64}$")


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class Performance(Record):
    """Signed producer declaration; an unmatched-candidate fraction is not screening FPR."""

    measured: bool = Field(strict=True)
    metric: str = Field(min_length=1, max_length=200)
    false_positive_fraction: float | None = Field(default=None, ge=0, le=1, strict=True)
    test_images: int | None = Field(default=None, ge=1, strict=True)
    negative_images: int | None = Field(default=None, ge=0, strict=True)
    evaluation_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    limitations: str = Field(min_length=1, max_length=600)

    @model_validator(mode="after")
    def complete(self):
        """Require complete measured evidence and consistent optional image counts."""
        values = (
            self.false_positive_fraction,
            self.test_images,
            self.evaluation_sha256,
        )
        if self.measured and any(v is None for v in values):
            raise ValueError(
                "Measured performance needs a fraction, test size and evaluation hash"
            )
        if not self.measured and any(
            v is not None for v in (*values, self.negative_images)
        ):
            raise ValueError(
                "Unmeasured performance cannot carry evaluation counts or a fraction"
            )
        if (
            self.negative_images is not None
            and self.test_images is not None
            and self.negative_images > self.test_images
        ):
            raise ValueError("Negative images cannot exceed all evaluation images")
        return self


NOT_MEASURED = Performance(
    measured=False,
    metric="Unmatched-candidate fraction (1 - precision proxy)",
    limitations="No matching false-candidate evaluation is declared for this exact model.",
)


class Claims(Record):
    schema_version: Literal["lovisa-producer-signature-v1"]
    producer: Producer
    bundle_sha256: str = Hex64
    key_id: str = Hex64
    signed_at: datetime
    performance: Performance

    @model_validator(mode="after")
    def timezone_required(self):
        """Keep the declared signing time timezone-aware without claiming freshness."""
        if self.signed_at.tzinfo is None or self.signed_at.utcoffset() is None:
            raise ValueError("Signature time requires a timezone")
        return self


class Envelope(Record):
    claims: Claims
    signature_b64: str = Field(min_length=80, max_length=100)


class Check(Record):
    """A trust result; only verified pinned keys expose signed performance declarations."""

    status: Literal["verified", "unsigned", "untrusted-key"]
    producer: Producer | None = None
    key_id: str | None = None
    label: str | None = Field(default=None, max_length=200)
    performance: Performance | None = None


def canonical(value) -> bytes:
    """Serialize signed claims deterministically, rejecting nonfinite numbers."""
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def key_id(public_raw: bytes) -> str:
    """Identify the exact 32-byte Ed25519 public key with SHA-256."""
    if not isinstance(public_raw, bytes) or len(public_raw) != 32:
        raise ValueError("Ed25519 public key must contain 32 bytes")
    return hashlib.sha256(public_raw).hexdigest()


def _crypto():
    """Load local cryptography only for actual signing/key/proof operations."""
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ed25519
    except ImportError as error:
        raise ValueError(
            "The 'cryptography' package is required for signatures"
        ) from error
    return InvalidSignature, serialization, ed25519


def _public_raw(public_key) -> bytes:
    """Extract raw Ed25519 bytes, rejecting other signing algorithms."""
    _, serialization, ed25519 = _crypto()
    if not isinstance(public_key, ed25519.Ed25519PublicKey):
        raise TypeError("Producer public key must be Ed25519")
    return public_key.public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )


def generate_key(path) -> dict:
    """Create a new private PEM without overwrite; mode 0600 is enforced on POSIX."""
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
    """Return public material only; neither CLI nor return value contains private bytes."""
    raw = _public_raw(public_key)
    return {"key_id": key_id(raw), "public_key_b64": base64.b64encode(raw).decode()}


def load_private_key(path):
    """Load a bounded regular local Ed25519 PEM with owner-only POSIX permissions."""
    _, serialization, ed25519 = _crypto()
    path = Path(path)
    info = path.stat()
    if (
        path.is_symlink()
        or not stat.S_ISREG(info.st_mode)
        or info.st_size > MAX_KEY_BYTES
    ):
        raise ValueError("Signing key must be a bounded regular local file")
    if os.name == "posix" and stat.S_IMODE(info.st_mode) & 0o077:
        raise ValueError("Signing key must be readable only by its owner (chmod 600)")
    key = serialization.load_pem_private_key(path.read_bytes(), password=None)
    if not isinstance(key, ed25519.Ed25519PrivateKey):
        raise TypeError("Signing key must be Ed25519")
    return key


def _unique(pairs):
    """Reject ambiguous duplicate JSON keys."""
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("Duplicate signature/manifest JSON key")
        value[key] = item
    return value


def _json(raw):
    """Decode strict bounded JSON without NaN or Infinity extensions."""

    def nonfinite(value):
        raise ValueError("Nonfinite signature/manifest JSON number")

    return json.loads(raw, object_pairs_hook=_unique, parse_constant=nonfinite)


def _base64(value, length, label):
    """Require canonical base64 and exact algorithm-specific byte lengths."""
    try:
        raw = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError, TypeError) as error:
        raise ValueError(f"Invalid {label} encoding") from error
    if len(raw) != length or base64.b64encode(raw).decode() != value:
        raise ValueError(f"Invalid {label} length/encoding")
    return raw


def _safe_name(name):
    """Reject traversal, platform-specific aliases, control characters and metadata clashes."""
    return (
        isinstance(name, str)
        and 0 < len(name) <= 200
        and not PurePosixPath(name).is_absolute()
        and not any(c in name for c in ("\\", ":"))
        and not any(ord(c) < 32 or ord(c) == 127 for c in name)
        and not any(p in ("", ".", "..") for p in name.split("/"))
    )


def _archive(payload):
    """Validate central-directory limits before decompressing any member."""
    if (
        not isinstance(payload, bytes)
        or not payload
        or len(payload) > MAX_ARCHIVE_BYTES
    ):
        raise ValueError("Signed archive is empty/oversized")
    archive = zipfile.ZipFile(io.BytesIO(payload))
    entries = archive.infolist()
    names = [entry.filename for entry in entries]
    if (
        not 2 <= len(entries) <= MAX_MEMBERS
        or len(set(names)) != len(names)
        or "bundle.json" not in names
        or sum(entry.file_size for entry in entries) > MAX_EXPANDED_BYTES
        or any(
            not _safe_name(entry.filename)
            or entry.is_dir()
            or entry.flag_bits & 1
            or entry.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
            or stat.S_IFMT(entry.external_attr >> 16) not in (0, stat.S_IFREG)
            or not 0 <= entry.file_size <= MAX_MEMBER_BYTES
            for entry in entries
        )
    ):
        archive.close()
        raise ValueError("Unsafe, duplicate or oversized signed archive members")
    if archive.getinfo("bundle.json").file_size > MAX_MANIFEST_BYTES or (
        SIGNATURE_ENTRY in names
        and archive.getinfo(SIGNATURE_ENTRY).file_size > MAX_SIGNATURE_BYTES
    ):
        archive.close()
        raise ValueError("Manifest/signature is oversized")
    return archive


def validate_signature_envelope(bundle_raw, signature_raw, expected_producer=None):
    """Check strict optional claims and binding, without asserting key trust or proof."""
    if len(bundle_raw) > MAX_MANIFEST_BYTES or len(signature_raw) > MAX_SIGNATURE_BYTES:
        raise ValueError("Manifest/signature is oversized")
    envelope = Envelope.model_validate(_json(signature_raw))
    _base64(envelope.signature_b64, 64, "Ed25519 signature")
    if expected_producer is not None and envelope.claims.producer != expected_producer:
        raise ValueError("Signature names the wrong producer")
    if envelope.claims.bundle_sha256 != hashlib.sha256(bundle_raw).hexdigest():
        raise ValueError("Signature does not match this bundle")
    return envelope


def validate_archive(payload: bytes, expected_producer=None):
    """Bound and reconstruct manifest/artifact hashes plus optional signature structure.

    This is consistency validation, not cryptographic proof. Modality validators
    must still check schemas and source-derived geometry/pixels.
    """
    try:
        with _archive(payload) as archive:
            bundle_raw = archive.read("bundle.json")
            manifest = _json(bundle_raw)
            artifacts = (
                manifest.get("artifacts") if isinstance(manifest, dict) else None
            )
            if (
                not isinstance(artifacts, list)
                or not 1 <= len(artifacts) <= MAX_MEMBERS - 1
            ):
                raise ValueError("Missing/invalid manifest artifacts")
            expected = {"bundle.json"}
            for artifact in artifacts:
                if not isinstance(artifact, dict):
                    raise ValueError("Invalid manifest artifact")
                name, size, checksum = (
                    artifact.get("path"),
                    artifact.get("size_bytes"),
                    artifact.get("sha256"),
                )
                if (
                    not isinstance(name, str)
                    or not _safe_name(name)
                    or name in expected
                    or name == SIGNATURE_ENTRY
                    or type(size) is not int
                    or not 0 < size <= MAX_MEMBER_BYTES
                    or not isinstance(checksum, str)
                    or re.fullmatch(r"[a-f0-9]{64}", checksum) is None
                ):
                    raise ValueError(
                        "Unsafe/duplicate manifest artifact or invalid identity"
                    )
                expected.add(name)
                if archive.getinfo(name).file_size != size:
                    raise ValueError("Signed artifact size mismatch")
                actual = hashlib.sha256()
                count = 0
                with archive.open(name) as handle:
                    while chunk := handle.read(1024 * 1024):
                        count += len(chunk)
                        if count > size:
                            raise ValueError("Signed artifact exceeds declared size")
                        actual.update(chunk)
                if count != size or actual.hexdigest() != checksum:
                    raise ValueError("Signed artifact hash mismatch")
            names = set(archive.namelist())
            envelope = None
            if SIGNATURE_ENTRY in names:
                expected.add(SIGNATURE_ENTRY)
                envelope = validate_signature_envelope(
                    bundle_raw, archive.read(SIGNATURE_ENTRY), expected_producer
                )
            if names != expected:
                raise ValueError("Unlisted signed archive artifacts")
            return envelope
    except (
        zipfile.BadZipFile,
        KeyError,
        OSError,
        EOFError,
        TypeError,
        RuntimeError,
        UnicodeError,
        RecursionError,
        NotImplementedError,
    ) as error:
        raise ValueError("Invalid signed archive") from error


def sign_archive(
    payload: bytes, private_key, producer, performance=NOT_MEASURED
) -> bytes:
    """Sign only bounded, exact, hash-verified evidence; never bless malformed ZIPs."""
    if validate_archive(payload) is not None:
        raise ValueError("Archive is already signed")
    _, _, ed25519 = _crypto()
    if not isinstance(private_key, ed25519.Ed25519PrivateKey):
        raise TypeError("Signing key must be Ed25519")
    with _archive(payload) as source:
        claims = Claims(
            schema_version=SCHEMA,
            producer=producer,
            bundle_sha256=hashlib.sha256(source.read("bundle.json")).hexdigest(),
            key_id=public_info(private_key.public_key())["key_id"],
            signed_at=datetime.now(timezone.utc),
            performance=Performance.model_validate(performance),
        )
        envelope = Envelope(
            claims=claims,
            signature_b64=base64.b64encode(
                private_key.sign(canonical(claims))
            ).decode(),
        )
        stream = io.BytesIO()
        with zipfile.ZipFile(
            stream, "w", compression=zipfile.ZIP_DEFLATED
        ) as destination:
            for entry in source.infolist():
                with (
                    source.open(entry) as reader,
                    destination.open(entry.filename, "w") as writer,
                ):
                    while chunk := reader.read(1024 * 1024):
                        writer.write(chunk)
            destination.writestr(SIGNATURE_ENTRY, canonical(envelope))
    result = stream.getvalue()
    if len(result) > MAX_ARCHIVE_BYTES:
        raise ValueError("Signed archive exceeds response limit")
    return result


def check_archive(payload: bytes, trusted: dict, *, expected_producer=None) -> Check:
    """Verify exact evidence against pinned keys; unknown keys expose no performance.

    Consumers must reject ``untrusted-key`` for acceptance. Allowing unsigned old
    evidence is a separate explicit policy, not an automatic signature downgrade.
    """
    envelope = validate_archive(payload, expected_producer)
    if envelope is None:
        return Check(status="unsigned")
    claims = envelope.claims
    pinned = trusted.get(claims.key_id)
    if pinned is None:
        return Check(
            status="untrusted-key", producer=claims.producer, key_id=claims.key_id
        )
    if not isinstance(pinned, dict):
        raise ValueError("Invalid pinned producer key")
    InvalidSignature, _, ed25519 = _crypto()
    try:
        raw = _base64(pinned["public_key_b64"], 32, "pinned public key")
        if key_id(raw) != claims.key_id or pinned["producer"] != claims.producer:
            raise ValueError("Pinned key does not match the signing producer")
        ed25519.Ed25519PublicKey.from_public_bytes(raw).verify(
            _base64(envelope.signature_b64, 64, "Ed25519 signature"), canonical(claims)
        )
    except (InvalidSignature, KeyError, ValueError, TypeError) as error:
        raise ValueError("Producer signature verification failed") from error
    return Check(
        status="verified",
        producer=claims.producer,
        key_id=claims.key_id,
        label=pinned.get("label"),
        performance=claims.performance,
    )

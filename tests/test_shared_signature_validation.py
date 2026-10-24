"""Archive adversarial tests for the identical shared attestation implementation."""
import hashlib
import io
import json
import zipfile

import pytest

from medical_assistant.producer_signature import Performance, check_archive, generate_key, load_private_key, sign_archive, validate_archive


def payload(files=None, manifest=None):
    data = b"evidence"
    if manifest is None:
        manifest = {"artifacts": [{"path": "source.bin", "size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}]}
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name, value in (files or {"bundle.json": json.dumps(manifest).encode(), "source.bin": data}).items():
            z.writestr(name, value)
    return stream.getvalue()


@pytest.mark.parametrize("files", [
    {"bundle.json": b" " * 400_001, "source.bin": b"x"},
    {"bundle.json": b'{"artifacts":[],"artifacts":[]}', "source.bin": b"x"},
    {"bundle.json": b'{"artifacts":[]}', "../escape": b"x"},
    {"bundle.json": b'{"artifacts":[]}', "signature.json": b"x"*16_001},
])
def test_unsafe_archives_rejected_before_signing(files, tmp_path):
    key = tmp_path / "test.key"
    generate_key(key)
    raw = payload(files=files)
    with pytest.raises(ValueError):
        validate_archive(raw)
    with pytest.raises(ValueError):
        sign_archive(raw, load_private_key(key), "lovisa-ct")


def test_duplicate_zip_members_rejected():
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as z:
        z.writestr("bundle.json", "{}")
        with pytest.warns(UserWarning):
            z.writestr("bundle.json", "{}")
    with pytest.raises(ValueError):
        validate_archive(stream.getvalue())


def test_artifact_hash_tampering_and_extra_artifacts_rejected():
    with zipfile.ZipFile(io.BytesIO(payload())) as z:
        files = {name: z.read(name) for name in z.namelist()}
    files["source.bin"] = b"tampered"
    with pytest.raises(ValueError, match="hash"):
        validate_archive(payload(files=files))
    files["extra.bin"] = b"not-listed"
    with pytest.raises(ValueError):
        validate_archive(payload(files=files))


def test_pinned_bad_key_and_wrong_modality_fail_cleanly(tmp_path):
    key = tmp_path / "test.key"
    info = generate_key(key)
    raw = sign_archive(payload(), load_private_key(key), "lovisa-ct")
    assert check_archive(raw, {}).performance is None
    with pytest.raises(ValueError):
        check_archive(raw, {info["key_id"]: {"public_key_b64": "invalid", "producer": "lovisa-ct"}})
    with pytest.raises(ValueError, match="wrong producer"):
        validate_archive(raw, "lovisa-endo")


@pytest.mark.parametrize("update", [{"measured": "false"}, {"measured": False, "test_images": 2}, {"measured": True, "false_positive_fraction": .3, "test_images": 2, "negative_images": 3, "evaluation_sha256": "a"*64}])
def test_performance_types_and_consistency(update):
    with pytest.raises(ValueError):
        Performance(metric="candidate precision proxy", limitations="research only", **update)

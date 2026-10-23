"""Bounded synthetic imaging exchange. Model artifacts are never clinical facts."""
import io
import json
import math
import stat
import zipfile
from datetime import datetime
from pathlib import PurePosixPath
from typing import Literal

import numpy as np
from PIL import Image
from pydantic import Field, field_validator, model_validator

from medical_assistant.models import StrictModel

CLASSES = {
    "0": "Neither heuristic candidate (not a normality finding)",
    "1": "Brain-like candidate only (unvalidated)",
    "2": "Broad bone candidate only; includes soft tissue (unvalidated)",
    "3": "Heuristic candidate overlap (unvalidated)",
}
COLORS = np.array([[0, 0, 0], [0, 180, 170], [245, 165, 35], [165, 90, 210]], dtype=np.uint8)
MAX_ARCHIVE = 64 * 1024 * 1024
MAX_EXPANDED = 128 * 1024 * 1024


class Artifact(StrictModel):
    path: str
    role: Literal["mask", "source_preview", "overlay_preview"]
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(gt=0, le=8 * 1024 * 1024, strict=True)
    slice_index: int | None = Field(default=None, ge=0, le=63, strict=True)

    @field_validator("path")
    @classmethod
    def local_relative(cls, value):
        parts = value.split("/")
        if not value or "\\" in value or ":" in value or PurePosixPath(value).is_absolute() or any(p in ("", ".", "..") for p in parts):
            raise ValueError("Artifact paths must be safe relative files")
        if len(value) > 150:
            raise ValueError("Artifact path too long")
        return value


class Geometry(StrictModel):
    shape_zyx: tuple[int, int, int]
    spacing_zyx_mm: tuple[float, float, float]
    origin_lps: tuple[float, float, float]
    direction_lps: tuple[float, float, float, float, float, float, float, float, float]

    @model_validator(mode="after")
    def physical(self):
        z, y, x = self.shape_zyx
        if not (1 <= z <= 64 and 1 <= y <= 256 and 1 <= x <= 256):
            raise ValueError("Imaging workbench dimensions exceeded")
        if any(not math.isfinite(v) or not 0 < v <= 100 for v in self.spacing_zyx_mm):
            raise ValueError("Invalid spacing")
        if not np.isfinite([*self.origin_lps, *self.direction_lps]).all():
            raise ValueError("Invalid physical geometry")
        direction = np.array(self.direction_lps).reshape(3, 3)
        if not np.allclose(direction.T @ direction, np.eye(3), atol=1e-5) or not np.isclose(np.linalg.det(direction), 1, atol=1e-5):
            raise ValueError("Invalid direction matrix")
        return self


class ImagingBundle(StrictModel):
    schema_version: Literal["mhcra-imaging-v1"]
    synthetic: Literal[True]
    patient_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")
    study_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")
    job_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    acquisition_date: None
    processed_at: datetime
    source_series_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    checkpoint_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    onnx_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    model_name: Literal["UNetSmall"]
    classes: dict[str, str]
    geometry: Geometry
    voxel_counts: tuple[int, int, int, int]
    candidate_volumes_mm3: tuple[float, float, float, float]
    postprocessing_enabled: Literal[False]
    onnx_parity_passed: Literal[True]
    uncertainty_mean: float = Field(ge=0, le=1, allow_inf_nan=False)
    artifacts: list[Artifact] = Field(min_length=3, max_length=129)
    limitations: str = Field(min_length=1, max_length=1000)

    @field_validator("synthetic", "postprocessing_enabled", "onnx_parity_passed", mode="before")
    @classmethod
    def boolean_only(cls, value):
        if type(value) is not bool:
            raise ValueError("A literal boolean is required")
        return value

    @model_validator(mode="after")
    def consistent(self):
        if self.processed_at.tzinfo is None:
            raise ValueError("Processing timestamp requires timezone")
        if self.classes != CLASSES:
            raise ValueError("Unknown heuristic class definitions")
        total = math.prod(self.geometry.shape_zyx)
        if any(type(v) is not int or v < 0 for v in self.voxel_counts) or sum(self.voxel_counts) != total:
            raise ValueError("Candidate counts do not cover the source grid")
        for count, volume in zip(self.voxel_counts, self.candidate_volumes_mm3):
            if not math.isfinite(volume) or not math.isclose(volume, count * math.prod(self.geometry.spacing_zyx_mm), rel_tol=1e-6, abs_tol=1e-6):
                raise ValueError("Candidate volume/spacing mismatch")
        expected = {("mask", None)} | {(role, i) for role in ("source_preview", "overlay_preview") for i in range(self.geometry.shape_zyx[0])}
        if len({a.path for a in self.artifacts}) != len(self.artifacts) or len(self.artifacts) != len(expected) or {(a.role, a.slice_index) for a in self.artifacts} != expected:
            raise ValueError("Missing or duplicated mask/slice artifacts")
        if any(not a.path.endswith(".npz" if a.role == "mask" else ".png") for a in self.artifacts):
            raise ValueError("Unexpected artifact type")
        return self


def file_digest(payload):
    import hashlib
    return hashlib.sha256(payload).hexdigest()


def validate_bundle(payload: bytes, patient_id: str):
    """Read bounded bytes without extracting arbitrary archive paths or pickle."""
    if not payload or len(payload) > MAX_ARCHIVE:
        raise ValueError("Bundle exceeds 64 MiB or is empty")
    try:
        # Dispatch by explicit manifest version; never reinterpret boxes as masks.
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            if "nodules.json" in archive.namelist() and "bundle.json" not in archive.namelist():
                raise ValueError("Old CT nodule v1 export lacks verifiable source pixels; re-export the original CT workspace with the current v2 producer")
            if archive.getinfo("bundle.json").file_size > 400_000:
                raise ValueError("Manifest too large")
            from medical_assistant.nodule_exchange import read_exchange, unique_object
            header=json.loads(archive.read("bundle.json"),object_pairs_hook=unique_object)
            if not isinstance(header,dict):raise ValueError("Imaging manifest must be an object")
            if header.get("schema_version")=="mhcra-lung-nodules-v2":
                return read_exchange(payload,patient_id)
        with zipfile.ZipFile(io.BytesIO(payload)) as z:
            items = z.infolist()
            if len(items) > 130 or len({i.filename for i in items}) != len(items) or sum(i.file_size for i in items) > MAX_EXPANDED:
                raise ValueError("Duplicate or oversized archive members")
            if any(i.is_dir() or stat.S_ISLNK(i.external_attr >> 16) or i.flag_bits & 1 for i in items):
                raise ValueError("Only unencrypted regular artifact files are accepted")
            info = z.getinfo("bundle.json")
            if info.file_size > 200_000:
                raise ValueError("Manifest too large")
            raw = z.read(info)
            def unique_object(pairs):
                value = {}
                for key, item in pairs:
                    if key in value:
                        raise ValueError("Duplicate manifest JSON keys")
                    value[key] = item
                return value
            bundle = ImagingBundle.model_validate(json.loads(raw, object_pairs_hook=unique_object))
            if bundle.patient_id != patient_id:
                raise ValueError("Imaging bundle belongs to a different synthetic patient")
            if set(z.namelist()) != {"bundle.json", *(a.path for a in bundle.artifacts)}:
                raise ValueError("Unlisted archive files")
            artifacts = {}
            for a in bundle.artifacts:
                if z.getinfo(a.path).file_size != a.size_bytes:
                    raise ValueError("Artifact size mismatch")
                data = z.read(a.path)
                if file_digest(data) != a.sha256:
                    raise ValueError("Artifact hash mismatch")
                artifacts[a.path] = data
        _verify_pixels(bundle, artifacts)
        return bundle, raw, artifacts
    except (zipfile.BadZipFile, KeyError, OSError, RuntimeError, EOFError, TypeError, Image.DecompressionBombError) as error:
        raise ValueError("Invalid imaging archive or artifact") from error


def _verify_pixels(bundle, artifacts):
    mask = next(a for a in bundle.artifacts if a.role == "mask")
    data = artifacts[mask.path]
    with zipfile.ZipFile(io.BytesIO(data)) as nested:
        entries = nested.infolist()
        if len(entries) != 4 or {e.filename for e in entries} != {"predicted_labels.npy", "spacing_zyx.npy", "origin_lps.npy", "direction_lps.npy"} or sum(e.file_size for e in entries) > 8 * 1024 * 1024:
            raise ValueError("Unexpected or oversized mask arrays")
        # Validate NPY headers before np.load can allocate according to them.
        # ZIP byte limits alone cannot bound the allocation claimed in a header.
        for info in entries:
            member = io.BytesIO(nested.read(info))
            version = np.lib.format.read_magic(member)
            readers = {(1, 0): np.lib.format.read_array_header_1_0,
                       (2, 0): np.lib.format.read_array_header_2_0}
            if version not in readers:
                raise ValueError("Unsupported mask array header")
            shape, fortran, dtype = readers[version](member, max_header_size=1024)
            expected_shape = bundle.geometry.shape_zyx if info.filename == "predicted_labels.npy" else ((9,) if info.filename == "direction_lps.npy" else (3,))
            numeric = dtype.kind in "iuf" and dtype.itemsize <= 8 and not dtype.hasobject and dtype.fields is None
            if shape != expected_shape or fortran or not numeric or (info.filename == "predicted_labels.npy" and dtype != np.dtype("uint8")):
                raise ValueError("Mask array header shape, dtype or geometry mismatch")
            if math.prod(shape) * dtype.itemsize != len(member.getbuffer()) - member.tell():
                raise ValueError("Mask array header does not match payload size")
    with np.load(io.BytesIO(data), allow_pickle=False, max_header_size=1024) as arrays:
        labels = arrays["predicted_labels"]
        if labels.dtype != np.uint8 or labels.shape != bundle.geometry.shape_zyx or not np.isin(labels, [0, 1, 2, 3]).all():
            raise ValueError("Mask grid or classes mismatch")
        for key, expected in [("spacing_zyx", bundle.geometry.spacing_zyx_mm), ("origin_lps", bundle.geometry.origin_lps), ("direction_lps", bundle.geometry.direction_lps)]:
            actual = arrays[key]
            if actual.shape != (len(expected),) or actual.dtype.kind not in "iuf" or not np.isfinite(actual).all() or not np.allclose(actual, expected, rtol=1e-8, atol=1e-8):
                raise ValueError("Mask physical geometry mismatch")
        if [int((labels == i).sum()) for i in range(4)] != list(bundle.voxel_counts):
            raise ValueError("Mask counts mismatch")
    images = {}
    for a in bundle.artifacts:
        if a.role == "mask":
            continue
        with Image.open(io.BytesIO(artifacts[a.path])) as image:
            if image.format != "PNG" or image.mode != "RGB" or getattr(image, "n_frames", 1) != 1 or image.size != bundle.geometry.shape_zyx[:0:-1]:
                raise ValueError("Preview dimensions or format mismatch")
            images[a.role, a.slice_index] = np.array(image)
    for i in range(len(labels)):
        source = images["source_preview", i]
        if not (np.array_equal(source[:, :, 0], source[:, :, 1]) and np.array_equal(source[:, :, 1], source[:, :, 2])):
            raise ValueError("Source preview must be grayscale RGB")
        expected = source.copy()
        selected = labels[i] != 0
        expected[selected] = (0.55 * source[selected] + 0.45 * COLORS[labels[i][selected]]).astype(np.uint8)
        if not np.array_equal(expected, images["overlay_preview", i]):
            raise ValueError("Overlay does not match source preview and mask")

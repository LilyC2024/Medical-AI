"""Shared, ML-free MHCRA nodule exchange v2 validation and pixel rendering.

Vendored by MHCRA with only the contracts import rewritten; CI checks equality.
Hashes bind artifacts but do not authenticate producer execution or synthetic origin.
"""

from __future__ import annotations

import hashlib
import io
import json
import math
from pathlib import PurePosixPath
import stat
from typing import Literal
from datetime import datetime
import zipfile

import numpy as np
from PIL import Image
from pydantic import Field, field_validator, model_validator

from medical_assistant.nodule_models import (
    Record,
    Study,
    Review,
    Identifier,
    research_report,
)

MAX_ARCHIVE = 64 * 1024**2
MAX_EXPANDED = 128 * 1024**2
PENDING_REPORT = "Unreviewed synthetic research candidates. No reviewer approval or completed report exists.\n"


def byte_digest(payload):
    return hashlib.sha256(payload).hexdigest()


class ExchangeArtifact(Record):
    path: str
    role: Literal[
        "source_volume", "source_preview", "overlay_preview", "producer_report"
    ]
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(gt=0, le=32 * 1024**2, strict=True)
    slice_index: int | None = Field(default=None, ge=0, le=63, strict=True)

    @field_validator("path")
    @classmethod
    def safe_path(cls, value):
        if (
            len(value) > 150
            or not value
            or "\\" in value
            or ":" in value
            or PurePosixPath(value).is_absolute()
            or any(p in ("", ".", "..") for p in value.split("/"))
        ):
            raise ValueError("Unsafe nodule artifact path")
        if value in ("bundle.json", "source.mhcra.zip"):
            raise ValueError("Reserved nodule artifact path")
        return value


class NoduleBundle(Record):
    schema_version: Literal["mhcra-lung-nodules-v2"]
    synthetic: Literal[True]
    patient_id: Identifier
    study_id: Identifier
    job_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    acquisition_date: None
    processed_at: datetime
    status: Literal["pending_review", "producer_reviewed"]
    study: Study
    producer_review: Review | None
    artifacts: list[ExchangeArtifact] = Field(min_length=6, max_length=130)

    @field_validator("synthetic", mode="before")
    @classmethod
    def literal_synthetic(cls, value):
        if value is not True:
            raise ValueError("Synthetic input required")
        return value

    @model_validator(mode="after")
    def consistent(self):
        if (
            self.study.input_kind != "generated-synthetic"
            or self.study.protocol_attestation != "synthetic-phantom"
        ):
            raise ValueError("MHCRA rejects public research and clinical input")
        if (
            self.patient_id != self.study.patient_alias
            or self.study_id != self.study.study_id
        ):
            raise ValueError("Nodule patient/study identity mismatch")
        if self.processed_at.tzinfo is None:
            raise ValueError("Processing time requires timezone")
        depth, rows, cols = self.study.geometry.shape_zyx
        if not 2 <= depth <= 64 or not 1 <= rows <= 256 or not 1 <= cols <= 256:
            raise ValueError("Synthetic workbench limit: 64 slices, 256 pixels")
        if self.status == "producer_reviewed":
            if self.producer_review is None:
                raise ValueError("Missing producer review")
            self.producer_review.verify(self.study)
        elif self.producer_review is not None:
            raise ValueError("Pending export cannot claim producer review")
        expected = {
            (r, i) for r in ("source_preview", "overlay_preview") for i in range(depth)
        } | {("source_volume", None), ("producer_report", None)}
        if (
            len(self.artifacts) != len(expected)
            or len({a.path for a in self.artifacts}) != len(expected)
            or {(a.role, a.slice_index) for a in self.artifacts} != expected
        ):
            raise ValueError("Missing or duplicated nodule artifacts")
        for a in self.artifacts:
            suffix = {
                "source_volume": ".npy",
                "source_preview": ".png",
                "overlay_preview": ".png",
                "producer_report": ".md",
            }[a.role]
            if not a.path.endswith(suffix):
                raise ValueError("Wrong nodule artifact type")
        return self


def wire_pixels(study, hu, index, *, calipers=()):
    """Portable NumPy-only source/box/caliper pixels; no font-version dependency."""
    if not 0 <= index < hu.shape[0]:
        raise ValueError("Invalid source slice")
    gray = (np.clip((hu[index] + 1000) / 1400, 0, 1) * 255).astype(np.uint8)
    source = np.repeat(gray[:, :, None], 3, axis=2)
    overlay = source.copy()
    for c in study.candidates:
        lo, hi = np.array(c.box_zyx[:3]), np.array(c.box_zyx[3:])
        if lo[0] <= index <= hi[0]:
            y0, x0 = np.floor(lo[1:]).astype(int)
            y1, x1 = np.ceil(hi[1:]).astype(int)
            overlay[y0, x0 : x1 + 1] = [255, 176, 32]
            overlay[y1, x0 : x1 + 1] = [255, 176, 32]
            overlay[y0 : y1 + 1, x0] = [255, 176, 32]
            overlay[y0 : y1 + 1, x1] = [255, 176, 32]
    for c in calipers:
        c.length_mm(study.geometry)
        if c.start_zyx[0] == index:
            a, b = np.array(c.start_zyx[1:]), np.array(c.end_zyx[1:])
            count = int(math.ceil(np.max(np.abs(b - a)) * 4)) + 1
            points = np.rint(np.linspace(a, b, count)).astype(int)
            overlay[points[:, 0], points[:, 1]] = [0, 229, 255]
    return source, overlay


def source_pixels(bundle, artifacts):
    """Bound NPY header and exact payload before allocating source HU."""
    item = next(a for a in bundle.artifacts if a.role == "source_volume")
    data = artifacts[item.path]
    handle = io.BytesIO(data)
    version = np.lib.format.read_magic(handle)
    readers = {
        (1, 0): np.lib.format.read_array_header_1_0,
        (2, 0): np.lib.format.read_array_header_2_0,
    }
    if version not in readers:
        raise ValueError("Unsupported source array version")
    shape, fortran, dtype = readers[version](handle, max_header_size=1024)
    if (
        shape != bundle.study.geometry.shape_zyx
        or fortran
        or dtype != np.dtype("float32")
        or dtype.hasobject
    ):
        raise ValueError("Source array header shape/dtype mismatch")
    if len(data) - handle.tell() != math.prod(shape) * 4:
        raise ValueError("Source array payload mismatch")
    hu = np.load(io.BytesIO(data), allow_pickle=False, max_header_size=1024)
    if not np.isfinite(hu).all():
        raise ValueError("Nonfinite source pixels")
    return hu


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("Duplicate nodule JSON key")
        value[key] = item
    return value


def read_exchange(payload, patient_id):
    """Validate bounded ZIP without extracting paths; all source/overlay pixels checked."""
    if not payload or len(payload) > MAX_ARCHIVE:
        raise ValueError("Nodule archive exceeds 64MiB or is empty")
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as z:
            items = z.infolist()
            if (
                len(items) > 131
                or len({i.filename for i in items}) != len(items)
                or sum(i.file_size for i in items) > MAX_EXPANDED
            ):
                raise ValueError("Duplicate or oversized nodule archive")
            if any(
                i.is_dir() or stat.S_ISLNK(i.external_attr >> 16) or i.flag_bits & 1
                for i in items
            ):
                raise ValueError(
                    "Only regular unencrypted nodule artifacts are accepted"
                )
            if z.getinfo("bundle.json").file_size > 400_000:
                raise ValueError("Nodule manifest too large")
            raw = z.read("bundle.json")
            bundle = NoduleBundle.model_validate(
                json.loads(raw, object_pairs_hook=unique_object)
            )
            if bundle.patient_id != patient_id:
                raise ValueError(
                    "Nodule bundle belongs to a different synthetic patient"
                )
            if set(z.namelist()) != {
                "bundle.json",
                *(a.path for a in bundle.artifacts),
            }:
                raise ValueError("Unlisted nodule artifacts")
            artifacts = {}
            for a in bundle.artifacts:
                if z.getinfo(a.path).file_size != a.size_bytes:
                    raise ValueError("Nodule artifact size mismatch")
                data = z.read(a.path)
                if byte_digest(data) != a.sha256:
                    raise ValueError("Nodule artifact hash mismatch")
                artifacts[a.path] = data
        hu = source_pixels(bundle, artifacts)
        report = next(a for a in bundle.artifacts if a.role == "producer_report")
        expected_report = (
            research_report(bundle.study, bundle.producer_review)
            if bundle.producer_review
            else PENDING_REPORT
        )
        if artifacts[report.path].decode("utf-8") != expected_report:
            raise ValueError(
                "Producer report does not match structured findings/review"
            )
        calipers = (
            [d.caliper for d in bundle.producer_review.decisions if d.caliper]
            if bundle.producer_review
            else []
        )
        for index in range(len(hu)):
            source, overlay = wire_pixels(bundle.study, hu, index, calipers=calipers)
            for role, expected in (
                ("source_preview", source),
                ("overlay_preview", overlay),
            ):
                a = next(
                    a
                    for a in bundle.artifacts
                    if a.role == role and a.slice_index == index
                )
                with Image.open(io.BytesIO(artifacts[a.path])) as image:
                    if (
                        image.format != "PNG"
                        or image.mode != "RGB"
                        or getattr(image, "n_frames", 1) != 1
                        or image.size != hu.shape[:0:-1]
                    ):
                        raise ValueError("Nodule preview format/dimensions mismatch")
                    if not np.array_equal(np.array(image), expected):
                        raise ValueError(
                            "Nodule preview does not match source/annotations"
                        )
        return bundle, raw, artifacts
    except (
        zipfile.BadZipFile,
        KeyError,
        OSError,
        RuntimeError,
        EOFError,
        TypeError,
        Image.DecompressionBombError,
    ) as error:
        raise ValueError("Invalid nodule archive or artifact") from error

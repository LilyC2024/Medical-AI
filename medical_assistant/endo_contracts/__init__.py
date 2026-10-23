"""ML-free, bounded RGB evidence protocol shared with LOVISA. No clinical inference."""

from __future__ import annotations

import hashlib
import io
import json
import math
import stat
import zipfile
from collections import deque
from datetime import datetime
from pathlib import PurePosixPath
from typing import Annotated, Literal

import numpy as np
from PIL import Image
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

VERSION = "lovisa-endo-image-v1"
MAX_BYTES = 16 * 1024**2
MAX_PIXELS = 2048 * 2048
LIMITATION = "Research candidates only; no cancer diagnosis, normal-examination conclusion or calibrated millimetre measurement."
Id = Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")]
Hash = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]


class Record(BaseModel):
    model_config = ConfigDict(
        extra="forbid", validate_assignment=True, allow_inf_nan=False
    )


def sha(data):
    """Hash supplied bytes with SHA-256 for consistency checking."""
    return hashlib.sha256(data).hexdigest()


def digest(value):
    """Hash canonical structured content without claiming producer authenticity."""
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    return sha(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    )


class ModelInfo(Record):
    name: Literal["synthetic-fixture", "UNetSmall"]
    backend: Literal["fixture", "torch-cpu", "onnx-cpu", "openvino-cpu", "openvino-npu"]
    checkpoint_sha256: Hash
    recipe_sha256: Hash
    threshold: float = Field(ge=0, le=1)
    min_area_px: int = Field(ge=1, le=MAX_PIXELS, strict=True)
    evaluation_scope: Literal[
        "software-fixture",
        "synthetic-only",
        "positive-images-only",
        "includes-negative-images",
    ]

    @model_validator(mode="after")
    def matching(self):
        """Keep fixture provenance and evaluation scope consistent."""
        if (self.name == "synthetic-fixture") != (self.backend == "fixture"):
            raise ValueError("Fixture provenance mismatch")
        if (self.backend == "fixture") != (self.evaluation_scope == "software-fixture"):
            raise ValueError("Fixture evaluation scope mismatch")
        return self


class Candidate(Record):
    candidate_id: Id
    box_xyxy: tuple[int, int, int, int]
    area_px: int = Field(ge=1, le=MAX_PIXELS, strict=True)
    mean_model_score: float = Field(ge=0, le=1)


class Study(Record):
    study_id: Id
    patient_alias: Id
    input_kind: Literal["generated-synthetic", "approved-public-research"]
    source_sha256: Hash
    width: int = Field(ge=16, le=2048, strict=True)
    height: int = Field(ge=16, le=2048, strict=True)
    acquisition_date: None = None
    model: ModelInfo
    candidates: list[Candidate] = Field(max_length=100)

    @model_validator(mode="after")
    def bounds(self):
        """Check candidate identities, box bounds and fixture scope."""
        if len({c.candidate_id for c in self.candidates}) != len(self.candidates):
            raise ValueError("Duplicate candidate ID")
        for c in self.candidates:
            x0, y0, x1, y1 = c.box_xyxy
            if not (0 <= x0 < x1 <= self.width and 0 <= y0 < y1 <= self.height):
                raise ValueError("Candidate outside source image")
            if c.area_px > (x1 - x0) * (y1 - y0):
                raise ValueError("Candidate area exceeds box")
        if self.model.backend == "fixture" and self.input_kind != "generated-synthetic":
            raise ValueError("Fixture cannot process public research images")
        return self


class Decision(Record):
    candidate_id: Id
    decision: Literal["accept", "reject", "uncertain"]


class Review(Record):
    study_digest: Hash
    reviewer: str = Field(min_length=1, max_length=100, pattern=r"^[^\r\n]+$")
    attested: Literal[True]
    decisions: list[Decision]

    @field_validator("attested", mode="before")
    @classmethod
    def explicit(cls, value):
        """Require a literal true human image-review attestation."""
        if value is not True:
            raise ValueError("Explicit image review attestation required")
        return value

    def verify(self, study):
        """Recheck original-source association and every derived workspace annotation."""
        if self.study_digest != digest(study):
            raise ValueError("Stale or mismatched endoscopy review")
        if sorted(d.candidate_id for d in self.decisions) != sorted(
            c.candidate_id for c in study.candidates
        ):
            raise ValueError("Review every endoscopy candidate exactly once")
        if any(d.decision == "uncertain" for d in self.decisions):
            raise ValueError("Uncertain candidates block acceptance")


class Artifact(Record):
    path: str = Field(min_length=1, max_length=100)
    role: Literal["source_preview", "probability", "mask", "overlay_preview"]
    sha256: Hash
    size_bytes: int = Field(gt=0, le=4 * 1024**2, strict=True)
    slice_index: Literal[0] = 0

    @field_validator("path")
    @classmethod
    def safe(cls, path):
        """Reject absolute, traversal and reserved artifact paths."""
        if (
            PurePosixPath(path).is_absolute()
            or "\\" in path
            or ":" in path
            or any(p in ("", ".", "..") for p in path.split("/"))
            or path in ("bundle.json", "source.mhcra.zip")
        ):
            raise ValueError("Unsafe/reserved artifact path")
        return path


class Bundle(Record):
    schema_version: Literal["lovisa-endo-image-v1"] = VERSION
    synthetic: Literal[True]
    patient_id: Id
    study_id: Id
    job_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    acquisition_date: None = None
    processed_at: datetime
    study: Study
    artifacts: list[Artifact] = Field(min_length=4, max_length=4)

    @field_validator("synthetic", mode="before")
    @classmethod
    def synthetic_only(cls, value):
        """Require an explicit synthetic flag rather than truthy coercion."""
        if value is not True:
            raise ValueError("LOVISA requires literal synthetic input")
        return value

    @model_validator(mode="after")
    def consistent(self):
        """Check study identity, modality bounds and exact artifact membership."""
        if self.study.width > 512 or self.study.height > 512:
            raise ValueError(
                "LOVISA synthetic images are limited to 512 pixels per side"
            )
        if self.study.input_kind != "generated-synthetic":
            raise ValueError("LOVISA rejects public research images")
        if (self.patient_id, self.study_id) != (
            self.study.patient_alias,
            self.study.study_id,
        ):
            raise ValueError("Patient/study mismatch")
        if self.processed_at.tzinfo is None:
            raise ValueError("Timezone required")
        if len({a.path for a in self.artifacts}) != 4 or {
            a.role for a in self.artifacts
        } != {"source_preview", "probability", "mask", "overlay_preview"}:
            raise ValueError("Missing/duplicate endoscopy artifact")
        if any(
            not a.path.endswith(".npy" if a.role == "probability" else ".png")
            for a in self.artifacts
        ):
            raise ValueError("Artifact suffix mismatch")
        return self


def regions(probability, threshold, min_area):
    """4-connected predicted components, half-open source coordinates; no GT use."""
    selected = probability >= threshold
    seen = np.zeros(selected.shape, dtype=bool)
    mask = np.zeros(selected.shape, dtype=np.uint8)
    candidates = []
    height, width = selected.shape
    for y, x in zip(*np.where(selected)):
        if seen[y, x]:
            continue
        queue, points = deque([(int(y), int(x))]), []
        seen[y, x] = True
        while queue:
            yy, xx = queue.popleft()
            points.append((yy, xx))
            for ny, nx in ((yy - 1, xx), (yy + 1, xx), (yy, xx - 1), (yy, xx + 1)):
                if (
                    0 <= ny < height
                    and 0 <= nx < width
                    and selected[ny, nx]
                    and not seen[ny, nx]
                ):
                    seen[ny, nx] = True
                    queue.append((ny, nx))
        if len(points) < min_area:
            continue
        ys, xs = np.array(points).T
        mask[ys, xs] = 255
        candidates.append(
            Candidate(
                candidate_id=f"polyp-{len(candidates) + 1}",
                box_xyxy=(
                    int(xs.min()),
                    int(ys.min()),
                    int(xs.max() + 1),
                    int(ys.max() + 1),
                ),
                area_px=len(points),
                mean_model_score=float(probability[ys, xs].mean(dtype=np.float64)),
            )
        )
        if len(candidates) > 100:
            raise ValueError("Too many candidate regions; no silent truncation")
    return mask, candidates


def overlay_pixels(source, mask, candidates):
    """Render deterministic amber candidate masks and boxes over source pixels."""
    overlay = source.copy()
    selected = mask > 0
    overlay[selected] = (
        source[selected].astype(np.float64) * 0.55 + np.array([255, 176, 32]) * 0.45
    ).astype(np.uint8)
    for c in candidates:
        x0, y0, x1, y1 = c.box_xyxy
        overlay[y0, x0:x1] = overlay[y1 - 1, x0:x1] = [255, 176, 32]
        overlay[y0:y1, x0] = overlay[y0:y1, x1 - 1] = [255, 176, 32]
    return overlay


def png(array):
    """Encode a canonical PNG artifact without external resources."""
    buffer = io.BytesIO()
    Image.fromarray(array).save(buffer, format="PNG")
    return buffer.getvalue()


def array_bytes(array):
    """Encode a non-object NumPy array for bounded source verification."""
    buffer = io.BytesIO()
    np.save(buffer, array, allow_pickle=False)
    return buffer.getvalue()


def _image(data, mode, shape):
    """Validate image dimensions and format before decoding pixel arrays."""
    with Image.open(io.BytesIO(data)) as image:
        if (
            image.format != "PNG"
            or image.mode != mode
            or image.size != shape
            or getattr(image, "n_frames", 1) != 1
        ):
            raise ValueError("Image format/dimensions mismatch")
        return np.array(image)


def _probability(data, shape):
    """Bound array headers and payload before allocating a finite probability map."""
    stream = io.BytesIO(data)
    if np.lib.format.read_magic(stream) != (1, 0):
        raise ValueError("Unexpected probability array version")
    declared, fortran, dtype = np.lib.format.read_array_header_1_0(
        stream, max_header_size=1024
    )
    if (
        declared != shape
        or fortran
        or dtype != np.dtype("float32")
        or len(data) - stream.tell() != math.prod(shape) * 4
    ):
        raise ValueError("Probability array header/payload mismatch")
    value = np.load(io.BytesIO(data), allow_pickle=False, max_header_size=1024)
    if not np.isfinite(value).all() or np.any(value < 0) or np.any(value > 1):
        raise ValueError("Invalid probability values")
    return value


def unique(pairs):
    """Reject duplicate JSON keys instead of silently accepting the last value."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def read_exchange(payload, patient_id):
    """Verify all bytes and derived pixels before storing; hashes are not authenticity."""
    if not payload or len(payload) > MAX_BYTES:
        raise ValueError("Endoscopy archive is empty/oversized")
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            entries = archive.infolist()
            if (
                len(entries) != 5
                or len({e.filename for e in entries}) != 5
                or sum(e.file_size for e in entries) > MAX_BYTES
            ):
                raise ValueError("Duplicate/missing/oversized archive members")
            if any(
                e.is_dir() or stat.S_ISLNK(e.external_attr >> 16) or e.flag_bits & 1
                for e in entries
            ):
                raise ValueError("Regular unencrypted files required")
            if archive.getinfo("bundle.json").file_size > 100_000:
                raise ValueError("Manifest too large")
            raw = archive.read("bundle.json")
            bundle = Bundle.model_validate(json.loads(raw, object_pairs_hook=unique))
            if bundle.patient_id != patient_id:
                raise ValueError("Endoscopy patient mismatch")
            if set(archive.namelist()) != {
                "bundle.json",
                *(a.path for a in bundle.artifacts),
            }:
                raise ValueError("Unlisted artifacts")
            artifacts = {}
            for a in bundle.artifacts:
                if archive.getinfo(a.path).file_size != a.size_bytes:
                    raise ValueError("Artifact size mismatch")
                data = archive.read(a.path)
                if sha(data) != a.sha256:
                    raise ValueError("Artifact hash mismatch")
                artifacts[a.path] = data
        by_role = {a.role: artifacts[a.path] for a in bundle.artifacts}
        study = bundle.study
        source = _image(by_role["source_preview"], "RGB", (study.width, study.height))
        if sha(source.tobytes()) != study.source_sha256:
            raise ValueError("Source pixels mismatch")
        probability = _probability(by_role["probability"], (study.height, study.width))
        mask, candidates = regions(
            probability, study.model.threshold, study.model.min_area_px
        )
        if [c.model_dump() for c in candidates] != [
            c.model_dump() for c in study.candidates
        ]:
            raise ValueError("Candidates do not match predicted regions")
        if not np.array_equal(
            _image(by_role["mask"], "L", (study.width, study.height)), mask
        ):
            raise ValueError("Mask does not match predicted regions")
        overlay = overlay_pixels(source, mask, candidates)
        if not np.array_equal(
            _image(by_role["overlay_preview"], "RGB", (study.width, study.height)),
            overlay,
        ):
            raise ValueError("Overlay mismatch")
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
        raise ValueError("Invalid endoscopy archive") from error

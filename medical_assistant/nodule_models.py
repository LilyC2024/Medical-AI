"""Versioned immutable-by-convention records; all persisted data is revalidated."""

from __future__ import annotations

import hashlib
import html
import json
from typing import Annotated, Literal

import numpy as np
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    model_validator,
)

Digest = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
Identifier = Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")]


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


def digest(value) -> str:
    """Canonical content identity; consistency check, not source authenticity."""
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


class Geometry(Record):
    shape_zyx: tuple[StrictInt, StrictInt, StrictInt]
    spacing_zyx_mm: tuple[float, float, float]
    origin_lps_mm: tuple[float, float, float]
    direction_lps: tuple[float, ...]

    @model_validator(mode="after")
    def valid_geometry(self):
        if (
            min(self.shape_zyx) < 1
            or max(self.shape_zyx) > 1024
            or np.prod(self.shape_zyx) > 128 * 1024**2
        ):
            raise ValueError("Unsupported source volume dimensions")
        if min(self.spacing_zyx_mm) <= 0 or len(self.direction_lps) != 9:
            raise ValueError("Invalid physical geometry")
        direction = np.array(self.direction_lps).reshape(3, 3)
        if not np.allclose(
            direction.T @ direction, np.eye(3), atol=1e-5
        ) or not np.isclose(np.linalg.det(direction), 1, atol=1e-5):
            raise ValueError("Direction must be a right-handed orthonormal LPS matrix")
        return self

    def to_lps(self, points_zyx):
        """Map source voxel centers to physical LPS millimetres, including obliquity."""
        xyz = np.asarray(points_zyx, dtype=float)[..., ::-1]
        return (xyz * np.array(self.spacing_zyx_mm)[::-1]) @ np.array(
            self.direction_lps
        ).reshape(3, 3).T + self.origin_lps_mm

    def from_lps(self, points_lps):
        xyz = (np.asarray(points_lps) - self.origin_lps_mm) @ np.array(
            self.direction_lps
        ).reshape(3, 3)
        return (xyz / np.array(self.spacing_zyx_mm)[::-1])[..., ::-1]


class SourceSlice(Record):
    index: Annotated[StrictInt, Field(ge=0)]
    sha256: Digest
    sop_uid_sha256: Digest


class Candidate(Record):
    candidate_id: Identifier
    box_zyx: tuple[float, float, float, float, float, float]
    score: Annotated[float, Field(ge=0, le=1)]
    kind: Literal["model_candidate"] = "model_candidate"

    @model_validator(mode="after")
    def ordered_box(self):
        if np.any(np.array(self.box_zyx[:3]) >= self.box_zyx[3:]):
            raise ValueError("Box requires strictly positive extents")
        return self


class ModelProvenance(Record):
    name: str
    checkpoint_sha256: Digest
    config_sha256: Digest
    execution_device: str
    software_versions: dict[str, str]
    synthetic_fixture: StrictBool
    score_threshold: Annotated[float, Field(ge=0, le=1)]


class Study(Record):
    schema_version: Literal["lung-nodule-study-v1"] = "lung-nodule-study-v1"
    study_id: Identifier
    patient_alias: Identifier
    input_kind: Literal["generated-synthetic", "approved-public-research"]
    acquisition_date: None = None
    source_sha256: Digest
    geometry: Geometry
    sources: Annotated[list[SourceSlice], Field(min_length=2, max_length=512)]
    model: ModelProvenance
    candidates: Annotated[list[Candidate], Field(max_length=300)]
    protocol_attestation: Literal[
        "synthetic-phantom", "adult-noncontrast-chest-complete"
    ]

    @model_validator(mode="after")
    def consistent(self):
        if len(self.sources) != self.geometry.shape_zyx[0] or [
            s.index for s in self.sources
        ] != list(range(len(self.sources))):
            raise ValueError(
                "Every source slice must occur exactly once in physical order"
            )
        if len({s.sop_uid_sha256 for s in self.sources}) != len(self.sources):
            raise ValueError("Duplicate source SOP identity")
        if self.source_sha256 != digest(
            {
                "geometry": self.geometry.model_dump(mode="json"),
                "sources": [s.model_dump(mode="json") for s in self.sources],
            }
        ):
            raise ValueError("Source identity mismatch")
        if (self.input_kind == "generated-synthetic") != (
            self.protocol_attestation == "synthetic-phantom"
        ):
            raise ValueError("Input/protocol attestation mismatch")
        if self.model.synthetic_fixture and self.input_kind != "generated-synthetic":
            raise ValueError("Fixture detector cannot process research patient data")
        ids = [c.candidate_id for c in self.candidates]
        if len(set(ids)) != len(ids):
            raise ValueError("Duplicate candidate identity")
        for c in self.candidates:
            if min(c.box_zyx[:3]) < 0 or np.any(
                np.array(c.box_zyx[3:]) > np.array(self.geometry.shape_zyx) - 1
            ):
                raise ValueError("Candidate outside source voxel centers")
            if c.score < self.model.score_threshold:
                raise ValueError("Candidate below recorded threshold")
        return self


class Caliper(Record):
    start_zyx: tuple[float, float, float]
    end_zyx: tuple[float, float, float]

    def length_mm(self, geometry):
        points = np.array([self.start_zyx, self.end_zyx])
        if (
            np.any(points < 0)
            or np.any(points > np.array(geometry.shape_zyx) - 1)
            or not np.isclose(points[0, 0], points[1, 0])
            or points[0, 0] != int(points[0, 0])
        ):
            raise ValueError("Caliper endpoints must lie on one source slice")
        length = float(np.linalg.norm(np.diff(geometry.to_lps(points), axis=0)))
        if length <= 0:
            raise ValueError("Caliper must have nonzero length")
        return length


class Decision(Record):
    candidate_id: Identifier
    decision: Literal["accept", "reject", "uncertain"]
    caliper: Caliper | None = None


class Review(Record):
    schema_version: Literal["lung-nodule-review-v1"] = "lung-nodule-review-v1"
    study_digest: Digest
    reviewer: Annotated[str, Field(min_length=1, max_length=100, pattern=r"^[^\r\n]+$")]
    qualified_reviewer_attestation: Literal[True]
    decisions: list[Decision]
    approved: Literal[True]

    @model_validator(mode="before")
    @classmethod
    def literal_booleans(cls, value):
        if isinstance(value, dict) and any(
            value.get(k) is not True
            for k in ("qualified_reviewer_attestation", "approved")
        ):
            raise ValueError(
                "Explicit reviewer approval and qualification attestation required"
            )
        return value

    def verify(self, study):
        if self.study_digest != digest(study):
            raise ValueError("Review is stale or belongs to a different study")
        if sorted(d.candidate_id for d in self.decisions) != sorted(
            c.candidate_id for c in study.candidates
        ):
            raise ValueError("Review every candidate exactly once")
        if any(d.decision == "uncertain" for d in self.decisions):
            raise ValueError("Uncertain candidates block completed review")
        for decision in self.decisions:
            if decision.caliper:
                if decision.decision != "accept":
                    raise ValueError(
                        "Only accepted candidates may carry reviewed calipers"
                    )
                decision.caliper.length_mm(study.geometry)
                candidate = next(
                    c
                    for c in study.candidates
                    if c.candidate_id == decision.candidate_id
                )
                points = np.array(
                    [decision.caliper.start_zyx, decision.caliper.end_zyx]
                )
                if np.any(points < candidate.box_zyx[:3]) or np.any(
                    points > candidate.box_zyx[3:]
                ):
                    raise ValueError(
                        "Caliper must reference the reviewed candidate box"
                    )


def research_report(study, review):
    """Compose only approved, structured observations; no LLM or cancer inference."""
    review.verify(study)
    lookup = {d.candidate_id: d for d in review.decisions}
    accepted = [
        c for c in study.candidates if lookup[c.candidate_id].decision == "accept"
    ]
    lines = [
        "# Reviewed lung nodule research summary",
        "",
        f"Study: {study.study_id}; subject alias: {study.patient_alias}.",
        f"Input: {study.input_kind}. Acquisition date unavailable. Prior comparison unavailable.",
        f"Reviewer attestation: {html.escape(review.reviewer)}. Local attestation; credentials not independently verified.",
        f"Model: {study.model.name}. Device: {study.model.execution_device}.",
        f"Candidates: {len(study.candidates)} generated; {len(accepted)} accepted for research review.",
        "",
    ]
    if study.model.synthetic_fixture:
        lines += [
            "SYNTHETIC FIXTURE FINDER: this output is a software demonstration, not trained nodule detection.",
            "",
        ]
    if not accepted:
        lines += [
            "No candidates were accepted. This does not establish a normal CT or exclude nodules/cancer.",
            "",
        ]
    for c in study.candidates:
        decision = lookup[c.candidate_id]
        lo, hi = np.array(c.box_zyx[:3]), np.array(c.box_zyx[3:])
        extent_xyz = ((hi - lo) * study.geometry.spacing_zyx_mm)[::-1]
        center = study.geometry.to_lps((lo + hi) / 2)
        lines += [
            f"- {c.candidate_id}: reviewer {decision.decision}; detector score {c.score:.4f} (not malignancy risk).",
            f"  Source-grid box extents x/y/z: {extent_xyz[0]:.2f}/{extent_xyz[1]:.2f}/{extent_xyz[2]:.2f} mm; these are not lesion diameters or segmentation volume.",
            f"  Box center LPS: ({center[0]:.2f}, {center[1]:.2f}, {center[2]:.2f}) mm; source slices {int(np.floor(lo[0]))}–{int(np.ceil(hi[0]))} (zero-based).",
        ]
        if decision.caliper:
            lines += [
                f"  Reviewer-placed in-plane caliper: {decision.caliper.length_mm(study.geometry):.2f} mm; slice {decision.caliper.start_zyx[0]:g}."
            ]
        for z in range(int(np.floor(lo[0])), int(np.ceil(hi[0])) + 1):
            lines.append(f"  Evidence slice {z}: SHA-256 {study.sources[z].sha256}.")
    lines += [
        "",
        "Conclusion: accepted entries are candidate image findings requiring clinician interpretation; no malignancy diagnosis or management recommendation is generated.",
        "Coverage and protocol are operator attestations, not automatically established by the model. Missed lesions and false positives remain possible. No laterality/lobar location is inferred from position alone.",
        f"Source-series digest: {study.source_sha256}",
        f"Study snapshot digest: {digest(study)}",
        f"Checkpoint SHA-256: {study.model.checkpoint_sha256}",
        f"Inference recipe SHA-256: {study.model.config_sha256}",
        f"Review digest: {digest(review)}",
        "",
    ]
    return "\n".join(lines)

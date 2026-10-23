"""Nodule source inspection and typed candidate/caliper controls; no inference."""

import numpy as np
import streamlit as st

from medical_assistant.nodule_exchange import NoduleBundle, source_pixels, wire_pixels
from medical_assistant.nodule_models import (
    Review as NoduleReview,
    Decision,
    Caliper,
    digest,
)


def pixels_for(manifest, path_for):
    bundle = NoduleBundle.model_validate(manifest)
    item = next(a for a in bundle.artifacts if a.role == "source_volume")
    return bundle, source_pixels(
        bundle, {item.path: path_for("source_volume", None).read_bytes()}
    )


def nodule_viewer(manifest, path_for, key, *, review=None):
    bundle = NoduleBundle.model_validate(manifest)
    study = bundle.study
    st.caption(
        "Synthetic lung nodule research · amber: candidate box · cyan: reviewed caliper. Detector scores are not malignancy risk; box extents are not lesion diameters or volume."
    )
    if study.model.synthetic_fixture:
        st.warning(
            "Non-ML generated-phantom fixture finder — not trained lesion detection."
        )
    st.caption(
        "CT review and final clinical approval are separate steps. This study remains research evidence."
    )
    ids = [c.candidate_id for c in study.candidates]
    selected = st.selectbox(
        "Jump to candidate", ["All slices", *ids], key=key + "_candidate"
    )
    candidate = next((c for c in study.candidates if c.candidate_id == selected), None)
    center = (
        int(round((candidate.box_zyx[0] + candidate.box_zyx[3]) / 2))
        if candidate
        else study.geometry.shape_zyx[0] // 2
    )
    index = st.slider(
        "Slice (zero-based)",
        0,
        study.geometry.shape_zyx[0] - 1,
        center,
        key=key + "_slice_" + selected,
    )
    left, right = st.columns(2)
    left.image(
        str(path_for("source_preview", index)),
        caption=f"Synthetic source slice {index}",
        width="stretch",
    )
    if review is None:
        right.image(
            str(path_for("overlay_preview", index)),
            caption="Verified source-grid candidate overlay",
            width="stretch",
        )
    else:
        _, hu = pixels_for(manifest, path_for)
        parsed = NoduleReview.model_validate(review)
        parsed.verify(study)
        calipers = [d.caliper for d in parsed.decisions if d.caliper]
        _, overlay = wire_pixels(study, hu, index, calipers=calipers)
        right.image(
            overlay, caption="Candidates and LOVISA-reviewed calipers", width="stretch"
        )
    st.caption(f"Source slice {index} · original evidence is retained with this study.")
    with st.expander("Candidate box geometry · details"):
        st.dataframe(
            [
                {
                    "ID": c.candidate_id,
                    "Detector score (not malignancy)": c.score,
                    "Source-grid box extents x/y/z mm": tuple(
                        round(v, 2)
                        for v in (
                            (np.array(c.box_zyx[3:]) - c.box_zyx[:3])
                            * study.geometry.spacing_zyx_mm
                        )[::-1]
                    ),
                }
                for c in study.candidates
            ],
            hide_index=True,
        )
    with st.expander("Source evidence, model and geometry · details"):
        st.code(f"Source slice {index} SHA-256: {study.sources[index].sha256}")
        st.json(manifest)


def candidate_controls(manifest, key):
    """Return typed local choices; nothing is persisted or approved by these controls."""
    bundle = NoduleBundle.model_validate(manifest)
    previous = (
        {d.candidate_id: d for d in bundle.producer_review.decisions}
        if bundle.producer_review
        else {}
    )
    decisions = []
    for c in bundle.study.candidates:
        st.write(f"Candidate {c.candidate_id}")
        old = previous.get(c.candidate_id)
        options = ["uncertain", "accept", "reject"]
        choice = st.selectbox(
            f"Decision {c.candidate_id}",
            options,
            index=options.index(old.decision) if old else 0,
            key=key + "_decision_" + c.candidate_id,
        )
        caliper = None
        enabled = st.checkbox(
            f"Include a source-plane caliper for {c.candidate_id}",
            value=bool(old and old.caliper),
            key=key + "_caliper_" + c.candidate_id,
        )
        if enabled:
            default = (
                old.caliper
                if old and old.caliper
                else Caliper(
                    start_zyx=(
                        int(round((c.box_zyx[0] + c.box_zyx[3]) / 2)),
                        c.box_zyx[1],
                        c.box_zyx[2],
                    ),
                    end_zyx=(
                        int(round((c.box_zyx[0] + c.box_zyx[3]) / 2)),
                        c.box_zyx[1],
                        c.box_zyx[5],
                    ),
                )
            )
            columns = st.columns(5)
            z = columns[0].number_input(
                f"Caliper slice {c.candidate_id}",
                min_value=0,
                max_value=bundle.study.geometry.shape_zyx[0] - 1,
                value=int(default.start_zyx[0]),
                key=key + "_z_" + c.candidate_id,
            )
            values = []
            for column, label, value, maximum, suffix in zip(
                columns[1:],
                ["Start row", "Start column", "End row", "End column"],
                [
                    default.start_zyx[1],
                    default.start_zyx[2],
                    default.end_zyx[1],
                    default.end_zyx[2],
                ],
                [
                    bundle.study.geometry.shape_zyx[1] - 1,
                    bundle.study.geometry.shape_zyx[2] - 1,
                ]
                * 2,
                ["y0", "x0", "y1", "x1"],
            ):
                values.append(
                    column.number_input(
                        f"{label} {c.candidate_id}",
                        min_value=0.0,
                        max_value=float(maximum),
                        value=float(value),
                        key=key + "_" + suffix + "_" + c.candidate_id,
                    )
                )
            caliper = Caliper(
                start_zyx=(z, values[0], values[1]), end_zyx=(z, values[2], values[3])
            )
        decisions.append(
            Decision(candidate_id=c.candidate_id, decision=choice, caliper=caliper)
        )
    return decisions


def build_nodule_review(manifest, decisions, reviewer, attested):
    bundle = NoduleBundle.model_validate(manifest)
    value = NoduleReview(
        study_digest=digest(bundle.study),
        reviewer=reviewer,
        qualified_reviewer_attestation=attested,
        approved=True,
        decisions=decisions,
    )
    value.verify(bundle.study)
    return value


def preview_calipers(manifest, path_for, decisions):
    bundle, hu = pixels_for(manifest, path_for)
    for decision in decisions:
        if decision.caliper:
            caliper = decision.caliper
            length = caliper.length_mm(bundle.study.geometry)
            plane = int(caliper.start_zyx[0])
            _, overlay = wire_pixels(bundle.study, hu, plane, calipers=[caliper])
            st.image(
                overlay,
                caption=f"Unapproved preview {decision.candidate_id}: {length:.2f} mm · source slice {plane}",
            )

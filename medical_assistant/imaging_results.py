"""Small, deterministic CT summaries shared by the viewer and clinical summary."""

import math

from medical_assistant.nodule_exchange import NoduleBundle
from medical_assistant.nodule_models import Review as NoduleReview


def summarize(manifest, review=None):
    if manifest.get("schema_version") not in (
        "mhcra-lung-nodules-v2",
        "lovisa-ct-research-v3",
    ):
        return {
            "study_id": manifest["study_id"],
            "mode": "Legacy tissue-mask demo",
            "status": "Research masks; not nodule detection",
            "rows": [],
            "conclusion": "Tissue-class counts do not establish a lesion diagnosis or a normal CT.",
            "voxel_counts": manifest["voxel_counts"],
        }
    bundle = NoduleBundle.model_validate(manifest)
    study = bundle.study
    parsed = NoduleReview.model_validate(review) if review else None
    if parsed:
        parsed.verify(study)
    decisions = {d.candidate_id: d for d in parsed.decisions} if parsed else {}
    rows = []
    for c in study.candidates:
        d = decisions.get(c.candidate_id)
        rows.append(
            {
                "Candidate": c.candidate_id,
                "Detector score": round(c.score, 4),
                "Source slices": f"{math.floor(c.box_zyx[0])}–{math.ceil(c.box_zyx[3])}",
                "Review": d.decision if d else "Pending",
                "Source SHA-256": study.sources[math.floor(c.box_zyx[0])].sha256,
                "Caliper mm": round(d.caliper.length_mm(study.geometry), 2)
                if d and d.caliper
                else None,
            }
        )
    return {
        "study_id": bundle.study_id,
        "mode": "Non-ML fixture"
        if study.model.synthetic_fixture
        else "Installed pretrained detector",
        "status": "Accepted research study" if parsed else "Pending human review",
        "rows": rows,
        "candidate_count": len(rows),
        "accepted_count": sum(d.decision == "accept" for d in decisions.values()),
        "caliper_count": sum(bool(d.caliper) for d in decisions.values()),
        "conclusion": f"{len(rows)} candidate(s) proposed; "
        + (
            "human review remains pending. "
            if not parsed
            else f"{sum(d.decision == 'accept' for d in decisions.values())} accepted for research review. "
        )
        + "Research only; no malignancy diagnosis or normal-CT conclusion is established.",
    }

"""Modality-specific candidate review binding; no clinical or safety decisions."""

from medical_assistant.endo_contracts import VERSION, Bundle, Review, digest


def is_endoscopy(manifest):
    return manifest.get("schema_version") == VERSION


def checked_endo_review(manifest, review, *, reviewer=None):
    bundle = Bundle.model_validate(manifest)
    value = Review.model_validate(
        review.model_dump() if isinstance(review, Review) else review
    )
    value.verify(bundle.study)
    if reviewer is not None and value.reviewer != reviewer:
        raise PermissionError("Endoscopy reviewer must match authenticated reviewer")
    return value


def endo_acceptance_digest(proposal, review):
    value = checked_endo_review(proposal["manifest"], review)
    return digest(
        {
            "proposal_sha256": proposal["sha256"],
            "endo_review": value.model_dump(mode="json"),
        }
    )


def verify_endo_snapshot(snapshot):
    value = checked_endo_review(
        snapshot["manifest"],
        snapshot.get("endo_review"),
        reviewer=snapshot["review"]["reviewer"],
    )
    if snapshot["review"]["draft_sha256"] != endo_acceptance_digest(snapshot, value):
        raise ValueError("Endoscopy decisions are not bound to acceptance")
    return value


def summarize_endo(manifest, review=None):
    bundle = Bundle.model_validate(manifest)
    parsed = checked_endo_review(manifest, review) if review else None
    lookup = {d.candidate_id: d.decision for d in parsed.decisions} if parsed else {}
    study = bundle.study
    return {
        "candidate_count": len(study.candidates),
        "accepted_count": sum(d == "accept" for d in lookup.values()),
        "rows": [
            {
                "Candidate": c.candidate_id,
                "Area (pixels)": c.area_px,
                "Image area (%)": round(
                    100 * c.area_px / (study.width * study.height), 2
                ),
                "Model score": round(c.mean_model_score, 3),
                "Review": lookup.get(c.candidate_id, "Pending"),
            }
            for c in study.candidates
        ],
        "mode": study.model.name,
        "scope": study.model.evaluation_scope,
    }

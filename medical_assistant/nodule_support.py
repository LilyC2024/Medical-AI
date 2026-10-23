"""Typed nodule review binding; does not change clinical facts or safety routing."""

from medical_assistant.nodule_exchange import NoduleBundle
from medical_assistant.nodule_models import (
    Review as NoduleReview,
    digest as structured_digest,
)


def is_nodule(manifest):
    return manifest.get("schema_version") == "mhcra-lung-nodules-v2"


def checked_nodule_review(manifest, review, *, reviewer=None):
    bundle = NoduleBundle.model_validate(manifest)
    value = NoduleReview.model_validate(
        review.model_dump() if isinstance(review, NoduleReview) else review
    )
    value.verify(bundle.study)
    if reviewer is not None and value.reviewer != reviewer:
        raise PermissionError(
            "Nodule reviewer must match authenticated imaging reviewer"
        )
    return value


def imaging_acceptance_digest(proposal, nodule_review=None):
    if not is_nodule(proposal["manifest"]):
        if nodule_review is not None:
            raise ValueError(
                "Nodule decisions cannot be attached to tissue-mask imaging"
            )
        return proposal["sha256"]
    if nodule_review is None:
        raise ValueError("Explicit nodule candidate review required")
    value = checked_nodule_review(proposal["manifest"], nodule_review)
    return structured_digest(
        {
            "proposal_sha256": proposal["sha256"],
            "nodule_review": value.model_dump(mode="json"),
        }
    )


def verify_nodule_snapshot(snapshot):
    if not is_nodule(snapshot["manifest"]):
        return None
    value = checked_nodule_review(
        snapshot["manifest"],
        snapshot.get("nodule_review"),
        reviewer=snapshot["review"]["reviewer"],
    )
    if snapshot["review"]["draft_sha256"] != imaging_acceptance_digest(snapshot, value):
        raise ValueError("Nodule choices/calipers are not bound to imaging acceptance")
    return value

"""Show producer-signature status and declared false-positive rates beside review controls."""

import streamlit as st

UNSIGNED = (
    "Unsigned producer archive. Hashes prove internal consistency only; anyone could "
    "have created these candidates. Inspect every candidate yourself."
)


def signature_notice(proposal):
    """Render the producer signature status recorded when the archive was prepared."""
    check = proposal.get("producer_signature") or {"status": "unsigned"}
    if check["status"] == "verified":
        st.success(
            f"Producer signature verified: {check['label']} "
            f"(key {check['key_id'][:12]}…). This identifies the exporter, not model accuracy."
        )
    elif check["status"] == "untrusted-key":
        st.warning(
            f"Signed by an unpinned key {check['key_id'][:12]}…. Treat as unsigned until "
            "its public key is pinned with `python -m medical_assistant.producer_trust`."
        )
    else:
        st.warning(UNSIGNED)


def false_positive_text(proposal):
    """Plain-language false-positive statement shown next to every candidate."""
    check = proposal.get("producer_signature") or {}
    performance = check.get("performance") if check.get("status") == "verified" else None
    if not performance:
        return "Known false-positive rate: not available (no verified producer claim)."
    if not performance["measured"]:
        return "Known false-positive rate for this model: not measured."
    rate = performance["false_positive_fraction"]
    return (
        f"Known false-positive rate for this model: about {rate:.0%} of candidate "
        f"regions ({performance['test_images']} test images, "
        f"{performance['negative_images']} negative). {performance['limitations']}"
    )

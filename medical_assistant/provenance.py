"""Identify exactly which model, prompts and safety policy produced a draft.

Recorded in the case state, bound into report approval and exported with the
report. Identity is not validation: these fields make runs comparable, they do not
show that the model adds value or is correct.
"""

import hashlib

from medical_assistant.agents import COMMON, ROLES
from medical_assistant.compact_reasoning import PROMPT

PROMPT_VERSION = "reasoning-prompt-v1"


def prompt_sha256():
    """Hash of every prompt text the reasoning step can send to the model."""
    text = "\n\x00\n".join((COMMON, ROLES["reasoning"], PROMPT))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def inference_provenance(inference, safety_decision):
    return {
        "model": inference.model,
        "model_digest": getattr(inference, "model_digest", None),
        "prompt_version": PROMPT_VERSION,
        "prompt_sha256": prompt_sha256(),
        "policy_version": safety_decision["policy_version"],
        "policy_sha256": safety_decision["policy_sha256"],
    }

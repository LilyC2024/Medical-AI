"""Concise literal UI errors with bounded explanations and inert markup."""

from pydantic import ValidationError

from medical_assistant.report import inline_text


def error_message(error, *, limit=600):
    """Escape an actionable bounded message; omit Pydantic inputs and help URLs.

    Validation errors can echo arbitrary uploaded text. Keep field locations and
    explanations, while original source content stays in its dedicated view.
    """
    if isinstance(error, ValidationError):
        issues = error.errors(include_url=False, include_input=False)
        messages = [
            f"{'.'.join(map(str, issue['loc'])) or 'Record'}: {issue['msg']}"
            for issue in issues[:3]
        ]
        if len(issues) > 3:
            messages.append(f"{len(issues) - 3} additional validation issues")
        text = "; ".join(messages)
    else:
        text = str(error)
    text = " ".join(text.split())
    if len(text) > limit:
        text = text[:limit] + "…"
    return inline_text(text)

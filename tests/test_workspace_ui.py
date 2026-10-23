"""Design navigation, escaping and genuinely nonblocking scripted analysis."""

import threading
import time

from test_ui import ui, login, wait_analysis, open_imaging, prepare_safety  # noqa: F401
from medical_assistant.ui.components import safe


def test_workspace_has_operating_guide_and_readable_history(ui):
    app, _, _, _ = ui
    login(app)
    assert app.title[0].value == "LOVISA"
    text = "\n".join(m.value for m in app.markdown)
    assert "Your review steps" in text and "The patient story" in "\n".join(
        h.value for h in app.subheader
    )
    assert "lv-timeline" in text and "fictional_patient.json" in text
    assert not app.get("download_button")
    open_imaging(app)
    assert not app.button(key="ct_generate").disabled
    assert any("Your review steps" in m.value for m in app.markdown)


def test_source_html_is_escaped_in_design_components():
    attack = (
        '<img src="https://example.invalid/x" onerror="alert(1)"><script>bad()</script>'
    )
    rendered = safe(attack)
    assert "<img" not in rendered and "<script>" not in rendered
    assert "&lt;img" in rendered and "&quot;" in rendered


def test_running_model_does_not_block_ui_and_can_be_cancelled(ui, monkeypatch):
    app, path, auth, inference = ui
    login(app)
    prepare_safety(app)
    entered, release = threading.Event(), threading.Event()
    original = inference.assess

    def slow(*args, **kwargs):
        entered.set()
        release.wait(3)
        return original(*args, **kwargs)

    monkeypatch.setattr(inference, "assess", slow)
    start = time.monotonic()
    app.button(key="generate").click().run(timeout=5)
    elapsed = time.monotonic() - start
    assert entered.wait(1)
    assert elapsed < 2.5 and not release.is_set()
    task = app.session_state.analysis_task
    assert not app.button(key="analysis_cancel").disabled
    assert not app.get("download_button")
    app.button(key="analysis_cancel").click().run()
    release.set()
    task._thread.join(timeout=2)
    assert not app.exception and "analysis_task" not in app.session_state
    assert "run_error" in app.session_state and not app.get("download_button")
    assert task._result is None

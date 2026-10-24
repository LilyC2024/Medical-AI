"""Opt-in, redacted, local-file OpenTelemetry spans for workflow steps.

Set ``LOVISA_TRACE_FILE`` to a local path to append one JSON span per line.
Nothing is exported over the network. Spans carry only the step name, a hashed
case ID, the resulting workflow status, timing and an exception *type*; record
text, patient identifiers, prompts, model output and notes are never attributes.
"""

import hashlib
import json
import os
import threading
from pathlib import Path

from langgraph.errors import GraphInterrupt

TRACE_ENV = "LOVISA_TRACE_FILE"
_providers, _lock = {}, threading.Lock()


def _tracer(path):
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

    path = Path(path).resolve()
    with _lock:
        if path not in _providers:
            path.parent.mkdir(parents=True, exist_ok=True)
            stream = path.open("a", encoding="utf-8")
            provider = TracerProvider(resource=Resource({"service.name": "lovisa"}))
            provider.add_span_processor(
                SimpleSpanProcessor(
                    ConsoleSpanExporter(
                        out=stream,
                        formatter=lambda span: json.dumps(json.loads(span.to_json())) + "\n",
                    )
                )
            )
            _providers[path] = provider
        return _providers[path].get_tracer("lovisa.workflow")


def case_ref(case_id):
    """Stable, non-reversible case reference for correlating spans."""
    return hashlib.sha256(str(case_id).encode()).hexdigest()[:16]


def traced(name, node):
    """Wrap a graph node in a span when tracing is enabled; otherwise return it unchanged."""
    path = os.environ.get(TRACE_ENV)
    if not path:
        return node
    tracer = _tracer(path)

    def run(state):
        with tracer.start_as_current_span(
            "lovisa." + name, record_exception=False, set_status_on_exception=False
        ) as span:
            span.set_attribute("lovisa.step", name)
            span.set_attribute("lovisa.case_ref", case_ref(state.get("case_id")))
            try:
                result = node(state)
            except GraphInterrupt:
                span.set_attribute("lovisa.outcome", "paused-for-human")
                raise
            except Exception as error:
                span.set_attribute("lovisa.outcome", "error")
                span.set_attribute("lovisa.error_type", type(error).__name__)
                raise
            status = result.get("status") if isinstance(result, dict) else None
            span.set_attribute("lovisa.outcome", status or "ok")
            return result

    return run

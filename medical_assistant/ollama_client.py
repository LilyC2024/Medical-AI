"""Ollama HTTP adapter: fixed loopback, no proxies, redirects, or cloud models."""

import json
import re
import time

import httpx

from medical_assistant.models import Assessment

BASE_URL = "http://127.0.0.1:11434"


class OllamaClient:
    def __init__(self, model: str = "gemma4:e2b", *, transport=None):
        if (
            not re.fullmatch(
                r"[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*(?::[A-Za-z0-9_.-]+)?", model
            )
            or "cloud" in model.lower()
        ):
            raise ValueError(
                "Choose an installed local Ollama model, not a cloud model"
            )
        self.model = model
        self._deadline = None
        self.http = httpx.Client(
            base_url=BASE_URL,
            timeout=httpx.Timeout(90, connect=3),
            trust_env=False,
            follow_redirects=False,
            transport=transport,
        )

    def close(self):
        self.http.close()

    def _post(self, path: str, body: dict) -> dict:
        remaining = (
            (self._deadline - time.monotonic()) if self._deadline is not None else 90
        )
        if remaining <= 0:
            raise TimeoutError(
                "Local analysis reached its response limit; no report was completed"
            )
        timeout = min(5 if path == "/api/show" else 90, remaining)
        try:
            response = self.http.post(
                path, json=body, timeout=httpx.Timeout(timeout, connect=min(3, timeout))
            )
        except httpx.TimeoutException as error:
            raise TimeoutError(
                "Local model did not respond in time; no report was completed"
            ) from error
        response.raise_for_status()
        return response.json()

    def ensure_local(self):
        # /api/show requires a locally installed model; reject remote-backed metadata too.
        details = self._post("/api/show", {"model": self.model})
        if any(details.get(key) for key in ("remote_host", "remote_model")):
            raise ValueError("Remote-backed Ollama models are prohibited")
        size = details.get("details", {}).get("parameter_size", "")
        if not size or size in ("0", "0B"):
            raise ValueError(
                "Ollama did not confirm a locally installed parameter model"
            )

    def assess(
        self, system: str, user: str, *, schema: dict | None = None
    ) -> Assessment:
        output_schema = schema if schema is not None else Assessment.model_json_schema()
        from medical_assistant.compact_reasoning import MARKER, PROMPT, prepare, expand

        compact = output_schema.get("$comment") == MARKER
        expansion = None
        if compact:
            record, refs, maps, user, output_schema = prepare(user)
            expansion = (record, refs, maps)
            system = PROMPT
        # Conservative byte budget reserves space for output and chat framing.
        # Fail instead of letting Ollama silently truncate a long clinical input.
        if len((system + user + json.dumps(output_schema)).encode("utf-8")) > 11_000:
            raise ValueError(
                "Request exceeds the conservative local context budget; shorten the supplied record"
            )
        self._deadline = time.monotonic() + 90
        self.ensure_local()
        result = self._post(
            "/api/chat",
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "stream": False,
                "think": False,
                "keep_alive": "15m",
                "format": output_schema,
                "options": {
                    "temperature": 0,
                    "num_ctx": 16384,
                    "num_predict": 1200 if compact else 2000,
                },
            },
        )
        if not result.get("done") or result.get("done_reason") == "length":
            raise ValueError(
                "Ollama returned an incomplete assessment; no report was completed"
            )
        self.last_metrics = {
            key: result.get(key)
            for key in ("total_duration", "prompt_eval_count", "eval_count")
        }
        parsed = json.loads(result["message"]["content"])
        return (
            expand(parsed, *expansion) if compact else Assessment.model_validate(parsed)
        )

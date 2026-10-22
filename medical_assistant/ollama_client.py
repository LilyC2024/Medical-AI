"""Ollama HTTP adapter: fixed loopback, no proxies, redirects, or cloud models."""

import json
import re

import httpx

from medical_assistant.models import Assessment

BASE_URL = "http://127.0.0.1:11434"


class OllamaClient:
    def __init__(self, model: str = "gemma4:e2b", *, transport=None):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*(?::[A-Za-z0-9_.-]+)?", model) or "cloud" in model.lower():
            raise ValueError("Choose an installed local Ollama model, not a cloud model")
        self.model = model
        self.http = httpx.Client(
            base_url=BASE_URL, timeout=httpx.Timeout(240, connect=5),
            trust_env=False, follow_redirects=False, transport=transport,
        )

    def close(self):
        self.http.close()

    def _post(self, path: str, body: dict) -> dict:
        response = self.http.post(path, json=body)
        response.raise_for_status()
        return response.json()

    def ensure_local(self):
        # /api/show requires a locally installed model; reject remote-backed metadata too.
        details = self._post("/api/show", {"model": self.model})
        if any(details.get(key) for key in ("remote_host", "remote_model")):
            raise ValueError("Remote-backed Ollama models are prohibited")
        size = details.get("details", {}).get("parameter_size", "")
        if not size or size in ("0", "0B"):
            raise ValueError("Ollama did not confirm a locally installed parameter model")

    def assess(self, system: str, user: str, *, schema: dict | None = None) -> Assessment:
        output_schema = schema if schema is not None else Assessment.model_json_schema()
        # Conservative byte budget reserves space for output and chat framing.
        # Fail instead of letting Ollama silently truncate a long clinical input.
        if len((system + user + json.dumps(output_schema)).encode("utf-8")) > 11_000:
            raise ValueError("Request exceeds the conservative local context budget; shorten the supplied record")
        self.ensure_local()
        result = self._post("/api/chat", {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "stream": False,
            "think": False,
            "format": output_schema,
            "options": {"temperature": 0, "num_ctx": 16384, "num_predict": 4000},
        })
        if not result.get("done") or result.get("done_reason") == "length":
            raise ValueError("Ollama returned an incomplete assessment; no report was completed")
        return Assessment.model_validate(json.loads(result["message"]["content"]))

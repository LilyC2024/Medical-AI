import json
import os

import httpx
import pytest

from medical_assistant.ollama_client import BASE_URL, OllamaClient


@pytest.mark.parametrize(
    "model", ["example:cloud", "https://ollama.com/model", "x?host=evil", ""]
)
def test_cloud_and_invalid_model_names_rejected(model):
    with pytest.raises(ValueError):
        OllamaClient(model)


def test_only_loopback_schema_and_no_streaming(monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://example.invalid:9999")
    requests = []

    def handler(request):
        requests.append(request)
        assert str(request.url).startswith(BASE_URL + "/api/")
        if request.url.path == "/api/tags":
            return httpx.Response(
                200, json={"models": [{"name": "gemma4:e2b", "digest": "d" * 64}]}
            )
        body = json.loads(request.content)
        if request.url.path == "/api/show":
            return httpx.Response(200, json={"details": {"parameter_size": "7B"}})
        assert body["stream"] is False
        assert body["format"]["type"] == "object"
        assert body["options"]["temperature"] == 0
        return httpx.Response(200, json={"done": True, "message": {"content": "{}"}})

    client = OllamaClient(transport=httpx.MockTransport(handler))
    assert client.assess("system", "user").findings == []
    assert [r.url.path for r in requests] == ["/api/show", "/api/tags", "/api/chat"]
    assert client.model_digest == "d" * 64
    client.close()


@pytest.mark.parametrize(
    "metadata",
    [
        {"remote_host": "https://ollama.com", "details": {"parameter_size": "7B"}},
        {"remote_model": "remote", "details": {"parameter_size": "7B"}},
        {"details": {"parameter_size": "0B"}},
        {},
    ],
)
def test_remote_backed_or_unconfirmed_model_fails_before_chat(metadata):
    paths = []

    def handler(request):
        paths.append(request.url.path)
        return httpx.Response(200, json=metadata)

    client = OllamaClient(transport=httpx.MockTransport(handler))
    with pytest.raises(ValueError):
        client.assess("system", "user")
    assert paths == ["/api/show"]
    client.close()


def test_redirects_never_followed():
    paths = []

    def handler(request):
        paths.append(str(request.url))
        return httpx.Response(307, headers={"Location": "https://example.invalid"})

    client = OllamaClient(transport=httpx.MockTransport(handler))
    with pytest.raises(httpx.HTTPStatusError):
        client.assess("system", "user")
    assert len(paths) == 1
    client.close()


@pytest.mark.parametrize(
    "result",
    [
        {"done": False},
        {"done": True, "done_reason": "length", "message": {"content": "{}"}},
        {"done": True, "message": {"content": "not json"}},
        {"done": True, "message": {"content": '{"unexpected_field": 1}'}},
    ],
)
def test_incomplete_or_malformed_output_is_not_accepted(result):
    def handler(request):
        payload = (
            {"details": {"parameter_size": "7B"}}
            if request.url.path == "/api/show"
            else result
        )
        return httpx.Response(200, json=payload)

    client = OllamaClient(transport=httpx.MockTransport(handler))
    with pytest.raises(ValueError):
        client.assess("system", "user")
    client.close()


def test_remote_tracing_disabled():
    for key in ("LANGCHAIN_TRACING_V2", "LANGCHAIN_TRACING", "LANGSMITH_TRACING"):
        assert os.environ[key] == "false"


def test_oversize_prompt_stops_before_any_http_request():
    def handler(request):
        raise AssertionError("No network request should occur for an oversized prompt")

    client = OllamaClient(transport=httpx.MockTransport(handler))
    with pytest.raises(ValueError, match="context budget"):
        client.assess("system", "x" * 11_001)
    client.close()


def test_requests_are_bounded_and_model_kept_warm():
    def handler(request):
        assert request.extensions["timeout"]["read"] <= 90
        if request.url.path == "/api/tags":
            return httpx.Response(
                200, json={"models": [{"name": "gemma4:e2b", "digest": "d" * 64}]}
            )
        body = json.loads(request.content)
        if request.url.path == "/api/show":
            assert request.extensions["timeout"]["read"] <= 5
            return httpx.Response(200, json={"details": {"parameter_size": "7B"}})
        assert body["keep_alive"] == "15m"
        assert body["options"]["num_predict"] == 2000
        return httpx.Response(200, json={"done": True, "message": {"content": "{}"}})

    client = OllamaClient(transport=httpx.MockTransport(handler))
    client.assess("system", "user")
    client.close()


def test_local_model_timeout_does_not_produce_assessment():
    def handler(request):
        raise httpx.ReadTimeout("scripted timeout")

    client = OllamaClient(transport=httpx.MockTransport(handler))
    with pytest.raises(TimeoutError, match="did not respond"):
        client.assess("system", "user")
    client.close()


@pytest.mark.parametrize("installed", ["e" * 64, None])
def test_pinned_digest_mismatch_or_missing_fails_before_chat(monkeypatch, installed):
    monkeypatch.setenv("LOVISA_OLLAMA_MODEL_DIGEST", "d" * 64)
    paths = []

    def handler(request):
        paths.append(request.url.path)
        if request.url.path == "/api/tags":
            models = [{"name": "gemma4:e2b", "digest": installed}] if installed else []
            return httpx.Response(200, json={"models": models})
        return httpx.Response(200, json={"details": {"parameter_size": "7B"}})

    client = OllamaClient(transport=httpx.MockTransport(handler))
    with pytest.raises(ValueError, match="pinned digest"):
        client.assess("system", "user")
    assert paths == ["/api/show", "/api/tags"]
    client.close()

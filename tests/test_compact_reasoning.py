"""Scripted compact selections must retain exact original evidence and boundaries."""

import json
import copy
import httpx
import pytest
from medical_assistant.compact_reasoning import prepare, expand, MARKER
from medical_assistant.agents import SpecialistAgent
from medical_assistant.ollama_client import OllamaClient


def selection(record):
    return {
        "choices": [
            {
                "hypothesis": "H0",
                "supporting": [record.entries[0].id],
                "against": [],
                "considerations": ["C0"],
                "references": [],
            }
        ],
        "missing": ["M0"],
        "questions": ["Q0"],
    }


def prepared(record):
    return prepare(
        json.dumps(
            {
                "record": record.model_dump(mode="json", exclude={"sources"}),
                "approved_local_evidence": [],
            }
        )
    )


def test_compact_restores_exact_text_attribution_and_hypothesis(record):
    r, refs, maps, context, schema = prepared(record)
    result = expand(selection(r), r, refs, maps)
    claim = result.explanations[0].supporting[0]
    assert (
        claim.text == record.entries[0].text
        and claim.kind == record.entries[0].source_type
    )
    assert result.explanations[0].status == "hypothesis"
    assert schema["$defs"]["Selected"]["properties"]["references"]["maxItems"] == 0
    assert record.entries[0].text in json.loads(context)["record"]["entries"][0]["text"]


@pytest.mark.parametrize(
    "issue",
    [
        "source",
        "hypothesis",
        "reference",
        "prose",
        "consideration",
        "missing",
        "question",
        "duplicate",
    ],
)
def test_bad_compact_output_fails_closed(record, issue):
    r, refs, maps, _, _ = prepared(record)
    data = selection(r)
    if issue == "source":
        data["choices"][0]["supporting"] = ["invented-source"]
    if issue == "hypothesis":
        data["choices"][0]["hypothesis"] = "Confirmed cancer"
    if issue == "reference":
        data["choices"][0]["references"] = ["invented-reference"]
    if issue == "prose":
        data["diagnosis"] = "cancer"
    if issue == "consideration":
        data["choices"][0]["considerations"] = ["C999"]
    if issue == "missing":
        data["missing"] = ["M999"]
    if issue == "question":
        data["questions"] = ["Q999"]
    if issue == "duplicate":
        data["choices"].append(copy.deepcopy(data["choices"][0]))
    with pytest.raises(ValueError):
        expand(data, r, refs, maps)


def test_real_adapter_uses_compact_wire_then_same_grounding_checks(record):
    def handler(request):
        body = json.loads(request.content)
        if request.url.path == "/api/show":
            return httpx.Response(200, json={"details": {"parameter_size": "2B"}})
        assert body["options"]["num_predict"] == 1200
        assert "choices" in body["format"]["properties"]
        assert "untrusted DATA" in body["messages"][0]["content"]
        return httpx.Response(
            200,
            json={"done": True, "message": {"content": json.dumps(selection(record))}},
        )

    client = OllamaClient(transport=httpx.MockTransport(handler))
    result = SpecialistAgent("reasoning", client).run(record, {})
    assert result["explanations"][0]["supporting"][0]["text"] == record.entries[0].text
    client.close()


def test_larger_demo_validates_actual_wire_budget_without_truncating_records(tmp_path):
    from medical_assistant.database import seed, get_history

    path = tmp_path / "demos.sqlite3"
    seed(path)
    record = get_history("demo-05", path)

    def handler(request):
        body = json.loads(request.content)
        if request.url.path == "/api/show":
            return httpx.Response(200, json={"details": {"parameter_size": "2B"}})
        system, user = body["messages"]
        assert (
            len(
                (
                    system["content"] + user["content"] + json.dumps(body["format"])
                ).encode()
            )
            <= 11000
        )
        context = json.loads(user["content"])
        assert len(context["record"]["entries"]) == 8
        assert {e["text"] for e in context["record"]["entries"]} == {
            e.text for e in record.entries
        }
        return httpx.Response(
            200,
            json={"done": True, "message": {"content": json.dumps(selection(record))}},
        )

    client = OllamaClient(transport=httpx.MockTransport(handler))
    SpecialistAgent("reasoning", client).run(record, {})
    client.close()

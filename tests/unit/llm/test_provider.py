import json

import pytest
from tests.unit.llm.conftest import chat, response

from ici_core.domain.evidence import ContextPack
from ici_core.ports import LLMProvider
from ici_llm.errors import InvalidOutput, RateLimited, Refused, Truncated, Unavailable

SCHEMA = {
    "type": "object",
    "properties": {"value": {"type": "number"}},
    "required": ["value"],
    "additionalProperties": False,
}


def test_real_sdk_payload_respects_the_port(sdk_provider, evidence_items):
    provider, calls = sdk_provider(chat())
    assert isinstance(provider, LLMProvider)
    assert (
        provider.compose("Capacity?", ContextPack(tuple(evidence_items)))
        == chat()["choices"][0]["message"]["content"]
    )
    path, body = calls[0]
    assert path.endswith("/chat/completions")
    assert body["temperature"] == 0.0
    assert body["max_completion_tokens"] == 512
    assert "max_tokens" not in body
    assert json.loads(body["messages"][1]["content"])["context"][0]["id"] == "e1"


@pytest.mark.parametrize(
    "finish,text,refusal,error",
    [
        ("length", "Partial answer", None, Truncated),
        ("length", "", None, Truncated),
        ("stop", "", None, InvalidOutput),
        ("stop", "Looks usable", "declined", Refused),
        ("content_filter", "partial", None, Refused),
        ("tool_calls", "partial", None, InvalidOutput),
    ],
)
def test_chat_failures_never_return_partial_text(sdk_provider, finish, text, refusal, error):
    provider, calls = sdk_provider(chat(text, finish=finish, refusal=refusal))
    with pytest.raises(error):
        provider.compose("question", ContextPack(), model="gpt-5")
    assert len(calls) == 1
    assert "temperature" not in calls[0][1]
    assert calls[0][1]["reasoning_effort"] == "minimal"


@pytest.mark.parametrize("model", ["gpt-4o-mini", "gpt-5"])
def test_structured_response_validates_schema(sdk_provider, model):
    payload = response() if model == "gpt-5" else chat('{"value":60}')
    provider, calls = sdk_provider(payload)
    assert provider.structured("extract", ContextPack(), SCHEMA, model=model) == {"value": 60}
    if model == "gpt-5":
        assert calls[0][0].endswith("/responses")
        assert calls[0][1]["text"] == {"format": {"type": "json_object"}}


@pytest.mark.parametrize(
    "text",
    ['{"value":"sixty"}', '{"extra":60}', '{"value":60,"value":61}', '{"value":NaN}', "[]", "{"],
)
def test_invalid_json_never_escapes(sdk_provider, text):
    provider, _ = sdk_provider(response(text))
    with pytest.raises(InvalidOutput):
        provider.structured("extract", ContextPack(), SCHEMA, model="gpt-5")


@pytest.mark.parametrize(
    "status,reason,refusal,error",
    [
        ("incomplete", "max_output_tokens", None, Truncated),
        ("incomplete", "content_filter", None, Refused),
        ("failed", None, None, InvalidOutput),
        ("completed", None, "declined", Refused),
    ],
)
def test_response_completion_status_is_checked(sdk_provider, status, reason, refusal, error):
    provider, _ = sdk_provider(response(status=status, reason=reason, refusal=refusal))
    with pytest.raises(error):
        provider.structured("extract", ContextPack(), SCHEMA, model="gpt-5")


@pytest.mark.parametrize(
    "status,error", [(429, RateLimited), (503, Unavailable), (401, Unavailable)]
)
def test_http_errors_are_typed_and_not_retried(sdk_provider, status, error):
    provider, calls = sdk_provider({"error": {"message": "SECRET MUST NOT ESCAPE"}}, status=status)
    with pytest.raises(error) as caught:
        provider.compose("question", ContextPack())
    assert len(calls) == 1
    assert "SECRET" not in str(caught.value)


def test_embeddings_preserve_input_order_and_validate_dimensions(sdk_provider):
    payload = {
        "object": "list",
        "model": "text-embedding-3-small",
        "data": [
            {"object": "embedding", "index": 1, "embedding": [0.2, 0.3]},
            {"object": "embedding", "index": 0, "embedding": [0.0, 0.1]},
        ],
        "usage": {"prompt_tokens": 4, "total_tokens": 4},
    }
    provider, calls = sdk_provider(payload)
    provider.embedding_dimensions = 2
    assert provider.embed(["first", "second"]) == [[0.0, 0.1], [0.2, 0.3]]
    assert provider.embed([]) == []
    assert len(calls) == 1
    provider.embedding_dimensions = 3
    with pytest.raises(InvalidOutput):
        provider.embed(["first", "second"])


def test_external_schema_references_cannot_fetch_network(sdk_provider):
    provider, _ = sdk_provider(chat('{"value":60}'))
    with pytest.raises(InvalidOutput):
        provider.structured("extract", ContextPack(), {"$ref": "https://example.invalid/schema"})

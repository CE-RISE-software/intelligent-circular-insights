"""Synthetic responses only. No fixture in this suite requires an API key."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import httpx
import pytest
from openai import OpenAI

from ici_llm.provider import OpenAIProvider
from ici_llm.transport import OpenAITransport, Request, TransportResult


def chat(text="The declared capacity is 60 kWh [e1].", *, finish="stop", refusal=None):
    return {
        "id": "synthetic-chat",
        "object": "chat.completion",
        "created": 0,
        "model": "gpt-4o-mini",
        "choices": [
            {
                "index": 0,
                "finish_reason": finish,
                "message": {"role": "assistant", "content": text, "refusal": refusal},
            }
        ],
        "usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120},
    }


def response(text='{"value":60}', *, status="completed", reason=None, refusal=None):
    part = (
        {"type": "refusal", "refusal": refusal}
        if refusal
        else {
            "type": "output_text",
            "text": text,
            "annotations": [],
        }
    )
    return {
        "id": "synthetic-response",
        "object": "response",
        "created_at": 0,
        "model": "gpt-5",
        "status": status,
        "incomplete_details": {"reason": reason} if reason else None,
        "output": [
            {
                "id": "msg-synthetic",
                "type": "message",
                "role": "assistant",
                "status": "completed",
                "content": [part],
            }
        ],
        "usage": {
            "input_tokens": 100,
            "output_tokens": 30,
            "total_tokens": 130,
            "output_tokens_details": {"reasoning_tokens": 10},
        },
    }


def claim_result(
    answer="The declared capacity is 60 kWh [e1].",
    *,
    supported=True,
    quote="The battery pack has a declared capacity of 60 kWh.",
    evidence_id="e1",
):
    return {
        "coverage_complete": True,
        "claims": [
            {
                "text": answer,
                "source_text": answer,
                "supported": supported,
                "support": [{"evidence_id": evidence_id, "quote": quote}],
            }
        ],
    }


@dataclass
class ScriptedTransport:
    responses: list[dict[str, Any]]
    requests: list[Request] = field(default_factory=list)

    def send(self, request: Request) -> TransportResult:
        self.requests.append(request)
        if not self.responses:
            raise AssertionError("Unexpected provider call")
        return TransportResult(self.responses.pop(0))


@pytest.fixture
def sdk_provider():
    clients = []

    def factory(payload, status=200):
        requests = []

        def handler(request):
            requests.append((request.url.path, json.loads(request.content)))
            return httpx.Response(status, json=payload)

        client = OpenAI(
            api_key="synthetic-key",
            http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        )
        clients.append(client)
        return OpenAIProvider(OpenAITransport(client=client)), requests

    yield factory
    for client in clients:
        client.close()

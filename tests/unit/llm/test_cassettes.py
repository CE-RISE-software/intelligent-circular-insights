import json
import os
from dataclasses import replace

import pytest
from tests.unit.llm.conftest import ScriptedTransport, chat

from ici_core.domain.evidence import ContextPack
from ici_llm.cassettes import CassetteTransport, redact
from ici_llm.errors import CassetteCorrupt, CassetteMiss, Truncated
from ici_llm.provider import CassetteProvider, OpenAIProvider
from ici_llm.transport import Request

pytestmark = pytest.mark.cassette


def test_record_then_replay_with_no_key_and_no_live_transport(tmp_path, evidence_items):
    pack = ContextPack(tuple(evidence_items))
    transport = ScriptedTransport([chat()])
    record = CassetteProvider(tmp_path, mode="record", provider=OpenAIProvider(transport))
    answer = record.compose("Capacity?", pack)
    assert record.compose("Capacity?", pack) == answer  # record-once even in record mode
    assert len(transport.requests) == 1
    assert "OPENAI_API_KEY" not in os.environ
    replay = CassetteProvider(tmp_path)
    assert replay.compose("Capacity?", pack) == answer
    assert replay.audit.cost.llm_calls == 0
    assert replay.audit.cost.usd == 0
    with pytest.raises(CassetteMiss):
        replay.compose("A drifted question", pack)
    changed = ContextPack((replace(evidence_items[0], text="Different facts"),))
    with pytest.raises(CassetteMiss):
        replay.compose("Capacity?", changed)


def test_request_identity_includes_every_effective_option():
    base = Request(
        "chat",
        {"model": "a", "schema": {"type": "object"}, "messages": [], "max_completion_tokens": 5},
        "p@1",
        "hash",
    )
    variants = [
        replace(base, endpoint="responses"),
        replace(base, prompt_hash="different"),
        replace(base, prompt_id="p@2"),
    ]
    for key, value in [
        ("model", "b"),
        ("schema", {}),
        ("messages", ["new"]),
        ("max_completion_tokens", 6),
    ]:
        variants.append(replace(base, kwargs={**base.kwargs, key: value}))
    assert all(x.key != base.key for x in variants)
    assert replace(base, kwargs=dict(reversed(list(base.kwargs.items())))).key == base.key


def test_corrupt_record_fails_even_in_record_mode(tmp_path):
    request = Request("chat", {"model": "a"})
    path = tmp_path / f"{request.key}.json"
    path.write_text('{"wrong": {}}')
    transport = CassetteTransport(tmp_path, mode="record", live=ScriptedTransport([]))
    with pytest.raises(CassetteCorrupt):
        transport.send(request)
    assert path.read_text() == '{"wrong": {}}'


def test_truncated_response_is_replayed_as_a_failure(tmp_path):
    record = CassetteProvider(
        tmp_path,
        mode="record",
        provider=OpenAIProvider(ScriptedTransport([chat("Partial", finish="length")])),
    )
    for provider in [record, CassetteProvider(tmp_path)]:
        with pytest.raises(Truncated):
            provider.compose("q", ContextPack())


def test_credentials_are_redacted_before_persistence(tmp_path):
    payload = chat("Contains sk-example-secret and exact-secret")
    payload["authorization"] = "Bearer another-secret"
    record = CassetteProvider(
        tmp_path,
        mode="record",
        secrets=("exact-secret",),
        provider=OpenAIProvider(ScriptedTransport([payload])),
    )
    record.compose("Do not persist this request text", ContextPack())
    saved = next(tmp_path.glob("*.json")).read_text()
    assert "sk-example-secret" not in saved
    assert "exact-secret" not in saved
    assert "another-secret" not in saved
    assert "Do not persist this request text" not in saved
    assert json.loads(saved)
    assert redact({"api-key": "secret"}) == {"api-key": "[REDACTED]"}


def test_invalid_mode_cannot_silently_go_live(tmp_path):
    with pytest.raises(ValueError):
        CassetteProvider(tmp_path, mode="typo")

import os
import socket

import pytest
from tests.unit.llm.conftest import ScriptedTransport, chat

from ici_core.domain.evidence import ContextPack
from ici_llm.budget import RequestBudget
from ici_llm.errors import BudgetExceeded
from ici_llm.prompts import PromptRegistry
from ici_llm.provider import OpenAIProvider


def test_call_ceiling_prevents_transport_invocation():
    transport = ScriptedTransport([chat()])
    provider = OpenAIProvider(transport, budget=RequestBudget(max_calls=1))
    provider.compose("q", ContextPack())
    with pytest.raises(BudgetExceeded):
        provider.compose("q", ContextPack())
    assert len(transport.requests) == 1


def test_token_ceiling_is_checked_before_a_call():
    transport = ScriptedTransport([])
    provider = OpenAIProvider(transport, budget=RequestBudget(max_reserved_tokens=1))
    with pytest.raises(BudgetExceeded):
        provider.compose("q", ContextPack())
    assert transport.requests == []


def test_prompts_are_versioned_and_hash_rendered_variables():
    registry = PromptRegistry()
    for name in ["compose", "structured"]:
        assert registry.render(name).id.endswith("@1")
    first = registry.render("grounding", answer="one")
    assert first.hash == registry.render("grounding", answer="one").hash
    assert first.hash != registry.render("grounding", answer="two").hash
    with pytest.raises(ValueError):
        registry.render("grounding")


def test_offline_suite_has_no_api_key_or_network():
    assert "OPENAI_API_KEY" not in os.environ
    with pytest.raises(RuntimeError, match="Network access is disabled"):
        socket.create_connection(("example.invalid", 443))
    with socket.socket() as connection, pytest.raises(RuntimeError, match="Network access"):
        connection.connect(("127.0.0.1", 1))

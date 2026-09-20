import json
from pathlib import Path

import pytest
from tests.unit.llm.conftest import ScriptedTransport, chat, claim_result, response

from ici_core.domain.confidence import OperatingPoint
from ici_core.domain.envelope import Decision
from ici_llm.provider import CassetteProvider, OpenAIProvider
from ici_llm.runtime import LLMRuntime


@pytest.mark.parametrize("model", ["gpt-4o-mini", "gpt-5"])
def test_selected_model_prompt_hashes_usage_and_guards_reach_envelope(bundle, query, model):
    decomposition = json.dumps(claim_result())
    transport = ScriptedTransport(
        [chat(), response(decomposition) if model == "gpt-5" else chat(decomposition)]
    )
    runtime = LLMRuntime(OpenAIProvider(transport))
    envelope = runtime.answer_question(bundle, query, model=model)
    assert envelope.decision is Decision.ANSWER
    assert {r.kwargs["model"] for r in transport.requests} == {model}
    assert envelope.trace.model == model
    assert len(envelope.trace.prompt_hashes) == 3
    assert envelope.trace.cost.llm_calls == 2
    assert envelope.trace.cost.usd > 0
    assert "guard" in envelope.trace.step_names()
    assert "ici.grounding@2" in str(envelope.trace.steps)


def test_refusal_is_an_explained_abstention(bundle, query):
    runtime = LLMRuntime(OpenAIProvider(ScriptedTransport([chat(refusal="declined")])))
    envelope = runtime.answer_question(bundle, query, point=OperatingPoint(tau=0.85))
    assert envelope.decision is Decision.ABSTAIN
    assert "declined" in envelope.abstain_reason
    assert envelope.operating_point.tau == 0.85
    assert envelope.trace.cost.llm_calls == 1


def test_unsupported_claim_abstains_and_preserves_operating_point(bundle, query):
    answer = "The declared capacity is 600 kWh [e1]."
    transport = ScriptedTransport([chat(answer), chat(json.dumps(claim_result(answer)))])
    envelope = LLMRuntime(OpenAIProvider(transport)).answer_question(
        bundle, query, point=OperatingPoint(tau=0.8)
    )
    assert envelope.decision is Decision.ABSTAIN
    assert envelope.answer is None
    assert "600" in envelope.abstain_reason
    assert envelope.operating_point.tau == 0.8


def test_sessions_do_not_share_model_audit_or_budget():
    runtime = LLMRuntime(OpenAIProvider(ScriptedTransport([])))
    first, second = runtime.request(model="gpt-5"), runtime.request()
    first.audit.guard("first-only", True)
    first.provider.budget.calls = 6
    assert second.provider.router.default == "gpt-4o-mini"
    assert first.provider.router.default == "gpt-5"
    assert second.audit.steps == []
    assert second.provider.budget.calls == 0


def test_record_assistance_shares_the_request_audit_and_provider():
    request = LLMRuntime(OpenAIProvider(ScriptedTransport([]))).request()
    assert request.records.provider is request.provider
    assert request.records.audit is request.audit


@pytest.mark.cassette
def test_full_answer_records_and_replays_both_calls_without_spend(tmp_path, bundle, query):
    transport = ScriptedTransport([chat(), chat(json.dumps(claim_result()))])
    record = LLMRuntime(
        CassetteProvider(tmp_path, mode="record", provider=OpenAIProvider(transport))
    )
    first = record.answer_question(bundle, query)
    replay = LLMRuntime(CassetteProvider(tmp_path))
    second = replay.answer_question(bundle, query)
    assert first.answer == second.answer
    assert first.grounding == second.grounding
    assert first.trace.prompt_hashes == second.trace.prompt_hashes
    assert second.trace.cost.usd == second.trace.cost.llm_calls == 0
    assert second.trace.cost.prompt_tokens == first.trace.cost.prompt_tokens
    assert len(transport.requests) == 2


@pytest.mark.cassette
def test_committed_synthetic_fixture_replays_end_to_end(bundle, query):
    directory = Path(__file__).resolve().parents[2] / "cassettes" / "synthetic"
    runtime = LLMRuntime(CassetteProvider(directory))
    result = runtime.answer_question(bundle, query)
    assert result.decision is Decision.ANSWER
    assert result.answer == "The declared capacity is 60 kWh [e1]."
    assert result.trace.cost.llm_calls == result.trace.cost.usd == 0

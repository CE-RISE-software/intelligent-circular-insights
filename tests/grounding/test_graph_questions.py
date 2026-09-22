"""CE-RISE may not fill a substrate gap with a plausible model-training claim.

These test the composition/grounding boundary, not the deferred X8 query planner.
"""

import json
from dataclasses import replace

import pytest
from tests.unit.llm.conftest import ScriptedTransport, chat, claim_result

from ici_core.domain.envelope import Decision
from ici_core.domain.modes import BackendMode
from ici_llm.provider import OpenAIProvider
from ici_llm.runtime import LLMRuntime


@pytest.fixture
def mode():
    return BackendMode.CE_RISE


@pytest.mark.parametrize(
    "question,answer",
    [
        ("Who audited this battery?", "The battery was audited by Example Auditor [e1]."),
        ("What is its warranty?", "The battery probably has a 10-year warranty [e1]."),
        ("What is its measured footprint?", "Its measured footprint is 42 kg CO2e [e1]."),
    ],
)
def test_a_claim_absent_from_the_substrate_abstains_even_with_a_real_citation(
    bundle, query, question, answer
):
    transport = ScriptedTransport(
        [chat(answer), chat(json.dumps(claim_result(answer, supported=False)))]
    )
    result = LLMRuntime(OpenAIProvider(transport)).answer_question(
        bundle, replace(query, text=question)
    )
    assert result.decision is Decision.ABSTAIN
    assert result.answer is None
    assert result.grounding.blocks_answering
    assert transport.requests[0].prompt_id == "ici.compose.ce_rise@2"

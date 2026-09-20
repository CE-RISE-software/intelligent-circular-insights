import copy
import json

import pytest
from tests.unit.llm.conftest import ScriptedTransport, chat, claim_result

from ici_core.domain.claims import GroundingVerdict
from ici_core.domain.evidence import ContextPack
from ici_core.ports import GroundingVerifier as GroundingPort
from ici_llm.errors import CassetteMiss
from ici_llm.grounding import GroundingVerifier
from ici_llm.provider import CassetteProvider, OpenAIProvider

ANSWER = "The declared capacity is 60 kWh [e1]."


def scenario(name):
    answer = ANSWER
    data = claim_result()
    if name == "paraphrase":
        answer = "The battery stores a declared 60 kWh [e1]."
        data = claim_result(answer)
    elif name == "fabricated_claim":
        answer = "It has a ten-year warranty [e1]."
        data = claim_result(answer, supported=False)
    elif name == "wrong_number":
        answer = "The declared capacity is 600 kWh [e1]."
        data = claim_result(answer)  # Even a mistaken positive model verdict must fail.
    elif name == "unknown_citation":
        answer = "The declared capacity is 60 kWh [missing]."
    elif name == "no_citation":
        answer = "The declared capacity is 60 kWh."
    elif name == "fabricated_quote":
        data["claims"][0]["support"][0]["quote"] = "A quote that never appeared."
    elif name == "uncited_support":
        data["claims"][0]["support"] = [{"evidence_id": "e2", "quote": "Chemistry is NMC811."}]
    elif name == "missing_support":
        data["claims"][0]["support"] = []
    elif name == "empty_claims":
        data["claims"] = []
    elif name == "omitted_sentence":
        answer += " It is fireproof [e1]."
    elif name == "incomplete_coverage":
        data["coverage_complete"] = False
    elif name == "empty_answer":
        answer = ""
    elif name == "qualifier_lost":
        answer = "The actual measured capacity is 60 kWh [e1]."
        data = claim_result(answer, supported=False)
    elif name == "wrong_unit":
        answer = "The declared capacity is 60 kW [e1]."
        data = claim_result(answer, supported=False)
    return answer, data


@pytest.mark.parametrize(
    "name",
    [
        "grounded",
        "paraphrase",
        "fabricated_claim",
        "wrong_number",
        "unknown_citation",
        "no_citation",
        "fabricated_quote",
        "uncited_support",
        "missing_support",
        "empty_claims",
        "omitted_sentence",
        "incomplete_coverage",
        "empty_answer",
        "qualifier_lost",
        "wrong_unit",
    ],
)
def test_grounding_cases(name, evidence_items):
    answer, data = scenario(name)
    provider = OpenAIProvider(ScriptedTransport([chat(json.dumps(data))]))
    verifier = GroundingVerifier(provider)
    assert isinstance(verifier, GroundingPort)
    report = verifier.verify(answer, ContextPack(tuple(evidence_items)))
    expected = (
        GroundingVerdict.FULLY_GROUNDED
        if name in {"grounded", "paraphrase"}
        else GroundingVerdict.UNRESOLVED_CLAIMS
    )
    assert report.verdict is expected
    assert bool(report.unresolved) == report.blocks_answering


def test_one_fabrication_among_several_claims_blocks(evidence_items):
    data = claim_result()
    extra = claim_result("It is fireproof [e1].", supported=False)["claims"][0]
    data["claims"].append(extra)
    verifier = GroundingVerifier(OpenAIProvider(ScriptedTransport([chat(json.dumps(data))])))
    report = verifier.verify(ANSWER + " " + extra["text"], ContextPack(tuple(evidence_items)))
    assert report.claims_total == 2
    assert report.claims_resolved == 1
    assert report.unresolved[0].text == extra["text"]


def test_verifier_refusal_blocks_answering(evidence_items):
    provider = OpenAIProvider(ScriptedTransport([chat(refusal="declined")]))
    report = GroundingVerifier(provider).verify(ANSWER, ContextPack(tuple(evidence_items)))
    assert report.blocks_answering
    assert report.unresolved[0].id == "decomposition_failed"


def test_cassette_miss_remains_a_test_failure(tmp_path, evidence_items):
    verifier = GroundingVerifier(CassetteProvider(tmp_path))
    with pytest.raises(CassetteMiss):
        verifier.verify(ANSWER, ContextPack(tuple(evidence_items)))


def test_claim_decomposition_does_not_mutate_evidence(evidence_items):
    before = copy.deepcopy(evidence_items)
    verifier = GroundingVerifier(
        OpenAIProvider(ScriptedTransport([chat(json.dumps(claim_result()))]))
    )
    verifier.verify(ANSWER, ContextPack(tuple(evidence_items)))
    assert evidence_items == before

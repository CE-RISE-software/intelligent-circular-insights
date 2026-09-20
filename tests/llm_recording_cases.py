"""The finite Sprint 1 recording set. Inputs contain no private user documents."""

import copy
import hashlib
from dataclasses import asdict

from tests.llm_scenarios import (
    DEMO_RECORD,
    SEARCH_QUESTIONS,
    broken_records,
    record_pack,
    search_pack,
)

from ici_core.domain.evidence import ContextPack
from ici_llm.composition import GroundedComposer, GroundedPrompt
from ici_llm.errors import Refused
from ici_llm.grounding import GroundingVerifier
from ici_llm.prompts import canonical
from ici_llm.records import RecordComposer

GROUNDING_ANSWERS = {
    "paraphrase": "The pack's stated capacity is 60 kWh [e1].",
    "fabricated": "The pack has a declared capacity of 60 kWh and a 10-year warranty [e1].",
}
CASE_NAMES = (
    *(f"search:{name}" for name in SEARCH_QUESTIONS),
    *(f"grounding:{name}" for name in GROUNDING_ANSWERS),
    "repair:grounded",
    *(f"repair:{name}" for name in broken_records()),
    "synthesis:grounded",
    "compat:gpt5",
    "embeddings:openai",
)


def run_case(name, provider):
    kind, label = name.split(":", 1)
    audit = provider.audit
    if kind == "search":
        try:
            candidate = (
                GroundedComposer(provider, audit)
                .compose(GroundedPrompt(SEARCH_QUESTIONS[label], search_pack()))
                .answer
            )
        except Refused:
            return {"decision": "abstain", "answer": None}
        report = GroundingVerifier(provider, audit=audit).verify(candidate, search_pack())
        return {
            "decision": "abstain" if report.blocks_answering else "answer",
            "answer": None if report.blocks_answering else candidate,
            "grounding": asdict(report),
        }
    if kind == "grounding":
        return asdict(
            GroundingVerifier(provider, audit=audit).verify(GROUNDING_ANSWERS[label], search_pack())
        )
    service = RecordComposer(provider, audit=audit)
    if kind == "repair":
        if label == "grounded":
            seed = copy.deepcopy(DEMO_RECORD)
            del seed["compliance"]
            return asdict(service.repair(seed, record_pack()))
        return asdict(service.repair(broken_records()[label], ContextPack()))
    if kind == "synthesis":
        return asdict(service.synthesize({"product": DEMO_RECORD["product"]}, record_pack()))
    if kind == "compat":
        return dict(
            provider.structured(
                SEARCH_QUESTIONS["capacity"],
                search_pack(),
                {
                    "type": "object",
                    "required": ["capacity_kwh"],
                    "additionalProperties": False,
                    "properties": {"capacity_kwh": {"type": "number", "const": 60}},
                },
                model="gpt-5",
            )
        )
    if kind == "embeddings":
        values = provider.embed(
            ["Declared capacity: 60 kWh.", "Estimated recyclability: 85 percent."]
        )
        return {
            "count": len(values),
            "dimensions": len(values[0]),
            "hash": hashlib.sha256(canonical(values).encode()).hexdigest(),
        }
    raise ValueError("unknown recording case")

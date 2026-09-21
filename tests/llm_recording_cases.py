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
    # Sprint 3.1: the same two operations through the *route's* code path rather
    # than a fixture pack. The composer cases above cannot cover the routes,
    # because the routes build their context from live retrieval and so hash
    # differently — which is exactly why the endpoints had no replayable cassette
    # when they shipped.
    "route-repair:battery",
    "route-synthesis:battery",
    "compat:gpt5",
    "embeddings:openai",
)

# Fixed, so the pack and therefore the request hash are identical at record time
# and replay time. A varying correlation id would scope memory recall differently
# and silently change the prompt.
ROUTE_CORRELATION = "recording"
ROUTE_SEED = {
    "dpp_id": "synthetic-demo-dpp-001",
    "product": {"brand": "Generic", "model": "BEV pack 60 kWh", "category": "battery"},
}


def _route_use_case(provider):
    """``SynthesizeRecord`` wired exactly as the routes wire it.

    The bundle supplies retrieval and the schema registry; only the composer is
    swapped for the recording provider. Reusing the real use case rather than
    re-deriving the pack here is the point: a hand-rolled approximation would
    record a hash the route never produces, which is the failure this case exists
    to prevent.
    """
    from apps.api.bundles import _build_normal
    from apps.api.settings import Settings

    from ici_core.usecases.synthesize_record import SynthesizeRecord

    bundle = _build_normal(Settings(llm_cassette_mode="replay"))
    return SynthesizeRecord(bundle, RecordComposer(provider, audit=provider.audit))


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
    if kind == "route-repair":
        from ici_core.domain.ids import CorrelationId, ProfileId

        result = _route_use_case(provider).repair(
            ROUTE_SEED,
            ProfileId("eu-dpp"),
            correlation_id=CorrelationId(ROUTE_CORRELATION),
        )
        return asdict(result)
    if kind == "route-synthesis":
        from ici_core.domain.ids import CorrelationId, ProfileId

        record = _route_use_case(provider)(
            ROUTE_SEED,
            ProfileId("eu-dpp"),
            correlation_id=CorrelationId(ROUTE_CORRELATION),
        )
        return {"dpp_id": str(record.dpp_id), "record": dict(record.payload)}
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

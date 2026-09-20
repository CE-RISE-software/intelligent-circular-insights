"""The Normal bundle, built exactly as the application builds it.

Unit tests prove each adapter in isolation; this proves the composition root wires
them into something that satisfies every port and answers a real question.
"""

from __future__ import annotations

import pytest
from apps.api.bundles import build_registry
from apps.api.settings import Settings

from ici_core.domain.facts import Fact, ValidationOutcome
from ici_core.domain.ids import ProductId
from ici_core.domain.impact import ImpactRequest, SubjectRef
from ici_core.domain.modes import BackendMode
from ici_core.domain.query import ProductScope, Query, RetrievalBudget
from ici_core.domain.rules import FactGraph, Triple
from ici_core.usecases.deps import ProviderBundle

PORTS = (
    "evidence",
    "memory",
    "substrates",
    "symbolic",
    "schemas",
    "impact",
    "records",
    "signals",
    "calibrator",
    "selective",
    "data_trust",
    "grounding",
    "llm",
    "ledger",
    "policy",
)


@pytest.fixture(scope="module")
def bundle() -> ProviderBundle:
    registry = build_registry((BackendMode.NORMAL,), Settings())
    return registry.for_mode(BackendMode.NORMAL)


def test_every_port_is_bound_to_something_real(bundle) -> None:
    for name in PORTS:
        adapter = getattr(bundle, name)
        assert adapter is not None, f"{name} is unbound"
        assert not type(adapter).__name__.startswith("Fake"), f"{name} is a test double"


def test_the_bundle_knows_its_own_mode(bundle) -> None:
    assert bundle.mode is BackendMode.NORMAL


def test_retrieval_returns_referenced_evidence(bundle) -> None:
    got = bundle.evidence.retrieve(Query(text="battery capacity"), RetrievalBudget())
    assert got and all(e.ref for e in got)


def test_memory_and_retrieval_compose_without_leaking(bundle) -> None:
    bundle.memory.commit(
        Fact(
            subject="battery",
            predicate="capacity",
            value="60 kWh",
            product_id=ProductId("integration-A"),
            provenance_ref="doc:1",
        ),
        ValidationOutcome.VALIDATED,
    )
    mine = bundle.memory.recall(
        ProductScope(product_id=ProductId("integration-A")), Query(text="capacity")
    )
    theirs = bundle.memory.recall(
        ProductScope(product_id=ProductId("integration-B")), Query(text="capacity")
    )
    assert [f.value for f in mine] == ["60 kWh"]
    assert list(theirs) == []


def test_symbolic_derives_over_the_real_ontology(bundle) -> None:
    graph = FactGraph((Triple("ProductA", "hasComponent", "Battery1"),))
    result = bundle.symbolic.entail(graph)
    assert result.fired
    assert result.traces and all(t.rule_id for t in result.traces)


def test_impact_reproduces_the_oracle_through_the_bundle(bundle) -> None:
    result = bundle.impact.assess(SubjectRef(id="apple_iphone15_pro_128gb"), ImpactRequest())
    assert round(result.total, 6) == 64.852055


def test_signals_calibration_and_decision_chain_together(bundle) -> None:
    from ici_core.domain.confidence import Confidence, OperatingPoint

    query = Query(text="battery capacity")
    pack_items = tuple(bundle.evidence.retrieve(query, RetrievalBudget()))
    from ici_core.domain.evidence import ContextPack

    signals = bundle.signals.emit(query, ContextPack(pack_items), None)
    raw = sum(signals.values.values()) / len(signals.values)
    calibrated = bundle.calibrator.calibrate(signals, raw)
    decision = bundle.selective.decide(
        Confidence(signals=signals, raw=raw, calibrated=calibrated),
        OperatingPoint(tau=0.5),
    )
    assert 0.0 <= calibrated <= 1.0
    assert decision.value in ("answer", "abstain")


def test_the_data_trust_seat_is_declared_empty(bundle) -> None:
    assert bundle.data_trust.is_null is True


def test_ce_rise_mode_is_absent_and_says_so(bundle) -> None:
    from ici_core.domain.errors import CapabilityError

    registry = build_registry((BackendMode.NORMAL, BackendMode.CE_RISE), Settings())
    assert BackendMode.CE_RISE not in registry.available()
    with pytest.raises(CapabilityError, match="not enabled"):
        registry.for_mode(BackendMode.CE_RISE)

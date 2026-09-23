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


# The three ports that carry data. Switching mode is meant to change what the
# features run *over*, so these are exactly the ports that may differ.
DATA_PORTS = frozenset({"substrates", "impact", "schemas"})

# Everything that decides whether an answer may be returned at all. A difference
# here would mean the two modes have different reliability semantics, which is the
# one thing the two-backend design must never let drift.
RELIABILITY_PORTS = frozenset(PORTS) - DATA_PORTS - {"ledger"}


def test_both_modes_build_and_differ_only_where_they_should(bundle) -> None:
    """Two modes, one product.

    An earlier version of this test asserted that the modes differed in exactly one
    port — and so *encoded* the bug it was meant to catch. CE-RISE mode had been made
    purely additive after a naive engine swap broke Carbon, which fixed the breakage
    by deleting the difference; every gate then passed while switching backends
    changed nothing any feature did. The contract is not "differ in as few places as
    possible". It is: differ in the data, never in the reliability path.
    """
    registry = build_registry((BackendMode.NORMAL, BackendMode.CE_RISE), Settings())
    assert set(registry.available()) == {BackendMode.NORMAL, BackendMode.CE_RISE}

    normal = registry.for_mode(BackendMode.NORMAL)
    ce_rise = registry.for_mode(BackendMode.CE_RISE)

    differing = {
        name for name in PORTS if type(getattr(normal, name)) is not type(getattr(ce_rise, name))
    }
    assert differing == DATA_PORTS, (
        f"modes differ in {sorted(differing)}, expected {sorted(DATA_PORTS)}.\n"
        f"Missing means the switch does not reach a feature; extra means the two\n"
        f"backends are drifting into two products."
    )
    assert not differing & RELIABILITY_PORTS

    # Shared by identity, not merely by type: the same calibrator and the same
    # selective policy, so a confidence figure means the same thing in both modes.
    for name in ("calibrator", "selective", "signals", "grounding", "llm"):
        assert getattr(normal, name) is getattr(ce_rise, name), name


def test_an_unbuilt_mode_is_a_typed_capability_error(bundle) -> None:
    from ici_core.domain.errors import CapabilityError

    registry = build_registry((BackendMode.NORMAL,), Settings())
    with pytest.raises(CapabilityError, match="not enabled"):
        registry.for_mode(BackendMode.CE_RISE)

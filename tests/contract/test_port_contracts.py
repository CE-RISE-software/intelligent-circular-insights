"""One suite per port, run against every implementation.

This is what stops the two modes becoming two products. When a CE-RISE adapter
cannot satisfy a clause, the correct answer is an explicit ``CapabilityError`` in
that port's declared capability set — never a silent difference in behaviour.

In Sprint 0 these run against the fakes, which proves the suites are wired and the
assertions are the right ones. Sprints 1 and 2 point the same suites at the real
adapters; nothing here changes.
"""

from __future__ import annotations

import contextlib

import pytest

from ici_core.domain.facts import Fact, ValidationOutcome
from ici_core.domain.ids import ProductId
from ici_core.domain.impact import ImpactRequest, SubjectRef
from ici_core.domain.query import ProductScope, Query, RetrievalBudget
from ici_core.domain.rules import FactGraph
from ici_core.usecases.deps import ProviderBundle

pytestmark = pytest.mark.contract


class TestEvidenceProviderContract:
    def test_returns_empty_not_none_when_nothing_matches(self, bundle: ProviderBundle) -> None:
        provider = type(bundle.evidence)()  # an empty instance of the same adapter
        got = provider.retrieve(Query(text="nothing matches this"), RetrievalBudget())
        assert got is not None
        assert list(got) == []

    def test_every_evidence_carries_a_resolvable_ref(
        self, bundle: ProviderBundle, query: Query
    ) -> None:
        for item in bundle.evidence.retrieve(query, RetrievalBudget()):
            assert item.ref, f"evidence {item.id} has no ref a reader could follow"

    def test_respects_the_retrieval_budget(self, bundle: ProviderBundle, query: Query) -> None:
        got = bundle.evidence.retrieve(query, RetrievalBudget(top_k_documents=1))
        assert len(list(got)) <= 1

    def test_is_deterministic_for_the_same_query(
        self, bundle: ProviderBundle, query: Query
    ) -> None:
        a = [e.id for e in bundle.evidence.retrieve(query, RetrievalBudget())]
        b = [e.id for e in bundle.evidence.retrieve(query, RetrievalBudget())]
        assert a == b


class TestFactMemoryContract:
    """The four properties §4.2 of the paper lists as missing from the prototype."""

    def test_recall_never_crosses_product_scope(self, bundle: ProviderBundle) -> None:
        # The single most important test in this file. In a compliance tool,
        # returning another product's facts is the worst thing this system can do,
        # and it fails silently.
        fact_a = Fact(
            subject="battery",
            predicate="capacity",
            value="60 kWh",
            product_id=ProductId("product-A"),
            provenance_ref="doc:a#1",
        )
        bundle.memory.commit(fact_a, ValidationOutcome.VALIDATED)

        leaked = bundle.memory.recall(
            ProductScope(product_id=ProductId("product-B")),
            Query(text="what is the capacity"),
        )
        assert list(leaked) == []

    def test_an_unvalidated_fact_cannot_be_stored(self, bundle: ProviderBundle) -> None:
        """Rejecting is the contract; *how* it rejects is the adapter's business.

        Asserting on an exception type would over-constrain implementations, so the
        assertion is on the observable outcome: the fact is not there afterwards.
        """
        scope = ProductScope(product_id=ProductId("p-unvalidated"))
        fact = Fact(
            subject="battery",
            predicate="capacity",
            value="60 kWh",
            product_id=ProductId("p-unvalidated"),
            provenance_ref="doc:a#1",
        )
        with contextlib.suppress(Exception):  # raising is one valid way to refuse
            bundle.memory.commit(fact, ValidationOutcome.REJECTED)
        stored = bundle.memory.recall(scope, Query(text="what is the capacity"))
        assert list(stored) == [], "an unvalidated fact must not be retrievable"

    def test_supersede_appends_and_does_not_mutate(self, bundle: ProviderBundle) -> None:
        scope = ProductScope(product_id=ProductId("p1"))
        first = Fact(
            subject="battery",
            predicate="capacity",
            value="60 kWh",
            product_id=ProductId("p1"),
            provenance_ref="doc:a#1",
        )
        old_id = bundle.memory.commit(first, ValidationOutcome.VALIDATED)

        corrected = Fact(
            subject="battery",
            predicate="capacity",
            value="62 kWh",
            product_id=ProductId("p1"),
            provenance_ref="doc:b#2",
        )
        bundle.memory.supersede(old_id, corrected, reason="datasheet revision B")

        history = list(bundle.memory.history("battery", scope))
        assert len(history) == 2, "the superseded version must remain readable"
        assert any(v.is_correction for v in history)

    def test_history_carries_the_reason(self, bundle: ProviderBundle) -> None:
        scope = ProductScope(product_id=ProductId("p1"))
        f = Fact(
            subject="battery",
            predicate="capacity",
            value="60 kWh",
            product_id=ProductId("p1"),
            provenance_ref="doc:a#1",
        )
        old = bundle.memory.commit(f, ValidationOutcome.VALIDATED)
        bundle.memory.supersede(
            old,
            Fact(
                subject="battery",
                predicate="capacity",
                value="62 kWh",
                product_id=ProductId("p1"),
                provenance_ref="doc:b#2",
            ),
            reason="datasheet revision B",
        )
        corrections = [v for v in bundle.memory.history("battery", scope) if v.is_correction]
        assert corrections and corrections[0].reason == "datasheet revision B"


class TestSubstrateRegistryContract:
    def test_facts_for_returns_a_graph_not_none(self, bundle: ProviderBundle) -> None:
        graph = bundle.substrates.facts_for(SubjectRef(id="p1"))
        assert isinstance(graph, FactGraph)

    def test_coverage_report_is_available(self, bundle: ProviderBundle) -> None:
        # ADR 0005: mounting knowledge is only defensible if its reach is measurable.
        assert bundle.substrates.coverage_report() is not None


class TestSymbolicValidatorContract:
    def test_entailment_reports_whether_it_fired(self, bundle: ProviderBundle) -> None:
        result = bundle.symbolic.entail(FactGraph())
        assert isinstance(result.fired, bool)

    def test_entailment_on_an_empty_graph_derives_nothing(self, bundle: ProviderBundle) -> None:
        assert bundle.symbolic.entail(FactGraph()).derived == ()


class TestSchemaRegistryContract:
    def test_profiles_are_enumerable(self, bundle: ProviderBundle) -> None:
        assert list(bundle.schemas.profiles())

    def test_conformance_is_typed_not_boolean(self, bundle: ProviderBundle) -> None:
        from ici_core.domain.ids import DppId
        from ici_core.domain.record import DPPRecord

        report = bundle.schemas.conform(
            DPPRecord(dpp_id=DppId("d1")), bundle.schemas.profiles()[0].id
        )
        assert hasattr(report, "violations"), "a bare bool is useless for repair"
        assert hasattr(report, "conforms")


class TestImpactEngineContract:
    def test_result_carries_a_unit(self, bundle: ProviderBundle) -> None:
        result = bundle.impact.assess(SubjectRef(id="p1"), ImpactRequest())
        assert result.unit, "a number without a unit is not an answer"

    def test_explain_returns_provenance_for_a_target(self, bundle: ProviderBundle) -> None:
        result = bundle.impact.assess(SubjectRef(id="p1"), ImpactRequest())
        assert bundle.impact.explain(result, "total").target == "total"


class TestCalibratorContract:
    def test_output_is_always_a_probability(self, bundle: ProviderBundle) -> None:
        from ici_core.domain.confidence import SignalVector

        for raw in (-5.0, 0.0, 0.5, 1.0, 5.0):
            got = bundle.calibrator.calibrate(SignalVector(), raw)
            assert 0.0 <= got <= 1.0, f"calibrate({raw}) returned {got}"

    def test_has_an_id_so_a_response_can_name_it(self, bundle: ProviderBundle) -> None:
        assert bundle.calibrator.id


class TestSelectivePolicyContract:
    def test_answers_at_or_above_tau_and_abstains_below(self, bundle: ProviderBundle) -> None:
        from ici_core.domain.confidence import Confidence, OperatingPoint
        from ici_core.domain.envelope import Decision

        point = OperatingPoint(tau=0.5)
        assert bundle.selective.decide(Confidence(calibrated=0.5), point) is Decision.ANSWER
        assert bundle.selective.decide(Confidence(calibrated=0.49), point) is Decision.ABSTAIN


class TestDataTrustContract:
    def test_the_shipped_implementation_declares_itself_null(self, bundle: ProviderBundle) -> None:
        # ADR: the seat exists, the occupant does not. The UI reads this to hide
        # a panel rather than showing an empty one.
        assert bundle.data_trust.is_null is True

    def test_a_null_provider_says_nothing_rather_than_guessing(
        self, bundle: ProviderBundle
    ) -> None:
        from ici_core.domain.confidence import OperatingPoint

        assert bundle.data_trust.assess(SubjectRef(id="p1"), "carbon", OperatingPoint()) is None


class TestDecisionPolicyContract:
    def test_declares_its_action_set(self, bundle: ProviderBundle) -> None:
        assert list(bundle.policy.actions())

    def test_chosen_action_is_in_the_declared_set(self, bundle: ProviderBundle) -> None:
        from ici_core.domain.confidence import SignalVector

        chosen = bundle.policy.act(SignalVector(), steps_taken=0)
        assert chosen in bundle.policy.actions()

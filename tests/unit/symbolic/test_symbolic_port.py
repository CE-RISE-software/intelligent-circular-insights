"""The symbolic port reproduces the oracle, and adds attribution it did not have.

The numbers here were captured from the pre-port service
(`tests/reference/symbolic/reasoner_surface.json`) before a line of this package
was written. If a refactor moves any of them, that is a regression, not an
improvement.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from ici_core.domain.claims import Claim
from ici_core.domain.ids import ClaimId
from ici_core.domain.rules import FactGraph, Triple
from ici_symbolic import OwlRlValidator, ReasonerConfig, rules_for

REFERENCE = (
    pathlib.Path(__file__).resolve().parents[2] / "reference" / "symbolic" / "reasoner_surface.json"
)


@pytest.fixture(scope="module")
def validator() -> OwlRlValidator:
    return OwlRlValidator.for_domain("battery")


@pytest.fixture(scope="module")
def oracle() -> dict:
    return json.loads(REFERENCE.read_text())


class TestReproducesTheOracle:
    def test_triple_count_is_unchanged(self, validator, oracle) -> None:
        assert len(validator.reasoner.graph) == oracle["triple_count"] == 4322

    def test_rules_add_the_same_seven_triples(self, validator, oracle) -> None:
        assert validator.reasoner.last_outcome.added_count == oracle["derived_by_rules"] == 7

    def test_the_same_products_are_found(self, validator, oracle) -> None:
        from ici_symbolic import local_name

        found = [local_name(p) for p in validator.reasoner.list_products()]
        assert found == oracle["products"] == ["ProductA", "ProductB", "ProductC"]

    @pytest.mark.parametrize("product", ["ProductA", "ProductB", "ProductC"])
    def test_obligations_match_per_product(self, validator, oracle, product) -> None:
        from ici_symbolic import local_name

        expected = oracle["obligations"][product]
        assert (
            sorted(local_name(u) for u in validator.reasoner.requires_compliance(product))
            == expected["compliance"]
        )
        assert (
            sorted(local_name(u) for u in validator.reasoner.requires_steps(product))
            == expected["steps"]
        )


class TestAttribution:
    """What the original could not do: say which rule produced which triple."""

    def test_every_added_triple_is_attributed_to_a_rule(self, validator) -> None:
        outcome = validator.reasoner.last_outcome
        attributed = sum(len(f.added) for f in outcome.firings)
        assert attributed == outcome.added_count == 7

    def test_rules_fired_names_only_rules_that_added_something(self, validator) -> None:
        outcome = validator.reasoner.last_outcome
        for firing in outcome.firings:
            assert firing.fired == (firing.rule.id in outcome.rules_fired)

    def test_every_rule_is_enumerable_and_described(self) -> None:
        # A rule set a domain expert cannot read is one nobody can review.
        for rule in rules_for("battery"):
            assert rule.id and rule.description.endswith(".")


class TestTargetedValidity:
    """The layer runs where facts exist, and says nothing where they do not."""

    def test_empty_graph_derives_nothing_and_does_not_fire(self, validator) -> None:
        result = validator.entail(FactGraph())
        assert result.derived == ()
        assert result.fired is False

    def test_unknown_subject_derives_nothing(self, validator) -> None:
        graph = FactGraph((Triple("NoSuchProduct", "hasComponent", "Widget"),))
        assert validator.entail(graph).derived == ()

    def test_known_product_derives_with_traces(self, validator) -> None:
        graph = FactGraph((Triple("ProductA", "hasComponent", "Battery1"),))
        result = validator.entail(graph)
        assert result.fired
        assert result.derived
        assert result.traces
        assert all(t.rule_id for t in result.traces)

    def test_derivation_is_narrow_not_everything_known(self, validator) -> None:
        # ProductB carries one obligation. Deriving five would mean the layer is
        # returning what it knows rather than what follows for this subject.
        graph = FactGraph((Triple("ProductB", "hasComponent", "Board2"),))
        subjects = {t.subject for t in validator.entail(graph).derived}
        assert subjects <= {"http://example.com/dpp#ProductB", "ProductB"}


class TestValidation:
    def test_no_claims_checked_when_nothing_fired(self, validator) -> None:
        report = validator.validate([Claim(id=ClaimId("c1"), text="anything")], FactGraph())
        assert report.checked == 0
        assert report.clean

    def test_claims_are_counted_when_rules_fired(self, validator) -> None:
        graph = FactGraph((Triple("ProductA", "hasComponent", "Battery1"),))
        validator.entail(graph)
        report = validator.validate([Claim(id=ClaimId("c1"), text="It meets RoHS.")], graph)
        assert report.checked == 1


class TestConfiguration:
    def test_unknown_domain_is_rejected_by_name(self) -> None:
        with pytest.raises(ValueError, match="unknown domain"):
            ReasonerConfig.for_domain("nonsense")

    def test_all_four_shipped_domains_load(self) -> None:
        for domain in ("battery", "textiles", "viessmann", "lexmark"):
            cfg = ReasonerConfig.for_domain(domain)
            assert cfg.ontology_path.is_file()
            assert cfg.namespace.endswith("#")

    def test_two_domains_coexist_in_one_process(self) -> None:
        # The original kept a module-level singleton keyed by an env var, which
        # made this impossible. Two backends in one process is the whole point.
        battery = OwlRlValidator.for_domain("battery")
        textiles = OwlRlValidator.for_domain("textiles")
        assert battery.reasoner.config.namespace != textiles.reasoner.config.namespace


class TestAblation:
    def test_disabling_a_rule_removes_exactly_its_conclusions(self, validator) -> None:
        before = len(validator.reasoner.graph)
        outcome = validator.reasoner.disable_rules(["bat_lead_implies_rohs"])
        assert "bat_lead_implies_rohs" not in outcome.rules_fired
        assert len(validator.reasoner.graph) < before
        validator.reasoner.enable_all_rules()
        assert len(validator.reasoner.graph) == before

    def test_reapplying_rules_is_idempotent(self, validator) -> None:
        # Rules are applied to a fresh copy each time. Without that, a second run
        # would keep the first run's conclusions and quietly corrupt an ablation.
        first = validator.reasoner.apply_rules().added_count
        second = validator.reasoner.apply_rules().added_count
        assert first == second == 7

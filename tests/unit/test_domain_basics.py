"""Small guarantees the rest of the system leans on."""

from __future__ import annotations

import pytest

from ici_core.domain.confidence import Confidence, OperatingPoint, SignalVector
from ici_core.domain.evidence import ContextPack, Evidence, EvidenceKind
from ici_core.domain.facts import Fact, ValidationOutcome
from ici_core.domain.ids import EvidenceId, ProductId
from ici_core.domain.modes import DEFAULT_MODE, BackendMode
from ici_core.domain.query import ProductScope, Query
from ici_core.domain.rules import EntailmentResult, FactGraph, Triple


class TestBackendMode:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("normal", BackendMode.NORMAL),
            ("ce-rise", BackendMode.CE_RISE),
            ("CE-RISE", BackendMode.CE_RISE),
            ("ce_rise", BackendMode.CE_RISE),
            ("  normal  ", BackendMode.NORMAL),
            ("nonsense", None),
            ("", None),
            (None, None),
        ],
    )
    def test_parse_is_lenient_but_never_guesses(
        self, raw: str | None, expected: BackendMode | None
    ) -> None:
        assert BackendMode.parse(raw) is expected

    def test_default_is_normal(self) -> None:
        assert DEFAULT_MODE is BackendMode.NORMAL


class TestQuery:
    def test_empty_text_is_rejected_at_the_boundary(self) -> None:
        # An empty query must never reach an LLM call.
        for bad in ("", "   ", "\n"):
            with pytest.raises(ValueError, match="empty"):
                Query(text=bad)

    def test_scope_knows_whether_it_is_product_scoped(self) -> None:
        assert not ProductScope(session="s1").is_product_scoped
        assert ProductScope(product_id=ProductId("p1")).is_product_scoped


class TestContextPack:
    def test_duplicate_ids_are_rejected(self) -> None:
        item = Evidence(id=EvidenceId("e1"), kind=EvidenceKind.PASSAGE, text="x", ref="r")
        with pytest.raises(ValueError, match="duplicate"):
            ContextPack((item, item))

    def test_merge_keeps_the_first_occurrence(self) -> None:
        a = Evidence(id=EvidenceId("e1"), kind=EvidenceKind.PASSAGE, text="first", ref="r1")
        b = Evidence(id=EvidenceId("e1"), kind=EvidenceKind.PASSAGE, text="second", ref="r2")
        merged = ContextPack((a,)).merge(ContextPack((b,)))
        assert len(merged) == 1
        assert merged.get(EvidenceId("e1")) is a

    def test_evidence_without_a_ref_is_rejected(self) -> None:
        # Evidence nobody can follow is useless for audit.
        with pytest.raises(ValueError, match="resolvable ref"):
            Evidence(id=EvidenceId("e"), kind=EvidenceKind.PASSAGE, text="x", ref="")


class TestFacts:
    def test_a_fact_without_provenance_cannot_exist(self) -> None:
        with pytest.raises(ValueError, match="provenance"):
            Fact(
                subject="battery",
                predicate="capacity",
                value="60 kWh",
                product_id=ProductId("p1"),
                provenance_ref="",
            )

    def test_validation_outcome_is_explicit(self) -> None:
        assert ValidationOutcome.VALIDATED != ValidationOutcome.REJECTED


class TestConfidence:
    def test_calibrated_must_be_a_probability(self) -> None:
        for bad in (-0.1, 1.1):
            with pytest.raises(ValueError, match=r"\[0,1\]"):
                Confidence(calibrated=bad)

    def test_weakest_returns_none_rather_than_inventing_a_reason(self) -> None:
        assert SignalVector().weakest() is None

    def test_operating_point_admits_only_at_or_above_tau(self) -> None:
        point = OperatingPoint(tau=0.6)
        assert point.admits(Confidence(calibrated=0.6))
        assert point.admits(Confidence(calibrated=0.61))
        assert not point.admits(Confidence(calibrated=0.59))


class TestEntailment:
    def test_fired_is_observable(self) -> None:
        """The paper reports precision *conditional on firing*, so this must be visible."""
        assert not EntailmentResult().fired
        assert EntailmentResult(rules_fired=("r1",)).fired

    def test_fact_graph_merge_is_a_set_union(self) -> None:
        t1 = Triple("a", "b", "c")
        t2 = Triple("d", "e", "f")
        merged = FactGraph((t1,)).merge(FactGraph((t1, t2)))
        assert len(merged) == 2

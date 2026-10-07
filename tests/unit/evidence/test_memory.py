"""Memory: the four properties §4.2 of the paper lists as missing from the prototype."""

from __future__ import annotations

from dataclasses import replace

import pytest

from ici_core.domain.facts import Fact, ValidationOutcome
from ici_core.domain.ids import ProductId
from ici_core.domain.query import ProductScope, Query
from ici_evidence import AppendOnlyFactMemory, UnvalidatedFactError

A = ProductId("product-A")
B = ProductId("product-B")


def fact(product: ProductId, value: str = "60 kWh", subject: str = "battery") -> Fact:
    return Fact(
        subject=subject,
        predicate="capacity",
        value=value,
        product_id=product,
        provenance_ref="doc:spec#p3",
    )


@pytest.fixture
def memory() -> AppendOnlyFactMemory:
    return AppendOnlyFactMemory()


class TestProductScoping:
    def test_recall_never_crosses_products(self, memory) -> None:
        # The single most important assertion in this file. Session-scoped recall
        # can hand back another product's facts, silently, and the answer looks
        # fine. In a compliance tool that is the worst available failure.
        memory.commit(fact(A), ValidationOutcome.VALIDATED)
        leaked = memory.recall(ProductScope(product_id=B), Query(text="capacity"))
        assert list(leaked) == []

    def test_recall_without_a_product_returns_nothing(self, memory) -> None:
        # Guessing a scope is how facts leak. No product, no recall.
        memory.commit(fact(A), ValidationOutcome.VALIDATED)
        assert list(memory.recall(ProductScope(session="s1"), Query(text="capacity"))) == []

    def test_recall_returns_this_products_facts(self, memory) -> None:
        memory.commit(fact(A), ValidationOutcome.VALIDATED)
        got = memory.recall(ProductScope(product_id=A), Query(text="battery capacity"))
        assert [f.value for f in got] == ["60 kWh"]


class TestValidationBeforeStorage:
    def test_an_unvalidated_fact_is_refused(self, memory) -> None:
        with pytest.raises(UnvalidatedFactError, match="unvalidated"):
            memory.commit(fact(A), ValidationOutcome.REJECTED)

    def test_a_refused_fact_is_not_retrievable(self, memory) -> None:
        with pytest.raises(UnvalidatedFactError):
            memory.commit(fact(A), ValidationOutcome.REJECTED)
        assert list(memory.recall(ProductScope(product_id=A), Query(text="capacity"))) == []

    def test_a_fact_without_provenance_cannot_be_built_at_all(self) -> None:
        with pytest.raises(ValueError, match="provenance"):
            Fact(
                subject="battery",
                predicate="capacity",
                value="60 kWh",
                product_id=A,
                provenance_ref="",
            )


class TestSupersession:
    def test_correction_appends_and_does_not_mutate(self, memory) -> None:
        old = memory.commit(fact(A, "60 kWh"), ValidationOutcome.VALIDATED)
        memory.supersede(
            old, fact(A, "62 kWh"), ValidationOutcome.VALIDATED, reason="datasheet revision B"
        )

        history = list(memory.history("battery", ProductScope(product_id=A)))
        assert len(history) == 2, "the superseded version must remain readable"
        assert [v.fact.value for v in history] == ["60 kWh", "62 kWh"]

    def test_recall_returns_only_the_current_version(self, memory) -> None:
        old = memory.commit(fact(A, "60 kWh"), ValidationOutcome.VALIDATED)
        memory.supersede(
            old, fact(A, "62 kWh"), ValidationOutcome.VALIDATED, reason="datasheet revision B"
        )
        got = memory.recall(ProductScope(product_id=A), Query(text="battery capacity"))
        assert [f.value for f in got] == ["62 kWh"]

    def test_a_correction_must_say_why(self, memory) -> None:
        old = memory.commit(fact(A), ValidationOutcome.VALIDATED)
        with pytest.raises(ValueError, match="must say why"):
            memory.supersede(old, fact(A, "62 kWh"), ValidationOutcome.VALIDATED, reason="")

    def test_superseding_an_unknown_fact_is_an_error(self, memory) -> None:
        from ici_core.domain.ids import FactId

        with pytest.raises(KeyError):
            memory.supersede(FactId("nope"), fact(A), ValidationOutcome.VALIDATED, reason="x")

    def test_rejected_correction_leaves_the_original_current(self, memory) -> None:
        old = memory.commit(fact(A), ValidationOutcome.VALIDATED)
        with pytest.raises(UnvalidatedFactError):
            memory.supersede(old, fact(A, "62 kWh"), ValidationOutcome.REJECTED, reason="x")
        got = memory.recall(ProductScope(product_id=A), Query(text="capacity"))
        assert [f.value for f in got] == ["60 kWh"]
        assert len(memory.history("battery", ProductScope(product_id=A))) == 1

    @pytest.mark.parametrize(
        "replacement",
        [fact(B), fact(A, subject="module"), replace(fact(A), predicate="voltage")],
        ids=["different-product", "different-subject", "different-predicate"],
    )
    def test_correction_must_keep_fact_identity(self, memory, replacement) -> None:
        old = memory.commit(fact(A), ValidationOutcome.VALIDATED)
        with pytest.raises(ValueError, match="product, subject, and predicate"):
            memory.supersede(old, replacement, ValidationOutcome.VALIDATED, reason="x")
        got = memory.recall(ProductScope(product_id=A), Query(text="capacity"))
        assert [f.value for f in got] == ["60 kWh"]
        assert memory.recall(ProductScope(product_id=B), Query(text="capacity")) == []
        assert len(memory.versions) == 1

    def test_only_the_current_version_can_be_corrected(self, memory) -> None:
        old = memory.commit(fact(A), ValidationOutcome.VALIDATED)
        current = memory.supersede(
            old, fact(A, "62 kWh"), ValidationOutcome.VALIDATED, reason="revision B"
        )
        with pytest.raises(ValueError, match="no longer current"):
            memory.supersede(
                old, fact(A, "64 kWh"), ValidationOutcome.VALIDATED, reason="revision C"
            )
        assert len(memory.history("battery", ProductScope(product_id=A))) == 2
        got = memory.recall(ProductScope(product_id=A), Query(text="capacity"))
        assert [f.value for f in got] == ["62 kWh"]
        memory.supersede(
            current, fact(A, "64 kWh"), ValidationOutcome.VALIDATED, reason="revision C"
        )
        got = memory.recall(ProductScope(product_id=A), Query(text="capacity"))
        assert [f.value for f in got] == ["64 kWh"]


class TestHistory:
    def test_history_carries_the_reason(self, memory) -> None:
        old = memory.commit(fact(A), ValidationOutcome.VALIDATED)
        memory.supersede(
            old, fact(A, "62 kWh"), ValidationOutcome.VALIDATED, reason="datasheet revision B"
        )
        corrections = [
            v for v in memory.history("battery", ProductScope(product_id=A)) if v.is_correction
        ]
        assert corrections[0].reason == "datasheet revision B"

    def test_history_is_product_scoped_too(self, memory) -> None:
        memory.commit(fact(A), ValidationOutcome.VALIDATED)
        assert list(memory.history("battery", ProductScope(product_id=B))) == []


def test_optional_log_does_not_restore_memory(tmp_path) -> None:
    path = tmp_path / "memory.jsonl"
    memory = AppendOnlyFactMemory(path=path)
    old = memory.commit(fact(A), ValidationOutcome.VALIDATED)
    memory.supersede(old, fact(A, "62 kWh"), ValidationOutcome.VALIDATED, reason="revision B")
    lines = path.read_text().strip().splitlines()
    assert len(lines) == 2, "append-only means both versions are on disk"
    assert '"supersedes": null' in lines[0]
    assert '"reason": "revision B"' in lines[1]
    restarted = AppendOnlyFactMemory(path=path)
    assert restarted.recall(ProductScope(product_id=A), Query(text="battery capacity")) == []

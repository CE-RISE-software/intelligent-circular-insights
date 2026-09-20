"""Retrieval: BM25-style scoring over passage-split seed documents."""

from __future__ import annotations

import pytest

from ici_core.domain.query import ProductScope, Query, RetrievalBudget
from ici_evidence import DocumentEvidenceProvider, split_passages, tokenize
from ici_substrates.paths import SEED_DOCS_ROOT


@pytest.fixture(scope="module")
def provider() -> DocumentEvidenceProvider:
    return DocumentEvidenceProvider.from_seed_docs(SEED_DOCS_ROOT)


class TestPassageSplitting:
    def test_paragraphs_are_packed_not_hard_cut(self) -> None:
        text = "\n\n".join(["short para"] * 20)
        chunks = split_passages(text, limit=100)
        assert all(len(c) <= 100 for c in chunks)
        assert len(chunks) > 1

    def test_an_oversized_block_is_still_emitted(self) -> None:
        assert split_passages("x" * 500, limit=100) == ["x" * 100]

    def test_empty_text_yields_nothing(self) -> None:
        assert split_passages("") == []


class TestRetrieval:
    def test_the_corpus_loaded(self, provider) -> None:
        assert len(provider.passages) > 0

    def test_returns_empty_not_none_for_no_match(self, provider) -> None:
        got = provider.retrieve(Query(text="zzzqqqxxx"), RetrievalBudget())
        assert got is not None and list(got) == []

    def test_every_result_carries_a_resolvable_ref(self, provider) -> None:
        got = provider.retrieve(Query(text="battery capacity"), RetrievalBudget())
        assert got
        for item in got:
            assert item.ref and "#" in item.ref
            assert item.source_file

    def test_respects_the_budget(self, provider) -> None:
        got = provider.retrieve(Query(text="battery"), RetrievalBudget(top_k_documents=2))
        assert len(list(got)) <= 2

    def test_is_deterministic(self, provider) -> None:
        q = Query(text="recycled content")
        a = [e.id for e in provider.retrieve(q, RetrievalBudget())]
        b = [e.id for e in provider.retrieve(q, RetrievalBudget())]
        assert a == b

    def test_results_are_ordered_best_first(self, provider) -> None:
        got = list(provider.retrieve(Query(text="battery capacity"), RetrievalBudget()))
        scores = [e.score for e in got if e.score is not None]
        assert scores == sorted(scores, reverse=True)

    def test_domain_scope_narrows_but_never_to_nothing(self, provider) -> None:
        # Filtering to an empty set would be worse than not filtering, so an
        # unknown domain falls back to the whole corpus rather than returning [].
        q = Query(text="battery", scope=ProductScope(domain="no_such_domain"))
        assert list(provider.retrieve(q, RetrievalBudget()))

    def test_an_empty_index_answers_empty(self) -> None:
        assert (
            list(DocumentEvidenceProvider().retrieve(Query(text="anything"), RetrievalBudget()))
            == []
        )


def test_tokenizer_keeps_identifiers_intact() -> None:
    # Part numbers and standard ids are exactly what these questions turn on.
    assert "en_62133-2" in tokenize("Conforms to EN_62133-2.")
    assert "b-0001" in tokenize("Product B-0001 report")

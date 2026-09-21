# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Questions about one supplied passport, over HTTP.

The last window from the demo's port table. What is asserted here is mostly that it
is *not* a second pipeline: the same use case runs, so the same envelope comes back,
and the only difference is which evidence provider is bound.

The demo answered these questions down a parallel path with its own ranking, its own
model call, its own confidence number and no grounding check. The window where a
user is most likely to paste an unfamiliar document therefore had the weakest
guarantees in the product. These tests exist to keep that from drifting back.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from apps.api.main import create_app
from apps.api.settings import Settings
from fastapi.testclient import TestClient

NORMAL = {"X-Backend-Mode": "normal"}
CE_RISE = {"X-Backend-Mode": "ce-rise"}

PASSPORT: dict[str, Any] = {
    "dpp_id": "bat-001",
    "schema_version": "1.0",
    "product": {"brand": "Generic", "model": "BEV pack 60 kWh", "category": "battery"},
    "materials": [{"name": "Lithium", "share_pct": 12}, {"name": "Steel", "share_pct": 40}],
    "compliance": {"standards": ["EN 62133-2"], "ce_marking": True},
}
DOC = json.dumps(PASSPORT, indent=2)


@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(create_app(Settings())) as c:
        yield c


class TestReadingTheDocument:
    def test_a_passport_splits_on_its_own_structure(self, client) -> None:
        body = client.post(
            "/api/single-dpp/parse", json={"content": DOC, "filename": "battery.json"}
        ).json()
        titles = {s["title"] for s in body["sections"]}
        # Keys, not character offsets: 'compliance' and 'materials' are different
        # subjects, and chunking by length would cut across them.
        assert {"Product", "Materials", "Compliance"} <= titles
        assert body["document_type"] == "json"

    def test_top_level_scalars_become_an_identity_section(self, client) -> None:
        body = client.post("/api/single-dpp/parse", json={"content": DOC}).json()
        identity = next(s for s in body["sections"] if s["id"] == "s-identity")
        paths = {f["path"] for f in identity["fields"]}
        assert {"/dpp_id", "/schema_version"} <= paths

    def test_each_section_carries_a_pointer_a_reader_can_follow(self, client) -> None:
        body = client.post("/api/single-dpp/parse", json={"content": DOC}).json()
        assert all(s["path"] for s in body["sections"])
        assert {"/product", "/materials", "/compliance"} <= {s["path"] for s in body["sections"]}

    def test_reading_a_document_needs_no_model_and_no_backend(self, client) -> None:
        # Deliberate: looking at a document the user already has should not depend
        # on a language model being reachable, and it should cost nothing.
        with TestClient(create_app(Settings(llm_disabled=True))) as c:
            assert c.post("/api/single-dpp/parse", json={"content": DOC}).status_code == 200

    def test_free_text_is_read_as_text(self, client) -> None:
        body = client.post(
            "/api/single-dpp/parse",
            json={"content": "Declared capacity: 60 kWh.\n\nRecycled cobalt: 12%."},
        ).json()
        assert body["document_type"] == "text"
        assert body["sections"]


class TestWhenTheDocumentIsWrong:
    def test_broken_json_is_reported_and_still_readable(self, client) -> None:
        # The most useful case this endpoint has: a malformed passport is exactly
        # what a user wants help with, so it is read as text and the problem is
        # named rather than the request failing.
        body = client.post("/api/single-dpp/parse", json={"content": '{"broken": '}).json()
        assert body["document_type"] == "text"
        assert any("does not parse" in w for w in body["warnings"])
        assert any("Validate" in w for w in body["warnings"])

    def test_an_oversized_document_is_declined_with_the_numbers(self, client) -> None:
        r = client.post("/api/single-dpp/parse", json={"content": "x" * 500_000})
        assert r.status_code == 422
        reason = r.json()["reason"]
        assert "500,000" in reason and "400,000" in reason

    def test_an_empty_document_cannot_be_asked_about(self, client) -> None:
        r = client.post(
            "/api/single-dpp/ask", json={"q": "anything", "content": ""}, headers=NORMAL
        )
        assert r.status_code == 422
        assert "nothing could be read" in r.json()["reason"]


class TestItIsNotASecondPipeline:
    """The point of the rewrite for this window."""

    @pytest.mark.parametrize("headers", [NORMAL, CE_RISE], ids=["normal", "ce-rise"])
    def test_it_never_500s_and_names_the_backend(self, client, headers) -> None:
        r = client.post(
            "/api/single-dpp/ask",
            json={"q": "Which standards does this carry?", "content": DOC},
            headers=headers,
        )
        assert r.status_code != 500
        assert r.headers["X-Backend-Mode-Used"] == headers["X-Backend-Mode"]

    def test_the_corpus_is_not_consulted(self, client) -> None:
        """A question the seed corpus can answer must not be answered from it.

        The whole premise is a passport that is *not* in the system, so evidence
        leaking in from the indexed collection would silently answer about a
        different product.
        """

        from ici_core.domain.query import ProductScope, Query, RetrievalBudget
        from ici_evidence import InlineDocumentProvider, parse_document

        provider = InlineDocumentProvider(parse_document(DOC, "battery.json"))
        found = provider.retrieve(
            Query(text="recycled cobalt content of the battery", scope=ProductScope()),
            RetrievalBudget(top_k_documents=4),
        )
        # Every ref points into the supplied document, never at a seed file.
        assert found
        assert all(e.ref.startswith("battery.json") for e in found)
        assert all(e.source_file == "battery.json" for e in found)

    def test_scoring_matches_the_corpus_reader(self, client) -> None:
        # Same BM25 constants on purpose: a score of 0.7 should mean the same thing
        # in both windows, or a user comparing them is being misled.
        from ici_evidence.documents import K1, B
        from ici_evidence.inline import K1 as INLINE_K1
        from ici_evidence.inline import B as INLINE_B

        assert (INLINE_K1, INLINE_B) == (K1, B)

    def test_a_lexical_miss_still_offers_the_document(self, client) -> None:
        """A short passport can hold the answer while matching no query term.

        'Is it compliant?' against a section titled 'certifications' scores zero.
        Falling back to the document lets the grounding verifier decide, which is a
        better judge than a term overlap of nothing.
        """
        from ici_core.domain.query import ProductScope, Query, RetrievalBudget
        from ici_evidence import InlineDocumentProvider, parse_document

        provider = InlineDocumentProvider(parse_document(DOC, "battery.json"))
        found = provider.retrieve(
            Query(text="zzzqqq unmatchable", scope=ProductScope()),
            RetrievalBudget(top_k_documents=3),
        )
        assert found, "an unmatched question should still see the document"
        assert all(e.score is None for e in found), "a fallback section must not claim a score"

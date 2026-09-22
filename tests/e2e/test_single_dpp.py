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
from apps.api.deps import get_llm_request
from apps.api.main import create_app
from apps.api.settings import Settings
from fastapi.testclient import TestClient
from tests.unit.llm.conftest import ScriptedTransport, chat, claim_result

from ici_core.domain.modes import BackendMode
from ici_llm.provider import OpenAIProvider
from ici_llm.runtime import LLMRuntime

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
        assert next(s for s in body["sections"] if s["id"] == "s-identity")["path"] == ""
        assert {"/product", "/materials", "/compliance"} <= {s["path"] for s in body["sections"]}

    def test_pointer_segments_escape_slashes_and_tildes(self, client) -> None:
        content = json.dumps({"a/b": {"x~y": "needle"}})
        body = client.post("/api/single-dpp/parse", json={"content": content}).json()
        section = next(s for s in body["sections"] if s["title"] == "A/b")
        assert section["path"] == "/a~1b"
        assert {f["path"] for f in section["fields"]} == {"/a~1b/x~0y"}

    def test_long_json_array_keeps_the_last_item_and_address(self, client) -> None:
        values = [f"item-{i:03d}" for i in range(250)] + ["distinctive-tail-marker"]
        content = json.dumps({"materials": values})
        body = client.post("/api/single-dpp/parse", json={"content": content}).json()
        assert body["document_type"] == "json"
        assert len(body["sections"]) > 1
        assert any(
            s["path"] == "/materials/250" and "distinctive-tail-marker" in s["preview"]
            for s in body["sections"]
        )

    def test_long_root_array_is_split_without_cutting_the_tail(self, client) -> None:
        content = json.dumps([f"item-{i:03d}" for i in range(250)] + ["root-tail-marker"])
        body = client.post("/api/single-dpp/parse", json={"content": content}).json()
        assert body["document_type"] == "json"
        assert any(
            s["path"] == "/250" and "root-tail-marker" in s["preview"] for s in body["sections"]
        )

    def test_long_text_paragraph_keeps_its_tail(self, client) -> None:
        from ici_evidence import parse_document

        document = parse_document("word " * 1_000 + "distinctive-tail-marker")
        assert len(document.sections) > 1
        assert all(len(section.text) <= 2_000 for section in document.sections)
        assert "distinctive-tail-marker" in document.sections[-1].text

    def test_many_short_identity_values_are_split_without_cutting_them(self, client) -> None:
        content = json.dumps({f"field_{i}": f"value_{i}" for i in range(300)})
        body = client.post("/api/single-dpp/parse", json={"content": content}).json()
        assert body["document_type"] == "json"
        assert len(body["sections"]) > 1
        assert all(len(s["preview"]) <= 600 for s in body["sections"])
        assert any(
            field == {"path": "/field_299", "value": "value_299"}
            for section in body["sections"]
            for field in section["fields"]
        )

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

    @pytest.mark.parametrize(
        "content",
        ['{"value": NaN}', '{"value": Infinity}', '{"value": 1e999}', '{"value": 1, "value": 2}'],
    )
    def test_nonstandard_or_ambiguous_json_is_not_treated_as_valid(self, client, content) -> None:
        body = client.post("/api/single-dpp/parse", json={"content": content}).json()
        assert body["document_type"] == "text"
        assert any("does not parse" in warning for warning in body["warnings"])

    @pytest.mark.parametrize("endpoint", ["parse", "ask"])
    def test_single_oversized_json_value_is_typed_decline(self, client, endpoint) -> None:
        payload = {"content": json.dumps({"notes": "x" * 3_000})}
        if endpoint == "ask":
            payload["q"] = "What do the notes say?"
        response = client.post(f"/api/single-dpp/{endpoint}", json=payload, headers=NORMAL)
        assert response.status_code == 422
        assert "2,000" in response.json()["reason"]

    def test_pathological_array_count_is_bounded(self, client) -> None:
        response = client.post(
            "/api/single-dpp/parse", json={"content": json.dumps(list(range(1_500)))}
        )
        assert response.status_code == 422
        assert "1,000 sections" in response.json()["reason"]

    def test_pathological_nesting_is_a_typed_decline_not_500(self, client) -> None:
        response = client.post(
            "/api/single-dpp/parse", json={"content": "[" * 1_100 + "0" + "]" * 1_100}
        )
        assert response.status_code == 422
        assert "nested too deeply" in response.json()["reason"]

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

    @pytest.mark.parametrize("headers", [NORMAL, CE_RISE], ids=["normal", "ce-rise"])
    @pytest.mark.parametrize(
        "change",
        [
            {"q": " "},
            {"tau": -0.1},
            {"tau": 1.1},
            {"top_k": -1},
            {"top_k": 101},
        ],
    )
    def test_invalid_question_threshold_and_budget_are_422_not_500(
        self, client, headers, change
    ) -> None:
        response = client.post(
            "/api/single-dpp/ask",
            json={"q": "standards", "content": DOC, **change},
            headers=headers,
        )
        assert response.status_code == 422
        assert response.headers["X-Backend-Mode-Used"] == headers["X-Backend-Mode"]

    def test_zero_retrieval_budget_abstains_without_model(self, client) -> None:
        response = client.post(
            "/api/single-dpp/ask",
            json={"q": "standards", "content": DOC, "top_k": 0},
            headers=NORMAL,
        )
        assert response.status_code == 200
        assert response.json()["decision"] == "abstain"
        assert response.json()["trace"]["cost"]["llm_calls"] == 0

    @pytest.mark.parametrize("headers", [NORMAL, CE_RISE], ids=["normal", "ce-rise"])
    def test_disabled_model_still_allows_reading_but_declines_asking(self, headers) -> None:
        with TestClient(create_app(Settings(llm_disabled=True))) as c:
            assert c.post("/api/single-dpp/parse", json={"content": DOC}).status_code == 200
            response = c.post(
                "/api/single-dpp/ask", json={"q": "standards", "content": DOC}, headers=headers
            )
            assert response.status_code == 422
            assert "disabled" in response.json()["reason"]
            assert response.headers["X-Backend-Mode-Used"] == headers["X-Backend-Mode"]

    def test_oversized_document_is_declined_before_asking(self, client) -> None:
        response = client.post(
            "/api/single-dpp/ask",
            json={"q": "standards", "content": "x" * 400_001},
            headers=NORMAL,
        )
        assert response.status_code == 422
        assert "400,000" in response.json()["reason"]


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

    @pytest.mark.parametrize("headers", [NORMAL, CE_RISE], ids=["normal", "ce-rise"])
    def test_request_scoped_model_and_audit_are_used(self, client, headers) -> None:
        answer = "The passport lists EN 62133-2 [sec-s2]."
        transport = ScriptedTransport(
            [
                chat(answer),
                chat(json.dumps(claim_result(answer, quote="EN 62133-2", evidence_id="sec-s2"))),
            ]
        )
        source = OpenAIProvider(transport)
        runtime = LLMRuntime(source)
        mode = BackendMode(headers["X-Backend-Mode"])
        client.app.dependency_overrides[get_llm_request] = lambda: runtime.request(mode=mode)
        try:
            response = client.post(
                "/api/single-dpp/ask",
                json={"q": "Which standards?", "content": DOC, "tau": 0},
                headers={**headers, "X-Model": "gpt-4o-mini"},
            )
        finally:
            client.app.dependency_overrides.pop(get_llm_request, None)
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["decision"] == "answer"
        assert body["trace"]["model"] == response.headers["X-Model-Used"] == "gpt-4o-mini"
        assert body["trace"]["cost"]["llm_calls"] == 2
        assert body["trace"]["prompt_hashes"]
        assert all(e["ref"].startswith("document/") for e in body["evidence"])
        assert all(e["ref"].startswith("document/") for e in body["provenance"])
        assert len(transport.requests) == 2
        assert source.audit.steps == []
        assert source.budget.calls == 0

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

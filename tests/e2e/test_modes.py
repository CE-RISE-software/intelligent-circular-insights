"""Both backends, over HTTP, in one process.

This is the parity matrix: the same questions asked of two backends, with the
response required to say which one answered and to decline honestly where it
cannot serve something.
"""

from __future__ import annotations

import pytest
from apps.api.main import create_app
from apps.api.settings import Settings
from fastapi.testclient import TestClient

NORMAL = {"X-Backend-Mode": "normal"}
CE_RISE = {"X-Backend-Mode": "ce-rise"}


@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(create_app(Settings())) as c:
        yield c


class TestBothModesAreLive:
    def test_both_bundles_were_built(self, client) -> None:
        assert set(client.get("/api/health").json()["modes_built"]) == {"normal", "ce-rise"}

    def test_settings_offers_both(self, client) -> None:
        assert set(client.get("/api/settings").json()["mode_allowed"]) == {"normal", "ce-rise"}


class TestSharedFeaturesWorkInBothModes:
    @pytest.mark.parametrize("headers", [NORMAL, CE_RISE], ids=["normal", "ce-rise"])
    def test_validate(self, client, headers) -> None:
        r = client.post("/api/validate", json={"dpp": {}}, headers=headers)
        assert r.status_code == 200
        assert r.json()["conforms"] is False
        assert r.json()["violations"]

    @pytest.mark.parametrize("headers", [NORMAL, CE_RISE], ids=["normal", "ce-rise"])
    def test_models_catalogue(self, client, headers) -> None:
        r = client.get("/api/ce-rise-models/catalog", headers=headers)
        assert r.status_code == 200

    @pytest.mark.parametrize("headers", [NORMAL, CE_RISE], ids=["normal", "ce-rise"])
    def test_the_response_names_the_backend_that_answered(self, client, headers) -> None:
        r = client.post("/api/validate", json={"dpp": {}}, headers=headers)
        assert r.json()["mode"] == headers["X-Backend-Mode"]

    @pytest.mark.parametrize("headers", [NORMAL, CE_RISE], ids=["normal", "ce-rise"])
    def test_no_endpoint_returns_500_in_either_mode(self, client, headers) -> None:
        for method, path, body in [
            ("GET", "/api/settings", None),
            ("GET", "/api/validate/profiles", None),
            ("GET", "/api/ce-rise-models/coverage", None),
            ("POST", "/api/carbon/calculate", {"product_id": "fairphone_4"}),
            ("GET", "/api/pef/overview", None),
            ("GET", "/api/carbon/subjects", None),
            # The gap that let a real 500 ship: /api/search was never in this list,
            # and a cassette miss escaped as an unhandled exception — which also
            # strips the mode header, because it propagates past the middleware.
            ("POST", "/api/search", {"q": "a question with no recorded answer"}),
        ]:
            r = (
                client.request(method, path, json=body, headers=headers)
                if body
                else client.request(method, path, headers=headers)
            )
            assert r.status_code != 500, f"{method} {path} in {headers} returned 500"


class TestWhereTheModesDiffer:
    def test_pef_studio_needs_a_graph_and_says_so_in_normal_mode(self, client) -> None:
        # A mode that cannot serve something gives a reason and a 422. Pretending,
        # or 500ing, would both be worse than declining.
        r = client.get("/api/pef/overview", headers=NORMAL)
        assert r.status_code == 422
        assert "no knowledge graph is mounted" in r.json()["reason"]

    def test_pef_studio_works_in_ce_rise_mode(self, client) -> None:
        body = client.get("/api/pef/overview", headers=CE_RISE).json()
        assert body["graph"]["triples"] == 5387
        assert body["competency_questions"]["answered"] == 16

    def test_the_compliance_caveat_travels_with_the_result(self, client) -> None:
        body = client.get("/api/pef/overview", headers=CE_RISE).json()
        assert "not an EF-compliant declaration" in body["compliance_note"]

    def test_carbon_differs_by_backend(self, client) -> None:
        # Normal reads a flat profile and multiplies a factor table; CE-RISE solves
        # a product system off the graph. Same question, two levels of rigour.
        flat = client.post(
            "/api/carbon/calculate",
            json={"product_id": "generic_bev_pack_60kwh"},
            headers=NORMAL,
        ).json()
        graph = client.post("/api/pef/calculate", json={}, headers=CE_RISE).json()
        assert flat["unit"] == "kg CO2e"
        assert graph["unit"] == "kg CO2 eq"
        assert round(graph["total"], 4) == 0.0594
        assert graph["data_quality"] is not None


class TestPefEndpoints:
    def test_calculate_reproduces_the_published_figures(self, client) -> None:
        body = client.post("/api/pef/calculate", json={}, headers=CE_RISE).json()
        assert round(body["total"], 4) == 0.0594
        assert round(body["data_quality"], 2) == 1.22
        assert all(stage["is_proxy"] for stage in body["by_stage"])

    def test_competency_questions_are_listed_with_their_requirement(self, client) -> None:
        body = client.get("/api/pef/competency-questions", headers=CE_RISE).json()
        assert len(body["questions"]) == 16
        assert body["total_in_paper"] == 173
        assert all(q["pef_requirement"] for q in body["questions"])

    def test_a_competency_question_runs_and_shows_its_sparql(self, client) -> None:
        body = client.post("/api/pef/competency-questions/cq-fu", headers=CE_RISE).json()
        assert body["answered"] is True
        assert body["rows"]
        assert "SELECT" in body["sparql"]

    def test_an_unknown_question_is_422_not_500(self, client) -> None:
        r = client.post("/api/pef/competency-questions/cq-nope", headers=CE_RISE)
        assert r.status_code == 422

    def test_sparql_accepts_a_read(self, client) -> None:
        r = client.post(
            "/api/pef/sparql",
            json={"query": "SELECT ?s WHERE { ?s ?p ?o }", "limit": 3},
            headers=CE_RISE,
        )
        assert r.status_code == 200

    @pytest.mark.parametrize(
        "hostile",
        [
            "DELETE WHERE { ?s ?p ?o }",
            "DROP GRAPH <g>",
            "SELECT * WHERE { SERVICE <http://evil> { ?s ?p ?o } }",
        ],
    )
    def test_sparql_refuses_writes_and_federation(self, client, hostile) -> None:
        r = client.post("/api/pef/sparql", json={"query": hostile}, headers=CE_RISE)
        assert r.status_code == 422
        assert r.json()["error"] == "capability_unavailable"


class TestTheResponseHeaderCannotLie:
    """The badge in the UI reads one header. It has to be right on every path."""

    @pytest.mark.parametrize("headers", [NORMAL, CE_RISE], ids=["normal", "ce-rise"])
    def test_every_route_stamps_the_mode_that_served(self, client, headers) -> None:
        for method, path, body in [
            ("GET", "/api/health", None),
            ("GET", "/api/settings", None),
            ("GET", "/api/validate/profiles", None),
            ("GET", "/api/carbon/subjects", None),
            ("POST", "/api/validate", {"dpp": {}}),
        ]:
            r = client.request(method, path, json=body, headers=headers)
            assert r.headers["X-Backend-Mode-Used"] == headers["X-Backend-Mode"], path

    def test_a_decline_still_names_the_backend_that_declined(self, client) -> None:
        # The 422 path is exactly where a badge is most likely to go stale, because
        # the handler never ran. The header is set by middleware, so it survives.
        r = client.get("/api/pef/overview", headers=NORMAL)
        assert r.status_code == 422
        assert r.headers["X-Backend-Mode-Used"] == "normal"

    def test_an_unknown_mode_falls_back_and_says_so(self, client) -> None:
        r = client.get("/api/health", headers={"X-Backend-Mode": "quantum"})
        assert r.status_code == 200
        assert r.headers["X-Backend-Mode-Used"] == "normal"
        assert r.headers["X-Backend-Mode-Source"] == "default"
        assert "quantum" in r.headers["X-Backend-Mode-Warning"]

    def test_no_header_means_the_deployment_default(self, client) -> None:
        r = client.get("/api/health")
        assert r.headers["X-Backend-Mode-Used"] == "normal"
        assert r.headers["X-Backend-Mode-Source"] == "default"

    def test_the_header_the_handler_saw_matches_the_header_it_returned(self, client) -> None:
        # Body and header are produced by different layers; this is the assertion
        # that they were resolved once, not twice.
        r = client.post("/api/validate", json={"dpp": {}}, headers=CE_RISE)
        assert r.json()["mode"] == r.headers["X-Backend-Mode-Used"]


class TestSubjectsAreDiscoverable:
    def test_normal_lists_the_product_profiles_on_disk(self, client) -> None:
        body = client.get("/api/carbon/subjects", headers=NORMAL).json()
        ids = {s["id"] for s in body["subjects"]}
        assert "fairphone_4" in ids
        assert all(s["kind"] == "product" for s in body["subjects"])

    def test_ce_rise_lists_the_studies_the_graph_declares(self, client) -> None:
        body = client.get("/api/carbon/subjects", headers=CE_RISE).json()
        # Same bundle key, different substrate: CE-RISE keeps the CSV engine, so the
        # carbon window still works for products the graph has never heard of.
        assert {s["id"] for s in body["subjects"]} == {
            s["id"] for s in client.get("/api/carbon/subjects", headers=NORMAL).json()["subjects"]
        }


class TestTheModelBeingUnreachableIsNotAServerError:
    """A deployment that cannot compose prose still has to answer honestly.

    Replay mode never calls the network, so a question with no recorded response
    has no answer available. That is a configuration fact, not a crash — and
    reporting it as a 500 also loses the mode header, because an unhandled
    exception propagates past ``ModeMiddleware`` before it can stamp one.
    """

    @pytest.mark.parametrize("headers", [NORMAL, CE_RISE], ids=["normal", "ce-rise"])
    def test_a_cassette_miss_declines_with_a_reason(self, client, headers) -> None:
        r = client.post(
            "/api/search",
            json={"q": "a question no cassette was ever recorded for"},
            headers=headers,
        )
        assert r.status_code == 422
        body = r.json()
        assert body["error"] == "model_unavailable"
        assert "replay mode" in body["reason"]
        # Actionable, not just apologetic.
        assert "LLM_CASSETTE_MODE=record" in body["reason"]

    @pytest.mark.parametrize("headers", [NORMAL, CE_RISE], ids=["normal", "ce-rise"])
    def test_the_badge_can_still_tell_who_declined(self, client, headers) -> None:
        r = client.post(
            "/api/search",
            json={"q": "a question no cassette was ever recorded for"},
            headers=headers,
        )
        assert r.headers["X-Backend-Mode-Used"] == headers["X-Backend-Mode"]

    @pytest.mark.parametrize("headers", [NORMAL, CE_RISE], ids=["normal", "ce-rise"])
    def test_a_question_with_no_evidence_abstains_without_reaching_the_model(
        self, client, headers
    ) -> None:
        # The composition step is never entered when the pack is empty, so this
        # path returns a full envelope with no model call and no spend. It is what
        # the frontend smoke test exercises, for exactly that reason.
        r = client.post(
            "/api/search",
            json={"q": "zzzqqq unmatchable gibberish token"},
            headers=headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["decision"] == "abstain"
        assert body["abstain_reason"]
        assert body["operating_point"]["tau"] == 0.5

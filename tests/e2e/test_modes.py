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

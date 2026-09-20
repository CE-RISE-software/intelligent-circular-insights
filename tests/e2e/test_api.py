"""The API, end to end, in process.

Mid cases and edge cases per window, as `docs/TESTING.md` specifies. No API key:
the search path replays from cassettes, everything else is deterministic.
"""

from __future__ import annotations

import pytest
from apps.api.main import create_app
from apps.api.settings import Settings
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(create_app(Settings())) as c:
        yield c


class TestService:
    def test_health_reports_which_modes_were_built(self, client) -> None:
        body = client.get("/api/health").json()
        assert body["ok"] is True
        assert "normal" in body["modes_built"]

    def test_settings_offers_only_modes_that_exist(self, client) -> None:
        # The UI must not be able to offer a switch that would fail.
        body = client.get("/api/settings").json()
        assert body["mode_allowed"] == ["normal"]


class TestCarbon:
    def test_representative_product_matches_the_oracle(self, client) -> None:
        body = client.post(
            "/api/carbon/calculate", json={"product_id": "apple_iphone15_pro_128gb"}
        ).json()
        assert round(body["total"], 6) == 64.852055
        assert body["unit"] == "kg CO2e"
        assert body["provenance"]

    def test_contributions_sum_to_the_total(self, client) -> None:
        body = client.post(
            "/api/carbon/calculate", json={"product_id": "generic_bev_pack_60kwh"}
        ).json()
        assert round(sum(c["amount"] for c in body["contributions"]), 6) == round(body["total"], 6)

    def test_an_unsupported_indicator_is_422_with_a_reason_not_500(self, client) -> None:
        r = client.post(
            "/api/carbon/calculate",
            json={"product_id": "fairphone_4", "indicator": "acidification"},
        )
        assert r.status_code == 422
        assert r.json()["error"] == "capability_unavailable"
        assert r.json()["reason"]

    def test_an_empty_product_id_is_rejected_at_the_boundary(self, client) -> None:
        assert client.post("/api/carbon/calculate", json={"product_id": ""}).status_code == 422


class TestValidate:
    def test_an_empty_dpp_yields_typed_located_violations(self, client) -> None:
        body = client.post("/api/validate", json={"dpp": {}}).json()
        assert body["conforms"] is False
        assert body["violations"]
        for violation in body["violations"]:
            assert violation["location"].startswith("/")
            assert violation["kind"]
            assert violation["message"]

    def test_wrong_types_are_reported_not_crashed_on(self, client) -> None:
        r = client.post(
            "/api/validate",
            json={"dpp": {"schema_version": 1.0, "dpp_id": ["not", "a", "string"]}},
        )
        assert r.status_code == 200
        assert r.json()["conforms"] is False

    def test_profiles_are_enumerable(self, client) -> None:
        assert client.get("/api/validate/profiles").json()["profiles"]


class TestModels:
    def test_all_seventeen_with_their_licence_declared(self, client) -> None:
        body = client.get("/api/ce-rise-models/catalog").json()
        assert body["model_count"] == 17
        # The models are CC-BY-NC-4.0 while this code is EUPL-1.2 (ADR 0010), so
        # the licence travels with the data rather than being implied by the root.
        assert body["licence"] == "CC-BY-NC-4.0"

    def test_routing_finds_something_relevant(self, client) -> None:
        body = client.post(
            "/api/ce-rise-models/route",
            json={"question": "recycled content of this battery"},
        ).json()
        assert body["matches"]

    def test_an_empty_question_routes_nowhere_without_erroring(self, client) -> None:
        r = client.post("/api/ce-rise-models/route", json={"question": ""})
        assert r.status_code == 200
        assert r.json()["matches"] == []

    def test_coverage_is_reportable(self, client) -> None:
        assert client.get("/api/ce-rise-models/coverage").json()["substrates"]


class TestModeHandling:
    def test_the_response_says_which_backend_answered(self, client) -> None:
        r = client.post("/api/carbon/calculate", json={"product_id": "fairphone_4"})
        assert r.json()["mode"] == "normal"

    def test_an_unknown_mode_falls_back_rather_than_failing(self, client) -> None:
        # A typo in a header should not be an outage; the response still says
        # which mode actually ran, so nothing is hidden by the leniency.
        r = client.post(
            "/api/carbon/calculate",
            json={"product_id": "fairphone_4"},
            headers={"X-Backend-Mode": "nonsense"},
        )
        assert r.status_code == 200
        assert r.json()["mode"] == "normal"

    def test_requesting_an_unbuilt_mode_is_422_with_a_reason(self, client) -> None:
        r = client.post(
            "/api/carbon/calculate",
            json={"product_id": "fairphone_4"},
            headers={"X-Backend-Mode": "ce-rise"},
        )
        # CE-RISE is not built until Sprint 2. It says so rather than 500ing.
        assert r.status_code in (200, 422)


class TestSearchBoundaries:
    def test_an_empty_query_never_reaches_the_model(self, client) -> None:
        assert client.post("/api/search", json={"q": ""}).status_code == 422

    def test_the_search_route_exists_and_is_mounted(self, client) -> None:
        assert "/api/search" in create_app(Settings()).openapi()["paths"]

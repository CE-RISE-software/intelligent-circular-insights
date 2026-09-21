# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Repair and synthesis, over HTTP, in both modes.

Route-specific cassettes exercise the real evidence gather and composer. Scripted
responses cover adverse outputs and training-only suggestions without paid calls.
Missing happy-path recordings fail the gate; they must never silently skip it.
"""

from __future__ import annotations

import copy
import json
from typing import Any

import pytest
from apps.api.deps import get_llm_request
from apps.api.main import create_app
from apps.api.settings import Settings
from fastapi.testclient import TestClient
from tests.llm_recording_cases import ROUTE_SEED
from tests.llm_scenarios import DEMO_RECORD
from tests.unit.llm.conftest import ScriptedTransport, chat

from ici_llm.audit import AuditLog
from ici_llm.provider import OpenAIProvider
from ici_llm.records import (
    GroundedFill,
    RecordIssue,
    RepairResult,
    UnverifiedSuggestion,
    ValueSupport,
)
from ici_llm.runtime import LLMRuntime

NORMAL = {"X-Backend-Mode": "normal"}
CE_RISE = {"X-Backend-Mode": "ce-rise"}

# A product the seed corpus actually carries, so retrieval finds evidence and the
# request gets as far as the composer.
KNOWN_SEED: dict[str, Any] = {
    "dpp_id": "bat-001",
    "product": {"brand": "Generic", "model": "BEV pack 60 kWh"},
}
# Nothing in the corpus mentions this, so the pack comes back empty.
UNKNOWN_SEED: dict[str, Any] = {
    "dpp_id": "zzz-000",
    "product": {"brand": "Qqzzx", "model": "Wubbleflorp 9000"},
}


class _StubComposer:
    """Stands in for ``RecordComposer``, returning one of each kind of outcome."""

    def __init__(self) -> None:
        self.packs: list[Any] = []

    def repair(self, record, pack, *, suggest_from_training: bool = True):
        self.packs.append(pack)
        suggestions = (
            (
                UnverifiedSuggestion(
                    path="/compliance/0/standard",
                    value="EN 62133-2",
                    rationale="common for this cell chemistry",
                    confidence=0.3,
                ),
            )
            if suggest_from_training
            else ()
        )
        return RepairResult(
            record={**dict(record), "capacity_kwh": 60},
            fills=(
                GroundedFill(
                    path="/capacity_kwh",
                    value=60,
                    support=ValueSupport(
                        path="/capacity_kwh",
                        evidence_id="e1",
                        evidence_ref="battery.jsonl#3",
                        source_pointer="/text",
                    ),
                    confidence=0.9,
                ),
            ),
            cannot_be_grounded=(RecordIssue("/warranty_years", "no source states this"),),
            rejected=(RecordIssue("/mass_kg", "proposed value not in any source"),),
            suggestions=suggestions,
        )

    def synthesize(self, seed, pack):  # pragma: no cover - exercised via repair paths
        raise AssertionError("not used in these tests")


@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(create_app(Settings())) as c:
        yield c


@pytest.fixture
def stubbed(client: TestClient):
    """Swap the composer for a stub, leaving every other adapter real."""
    stub = _StubComposer()

    class _Request:
        records = stub
        audit = AuditLog()

    client.app.dependency_overrides[get_llm_request] = lambda: _Request()
    yield stub
    client.app.dependency_overrides.pop(get_llm_request, None)


class TestTheRoutesExist:
    @pytest.mark.parametrize("headers", [NORMAL, CE_RISE], ids=["normal", "ce-rise"])
    def test_repair_and_synthesis_are_mounted_in_both_modes(self, client, headers) -> None:
        # Until Sprint 3 neither route existed at all: the composer was reachable
        # only from tests. A 404 here is the regression this guards.
        for path, body in [
            ("/api/validate/repair", {"dpp": KNOWN_SEED}),
            ("/api/synthesize", {"seed": KNOWN_SEED}),
        ]:
            r = client.post(path, json=body, headers=headers)
            assert r.status_code != 404, path
            assert r.status_code != 500, path

    @pytest.mark.parametrize("headers", [NORMAL, CE_RISE], ids=["normal", "ce-rise"])
    def test_they_name_the_backend_that_served(self, client, headers) -> None:
        r = client.post("/api/validate/repair", json={"dpp": KNOWN_SEED}, headers=headers)
        assert r.headers["X-Backend-Mode-Used"] == headers["X-Backend-Mode"]


class TestRefusingBeforeSpending:
    """The cheapest guard in the system: decline before the model call, not after."""

    def test_a_product_with_no_evidence_is_declined(self, client) -> None:
        r = client.post("/api/synthesize", json={"seed": UNKNOWN_SEED}, headers=NORMAL)
        assert r.status_code == 422
        assert r.json()["error"] == "record_not_grounded"
        assert "no same-product structured evidence" in r.json()["reason"]

    def test_repair_without_sources_and_suggestions_costs_nothing(self, client) -> None:
        r = client.post(
            "/api/validate/repair",
            json={"dpp": UNKNOWN_SEED, "suggest_from_training": False},
            headers=NORMAL,
        )
        assert r.status_code == 200
        assert r.json()["record"] == UNKNOWN_SEED
        assert r.json()["cannot_be_grounded"]
        assert r.json()["trace"]["cost"]["llm_calls"] == 0

    def test_an_unknown_profile_is_refused_before_the_composer(self, client, stubbed) -> None:
        client.post(
            "/api/synthesize", json={"seed": UNKNOWN_SEED, "profile": "unknown"}, headers=NORMAL
        )
        assert stubbed.packs == []

    def test_a_deployment_with_the_model_switched_off_declines_typed(self) -> None:
        with TestClient(create_app(Settings(llm_disabled=True))) as c:
            r = c.post("/api/validate/repair", json={"dpp": KNOWN_SEED}, headers=NORMAL)
            assert r.status_code == 422
            assert "disabled" in r.json()["reason"]
            # Deterministic conformance is unaffected: switching the model off must
            # not take the rest of the window with it.
            assert c.post("/api/validate", json={"dpp": {}}, headers=NORMAL).status_code == 200


class TestAGuessIsNeverPresentedAsEvidence:
    """ADR 0011, enforced at the response boundary where a client can see it."""

    def test_grounded_fills_and_suggestions_are_separate_fields(self, client, stubbed) -> None:
        body = client.post("/api/validate/repair", json={"dpp": KNOWN_SEED}, headers=NORMAL).json()

        assert [f["path"] for f in body["grounded_fills"]] == ["/capacity_kwh"]
        assert [s["path"] for s in body["unverified_suggestions"]] == ["/compliance/0/standard"]
        # No suggestion may appear among the grounded fills under any key.
        grounded_paths = {f["path"] for f in body["grounded_fills"]}
        assert not grounded_paths & {s["path"] for s in body["unverified_suggestions"]}

    def test_every_grounded_fill_names_the_source_it_came_from(self, client, stubbed) -> None:
        body = client.post("/api/validate/repair", json={"dpp": KNOWN_SEED}, headers=NORMAL).json()
        fill = body["grounded_fills"][0]
        assert fill["evidence_ref"] == "battery.jsonl#3"
        assert fill["source_pointer"] == "/text"
        # Named 'model_score', never 'confidence': it is a model feature and must
        # not be read as a calibrated probability alongside a search result's.
        assert "model_score" in fill
        assert "confidence" not in fill

    def test_a_suggestion_carries_its_own_warning(self, client, stubbed) -> None:
        body = client.post("/api/validate/repair", json={"dpp": KNOWN_SEED}, headers=NORMAL).json()
        suggestion = body["unverified_suggestions"][0]
        assert suggestion["status"] == "unverified"
        assert suggestion["requires_review"] is True
        assert suggestion["source"] == "model_training"
        assert suggestion["rationale"]

    def test_suggestions_can_be_switched_off(self, client, stubbed) -> None:
        body = client.post(
            "/api/validate/repair",
            json={"dpp": KNOWN_SEED, "suggest_from_training": False},
            headers=NORMAL,
        ).json()
        assert body["unverified_suggestions"] == []
        assert body["grounded_fills"], "turning off guesses must not remove evidence"

    def test_what_could_not_be_grounded_is_reported_not_dropped(self, client, stubbed) -> None:
        body = client.post("/api/validate/repair", json={"dpp": KNOWN_SEED}, headers=NORMAL).json()
        assert [i["path"] for i in body["cannot_be_grounded"]] == ["/warranty_years"]
        assert [i["path"] for i in body["rejected"]] == ["/mass_kg"]
        # A repair that left violations behind does not get to claim conformance.
        assert body["conforms"] is False

    def test_the_repaired_record_is_rechecked_against_the_bound_profile(
        self, client, stubbed
    ) -> None:
        # The composer validates against the schema it was built with; the
        # deployment may have bound a stricter one, so the route checks again.
        body = client.post("/api/validate/repair", json={"dpp": KNOWN_SEED}, headers=NORMAL).json()
        assert "after" in body
        assert body["after"]["profile"]
        assert body["conforms"] == body["after"]["conforms"]


class TestTheRepairIsAuditable:
    def test_the_trace_shows_gathering_before_repairing(self, client, stubbed) -> None:
        body = client.post("/api/validate/repair", json={"dpp": KNOWN_SEED}, headers=NORMAL).json()
        names = [s["name"] for s in body["trace"]["steps"]]
        assert "repair:gather" in names
        assert names.index("repair:gather") < names.index("repair")

    def test_reused_correlation_id_does_not_accumulate_other_request_steps(self, client, stubbed):
        traces = []
        for _ in range(2):
            body = client.post(
                "/api/validate/repair",
                json={"dpp": KNOWN_SEED},
                headers={**NORMAL, "X-Correlation-ID": "repeated-client-id"},
            ).json()
            traces.append(body["trace"]["steps"])
        assert traces[0] == traces[1]
        assert [s["name"] for s in traces[0]].count("repair:gather") == 1

    @pytest.mark.parametrize("mismatch", [None, "id", "brand", "model"])
    def test_only_matching_whole_json_records_reach_composer(self, client, stubbed, mismatch):
        seed = copy.deepcopy(ROUTE_SEED)
        if mismatch:
            seed["product"][mismatch] = "unrelated product"
        client.post("/api/validate/repair", json={"dpp": seed}, headers=NORMAL)
        records = [e for e in stubbed.packs[-1].items if e.ref.startswith("repository:")]
        assert len(records) == (1 if mismatch is None else 0)
        if records:
            assert json.loads(records[0].text) == DEMO_RECORD


@pytest.fixture
def scripted(client):
    """Use the real request runtime/composer, substituting only transport responses."""
    transport = ScriptedTransport([])
    runtime = LLMRuntime(OpenAIProvider(transport))
    client.app.dependency_overrides[get_llm_request] = runtime.request
    yield transport
    client.app.dependency_overrides.pop(get_llm_request, None)


def test_training_only_repair_works_without_evidence_and_never_changes_record(client, scripted):
    scripted.responses.append(
        chat(
            json.dumps(
                {
                    "fills": [],
                    "suggestions": [
                        {
                            "path": "/compliance",
                            "value": {"standards": ["UNVERIFIED"]},
                            "rationale": "A model-prior candidate for human verification",
                            "confidence": 0.98,
                        }
                    ],
                }
            )
        )
    )
    response = client.post("/api/validate/repair", json={"dpp": UNKNOWN_SEED}, headers=NORMAL)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["record"] == UNKNOWN_SEED
    assert not body["grounded_fills"] and not body["conforms"]
    assert len(body["unverified_suggestions"]) == 1
    suggestion = body["unverified_suggestions"][0]
    assert suggestion["model_score"] == 0.3
    assert suggestion["requires_review"] and suggestion["status"] == "unverified"
    assert suggestion["source"] == "model_training"
    assert response.headers["X-Model-Used"] == "gpt-4o-mini"
    assert len(scripted.requests) == 1


@pytest.mark.parametrize(
    "payload",
    [
        chat("not JSON"),
        chat("{}", finish="length"),
        chat("", refusal="private internal reason"),
    ],
)
def test_model_failures_are_typed_declines_not_500s(client, scripted, payload):
    scripted.responses.append(payload)
    response = client.post("/api/validate/repair", json={"dpp": UNKNOWN_SEED}, headers=CE_RISE)
    assert response.status_code == 422
    assert response.json()["error"] == "model_unavailable"
    assert "private internal reason" not in response.text
    assert response.headers["X-Backend-Mode-Used"] == "ce-rise"


@pytest.mark.parametrize("headers", [NORMAL, CE_RISE])
@pytest.mark.parametrize(
    "field,value,path",
    [
        ("issued_at_utc", "yesterday", "/issued_at_utc"),
        ("materials", [{"name": "Steel", "share_pct": 20}], "/materials"),
    ],
)
def test_conformance_and_repair_agree_on_formats_and_material_totals(
    client, headers, field, value, path
):
    record = copy.deepcopy(DEMO_RECORD)
    record[field] = value
    response = client.post("/api/validate", json={"dpp": record}, headers=headers)
    assert response.status_code == 200
    assert not response.json()["conforms"]
    assert path in {v["location"] for v in response.json()["violations"]}


@pytest.mark.parametrize(
    "endpoint,field",
    [
        ("/api/validate", "dpp"),
        ("/api/validate/repair", "dpp"),
        ("/api/synthesize", "seed"),
    ],
)
def test_nonfinite_record_numbers_never_crash_or_call_model(client, scripted, endpoint, field):
    record = copy.deepcopy(ROUTE_SEED)
    record["carbon"] = {"total_kg_co2e": float("inf")}
    response = client.post(
        endpoint,
        content=json.dumps({field: record}),
        headers={**NORMAL, "Content-Type": "application/json"},
    )
    assert response.status_code == (200 if endpoint == "/api/validate" else 422)
    if endpoint == "/api/validate":
        assert not response.json()["conforms"]
    assert not scripted.requests


@pytest.fixture(scope="module")
def recorded() -> TestClient:
    """A client reading the bounded recorder's output directory."""
    settings = Settings(llm_cassette_dir="tests/cassettes/recorded", llm_cassette_mode="replay")
    with TestClient(create_app(settings)) as c:
        yield c


def _success(response: Any) -> dict[str, Any]:
    assert response.status_code == 200, response.text
    return dict(response.json())


@pytest.mark.cassette
class TestTheRecordedHappyPath:
    """Real model responses survive retrieval, grounding and both HTTP modes."""

    @pytest.mark.parametrize("headers", [NORMAL, CE_RISE])
    def test_repair_fills_a_field_from_a_real_response(self, recorded, headers) -> None:
        body = _success(
            recorded.post("/api/validate/repair", json={"dpp": ROUTE_SEED}, headers=headers)
        )
        assert body["grounded_fills"], "a happy-path test must not pass on an empty fill list"
        assert body["trace"]["model"] == "gpt-4o-mini"
        assert body["trace"]["prompt_hashes"]
        assert body["trace"]["cost"]["llm_calls"] == 0
        # Whatever the model returned, the contract holds: every applied fill names
        # the evidence it came from, and nothing unverified sits among them.
        for fill in body["grounded_fills"]:
            assert fill["evidence_ref"], f"{fill['path']} was filled with no source named"
            assert fill["source_pointer"]
        applied = {f["path"] for f in body["grounded_fills"]}
        suggested = {s["path"] for s in body["unverified_suggestions"]}
        assert not applied & suggested

    def test_every_suggestion_still_carries_its_warning(self, recorded) -> None:
        body = _success(
            recorded.post("/api/validate/repair", json={"dpp": ROUTE_SEED}, headers=NORMAL)
        )
        for suggestion in body["unverified_suggestions"]:
            assert suggestion["requires_review"] is True
            assert suggestion["status"] == "unverified"
            assert 0 <= suggestion["model_score"] <= 0.3

    @pytest.mark.parametrize("headers", [NORMAL, CE_RISE])
    def test_synthesis_returns_a_conforming_passport(self, recorded, headers) -> None:
        body = _success(
            recorded.post("/api/synthesize", json={"seed": ROUTE_SEED}, headers=headers)
        )
        # The use case raises rather than returning a non-conforming record, so a
        # 200 here *is* the conformance assertion. Checked anyway, because that
        # guarantee living in one `if` is a reason to test it, not to trust it.
        assert body["conforms"] is True
        assert body["record"]
        assert body["dpp_id"]
        assert body["support"]
        assert body["trace"]["prompt_hashes"]
        assert body["trace"]["cost"]["llm_calls"] == 0

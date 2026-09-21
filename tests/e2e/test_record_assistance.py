# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Repair and synthesis, over HTTP, in both modes.

These cover the wiring rather than the composing. ``RecordComposer`` is Codex's and
is tested against recorded cassettes in ``tests/unit/llm/``; what was missing until
now was everything between it and a caller — the use case that decides what the
system is willing to hand back, the routes, and the response shape that keeps a
model's guess from being read as evidence.

The cassettes recorded for the composer cannot be replayed through these routes,
and that is not a gap in them: they were recorded against a fixture context pack,
while the route builds its pack from live retrieval. So the model-calling paths are
driven by a stub, and the paths that must refuse *before* spending anything are
driven for real — which is the half that matters most, because a refusal that
happens after the call has already cost what it was meant to save.
"""

from __future__ import annotations

from typing import Any

import pytest
from apps.api.deps import get_llm_request
from apps.api.main import create_app
from apps.api.settings import Settings
from fastapi.testclient import TestClient

from ici_llm.records import (
    GroundedFill,
    RecordIssue,
    RepairResult,
    UnverifiedSuggestion,
    ValueSupport,
)

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
                    confidence=0.4,
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
        assert r.json()["error"] == "capability_unavailable"
        assert "no evidence was found" in r.json()["reason"]

    def test_repair_of_an_unknown_product_is_declined_too(self, client) -> None:
        r = client.post("/api/validate/repair", json={"dpp": UNKNOWN_SEED}, headers=NORMAL)
        assert r.status_code == 422
        assert "no evidence was found" in r.json()["reason"]

    def test_the_refusal_happens_without_touching_the_composer(self, client, stubbed) -> None:
        # The stub records every pack it is handed. If the refusal fired correctly,
        # it was never called — which is the whole point of checking evidence first.
        client.post("/api/synthesize", json={"seed": UNKNOWN_SEED}, headers=NORMAL)
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


@pytest.fixture(scope="module")
def recorded() -> TestClient:
    """A client reading the bounded recorder's output directory."""
    settings = Settings(llm_cassette_dir="tests/cassettes/recorded", llm_cassette_mode="replay")
    with TestClient(create_app(settings)) as c:
        yield c


def _or_skip(response: Any) -> dict[str, Any]:
    if response.status_code == 422 and response.json().get("error") == "model_unavailable":
        pytest.skip("no route cassette recorded yet — run `make record` with a key in .env")
    assert response.status_code == 200, response.text
    return dict(response.json())


class TestTheRecordedHappyPath:
    """The route driven by a real recorded response, once one exists.

    Dormant by design. Until ``make record`` has been run with a key, these skip
    with a message saying so — and a skip is visible in the suite output, where a
    silently-passing stub would not be. Once the cassettes are recorded they lock
    in the one thing the stub cannot: that the *real* model's structured output
    survives the whole path, from retrieval through grounding to the response
    shape, without anyone editing a fixture to make it fit.

    Read from ``tests/cassettes/recorded`` rather than the default directory,
    because that is where the bounded recorder writes and the two sets are kept
    apart on purpose: the default holds hand-built fixtures, and relabelling one as
    a live recording would misrepresent what the model actually returned.
    """

    def test_repair_fills_a_field_from_a_real_response(self, recorded) -> None:
        body = _or_skip(
            recorded.post("/api/validate/repair", json={"dpp": KNOWN_SEED}, headers=NORMAL)
        )
        # Whatever the model returned, the contract holds: every applied fill names
        # the evidence it came from, and nothing unverified sits among them.
        for fill in body["grounded_fills"]:
            assert fill["evidence_ref"], f"{fill['path']} was filled with no source named"
            assert fill["source_pointer"]
        applied = {f["path"] for f in body["grounded_fills"]}
        suggested = {s["path"] for s in body["unverified_suggestions"]}
        assert not applied & suggested

    def test_every_suggestion_still_carries_its_warning(self, recorded) -> None:
        body = _or_skip(
            recorded.post("/api/validate/repair", json={"dpp": KNOWN_SEED}, headers=NORMAL)
        )
        for suggestion in body["unverified_suggestions"]:
            assert suggestion["requires_review"] is True
            assert suggestion["status"] == "unverified"

    def test_synthesis_returns_a_conforming_passport(self, recorded) -> None:
        body = _or_skip(recorded.post("/api/synthesize", json={"seed": KNOWN_SEED}, headers=NORMAL))
        # The use case raises rather than returning a non-conforming record, so a
        # 200 here *is* the conformance assertion. Checked anyway, because that
        # guarantee living in one `if` is a reason to test it, not to trust it.
        assert body["conforms"] is True
        assert body["record"]
        assert body["dpp_id"]

"""Opt-in, capped checks of real model responses through the HTTP routes."""

from __future__ import annotations

import json

import pytest
from apps.api.main import create_app
from apps.api.settings import Settings
from fastapi.testclient import TestClient
from tests.llm_recording_cases import ROUTE_SEED
from tooling.record_llm import BoundedRecorder

from ici_llm.transport import OpenAITransport

BATTERY_QUESTION = "What is the declared capacity of the BMZ Group e-Bike LMT 36V-14Ah battery?"


@pytest.mark.live
def test_live_model_answers_and_record_assistance_over_http(tmp_path):
    settings = Settings(llm_cassette_mode="live", llm_model_default="gpt-4o-mini")
    assert settings.openai_api_key, (
        "Set OPENAI_API_KEY in .env or the environment before --run-live"
    )

    # One cumulative ceiling across all routes, recorded before each network attempt.
    # This is a reservation estimate, not an assertion about actual provider billing.
    recorder = BoundedRecorder(
        OpenAITransport(api_key=settings.openai_api_key),
        tmp_path / "live-attempts.json",
        max_calls=12,
        max_reserved_usd=0.15,
    )
    observed = {}
    with TestClient(create_app(settings)) as client:
        for bundle in client.app.state.registry.bundles.values():
            bundle.llm.transport = recorder

        single = client.post(
            "/api/single-dpp/ask",
            json={
                "q": "What is the declared capacity?",
                "content": json.dumps(
                    {"product": "Synthetic battery", "declared_capacity": "60 kWh"}
                ),
                "tau": 0,
            },
            headers={"X-Backend-Mode": "normal"},
        )
        observed["single_dpp"] = (single.status_code, single.json())

        for model in ("gpt-4o-mini", "gpt-5"):
            search = client.post(
                "/api/search",
                json={"q": BATTERY_QUESTION, "tau": 0, "top_k_documents": 2},
                headers={"X-Backend-Mode": "ce-rise", "X-Model": model},
            )
            observed[f"ce_rise_{model}"] = (search.status_code, search.json())

        repair = client.post(
            "/api/validate/repair",
            json={"dpp": ROUTE_SEED, "suggest_from_training": True},
            headers={"X-Backend-Mode": "normal"},
        )
        observed["repair"] = (repair.status_code, repair.json())

        synthesis = client.post(
            "/api/synthesize",
            json={"seed": ROUTE_SEED},
            headers={"X-Backend-Mode": "normal"},
        )
        observed["synthesis"] = (synthesis.status_code, synthesis.json())

    for name in ("single_dpp", "ce_rise_gpt-4o-mini", "ce_rise_gpt-5"):
        status, body = observed[name]
        assert status == 200, (name, status, body)
        assert body["decision"] == "answer", (name, body.get("abstain_reason"))
        assert body["grounding"]["verdict"] == "fully_grounded", name
    assert "60 kWh" in observed["single_dpp"][1]["answer"]
    for name in ("ce_rise_gpt-4o-mini", "ce_rise_gpt-5"):
        assert "14 Ah" in observed[name][1]["answer"]

    repair_status, repaired = observed["repair"]
    assert repair_status == 200, (repair_status, repaired)
    assert repaired["conforms"] is True
    assert repaired["grounded_fills"]
    assert all(item["evidence_id"] for item in repaired["grounded_fills"])
    assert all(item["requires_review"] for item in repaired["unverified_suggestions"])

    synthesis_status, synthesized = observed["synthesis"]
    assert synthesis_status == 200, (synthesis_status, synthesized)
    assert synthesized["conforms"] is True
    assert synthesized["support"]
    assert len(recorder.events) >= 7
    assert all(event["status"] == "recorded" for event in recorder.events)

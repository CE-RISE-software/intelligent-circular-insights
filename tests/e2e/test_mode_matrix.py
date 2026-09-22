"""Exercise the actual HTTP → request runtime → transport seam, entirely offline."""

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest
from apps.api.bundles import BundleRegistry, build_registry
from apps.api.main import create_app
from apps.api.settings import Settings
from fastapi.testclient import TestClient
from pydantic import ValidationError
from tests.unit.llm.conftest import chat, claim_result, response

from ici_core.domain.modes import BackendMode
from ici_llm.cassettes import CassetteTransport
from ici_llm.errors import CassetteCorrupt
from ici_llm.prompts import PromptRegistry
from ici_llm.provider import CassetteProvider, OpenAIProvider
from ici_llm.transport import OpenAITransport, TransportResult


@pytest.fixture
def mode():
    return BackendMode.NORMAL


class OfflineTransport:
    def __init__(self):
        self.requests = []

    def send(self, request):
        self.requests.append(request)
        if request.prompt_id.startswith("ici.compose"):
            return TransportResult(chat())
        content = json.dumps(claim_result())
        return TransportResult(
            response(content) if request.endpoint == "responses" else chat(content)
        )


@pytest.fixture
def http(monkeypatch, bundle):
    clients = []

    def create(*, settings=None, provider=None):
        transport = OfflineTransport()
        provider = provider or OpenAIProvider(transport)
        registry = BundleRegistry({m: replace(bundle, mode=m, llm=provider) for m in BackendMode})
        monkeypatch.setattr("apps.api.main.build_registry", lambda *_: registry)
        client = TestClient(create_app(settings or Settings()))
        client.__enter__()
        clients.append(client)
        return client, transport, provider

    yield create
    for client in reversed(clients):
        client.__exit__(None, None, None)


def test_llm_mode_selects_the_system_prompt_actually_sent_and_traced(http):
    client, transport, _ = http()
    hashes = []
    for mode, prompt_name in [("normal", "compose"), ("ce-rise", "compose_ce_rise")]:
        r = client.post(
            "/api/search",
            json={"q": "What is the declared capacity?"},
            headers={"X-Backend-Mode": mode, "X-Correlation-Id": mode},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["decision"] == "answer"
        assert body["mode"] == r.headers["X-Backend-Mode-Used"] == mode
        sent = transport.requests[-2]
        prompt = PromptRegistry().render(prompt_name)
        assert sent.kwargs["messages"][0] == {"role": "system", "content": prompt.text}
        assert sent.prompt_id == prompt.id
        assert sent.prompt_hash in body["trace"]["prompt_hashes"]
        assert body["trace"]["correlation_id"] == mode
        assert len(body["trace"]["prompt_hashes"]) == 3
        assert body["trace"]["cost"]["llm_calls"] == 2
        assert any(s["name"] == "guard" for s in body["trace"]["steps"])
        hashes.append(sent.prompt_hash)
    assert hashes[0] != hashes[1]
    assert "mounted substrates are authoritative" in prompt.text
    assert "abstain rather than soften" in prompt.text
    assert "without repeating the product name or its unrelated" in prompt.text


@pytest.mark.parametrize("model", ["gpt-4o-mini", "gpt-5", "unknown"])
def test_llm_model_header_reaches_both_composition_and_grounding(http, model):
    client, transport, _ = http()
    r = client.post(
        "/api/search", json={"q": "What is the declared capacity?"}, headers={"X-Model": model}
    )
    selected = "gpt-4o-mini" if model == "unknown" else model
    assert r.status_code == 200
    assert r.headers["X-Model-Used"] == r.json()["trace"]["model"] == selected
    assert {req.kwargs["model"] for req in transport.requests} == {selected}


def test_llm_mode_fallback_uses_normal_prompt_not_an_untrusted_header(http):
    client, transport, _ = http()
    r = client.post(
        "/api/search",
        json={"q": "What is the declared capacity?"},
        headers={"X-Backend-Mode": "not-a-mode"},
    )
    assert r.status_code == 200
    assert r.headers["X-Backend-Mode-Used"] == "normal"
    assert transport.requests[0].prompt_id == "ici.compose@1"


def test_llm_parallel_requests_have_independent_mode_model_budget_and_audit(http):
    client, transport, source = http()

    def run(i):
        mode, model = ("normal", "gpt-4o-mini") if i % 2 else ("ce-rise", "gpt-5")
        r = client.post(
            "/api/search",
            json={"q": "What is the declared capacity?"},
            headers={"X-Backend-Mode": mode, "X-Model": model},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["mode"] == mode
        assert body["trace"]["model"] == model
        assert body["trace"]["cost"]["llm_calls"] == 2
        assert len(body["trace"]["prompt_hashes"]) == 3
        llm_steps = [json.loads(s["detail"]) for s in body["trace"]["steps"] if s["name"] == "llm"]
        expected = "ici.compose@1" if mode == "normal" else "ici.compose.ce_rise@2"
        assert llm_steps[0]["prompt_id"] == expected

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(run, range(12)))
    assert len(transport.requests) == 24
    assert source.audit.steps == []
    assert source.budget.calls == 0


def test_llm_repeated_cassette_misses_never_exhaust_a_shared_budget(http, tmp_path):
    client, _, source = http(provider=CassetteProvider(tmp_path))
    for _ in range(12):
        r = client.post("/api/search", json={"q": "What is the declared capacity?"})
        assert r.status_code == 422
        assert r.json()["error"] == "model_unavailable"
        assert r.json()["mode"] == r.headers["X-Backend-Mode-Used"] == "normal"
    assert source.budget.calls == 0


def test_llm_corrupt_cassette_declines_without_leaking_internal_details(http):
    class CorruptTransport:
        def send(self, request):
            raise CassetteCorrupt("private filesystem path")

    client, _, _ = http(provider=OpenAIProvider(CorruptTransport()))
    r = client.post("/api/search", json={"q": "capacity"}, headers={"X-Backend-Mode": "ce-rise"})
    assert r.status_code == 422
    assert r.json()["mode"] == r.headers["X-Backend-Mode-Used"] == "ce-rise"
    assert "Restore the reviewed cassette" in r.json()["reason"]
    assert "private filesystem" not in r.text


def test_llm_disabled_declines_without_a_call_but_validation_still_works(http):
    client, transport, _ = http(settings=Settings(llm_disabled=True))
    r = client.post("/api/search", json={"q": "What is the declared capacity?"})
    assert r.status_code == 422
    assert "disabled" in r.json()["reason"]
    assert transport.requests == []
    assert client.post("/api/validate", json={"dpp": {}}).status_code == 200


def test_search_uses_the_deployment_threshold_and_accepts_zero_override(http):
    client, _, _ = http(settings=Settings(default_tau=0.95))
    first = client.post("/api/search", json={"q": "capacity"}).json()
    assert first["operating_point"]["tau"] == 0.95
    assert first["decision"] == "abstain"
    second = client.post("/api/search", json={"q": "capacity", "tau": 0}).json()
    assert second["operating_point"]["tau"] == 0
    assert second["decision"] == "answer"


@pytest.mark.parametrize(
    "payload",
    [
        {"q": "   "},
        {"q": "\n\t"},
        {"q": "capacity", "tau": -0.1},
        {"q": "capacity", "tau": 1.1},
        {"q": "capacity", "tau": "NaN"},
        {"q": "capacity", "top_k_documents": -1},
        {"q": "capacity", "top_k_memory": 101},
    ],
)
def test_invalid_search_input_returns_422_before_any_model_call(http, payload):
    client, transport, _ = http()
    r = client.post("/api/search", json=payload)
    assert r.status_code == 422
    assert r.headers["X-Backend-Mode-Used"] == "normal"
    assert not transport.requests


@pytest.mark.parametrize("cassette_mode", ["live", "record", "replay"])
def test_llm_bundle_honors_settings_without_instantiating_an_sdk_client(cassette_mode, tmp_path):
    settings = Settings(
        llm_cassette_mode=cassette_mode,
        llm_cassette_dir=str(tmp_path),
        llm_model_default="gpt-5",
        openai_api_key="synthetic-not-a-secret",
    )
    source = build_registry((BackendMode.NORMAL,), settings).for_mode(BackendMode.NORMAL).llm
    assert source.router.default == "gpt-5"
    transport = source.transport
    if cassette_mode != "live":
        assert isinstance(transport, CassetteTransport)
        assert transport.mode == cassette_mode
        transport = transport.live
    assert isinstance(transport, OpenAITransport)
    assert transport.redaction_key == "synthetic-not-a-secret"
    assert transport._client is None


def test_invalid_cassette_mode_fails_at_configuration_boundary():
    with pytest.raises(ValidationError):
        Settings(llm_cassette_mode="typo")

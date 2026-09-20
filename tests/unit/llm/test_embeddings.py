import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest

from ici_llm.embeddings import (
    CachedEmbeddings,
    EmbeddingProvider,
    MiniLMEmbeddings,
    OpenAIEmbeddings,
)
from ici_llm.errors import InvalidOutput, Unavailable
from ici_llm.provider import OpenAIProvider
from ici_llm.transport import TransportResult


class FakeArray:
    def __init__(self, rows):
        self.rows = rows

    def tolist(self):
        return self.rows


class LocalModel:
    def __init__(self):
        self.calls = []

    def get_sentence_embedding_dimension(self):
        return 384

    def encode(self, texts, **options):
        self.calls.append((texts, options))
        return FakeArray([[len(t) / 1000] * 384 for t in texts])


class EmbeddingTransport:
    def __init__(self):
        self.calls = []

    def send(self, request):
        self.calls.append(request)
        return TransportResult(
            {
                "data": [
                    {"index": i, "embedding": [len(t) / 1000] * request.kwargs["dimensions"]}
                    for i, t in enumerate(request.kwargs["input"])
                ],
                "usage": {"prompt_tokens": 2},
            }
        )


@pytest.fixture(params=["local", "openai"])
def backend(request):
    if request.param == "local":
        model = LocalModel()
        return MiniLMEmbeddings(_model=model, revision="test-commit"), model.calls
    transport = EmbeddingTransport()
    provider = OpenAIProvider(transport, embedding_dimensions=384)
    return OpenAIEmbeddings(provider, index_dimensions=384), transport.calls


@pytest.mark.contract
def test_backends_share_batch_cache_order_persistence_contract(tmp_path, backend):
    engine, calls = backend
    path = tmp_path / "vectors.sqlite"
    with CachedEmbeddings(engine, path, index_dimensions=384, batch_size=2) as cache:
        assert cache.embed([]) == []
        first = cache.embed(["one", "second", "one", "third"])
        assert len(first) == 4 and all(len(v) == 384 for v in first)
        assert first[0] == first[2] and first[0] != first[1]
        assert len(calls) == 2
        assert cache.embed(["second", "one"]) == [first[1], first[0]]
        assert len(calls) == 2
    with CachedEmbeddings(engine, path, index_dimensions=384) as cache:
        assert cache.embed(["one"])[0] == first[0]
        assert len(calls) == 2
        first[0][0] = 900
        assert cache.embed(["one"])[0][0] != 900
    assert b"second" not in path.read_bytes()


@pytest.mark.contract
def test_mismatch_fails_before_any_call(tmp_path, backend):
    engine, calls = backend
    with pytest.raises(ValueError, match="dimension"):
        CachedEmbeddings(engine, tmp_path / "cache", index_dimensions=1536)
    assert not calls
    with pytest.raises(ValueError):
        MiniLMEmbeddings(index_dimensions=1536)
    with pytest.raises(ValueError):
        OpenAIEmbeddings(OpenAIProvider(), index_dimensions=384)


def test_cache_identity_prevents_same_dimension_model_contamination(tmp_path):
    path = tmp_path / "cache"
    with CachedEmbeddings(
        MiniLMEmbeddings(_model=LocalModel(), revision="one"), path, index_dimensions=384
    ):
        pass
    with pytest.raises(ValueError, match="different model"):
        CachedEmbeddings(
            MiniLMEmbeddings(_model=LocalModel(), revision="two"), path, index_dimensions=384
        )


@pytest.mark.parametrize("value", [[0.0], [float("nan")] * 384, [True] * 384])
def test_corrupt_cached_vectors_fail_closed(tmp_path, value):
    path = tmp_path / "cache"
    with CachedEmbeddings(
        MiniLMEmbeddings(_model=LocalModel()), path, index_dimensions=384
    ) as cache:
        cache.embed(["one"])
        with sqlite3.connect(path) as db:
            db.execute("UPDATE vectors SET value=?", (json.dumps(value),))
        with pytest.raises(InvalidOutput):
            cache.embed(["one"])


def test_threads_do_not_duplicate_embedding_calls(tmp_path):
    model = LocalModel()
    with CachedEmbeddings(
        MiniLMEmbeddings(_model=model), tmp_path / "cache", index_dimensions=384
    ) as cache:
        with ThreadPoolExecutor(4) as pool:
            vectors = list(pool.map(lambda _: cache.embed(["same text"]), range(8)))
        assert all(v == vectors[0] for v in vectors) and len(model.calls) == 1
        wrapper = EmbeddingProvider(OpenAIProvider(), cache)
        assert wrapper.embed(["same text"]) == vectors[0]
        with pytest.raises(ValueError):
            cache.embed([""])


def test_missing_local_dependency_fails_without_fake_vectors(monkeypatch):
    def unavailable(name):
        raise ImportError(name)

    monkeypatch.setattr("ici_llm.embeddings.importlib.import_module", unavailable)
    with pytest.raises(Unavailable):
        MiniLMEmbeddings()


def test_embedding_calls_do_not_overwrite_composition_model_in_trace():
    provider = OpenAIProvider(EmbeddingTransport(), embedding_dimensions=384)
    provider.audit.model = "gpt-5"
    provider.embed(["one"])
    assert provider.audit.model == "gpt-5"
    assert provider.audit.cost.usd > 0


def test_backend_factory_keeps_minilm_default(monkeypatch):
    from ici_llm.embeddings import load_embeddings

    local = MiniLMEmbeddings(_model=LocalModel())
    monkeypatch.setattr("ici_llm.embeddings.MiniLMEmbeddings", lambda **kwargs: local)
    assert load_embeddings() is local
    with pytest.raises(ValueError):
        load_embeddings(backend="unknown")
    with pytest.raises(ValueError):
        load_embeddings(backend="openai")

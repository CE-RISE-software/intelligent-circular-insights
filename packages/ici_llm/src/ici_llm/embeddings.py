# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Dimension-checked backends and a content-addressed, model-bound SQLite cache."""

from __future__ import annotations

import hashlib
import importlib
import json
import math
import sqlite3
import threading
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Protocol

from ici_core.domain.evidence import ContextPack
from ici_core.ports import LLMProvider
from ici_llm.errors import InvalidOutput, Unavailable
from ici_llm.prompts import canonical
from ici_llm.provider import OpenAIProvider


class EmbeddingBackend(Protocol):
    @property
    def dimensions(self) -> int: ...
    @property
    def identity(self) -> str: ...
    def embed(self, texts: Sequence[str]) -> Sequence[Sequence[float]]: ...


def _vectors(rows: Sequence[Sequence[float]], count: int, dimensions: int) -> list[list[float]]:
    if len(rows) != count:
        raise InvalidOutput("Embedding batch size does not match the input.")
    result: list[list[float]] = []
    for row in rows:
        if len(row) != dimensions or any(
            isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
            for v in row
        ):
            raise InvalidOutput("Embedding dimensions or values are invalid.")
        result.append([float(v) for v in row])
    return result


def _inputs(texts: Sequence[str]) -> None:
    if any(not isinstance(t, str) or not t.strip() for t in texts):
        raise ValueError("embedding inputs must be nonempty strings")


class OpenAIEmbeddings:
    def __init__(self, provider: OpenAIProvider, *, index_dimensions: int = 1536) -> None:
        self.provider = provider
        self.dimensions = provider.embedding_dimensions
        self.identity = f"openai:{provider.embedding_model}:{self.dimensions}:float:v1"
        if self.dimensions != index_dimensions:
            raise ValueError("embedding dimensions do not match the index")

    def embed(self, texts: Sequence[str]) -> Sequence[Sequence[float]]:
        return self.provider.embed(texts)


class MiniLMEmbeddings:
    """Local-only by default: missing dependencies/weights fail, never random vectors.

    Cache identity includes the resolved Hugging Face commit, not the mutable main
    alias. Downloads require an explicit local_files_only=False configuration.
    """

    def __init__(
        self,
        *,
        index_dimensions: int = 384,
        batch_size: int = 32,
        revision: str = "main",
        local_files_only: bool = True,
        _model: Any = None,
    ) -> None:
        if index_dimensions != 384 or batch_size < 1:
            raise ValueError("MiniLM requires a 384-dimensional index and a positive batch size")
        self.dimensions, self.batch_size = 384, batch_size
        name = "sentence-transformers/all-MiniLM-L6-v2"
        if _model is None:
            try:
                hub = importlib.import_module("huggingface_hub")
                location = hub.snapshot_download(
                    name, revision=revision, local_files_only=local_files_only
                )
                resolved = Path(location).name
                library = importlib.import_module("sentence_transformers")
                _model = library.SentenceTransformer(
                    location, device="cpu", local_files_only=True, trust_remote_code=False
                )
            except (ImportError, OSError, ValueError):
                raise Unavailable(
                    "MiniLM dependencies or cached weights are unavailable."
                ) from None
        else:
            resolved = revision
        if _model.get_sentence_embedding_dimension() != self.dimensions:
            raise ValueError("loaded MiniLM dimensions do not match the index")
        self.identity = f"minilm:{name}:{resolved}:384:normalized:v1"
        self._model = _model

    def embed(self, texts: Sequence[str]) -> Sequence[Sequence[float]]:
        _inputs(texts)
        if not texts:
            return []
        values = self._model.encode(
            list(texts),
            batch_size=self.batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return _vectors(values.tolist(), len(texts), self.dimensions)


def load_embeddings(
    *,
    index_dimensions: int = 384,
    backend: str = "minilm",
    provider: OpenAIProvider | None = None,
) -> EmbeddingBackend:
    """Composition-root factory; the legacy local MiniLM backend stays the default."""
    if backend == "minilm":
        return MiniLMEmbeddings(index_dimensions=index_dimensions)
    if backend == "openai" and provider is not None:
        return OpenAIEmbeddings(provider, index_dimensions=index_dimensions)
    raise ValueError("unknown backend or missing explicit OpenAI provider")


class CachedEmbeddings:
    """One cache file per immutable backend identity. No raw text is stored.

    Batches commit atomically; failed batches do not persist partial vectors.
    A process-local lock also prevents duplicate calls from concurrent threads.
    Separate processes may duplicate computation, but cannot corrupt the cache.
    """

    def __init__(
        self, backend: EmbeddingBackend, path: Path, *, index_dimensions: int, batch_size: int = 32
    ) -> None:
        if backend.dimensions != index_dimensions or index_dimensions < 1 or batch_size < 1:
            raise ValueError("embedding dimensions/batch size do not match index configuration")
        self.backend, self.dimensions, self.identity = backend, backend.dimensions, backend.identity
        self.batch_size = batch_size
        self._lock = threading.RLock()
        path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(path, check_same_thread=False)
        try:
            with self._db:
                self._db.execute(
                    "CREATE TABLE IF NOT EXISTS metadata "
                    "(id INTEGER PRIMARY KEY, value TEXT NOT NULL)"
                )
                self._db.execute(
                    "CREATE TABLE IF NOT EXISTS vectors "
                    "(hash TEXT PRIMARY KEY, value TEXT NOT NULL)"
                )
                expected = canonical(
                    {"identity": self.identity, "dimensions": self.dimensions, "version": 1}
                )
                self._db.execute("INSERT OR IGNORE INTO metadata VALUES (1, ?)", (expected,))
                if (
                    self._db.execute("SELECT value FROM metadata WHERE id=1").fetchone()[0]
                    != expected
                ):
                    raise ValueError(
                        "embedding cache belongs to a different model, revision or dimension"
                    )
        except Exception:
            self._db.close()
            raise

    def embed(self, texts: Sequence[str]) -> Sequence[Sequence[float]]:
        _inputs(texts)
        with self._lock:
            keys = [hashlib.sha256(text.encode("utf-8")).hexdigest() for text in texts]
            vectors: dict[str, list[float]] = {}
            missing: dict[str, str] = {}
            for key, text in zip(keys, texts, strict=True):
                if key in vectors or key in missing:
                    continue
                row = self._db.execute("SELECT value FROM vectors WHERE hash=?", (key,)).fetchone()
                if row:
                    try:
                        vectors[key] = _vectors([json.loads(row[0])], 1, self.dimensions)[0]
                    except (ValueError, TypeError):
                        raise InvalidOutput(
                            "The embedding cache contains an invalid vector."
                        ) from None
                else:
                    missing[key] = text
            pending = list(missing.items())
            for offset in range(0, len(pending), self.batch_size):
                batch = pending[offset : offset + self.batch_size]
                values = _vectors(
                    self.backend.embed([text for _, text in batch]), len(batch), self.dimensions
                )
                with self._db:
                    for (key, _), value in zip(batch, values, strict=True):
                        self._db.execute(
                            "INSERT OR IGNORE INTO vectors VALUES (?, ?)", (key, canonical(value))
                        )
                        vectors[key] = value
            return [list(vectors[key]) for key in keys]

    def close(self) -> None:
        with self._lock:
            self._db.close()

    def __enter__(self) -> CachedEmbeddings:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


class EmbeddingProvider:
    """Swap embedding backends without changing the frozen LLMProvider port."""

    def __init__(self, provider: LLMProvider, embeddings: EmbeddingBackend) -> None:
        self.provider, self.embeddings = provider, embeddings

    def compose(
        self,
        instruction: str,
        pack: ContextPack,
        *,
        model: str | None = None,
        max_tokens: int = 512,
    ) -> str:
        return self.provider.compose(instruction, pack, model=model, max_tokens=max_tokens)

    def structured(
        self,
        instruction: str,
        pack: ContextPack,
        schema: Mapping[str, Any],
        *,
        model: str | None = None,
    ) -> Mapping[str, Any]:
        return self.provider.structured(instruction, pack, schema, model=model)

    def embed(self, texts: Sequence[str]) -> Sequence[Sequence[float]]:
        return self.embeddings.embed(texts)

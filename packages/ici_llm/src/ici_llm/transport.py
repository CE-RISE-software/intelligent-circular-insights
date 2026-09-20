# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""One explicit live boundary; replay never instantiates an OpenAI client."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Protocol

from openai import APIConnectionError, APIStatusError, OpenAI, RateLimitError

from ici_llm.errors import RateLimited, Unavailable
from ici_llm.prompts import canonical


@dataclass(frozen=True)
class Request:
    endpoint: str
    kwargs: dict[str, Any]
    prompt_id: str = ""
    prompt_hash: str = ""

    @property
    def key(self) -> str:
        material = {
            "version": 1,
            "endpoint": self.endpoint,
            "kwargs": self.kwargs,
            "prompt_id": self.prompt_id,
            "prompt_hash": self.prompt_hash,
        }
        return hashlib.sha256(canonical(material).encode()).hexdigest()


@dataclass(frozen=True)
class TransportResult:
    response: dict[str, Any]
    replayed: bool = False


class Transport(Protocol):
    def send(self, request: Request) -> TransportResult: ...


class OpenAITransport:
    """Constructing this object is cheap; sending explicitly permits live I/O.

    SDK retries are disabled so a single transport invocation cannot hide extra
    charged attempts. Application retry policy is a later Sprint 4 deliverable.
    """

    def __init__(self, *, api_key: str = "", client: OpenAI | None = None) -> None:
        self._api_key = api_key
        self._client = client

    @property
    def redaction_key(self) -> str:
        return self._client.api_key if self._client else self._api_key

    def send(self, request: Request) -> TransportResult:
        if request.endpoint not in {"chat", "responses", "embeddings"}:
            raise ValueError("unsupported endpoint")
        if self._client is None:
            if not self._api_key:
                raise Unavailable("No OpenAI credentials were configured.")
            self._client = OpenAI(api_key=self._api_key, max_retries=0, timeout=30.0)
        client = self._client.with_options(max_retries=0, timeout=30.0)
        try:
            if request.endpoint == "chat":
                response = client.chat.completions.create(**request.kwargs)
            elif request.endpoint == "responses":
                response = client.responses.create(**request.kwargs)
            else:
                response = client.embeddings.create(**request.kwargs)
        except RateLimitError:
            raise RateLimited("The model provider rate limit was reached.") from None
        except APIConnectionError:
            raise Unavailable("The model provider could not be reached.") from None
        except APIStatusError as exc:
            raise Unavailable(f"The model provider returned HTTP {exc.status_code}.") from None
        return TransportResult(response.model_dump(mode="json"))

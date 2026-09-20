# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Implement the frozen LLMProvider port over a replaceable transport."""

from __future__ import annotations

import hashlib
import json
import math
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, ValidationError
from referencing import Registry
from referencing.exceptions import Unresolvable

from ici_core.domain.evidence import ContextPack
from ici_llm.audit import AuditLog
from ici_llm.budget import RequestBudget
from ici_llm.compat import grounded_chat_kwargs, structured_options
from ici_llm.errors import InvalidOutput, Refused, Truncated
from ici_llm.prompts import PromptRegistry, canonical, evidence_json
from ici_llm.routing import ModelRouter
from ici_llm.transport import OpenAITransport, Request, Transport, TransportResult


def validate_object(value: Any, schema: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InvalidOutput("Structured output must be a JSON object.")
    try:
        canonical(value)
    except (ValueError, TypeError):
        raise InvalidOutput("Structured output must contain only finite JSON values.") from None
    try:
        # An empty registry rejects external $refs instead of fetching them.
        Draft202012Validator(dict(schema), registry=Registry()).validate(value)
    except (ValidationError, Unresolvable):
        raise InvalidOutput("Structured output does not match the requested schema.") from None
    return value


def _json_object(text: str) -> dict[str, Any]:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON member")
            result[key] = value
        return result

    def reject_constant(_: str) -> None:
        raise ValueError("nonfinite JSON number")

    try:
        value = json.loads(text, object_pairs_hook=unique, parse_constant=reject_constant)
        canonical(value)  # Also rejects overflowing exponents such as 1e400.
    except (TypeError, ValueError):
        raise InvalidOutput("The provider returned malformed JSON.") from None
    if not isinstance(value, dict):
        raise InvalidOutput("Structured output must be a JSON object.")
    return value


def _chat_text(response: dict[str, Any]) -> str:
    choices = response.get("choices") or []
    if len(choices) != 1:
        raise InvalidOutput("Expected exactly one completion.")
    choice = choices[0]
    message = choice.get("message") or {}
    finish = choice.get("finish_reason")
    if message.get("refusal") or finish == "content_filter":
        raise Refused("The model declined to answer this request.")
    if finish == "length":
        raise Truncated("The completion reached its token limit.")
    if finish != "stop":
        raise InvalidOutput("The completion did not finish normally.")
    text = message.get("content")
    if not isinstance(text, str) or not text.strip():
        raise InvalidOutput("The provider returned no answer text.")
    return text.strip()


def _response_text(response: dict[str, Any]) -> str:
    pieces: list[str] = []
    for item in response.get("output") or []:
        if item.get("type") != "message":
            continue
        for part in item.get("content") or []:
            if part.get("type") == "refusal":
                raise Refused("The model declined to answer this request.")
            if part.get("type") == "output_text" and isinstance(part.get("text"), str):
                pieces.append(part["text"])
    reason = (response.get("incomplete_details") or {}).get("reason")
    if response.get("status") == "incomplete" and reason == "max_output_tokens":
        raise Truncated("The response reached its token limit.")
    if reason == "content_filter":
        raise Refused("The model declined to answer this request.")
    if response.get("status") != "completed":
        raise InvalidOutput("The response did not complete.")
    text = "".join(pieces).strip()
    if not text:
        raise InvalidOutput("The provider returned no answer text.")
    return text


class OpenAIProvider:
    """Use per request when supplying a budget or audit log; see LLMRuntime.

    Direct construction permits live calls. Use CassetteProvider for test runs.
    Configuration is supplied by the composition root, never read from env here.
    """

    def __init__(
        self,
        transport: Transport | None = None,
        *,
        api_key: str = "",
        router: ModelRouter | None = None,
        prompts: PromptRegistry | None = None,
        audit: AuditLog | None = None,
        budget: RequestBudget | None = None,
        structured_max_tokens: int = 4096,
        embedding_model: str = "text-embedding-3-small",
        embedding_dimensions: int = 1536,
    ) -> None:
        self.transport = transport if transport is not None else OpenAITransport(api_key=api_key)
        self.router = router or ModelRouter()
        self.prompts = prompts or PromptRegistry()
        self.audit = audit or AuditLog()
        self.budget = budget or RequestBudget()
        self.structured_max_tokens = structured_max_tokens
        self.embedding_model = embedding_model
        self.embedding_dimensions = embedding_dimensions
        if structured_max_tokens < 1 or embedding_dimensions < 1:
            raise ValueError("token and dimension limits must be positive")

    def compose(
        self,
        instruction: str,
        pack: ContextPack,
        *,
        model: str | None = None,
        max_tokens: int = 512,
    ) -> str:
        if max_tokens < 1:
            raise ValueError("max_tokens must be positive")
        resolved = self.router.resolve(model)
        request = self._request(
            "compose",
            instruction,
            pack,
            resolved,
            "chat",
            grounded_chat_kwargs(resolved, 0.0, max_tokens),
        )
        return self._complete(request)

    def structured(
        self,
        instruction: str,
        pack: ContextPack,
        schema: Mapping[str, Any],
        *,
        model: str | None = None,
    ) -> Mapping[str, Any]:
        Draft202012Validator.check_schema(dict(schema))
        resolved = self.router.resolve(model)
        endpoint, options = structured_options(resolved, self.structured_max_tokens)
        request = self._request(
            "structured", instruction, pack, resolved, endpoint, options, schema
        )
        text = self._complete(request)
        try:
            value = validate_object(_json_object(text), schema)
        except InvalidOutput:
            self.audit.guard("structured_schema", False)
            raise
        self.audit.guard("structured_schema", True)
        return value

    def embed(self, texts: Sequence[str]) -> Sequence[Sequence[float]]:
        if not texts:
            return []
        if any(not isinstance(text, str) or not text.strip() for text in texts):
            raise ValueError("embedding inputs must be nonempty strings")
        request = Request(
            "embeddings",
            {
                "model": self.embedding_model,
                "input": list(texts),
                "encoding_format": "float",
                "dimensions": self.embedding_dimensions,
            },
        )
        result = self._send(request)
        rows = result.response.get("data") or []
        try:
            rows = sorted(rows, key=lambda row: row["index"])
            if [row["index"] for row in rows] != list(range(len(texts))):
                raise ValueError("missing or duplicate embedding")
            vectors = [row["embedding"] for row in rows]
            for vector in vectors:
                if len(vector) != self.embedding_dimensions or any(
                    isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x)
                    for x in vector
                ):
                    raise ValueError("invalid dimensions or values")
        except (KeyError, TypeError, ValueError):
            raise InvalidOutput("The provider returned invalid embedding vectors.") from None
        return vectors

    def _request(
        self,
        name: str,
        instruction: str,
        pack: ContextPack,
        model: str,
        endpoint: str,
        options: dict[str, Any],
        schema: Mapping[str, Any] | None = None,
    ) -> Request:
        if name == "structured" and schema and schema.get("x-ici-unverified-suggestions") is True:
            name = "structured_suggestions"
        prompt = self.prompts.render(name)
        payload: dict[str, Any] = {
            "instruction": instruction,
            "context": json.loads(evidence_json(pack)),
        }
        if schema is not None:
            payload["schema"] = dict(schema)
        messages = [
            {"role": "system", "content": prompt.text},
            {"role": "user", "content": canonical(payload)},
        ]
        digest = hashlib.sha256(
            canonical({"id": prompt.id, "messages": messages}).encode()
        ).hexdigest()
        return Request(
            endpoint,
            {
                "model": model,
                "input" if endpoint == "responses" else "messages": messages,
                **options,
            },
            prompt.id,
            digest,
        )

    def _complete(self, request: Request) -> str:
        result = self._send(request)
        try:
            text = (
                _chat_text(result.response)
                if request.endpoint == "chat"
                else _response_text(result.response)
            )
        except (Refused, Truncated, InvalidOutput) as exc:
            self.audit.guard(type(exc).__name__, False)
            raise
        self.audit.guard("complete_response", True)
        return text

    def _send(self, request: Request) -> TransportResult:
        self.budget.reserve(request)
        start = time.perf_counter()
        result = None
        status = "ok"
        try:
            result = self.transport.send(request)
            return result
        except Exception as exc:
            status = type(exc).__name__
            raise
        finally:
            self.audit.record(request, result, (time.perf_counter() - start) * 1000, status)


class CassetteProvider(OpenAIProvider):
    """The same port with record/replay below prompt rendering and validation."""

    def __init__(
        self,
        directory: str | Path,
        *,
        mode: str = "replay",
        provider: OpenAIProvider | None = None,
        secrets: tuple[str, ...] = (),
    ) -> None:
        from ici_llm.cassettes import CassetteTransport

        source = provider or OpenAIProvider()
        if isinstance(source.transport, OpenAITransport):
            secrets = (*secrets, source.transport.redaction_key)
        super().__init__(
            CassetteTransport(Path(directory), mode=mode, live=source.transport, secrets=secrets),
            router=source.router,
            prompts=source.prompts,
            audit=source.audit,
            budget=source.budget,
            structured_max_tokens=source.structured_max_tokens,
            embedding_model=source.embedding_model,
            embedding_dimensions=source.embedding_dimensions,
        )

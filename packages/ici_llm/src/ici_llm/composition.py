# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Guarded candidate composition; the core still verifies every final claim."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ici_core.domain.errors import GenerationError
from ici_core.domain.evidence import ContextPack
from ici_core.ports import LLMProvider
from ici_llm.audit import AuditLog
from ici_llm.errors import Refused
from ici_llm.guards import (
    AnswerHint,
    asks_unsupported_requirement,
    grounded_hint,
    invalid_evidence_citations,
    looks_like_header_copy,
    misses_reliable_hint,
)


@dataclass(frozen=True)
class GroundedPrompt:
    question: str
    pack: ContextPack
    hint: AnswerHint = AnswerHint()


@dataclass(frozen=True)
class Composition:
    answer: str
    used_fallback: bool = False


class GroundedComposer:
    def __init__(self, provider: LLMProvider, audit: AuditLog) -> None:
        self.provider, self.audit = provider, audit

    def compose(
        self, prompt: GroundedPrompt, *, model: str | None = None, max_tokens: int = 512
    ) -> Composition:
        unsupported = asks_unsupported_requirement(prompt.question, prompt.hint.kind)
        self.audit.guard("supported_requirement", not unsupported)
        if unsupported or prompt.hint.kind == "abstain":
            raise Refused("The requested requirement cannot be established from the evidence.")
        try:
            answer = self.provider.compose(
                prompt.question, prompt.pack, model=model, max_tokens=max_tokens
            )
        except Refused:
            raise  # Never circumvent a model refusal with another generation path.
        except GenerationError:
            return self._fallback(prompt)
        checks = {
            "evidence_citations": not invalid_evidence_citations(
                answer, prompt.pack, require_citation=True
            ),
            "not_header_copy": not looks_like_header_copy(answer),
            "reliable_hint_preserved": not misses_reliable_hint(
                prompt.question, answer, prompt.hint
            ),
            "not_model_abstention": not answer.lower().startswith("insufficient evidence"),
        }
        for name, passed in checks.items():
            self.audit.guard(name, passed)
        return Composition(answer) if all(checks.values()) else self._fallback(prompt)

    def _fallback(self, prompt: GroundedPrompt) -> Composition:
        allowed = grounded_hint(prompt.hint, prompt.pack)
        self.audit.guard("grounded_extractive_fallback", allowed)
        if allowed:
            return Composition(prompt.hint.text, used_fallback=True)
        raise Refused("No complete, cited answer or grounded extraction was available.")


class GuardedProvider:
    """Frozen LLMProvider-compatible wrapper. Hints are explicit, never metadata."""

    def __init__(
        self, provider: LLMProvider, audit: AuditLog, hint: AnswerHint = AnswerHint()
    ) -> None:
        self.provider, self.audit, self.hint = provider, audit, hint

    def compose(
        self,
        instruction: str,
        pack: ContextPack,
        *,
        model: str | None = None,
        max_tokens: int = 512,
    ) -> str:
        return (
            GroundedComposer(self.provider, self.audit)
            .compose(
                GroundedPrompt(instruction, pack, self.hint), model=model, max_tokens=max_tokens
            )
            .answer
        )

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
        return self.provider.embed(texts)

# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Request-scoped binding for the composition root, without changing any port."""

from __future__ import annotations

from dataclasses import dataclass, replace

from ici_core.domain.confidence import OperatingPoint
from ici_core.domain.envelope import ReliabilityEnvelope
from ici_core.domain.modes import BackendMode
from ici_core.domain.query import Query, RetrievalBudget
from ici_core.usecases.answer_question import AnswerQuestion
from ici_core.usecases.deps import ProviderBundle
from ici_llm.audit import AuditLog
from ici_llm.budget import RequestBudget
from ici_llm.composition import GuardedProvider
from ici_llm.embeddings import EmbeddingBackend, EmbeddingProvider
from ici_llm.grounding import GroundingVerifier
from ici_llm.guards import AnswerHint
from ici_llm.provider import OpenAIProvider
from ici_llm.records import RecordComposer
from ici_llm.routing import ModelRouter


@dataclass(frozen=True)
class LLMRequest:
    provider: OpenAIProvider
    grounding: GroundingVerifier
    audit: AuditLog

    def bind(
        self,
        bundle: ProviderBundle,
        *,
        hint: AnswerHint = AnswerHint(),
        embeddings: EmbeddingBackend | None = None,
    ) -> ProviderBundle:
        guarded = GuardedProvider(self.provider, self.audit, hint)
        return replace(
            bundle,
            llm=EmbeddingProvider(guarded, embeddings) if embeddings else guarded,
            grounding=self.grounding,
        )

    @property
    def records(self) -> RecordComposer:
        return RecordComposer(self.provider, audit=self.audit, prompts=self.provider.prompts)

    def finish(self, envelope: ReliabilityEnvelope) -> ReliabilityEnvelope:
        return replace(envelope, trace=self.audit.enrich(envelope.trace))


@dataclass(frozen=True)
class LLMRuntime:
    """Safe to share. Every session gets fresh audit state and budget counters."""

    provider: OpenAIProvider
    max_calls: int = 8
    max_reserved_tokens: int = 100_000

    def request(self, *, model: str | None = None, mode: BackendMode | None = None) -> LLMRequest:
        source = self.provider
        selected = source.router.resolve(model)
        audit = AuditLog(prices=dict(source.audit.prices))
        provider = OpenAIProvider(
            source.transport,
            router=ModelRouter(default=selected, allowed=source.router.allowed),
            prompts=source.prompts,
            audit=audit,
            budget=RequestBudget(self.max_calls, self.max_reserved_tokens),
            structured_max_tokens=source.structured_max_tokens,
            embedding_model=source.embedding_model,
            embedding_dimensions=source.embedding_dimensions,
            mode=mode if mode is not None else source.mode,
        )
        return LLMRequest(
            provider, GroundingVerifier(provider, prompts=source.prompts, audit=audit), audit
        )

    def answer_question(
        self,
        bundle: ProviderBundle,
        query: Query,
        *,
        model: str | None = None,
        budget: RetrievalBudget | None = None,
        point: OperatingPoint | None = None,
        hint: AnswerHint = AnswerHint(),
    ) -> ReliabilityEnvelope:
        request = self.request(model=model, mode=bundle.mode)
        envelope = AnswerQuestion(request.bind(bundle, hint=hint))(
            query, budget=budget, point=point
        )
        return request.finish(envelope)

# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Audited LLM composition, record assistance, embeddings and offline replay."""

from ici_llm.composition import GroundedComposer, GroundedPrompt, GuardedProvider
from ici_llm.embeddings import CachedEmbeddings, MiniLMEmbeddings, OpenAIEmbeddings, load_embeddings
from ici_llm.grounding import GroundingVerifier
from ici_llm.guards import AnswerHint
from ici_llm.provider import CassetteProvider, OpenAIProvider
from ici_llm.records import RecordComposer, RecordGenerationError, UnverifiedSuggestion
from ici_llm.routing import ModelRouter
from ici_llm.runtime import LLMRuntime

__all__ = [
    "AnswerHint",
    "CachedEmbeddings",
    "CassetteProvider",
    "GroundedComposer",
    "GroundedPrompt",
    "GroundingVerifier",
    "GuardedProvider",
    "LLMRuntime",
    "MiniLMEmbeddings",
    "ModelRouter",
    "OpenAIEmbeddings",
    "OpenAIProvider",
    "RecordComposer",
    "RecordGenerationError",
    "UnverifiedSuggestion",
    "load_embeddings",
]

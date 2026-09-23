# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""What a caller asks, and what it is asked about."""

from __future__ import annotations

from dataclasses import dataclass, field

from ici_core.domain.ids import CorrelationId, ProductId


@dataclass(frozen=True)
class ProductScope:
    """The subject a query is about.

    ``product_id`` is what makes memory recall safe. Recall scoped only by session
    can return facts recorded about a different product, which in a compliance tool
    is the worst kind of quiet failure (ARCHITECTURE.md §9.2). Ports that read
    stored facts take this, not a session string.
    """

    product_id: ProductId | None = None
    domain: str | None = None
    session: str | None = None

    @property
    def is_product_scoped(self) -> bool:
        return self.product_id is not None


@dataclass(frozen=True)
class RetrievalBudget:
    """How much evidence gathering a request is allowed."""

    top_k_documents: int = 4
    top_k_memory: int = 3
    top_k_facts: int = 12
    """Triples read from the mounted substrates and offered as evidence.

    Higher than the document budget because a triple is one short assertion rather
    than a passage, and a subject the graph actually models is described by several
    of them at once. Bounded all the same: a mounted substrate is not a licence to
    put an entire subgraph in front of the model.
    """

    max_steps: int = 6
    max_context_chars: int = 12_000


@dataclass(frozen=True)
class Query:
    """A question, its subject, and the request it belongs to."""

    text: str
    scope: ProductScope = field(default_factory=ProductScope)
    correlation_id: CorrelationId = CorrelationId("")

    def __post_init__(self) -> None:
        if not self.text or not self.text.strip():
            raise ValueError("query text must not be empty")

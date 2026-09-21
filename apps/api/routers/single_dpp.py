# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Questions about one passport the caller supplied.

Two endpoints. ``/parse`` splits a pasted or uploaded document into addressable
sections so the window can show what it found before anything is asked of it.
``/ask`` answers a question **from that document alone** — the indexed corpus is
not consulted, because the whole point is a passport that is not in the system yet.

The important line here is how thin this is. ``/ask`` swaps one adapter — the
evidence provider — and runs the same ``AnswerQuestion`` use case as the main
search window. Nothing else changes, so a single-document answer carries the same
reliability envelope: calibrated confidence against the same operating point, the
grounding verifier rejecting any claim that cannot be traced back to a section, an
abstention that names the weak signal, and provenance pointing at the JSON Pointer
it came from.

The demo did this differently, and that is worth recording. It ran a second,
parallel pipeline with its own ranking, its own model call, its own confidence
number and no grounding check at all — so the window where a user is most likely
to paste an unfamiliar document had the weakest guarantees in the product, and its
confidence number was not comparable with the one the search window reported.
Nothing is lost by folding it back into the shared path; a whole class of
divergence is.

Stateless by design: the document is never written to disk and never indexed. The
window holds it and sends it with each question, which costs a little bandwidth and
means a passport a user was only checking does not silently join the corpus.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field

from apps.api.deps import get_bundle
from apps.api.routers.search import _serialise
from ici_core.domain.confidence import OperatingPoint
from ici_core.domain.errors import CapabilityError
from ici_core.domain.ids import CorrelationId
from ici_core.domain.query import ProductScope, Query, RetrievalBudget
from ici_core.usecases.answer_question import AnswerQuestion
from ici_core.usecases.deps import ProviderBundle

router = APIRouter(prefix="/single-dpp", tags=["single-dpp"])


class ParseRequest(BaseModel):
    content: str = Field(description="The passport, as JSON or as free text.")
    filename: str | None = None


class AskRequest(BaseModel):
    q: str = Field(min_length=1)
    content: str
    filename: str | None = None
    tau: float | None = None
    top_k: int = 4


def _parse(content: str, filename: str | None) -> Any:
    from ici_evidence import DocumentTooLarge, parse_document

    try:
        return parse_document(content, filename)
    except DocumentTooLarge as exc:
        # A typed decline rather than a 500 or a silent truncation: the caller can
        # act on "too big", and cannot act on a document quietly cut in half.
        raise CapabilityError(
            capability="single-passport inquiry",
            mode="",
            reason=str(exc),
        ) from exc


@router.post("/parse")
def parse(req: ParseRequest) -> dict[str, Any]:
    """What the window shows before a question is asked.

    Deliberately requires no bundle and no model: reading a document the user
    already has should not depend on a backend being reachable, and it costs
    nothing.
    """
    document = _parse(req.content, req.filename)
    return {
        "filename": document.filename,
        "document_type": document.document_type,
        "title": document.title,
        "char_count": document.char_count,
        # Reported rather than swallowed. "This looks like JSON but does not parse"
        # is the most useful thing this endpoint can say about a broken passport.
        "warnings": list(document.warnings),
        "sections": [
            {
                "id": s.id,
                "title": s.title,
                "path": s.path,
                "kind": s.kind,
                "summary": s.summary,
                "preview": s.text[:600],
                "fields": [{"path": k, "value": v} for k, v in s.fields],
            }
            for s in document.sections
        ],
    }


@router.post("/ask")
def ask(
    req: AskRequest,
    bundle: Annotated[ProviderBundle, Depends(get_bundle)],
    x_correlation_id: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    """Answer from the supplied document only, through the shared inference path."""
    from dataclasses import replace

    from ici_evidence import InlineDocumentProvider

    document = _parse(req.content, req.filename)
    if not document.sections:
        raise CapabilityError(
            capability="single-passport inquiry",
            mode=bundle.mode.value,
            reason="nothing could be read from this document, so there is nothing to answer from",
        )

    # The one substitution. Memory is left alone: a previously validated fact about
    # this product is still legitimate support, and excluding it would make the
    # window worse at exactly the questions it exists for.
    scoped = replace(bundle, evidence=InlineDocumentProvider(document))

    envelope = AnswerQuestion(scoped)(
        Query(
            text=req.q,
            # No product scope. The document *is* the scope, and claiming a product
            # id we have not verified would let one passport's facts be recalled
            # against another's.
            scope=ProductScope(),
            correlation_id=CorrelationId(x_correlation_id or "anonymous"),
        ),
        budget=RetrievalBudget(top_k_documents=req.top_k, top_k_memory=0),
        point=OperatingPoint(tau=req.tau if req.tau is not None else 0.5),
    )

    return {
        **_serialise(envelope),
        "document": {
            "filename": document.filename,
            "title": document.title,
            "sections": len(document.sections),
            "document_type": document.document_type,
        },
    }

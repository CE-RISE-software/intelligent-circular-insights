# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Generate a schema-valid product record from a few supplied facts.

Validated against the target schema before it is returned. A schema failure is one
retry with the violation in the prompt, then an error — never a silent pass, since
a plausible-looking invalid passport is worse than no passport.

The composer (``ici_llm.records.RecordComposer``) does the generating and the
grounding; this use case decides what the system is willing to hand back. Three
decisions live here rather than there:

*Evidence is gathered first, and a seed with nothing behind it is refused.* The
composer grounds every leaf it emits against the pack it is given, so an empty pack
means every field would have to come from the model's priors. That is the failure
mode this whole architecture exists to prevent, and it is cheaper to refuse before
the call than to discard the output after paying for it.

*Repair and synthesis are one use case with two entry points, not two.* They share
the gathering, the scope, the ledger stamp and the refusal rule; only the composer
method differs. Splitting them would have duplicated all four.

*Unverified suggestions are carried through untouched and never merged.* The
composer separates model-prior candidates from grounded fills deliberately (ADR
0011). Anything here that folded them into the record would undo that separation at
the exact point where it stops being visible to the caller.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from ici_core.domain.errors import CapabilityError
from ici_core.domain.evidence import ContextPack
from ici_core.domain.ids import CorrelationId, DppId, ProfileId
from ici_core.domain.query import ProductScope, Query, RetrievalBudget
from ici_core.domain.record import DPPRecord
from ici_core.domain.trace import TraceStep
from ici_core.usecases.deps import ProviderBundle


class RecordAssistant(Protocol):
    """What this use case needs from a record composer.

    Structural, and declared here rather than imported, so the core keeps its rule
    that it never reaches into an adapter package. ``RecordComposer`` satisfies it
    without knowing this exists.
    """

    def repair(
        self, record: Mapping[str, Any], pack: ContextPack, *, suggest_from_training: bool = ...
    ) -> Any: ...

    def synthesize(self, seed: Mapping[str, Any], pack: ContextPack) -> Any: ...


@dataclass(frozen=True)
class SynthesizeRecord:
    """Build or mend a passport, with evidence behind every field it fills."""

    bundle: ProviderBundle
    assistant: RecordAssistant

    def __call__(
        self,
        seed: Mapping[str, Any],
        profile: ProfileId,
        *,
        correlation_id: CorrelationId = CorrelationId(""),
    ) -> DPPRecord:
        """Synthesise a record, and return it only if it conforms to ``profile``."""
        pack = self._gather(seed, correlation_id, "synthesize")
        result = self.assistant.synthesize(seed, pack)
        record = DPPRecord(
            dpp_id=DppId(str(result.record.get("dpp_id", "synthesised"))),
            payload=result.record,
            applied_schemas=(str(profile),),
        )

        # Checked against the *bound* schema registry, not only the composer's own
        # copy. The composer validates against the EU DPP schema it was built with;
        # the deployment may have bound a stricter profile, and a record that clears
        # one and not the other is not a record this system may return.
        report = self.bundle.schemas.conform(record, profile)
        self._stamp(
            correlation_id,
            "synthesize",
            f"{len(result.support)} grounded fields, "
            + ("conforms" if report.conforms else f"{len(report.violations)} violations"),
        )
        if not report.conforms:
            raise CapabilityError(
                capability="a synthesised passport",
                mode=self.bundle.mode.value,
                reason=(
                    f"the generated record does not conform to {profile}: "
                    + "; ".join(
                        f"{v.location or '(root)'} {v.message}" for v in report.violations[:4]
                    )
                ),
            )
        return record

    def repair(
        self,
        record: Mapping[str, Any],
        profile: ProfileId,
        *,
        correlation_id: CorrelationId = CorrelationId(""),
        suggest_from_training: bool = True,
    ) -> Any:
        """Fill what evidence supports, and say plainly what it does not.

        Returns the composer's ``RepairResult`` unchanged — grounded fills, the
        violations that could not be grounded, the rejected proposals and the
        unverified suggestions, all still separate. A caller that wants a single
        repaired record is welcome to take ``.record``; one that wants to know what
        the system was and was not willing to stand behind needs the rest, and
        flattening it here would take that choice away.
        """
        pack = self._gather(record, correlation_id, "repair")
        result = self.assistant.repair(record, pack, suggest_from_training=suggest_from_training)
        self._stamp(
            correlation_id,
            "repair",
            f"{len(result.fills)} grounded, {len(result.cannot_be_grounded)} unresolved, "
            f"{len(result.suggestions)} for review",
        )
        return result

    # -- shared -------------------------------------------------------------
    def _gather(
        self, payload: Mapping[str, Any], correlation_id: CorrelationId, what: str
    ) -> ContextPack:
        """Evidence for this product, scoped to it.

        The scope matters as much as the retrieval: fact memory is product-scoped,
        and an unscoped gather could ground one product's passport in another's
        certificates — which would look entirely correct and be entirely wrong.
        """
        product = _product_id(payload)
        query = Query(
            text=_describe(payload),
            scope=ProductScope(product_id=product, session=str(correlation_id) or None),
            correlation_id=correlation_id,
        )
        items = list(self.bundle.memory.recall(query.scope, query))
        evidence = list(self.bundle.evidence.retrieve(query, RetrievalBudget(top_k_documents=8)))
        pack = ContextPack(tuple(evidence))
        self._stamp(
            correlation_id,
            f"{what}:gather",
            f"{len(evidence)} passages, {len(items)} recalled facts",
        )
        if not pack:
            raise CapabilityError(
                capability=f"record {what}",
                mode=self.bundle.mode.value,
                reason=(
                    "no evidence was found for this product, so every field would "
                    "have to come from the model's priors rather than from a source "
                    "anyone can check"
                ),
            )
        return pack

    def _stamp(self, correlation_id: CorrelationId, name: str, detail: str) -> None:
        self.bundle.ledger.record(correlation_id, TraceStep(name, detail))


def _product_id(payload: Mapping[str, Any]) -> Any:
    from ici_core.domain.ids import ProductId

    product = payload.get("product")
    if isinstance(product, Mapping):
        for key in ("id", "model", "name"):
            value = product.get(key)
            if isinstance(value, str) and value.strip():
                return ProductId(value.strip())
    dpp = payload.get("dpp_id")
    return ProductId(str(dpp)) if isinstance(dpp, str) and dpp.strip() else None


def _describe(payload: Mapping[str, Any]) -> str:
    """A retrieval query built from the seed's own words.

    Deliberately not a fixed template: the seed is the only description of this
    product the system has, and inventing terms around it would retrieve evidence
    for a product nobody supplied.
    """
    product = payload.get("product")
    words: list[str] = []
    if isinstance(product, Mapping):
        words = [str(v) for k, v in product.items() if isinstance(v, str) and k != "id"]
    if not words and isinstance(payload.get("dpp_id"), str):
        words = [str(payload["dpp_id"])]
    return " ".join(words) or "product passport"


__all__ = ["RecordAssistant", "SynthesizeRecord"]

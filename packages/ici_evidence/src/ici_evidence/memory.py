# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Persistent fact memory: product-scoped, append-only, superseding.

The published prototype is scoped by *session* and stores whatever it is handed.
§4.2 of the paper lists what it does not do — provenance validation, immutable
supersession, correction history — as requirements for production rather than
properties evaluated. All four are implemented here, because one of them is not a
research nicety: session-scoped recall can return a fact recorded about a
different product, and in a compliance tool that is the worst failure available,
since it is silent and the answer looks fine.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from ici_core.domain.facts import Fact, FactVersion, ValidationOutcome
from ici_core.domain.ids import FactId, ProductId
from ici_core.domain.query import ProductScope, Query
from ici_evidence.documents import tokenize


class UnvalidatedFactError(ValueError):
    """Raised when something tries to store a fact that did not pass validation."""


@dataclass
class AppendOnlyFactMemory:
    """Implements ``FactMemory``.

    The log is append-only: a correction writes a new version linked to the one it
    replaces, and nothing is ever mutated or deleted. "What did we believe, and
    when" therefore stays answerable, which is the whole point of writing facts
    down rather than re-reading documents.
    """

    versions: list[FactVersion] = field(default_factory=list)
    path: Path | None = None
    _seq: int = field(default=0, init=False)

    # -- FactMemory ---------------------------------------------------------
    def recall(self, scope: ProductScope, q: Query) -> Sequence[Fact]:
        if scope.product_id is None:
            # No product, no recall. Guessing a scope is how facts leak.
            return []
        terms = set(tokenize(q.text))
        live = self._live_for(scope.product_id)
        if not terms:
            return [v.fact for v in live]

        scored = [
            (len(terms & set(tokenize(f"{v.fact.subject} {v.fact.predicate} {v.fact.value}"))), v)
            for v in live
        ]
        return [v.fact for score, v in sorted(scored, key=lambda p: -p[0]) if score > 0]

    def commit(self, fact: Fact, validation: ValidationOutcome) -> FactId:
        if validation is not ValidationOutcome.VALIDATED:
            raise UnvalidatedFactError(
                f"refusing to store an unvalidated fact about {fact.product_id!r}; "
                f"outcome was {validation.value}"
            )
        return self._append(fact, supersedes=None, reason=None)

    def supersede(self, old: FactId, new: Fact, reason: str) -> FactId:
        if not any(v.id == old for v in self.versions):
            raise KeyError(f"cannot supersede unknown fact {old!r}")
        if not reason:
            raise ValueError("a correction must say why; an unexplained change is noise")
        return self._append(new, supersedes=old, reason=reason)

    def history(self, subject: str, scope: ProductScope) -> Sequence[FactVersion]:
        if scope.product_id is None:
            return []
        return [
            v
            for v in self.versions
            if v.fact.product_id == scope.product_id and v.fact.subject == subject
        ]

    # -- internals ----------------------------------------------------------
    def _append(self, fact: Fact, *, supersedes: FactId | None, reason: str | None) -> FactId:
        self._seq += 1
        version = FactVersion(
            id=FactId(f"mem-{self._seq:06d}"),
            fact=fact,
            supersedes=supersedes,
            reason=reason,
        )
        self.versions.append(version)
        self._flush(version)
        return version.id

    def _live_for(self, product: ProductId) -> list[FactVersion]:
        """Current versions only — superseded ones stay readable via history()."""
        replaced = {v.supersedes for v in self.versions if v.supersedes}
        return [v for v in self.versions if v.fact.product_id == product and v.id not in replaced]

    def _flush(self, version: FactVersion) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    {
                        "id": version.id,
                        "subject": version.fact.subject,
                        "predicate": version.fact.predicate,
                        "value": version.fact.value,
                        "product_id": version.fact.product_id,
                        "provenance_ref": version.fact.provenance_ref,
                        "recorded_at": version.fact.recorded_at.isoformat(),
                        "supersedes": version.supersedes,
                        "reason": version.reason,
                    }
                )
                + "\n"
            )

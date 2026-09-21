# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Expand one number or claim into its full derivation.

The audit panel calls this when a practitioner clicks a figure: which sources,
which factors, which scaling chain, which arithmetic. In CE-RISE mode it reaches
all the way to the triple and the file it lives in.

The rule this enforces is narrow and the reason for it is not. An explanation is
assembled **only** from links the envelope already carries. It never re-runs the
engine and never goes looking for a better source, because an explanation produced
by a second, independent derivation is not an explanation of the first — it is a
new claim that happens to agree, and the two can silently drift. If a figure's
provenance was not captured when it was computed, the honest answer is that it
cannot be explained, and that is what this returns.

Which is also why it is stricter than it looks: asking to explain a target the
envelope has no links for raises rather than returning an empty derivation, since
an empty provenance block reads as "nothing supports this" when the truth is "we
did not record what does".
"""

from __future__ import annotations

from dataclasses import dataclass

from ici_core.domain.envelope import ProvenanceKind, ReliabilityEnvelope
from ici_core.domain.errors import CapabilityError
from ici_core.domain.impact import Provenance
from ici_core.usecases.deps import ProviderBundle

TOTAL = "total"
"""The whole result. Any other target is matched against provenance refs."""


@dataclass(frozen=True)
class ExplainAnswer:
    bundle: ProviderBundle

    def __call__(self, envelope: ReliabilityEnvelope, target: str) -> Provenance:
        if not envelope.provenance:
            raise CapabilityError(
                capability=f"an explanation of {target!r}",
                mode=envelope.mode.value,
                reason=(
                    "this result carries no provenance, so its derivation was not "
                    "recorded when it was produced; re-running the engine here would "
                    "produce a second derivation rather than explain the first"
                ),
            )

        links = envelope.provenance
        if target != TOTAL:
            narrowed = tuple(link for link in links if target in link.ref)
            if not narrowed:
                raise CapabilityError(
                    capability=f"an explanation of {target!r}",
                    mode=envelope.mode.value,
                    reason=(
                        f"nothing in this result's provenance refers to {target!r}; "
                        f"available: {', '.join(sorted({link.ref for link in links})[:6])}"
                    ),
                )
            links = narrowed

        return Provenance(
            target=target,
            links=links,
            arithmetic=_arithmetic(envelope, target),
        )


def _arithmetic(envelope: ReliabilityEnvelope, target: str) -> str | None:
    """The one line a reader checks first.

    Only stated for the whole result, and only when the envelope carries a
    quantified value — a derivation for one contributing step is the engine's to
    give through ``ImpactEngine.explain``, not something to reconstruct here from
    links that may not be the full set.
    """
    if target != TOTAL or envelope.value is None:
        return None
    counted = sum(1 for link in envelope.provenance if link.kind is not ProvenanceKind.RULE)
    rules = len(envelope.provenance) - counted
    parts = [f"{envelope.value.amount:.6g} {envelope.value.unit}"]
    if envelope.value.basis:
        parts.append(f"per {envelope.value.basis}")
    parts.append(f"from {counted} source{'' if counted == 1 else 's'}")
    if rules:
        parts.append(f"and {rules} fired rule{'' if rules == 1 else 's'}")
    return " ".join(parts)


__all__ = ["TOTAL", "ExplainAnswer"]

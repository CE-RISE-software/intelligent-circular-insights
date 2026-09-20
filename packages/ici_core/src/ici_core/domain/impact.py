# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Environmental impact requests and results.

Kept general on purpose. The Normal mode engine works from flat profiles and CSV
factor tables; the CE-RISE engine solves a supply chain off an RDF graph. Both
answer the same question, so the core sees one shape.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from ici_core.domain.envelope import ProvenanceLink


@dataclass(frozen=True)
class SubjectRef:
    """What is being assessed."""

    id: str
    kind: str = "product"


@dataclass(frozen=True)
class ImpactRequest:
    indicator: str = "climate_change"
    functional_unit: str | None = None
    scenario: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ImpactContribution:
    """One slice of a result — a life cycle stage, an activity, a flow."""

    label: str
    amount: float
    unit: str
    share: float | None = None
    is_proxy: bool = False
    """True when the factor behind this number is a documented proxy, not a
    licensed value. Badged in the API response and on every screen."""


@dataclass(frozen=True)
class ImpactResult:
    subject: SubjectRef
    indicator: str
    total: float
    unit: str
    functional_unit: str | None = None
    contributions: tuple[ImpactContribution, ...] = ()
    uncertainty: tuple[float, float] | None = None
    data_quality: float | None = None
    diagnostics: tuple[str, ...] = ()
    uses_proxy_factors: bool = False


@dataclass(frozen=True)
class Provenance:
    """The full derivation of one number, down to the arithmetic."""

    target: str
    links: tuple[ProvenanceLink, ...] = ()
    arithmetic: str | None = None
    scaling_chain: tuple[str, ...] = ()

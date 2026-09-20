# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Building and holding the per-mode adapter bundles.

Both bundles are constructed once at startup and held immutably, so resolving a
mode at request time is a dictionary lookup rather than a re-initialisation. That
is what makes per-request switching affordable, and what makes it possible to run
the same question through both backends in one process.

This module and ``deps.py`` are the only places that know both adapter sets exist.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from apps.api.settings import Settings, get_settings
from ici_core.domain.errors import CapabilityError
from ici_core.domain.modes import BackendMode
from ici_core.usecases.deps import ProviderBundle


@dataclass(frozen=True)
class BundleRegistry:
    """The built bundles, keyed by mode."""

    bundles: dict[BackendMode, ProviderBundle]

    def for_mode(self, mode: BackendMode) -> ProviderBundle:
        bundle = self.bundles.get(mode)
        if bundle is None:
            raise CapabilityError(
                capability="backend",
                mode=mode.value,
                reason="this mode is not enabled in this deployment",
            )
        return bundle

    def available(self) -> tuple[BackendMode, ...]:
        return tuple(self.bundles)


def build_registry(
    modes: tuple[BackendMode, ...], settings: Settings | None = None
) -> BundleRegistry:
    """Construct one bundle per enabled mode.

    Sprint 1 supplies the Normal adapters and Sprint 2 the CE-RISE ones. Until
    then a mode with no adapters is simply absent from the registry, which
    surfaces as a typed 422 rather than a half-wired bundle that fails later and
    less clearly.
    """
    settings = settings or get_settings()
    built: dict[BackendMode, ProviderBundle] = {}
    for mode in modes:
        bundle = _build(mode, settings)
        if bundle is not None:
            built[mode] = bundle
    return BundleRegistry(built)


def _build(mode: BackendMode, settings: Settings) -> ProviderBundle | None:
    if mode is BackendMode.NORMAL:
        return _build_normal(settings)
    if mode is BackendMode.CE_RISE:
        return _build_ce_rise(settings)
    return None


def _build_ce_rise(settings: Settings) -> ProviderBundle:
    """The CE-RISE adapter set.

    Differs from Normal in exactly one place: the substrate registry mounts the WP3
    knowledge graph, which carries real triples for the symbolic layer to reason over
    and a graph-solved assessment behind PEF Studio.

    It *adds*; it does not replace. The deterministic CSV carbon path stays, because
    running both side by side is the demonstration — one workbench, two levels of
    rigour, with a visible upgrade path between them. Everything else is shared,
    deliberately: two modes that differed everywhere would be two products.

    Built on top of the Normal bundle rather than beside it, so a difference between
    them is visible here as an override rather than hidden in two parallel lists.
    """
    from ici_core.ledger import InMemoryLedger
    from ici_substrates.pefdpp import PefdppSubstrateRegistry, build_services

    graph, lca = build_services()
    normal = _build_normal(settings)
    return replace(
        normal,
        mode=BackendMode.CE_RISE,
        substrates=PefdppSubstrateRegistry(graph=graph, lca=lca),
        ledger=InMemoryLedger(mode=BackendMode.CE_RISE),
    )


def _build_normal(settings: Settings) -> ProviderBundle:
    """The Normal-mode adapter set.

    Flat product profiles, CSV emission factors, JSON-Schema validation, hybrid
    lexical retrieval, OWL 2 RL over the DPP ontology. Fast, broad, shallow — the
    counterpart to the graph-grounded set Sprint 2 mounts.

    Everything is constructed here and nowhere else. This is the only function in
    the codebase that knows which concrete adapter implements which port.
    """
    from ici_core.ledger import InMemoryLedger
    from ici_datatrust import NullDataTrustProvider
    from ici_evidence import AppendOnlyFactMemory, DocumentEvidenceProvider
    from ici_llm.grounding import GroundingVerifier
    from ici_llm.provider import CassetteProvider
    from ici_policy import HeuristicRouter
    from ici_reliability import EvidenceSignals, IsotonicCalibrator, ThresholdSelectivePolicy
    from ici_substrates import (
        CeRiseModelRegistry,
        CsvFactorImpactEngine,
        InMemoryRepository,
        JsonSchemaRegistry,
    )
    from ici_substrates.paths import SEED_DOCS_ROOT
    from ici_symbolic import OwlRlValidator

    # Cassette-backed by default: replay makes no network call and fails loudly on a
    # miss, so running the suite can never quietly spend money. Recording is a
    # deliberate act (LLM_CASSETTE_MODE=record), not something a test can trigger.
    llm = CassetteProvider(settings.llm_cassette_dir, mode=settings.llm_cassette_mode)
    grounding = GroundingVerifier(llm, prompts=llm.prompts, audit=llm.audit)

    return ProviderBundle(
        mode=BackendMode.NORMAL,
        evidence=DocumentEvidenceProvider.from_seed_docs(SEED_DOCS_ROOT),
        memory=AppendOnlyFactMemory(),
        substrates=CeRiseModelRegistry(),
        symbolic=OwlRlValidator.for_domain("battery"),
        schemas=JsonSchemaRegistry(),
        impact=CsvFactorImpactEngine.from_data_root(),
        records=InMemoryRepository(),
        signals=EvidenceSignals(),
        calibrator=IsotonicCalibrator(),
        selective=ThresholdSelectivePolicy(),
        data_trust=NullDataTrustProvider(),
        grounding=grounding,
        llm=llm,
        ledger=InMemoryLedger(mode=BackendMode.NORMAL),
        policy=HeuristicRouter(),
    )

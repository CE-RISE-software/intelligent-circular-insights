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
from pathlib import Path

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
    # Built once and shared. Every mode is derived from the Normal set, so building
    # it per mode would give each one its own calibrator, its own audit log and its
    # own copy of the recorder's spend ceiling — three things that are supposed to be
    # properties of the deployment rather than of the backend you happen to be in.
    normal = _build_normal(settings)
    built: dict[BackendMode, ProviderBundle] = {}
    for mode in modes:
        bundle = _build(mode, normal)
        if bundle is not None:
            built[mode] = bundle
    return BundleRegistry(built)


def _build(mode: BackendMode, normal: ProviderBundle) -> ProviderBundle | None:
    if mode is BackendMode.NORMAL:
        return normal
    if mode is BackendMode.CE_RISE:
        return _build_ce_rise(normal)
    return None


def _build_ce_rise(normal: ProviderBundle) -> ProviderBundle:
    """The CE-RISE adapter set: the same five features, run over CE-RISE data.

    The mode switch has to change what QA, Carbon, Validate, Repair and Synthesize
    *do*, not merely unlock an extra window. Each override below names which feature
    it moves and why that feature's CE-RISE answer is arrived at the way it is.

    What it must not do is substitute blindly. An earlier draft swapped the impact
    engine outright and Carbon stopped working for the five products the graph has
    never heard of; the repair was to make CE-RISE purely additive, which removed the
    breakage by removing the difference. Both drafts were wrong in the same way: they
    treated two sources that model different things as interchangeable, then argued
    about which one wins. They do not model the same thing, so neither wins — each
    answers for what it actually covers, and the result says which one answered.

    Derived from the Normal bundle rather than built beside it, so every difference
    between the two modes is visible here as an override rather than hidden in two
    parallel lists — and so the reliability path is shared by identity, not merely
    configured the same way twice.
    """
    from ici_core.domain.ids import ProfileId
    from ici_core.ledger import InMemoryLedger
    from ici_substrates import (
        CeRiseModelRegistry,
        CompositeSubstrateRegistry,
        LayeredImpactEngine,
        LayeredSchemaRegistry,
    )
    from ici_substrates.pefdpp import PefdppSubstrateRegistry, build_services
    from ici_substrates.registry.schemas import (
        CE_RISE_GENERATED,
        CE_RISE_PREFIX,
        CE_RISE_ROOTS,
        EU_DPP,
    )

    graph, lca = build_services()
    pefdpp = PefdppSubstrateRegistry(graph=graph, lca=lca)

    # Which CE-RISE models a record may be routed to: those that declare a document
    # root, and only ones actually generated. Offering a profile whose schema is
    # missing would fail at validation time rather than simply not being on the list.
    vocabulary = tuple(
        ProfileId(f"{CE_RISE_PREFIX}{name}")
        for name in sorted(CE_RISE_ROOTS)
        if (CE_RISE_GENERATED / f"{name}.json").is_file()
    )

    return replace(
        normal,
        mode=BackendMode.CE_RISE,
        # QA: the WP3 graph *and* the model catalogue, never one instead of the other.
        # The graph goes first because it is the more specific source; anything it
        # does not implement falls through to the catalogue.
        substrates=CompositeSubstrateRegistry(members=(pefdpp, CeRiseModelRegistry())),
        # Carbon: the graph answers for the study it models, the factor table for the
        # products it models. Routed, not substituted -- the two describe different
        # systems with different functional units, four orders of magnitude apart, and
        # mapping one onto the other would produce a confidently wrong number. Every
        # result names the engine that produced it.
        impact=LayeredImpactEngine(preferred=pefdpp.impact, fallback=normal.impact),
        # Validate, and through it Repair and Synthesize: a record is checked against
        # the consortium's model that recognises its vocabulary, and against the EU
        # DPP schema when none does. Routed for the same reason carbon is -- the two
        # describe different documents, sharing not one top-level term, so checking
        # both at once would reject every record ever written. A named profile is
        # still honoured exactly.
        schemas=LayeredSchemaRegistry(
            inner=normal.schemas, base_profile=EU_DPP, candidates=vocabulary
        ),
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
    from ici_llm.provider import CassetteProvider, OpenAIProvider
    from ici_llm.routing import ModelRouter
    from ici_policy import HeuristicRouter
    from ici_reliability import EvidenceSignals, IsotonicCalibrator, ThresholdSelectivePolicy
    from ici_substrates import (
        CeRiseModelRegistry,
        CsvFactorImpactEngine,
        InMemoryRepository,
        JsonSchemaRegistry,
        ModeAwareImpactEngine,
    )
    from ici_substrates.paths import SEED_DOCS_ROOT
    from ici_symbolic import OwlRlValidator

    # Cassette-backed by default: replay makes no network call and fails loudly on a
    # miss, so running the suite can never quietly spend money. Recording is a
    # deliberate act (LLM_CASSETTE_MODE=record), not something a test can trigger.
    source = OpenAIProvider(
        api_key=settings.openai_api_key,
        router=ModelRouter(settings.llm_model_default, settings.allowed_models),
    )
    llm = (
        source
        if settings.llm_cassette_mode == "live"
        else CassetteProvider(
            settings.llm_cassette_dir, mode=settings.llm_cassette_mode, provider=source
        )
    )
    grounding = GroundingVerifier(llm, prompts=llm.prompts, audit=llm.audit)

    return ProviderBundle(
        mode=BackendMode.NORMAL,
        evidence=DocumentEvidenceProvider.from_seed_docs(SEED_DOCS_ROOT),
        memory=AppendOnlyFactMemory(),
        substrates=CeRiseModelRegistry(),
        symbolic=OwlRlValidator.for_domain("battery"),
        schemas=JsonSchemaRegistry(),
        impact=ModeAwareImpactEngine(CsvFactorImpactEngine.from_data_root()),
        records=InMemoryRepository.from_directory(Path(settings.record_evidence_dir)),
        signals=EvidenceSignals(),
        calibrator=IsotonicCalibrator(),
        selective=ThresholdSelectivePolicy(),
        data_trust=NullDataTrustProvider(),
        grounding=grounding,
        llm=llm,
        ledger=InMemoryLedger(mode=BackendMode.NORMAL),
        policy=HeuristicRouter(),
    )

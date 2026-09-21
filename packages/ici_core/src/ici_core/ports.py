# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""The fifteen ports. This file is the seam, and it is frozen after Sprint 0.

Ports are ``typing.Protocol``, not abstract base classes. Structural typing means
an adapter never imports anything from here to satisfy one, and a test double is a
plain dataclass rather than a subclass. That keeps the dependency arrow pointing
one way — every adapter depends on the core, the core depends on nobody — which
``import-linter`` enforces in CI.

Each port earns its place by being something a mode swaps, or something the
research programme needs to be able to replace later (ARCHITECTURE.md §9). Where a
port has no real implementation in this release, it has a null one and says so.

Changing a signature here after Sprint 0 requires an ADR and a CHANGELOG entry,
because two workers are building against it in parallel.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol, runtime_checkable

from ici_core.domain.claims import Claim, GroundingReport
from ici_core.domain.confidence import (
    CalibrationDiagnostics,
    Confidence,
    OperatingPoint,
    SignalVector,
)
from ici_core.domain.datatrust import DataTrust
from ici_core.domain.envelope import Decision
from ici_core.domain.evidence import ContextPack, Evidence
from ici_core.domain.facts import Fact, FactVersion, ValidationOutcome
from ici_core.domain.ids import (
    CalibratorId,
    CorrelationId,
    DppId,
    FactId,
    ProfileId,
    SignalName,
)
from ici_core.domain.impact import (
    ImpactRequest,
    ImpactResult,
    Provenance,
    SubjectRef,
)
from ici_core.domain.query import ProductScope, Query, RetrievalBudget
from ici_core.domain.record import ConformanceReport, DPPRecord, SchemaProfile
from ici_core.domain.rules import EntailmentResult, FactGraph, ValidationReport
from ici_core.domain.substrate import CoverageReport, Substrate
from ici_core.domain.trace import Trace, TraceStep

# ============================================================== evidence and knowledge


@runtime_checkable
class EvidenceProvider(Protocol):
    """Finds candidate evidence for a query.

    Normal mode retrieves passages from a document corpus with hybrid sparse and
    dense search. CE-RISE mode can additionally read from a mounted graph. Both
    return the same thing, and every item carries a ref a reader can follow.
    """

    def retrieve(self, q: Query, budget: RetrievalBudget) -> Sequence[Evidence]:
        """Return evidence, best first. Empty is a valid answer; None is not."""
        ...


@runtime_checkable
class FactMemory(Protocol):
    """Persistent facts, product-scoped and append-only.

    The published prototype is session-scoped and mutates in place. This interface
    is the corrected one: recall takes a ``ProductScope`` so facts cannot leak
    across products, storage takes a validation outcome so unvalidated facts cannot
    be committed, and corrections append rather than overwrite so the history of
    what was believed stays readable.
    """

    def recall(self, scope: ProductScope, q: Query) -> Sequence[Fact]:
        """Facts about *this* product only. Never another product's, ever."""
        ...

    def commit(self, fact: Fact, validation: ValidationOutcome) -> FactId:
        """Store a validated fact. Must reject anything not VALIDATED."""
        ...

    def supersede(self, old: FactId, new: Fact, reason: str) -> FactId:
        """Append a correction. The superseded version stays readable."""
        ...

    def history(self, subject: str, scope: ProductScope) -> Sequence[FactVersion]:
        """The correction chain for a subject, oldest first."""
        ...


@runtime_checkable
class SubstrateRegistry(Protocol):
    """Mounts knowledge, and reports how much of the workload it reaches."""

    def mounted(self) -> Sequence[Substrate]: ...

    def facts_for(self, subject: SubjectRef) -> FactGraph:
        """Every triple the mounted substrates know about this subject."""
        ...

    def coverage_report(self) -> CoverageReport:
        """Fire rate and conditional precision per substrate (ADR 0005)."""
        ...


@runtime_checkable
class SymbolicValidator(Protocol):
    """Derives what follows from the facts, and checks claims against the rules.

    Expressiveness is deliberately restricted to a decidable fragment evaluated
    under OWL 2 RL semantics, so entailment always terminates. The value is not
    only the conclusion but the trace: which rule fired, on which premises.
    """

    def entail(self, graph: FactGraph) -> EntailmentResult: ...

    def validate(self, claims: Sequence[Claim], graph: FactGraph) -> ValidationReport: ...


@runtime_checkable
class SchemaRegistry(Protocol):
    """Conformance checking against EU DPP schemas, CE-RISE modules, SHACL shapes."""

    def profiles(self) -> Sequence[SchemaProfile]: ...

    def conform(self, record: DPPRecord, profile: ProfileId) -> ConformanceReport:
        """Typed violations with locations. Never a bare boolean."""
        ...


@runtime_checkable
class ImpactEngine(Protocol):
    """Computes an environmental result, and explains any number in it."""

    def assess(self, subject: SubjectRef, req: ImpactRequest) -> ImpactResult: ...

    def explain(self, result: ImpactResult, target: str) -> Provenance:
        """The derivation of one number: sources, factors, scaling, arithmetic."""
        ...

    def subjects(self) -> Sequence[SubjectRef]:
        """What this engine can assess.

        On the port because a caller that cannot discover the subjects has to
        hard-code them, which is how the demo ended up shipping a product list
        that had drifted from the data directory.
        """
        ...


@runtime_checkable
class DPPRepository(Protocol):
    """Stored product records."""

    def get(self, dpp_id: DppId) -> DPPRecord | None: ...

    def put(self, record: DPPRecord) -> None: ...

    def list_ids(self) -> Sequence[DppId]: ...


# ==================================================================== reliability


@runtime_checkable
class ConfidenceSignals(Protocol):
    """Emits the named signals that describe how an answer could be weak.

    Kept as a vector rather than collapsed to a scalar. That is what lets an
    abstention name the weak signal, and what makes a vector calibrator possible
    later without touching this call site (ADR 0007).
    """

    def emit(
        self,
        q: Query,
        pack: ContextPack,
        entailment: EntailmentResult | None,
        generation_probability: float | None = None,
    ) -> SignalVector: ...

    def names(self) -> Sequence[SignalName]:
        """Every signal this implementation can emit, for the audit panel."""
        ...


@runtime_checkable
class Calibrator(Protocol):
    """Maps a raw score to something that behaves like a probability.

    Isotonic ships as the default because it is what the system does today.
    Temperature and a vector calibrator exist unfitted; the seat is the point.
    """

    @property
    def id(self) -> CalibratorId: ...

    def fit(self, signals: Sequence[SignalVector], correct: Sequence[bool]) -> None: ...

    def calibrate(self, signals: SignalVector, raw: float) -> float:
        """Return a calibrated probability in [0, 1]."""
        ...

    def diagnostics(self) -> CalibrationDiagnostics: ...


@runtime_checkable
class SelectivePolicy(Protocol):
    """Turns a calibrated confidence into answer-or-abstain.

    Separate from the calibrator because the threshold is a deployment policy: a
    mandated coverage floor in one setting, stricter abstention in another. It is
    returned with the response so the operating point is auditable.
    """

    def threshold_for(self, coverage_target: float) -> float: ...

    def decide(self, confidence: Confidence, point: OperatingPoint) -> Decision: ...


@runtime_checkable
class DataTrustProvider(Protocol):
    """The bias-aware seat. Null-implemented in both shipped modes.

    When it lands it answers: given that a value is *present*, how much should we
    trust it? Returns a debiased value, a credible interval, and how sensitive the
    answer is to the policy target — which become two more confidence signals.
    """

    def assess(
        self,
        subject: SubjectRef,
        attribute: str,
        point: OperatingPoint,
    ) -> DataTrust | None:
        """None when this provider has nothing to say about the attribute."""
        ...

    @property
    def is_null(self) -> bool:
        """True for the null implementation, so the UI can hide the panel."""
        ...


@runtime_checkable
class GroundingVerifier(Protocol):
    """Checks that every claim in an answer resolves to evidence in the pack.

    This is what makes evidence-before-generation a mechanism rather than a
    prompt instruction. It does not prove parametric knowledge never leaks — no
    black-box method does — but an answer containing a claim that resolves to
    nothing cannot be returned, which is the part that matters operationally.

    Owned by Codex (CODEX_TASKS.md X1): decomposition needs a model in the loop.
    """

    def verify(self, answer: str, pack: ContextPack) -> GroundingReport: ...


# ======================================================================== shared


@runtime_checkable
class LLMProvider(Protocol):
    """The only thing in the system that talks to a model.

    Owned by Codex. Nothing outside ``ici_llm`` knows which model is in use;
    model-specific behaviour lives in that package's ``compat`` module and nowhere
    else. Every call is cassette-recorded, so the test suite makes no live calls.
    """

    def compose(
        self,
        instruction: str,
        pack: ContextPack,
        *,
        model: str | None = None,
        max_tokens: int = 512,
    ) -> str:
        """Compose an answer bound to the pack. Raises rather than truncating."""
        ...

    def structured(
        self,
        instruction: str,
        pack: ContextPack,
        schema: Mapping[str, Any],
        *,
        model: str | None = None,
    ) -> Mapping[str, Any]: ...

    def embed(self, texts: Sequence[str]) -> Sequence[Sequence[float]]: ...


@runtime_checkable
class ProvenanceLedger(Protocol):
    """Collects trace steps for a request and hands back the finished trace."""

    def record(self, cid: CorrelationId, step: TraceStep) -> None: ...

    def trace(self, cid: CorrelationId) -> Trace: ...


@runtime_checkable
class DecisionPolicy(Protocol):
    """Chooses the next action: recall, retrieve, entail, query, answer, abstain.

    The supervised router ships as the default because it is the configuration
    that works. Bandit and offline-RL seats are empty (ADR 0008). Two choices make
    them usable later: the observation is the confidence signal vector rather than
    hand-made features, and ABSTAIN is expressible as an action rather than only as
    a downstream threshold.
    """

    def act(self, signals: SignalVector, steps_taken: int) -> str:
        """Return an action name from this policy's declared action set."""
        ...

    def actions(self) -> Sequence[str]: ...

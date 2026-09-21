"""Shared fixtures.

Fakes here are plain dataclasses, not mocks. Ports are ``Protocol``s, so anything
with the right shape satisfies one — which means a test double reads like a tiny
implementation rather than a pile of ``when(...).thenReturn(...)``.
"""

from __future__ import annotations

import os
import socket
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import pytest

from ici_core.domain.claims import GroundingReport, GroundingVerdict
from ici_core.domain.confidence import (
    CalibrationDiagnostics,
    Confidence,
    OperatingPoint,
    SignalVector,
)
from ici_core.domain.datatrust import DataTrust
from ici_core.domain.envelope import Decision
from ici_core.domain.evidence import ContextPack, Evidence, EvidenceKind
from ici_core.domain.facts import Fact, FactVersion, ValidationOutcome
from ici_core.domain.ids import (
    CalibratorId,
    CorrelationId,
    DppId,
    EvidenceId,
    FactId,
    ProductId,
    ProfileId,
    SignalName,
)
from ici_core.domain.impact import ImpactRequest, ImpactResult, Provenance, SubjectRef
from ici_core.domain.modes import BackendMode
from ici_core.domain.query import ProductScope, Query, RetrievalBudget
from ici_core.domain.record import ConformanceReport, DPPRecord, SchemaProfile
from ici_core.domain.rules import EntailmentResult, FactGraph, ValidationReport
from ici_core.domain.substrate import CoverageReport, Substrate
from ici_core.domain.trace import Trace, TraceStep
from ici_core.usecases.deps import ProviderBundle

MODES = [BackendMode.NORMAL, BackendMode.CE_RISE]


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--no-network", action="store_true", help="Block network access in every test")
    parser.addoption("--run-live", action="store_true", help="Explicitly allow marked live tests")


def pytest_configure(config: pytest.Config) -> None:
    if config.getoption("--run-live") and (
        config.getoption("--no-network") or os.environ.get("CI", "").lower() in {"1", "true"}
    ):
        raise pytest.UsageError("live tests cannot run in CI or with --no-network")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--run-live"):
        return
    live = [item for item in items if item.get_closest_marker("live")]
    items[:] = [item for item in items if not item.get_closest_marker("live")]
    config.hook.pytest_deselected(items=live)


@pytest.fixture(autouse=True)
def _offline_by_default(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch):
    if request.config.getoption("--run-live") and request.node.get_closest_marker("live"):
        return
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    connect = socket.socket.connect
    connect_ex = socket.socket.connect_ex
    sendto = socket.socket.sendto

    def guarded_connect(sock, address):
        if sock.family in {socket.AF_INET, socket.AF_INET6}:
            raise RuntimeError("Network access is disabled for offline tests")
        return connect(sock, address)

    def guarded_connect_ex(sock, address):
        if sock.family in {socket.AF_INET, socket.AF_INET6}:
            raise RuntimeError("Network access is disabled for offline tests")
        return connect_ex(sock, address)

    def no_dns(*args, **kwargs):
        raise RuntimeError("Network access is disabled for offline tests")

    def guarded_sendto(sock, *args):
        if sock.family in {socket.AF_INET, socket.AF_INET6}:
            raise RuntimeError("Network access is disabled for offline tests")
        return sendto(sock, *args)

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", guarded_connect_ex)
    monkeypatch.setattr(socket.socket, "sendto", guarded_sendto)
    monkeypatch.setattr(socket, "getaddrinfo", no_dns)
    monkeypatch.setattr(socket, "gethostbyname", no_dns)
    monkeypatch.setattr(socket, "gethostbyname_ex", no_dns)


# --------------------------------------------------------------------- fakes
@dataclass
class FakeEvidenceProvider:
    items: list[Evidence] = field(default_factory=list)

    def retrieve(self, q: Query, budget: RetrievalBudget) -> Sequence[Evidence]:
        return self.items[: budget.top_k_documents]


@dataclass
class FakeFactMemory:
    """Product-scoped by construction, so the leakage contract test is meaningful."""

    store: dict[ProductId, list[FactVersion]] = field(default_factory=dict)
    _n: int = 0

    def recall(self, scope: ProductScope, q: Query) -> Sequence[Fact]:
        if scope.product_id is None:
            return []
        return [v.fact for v in self.store.get(scope.product_id, [])]

    def commit(self, fact: Fact, validation: ValidationOutcome) -> FactId:
        if validation is not ValidationOutcome.VALIDATED:
            raise ValueError("refusing to store an unvalidated fact")
        self._n += 1
        fid = FactId(f"f{self._n}")
        self.store.setdefault(fact.product_id, []).append(FactVersion(id=fid, fact=fact))
        return fid

    def supersede(self, old: FactId, new: Fact, reason: str) -> FactId:
        self._n += 1
        fid = FactId(f"f{self._n}")
        self.store.setdefault(new.product_id, []).append(
            FactVersion(id=fid, fact=new, supersedes=old, reason=reason)
        )
        return fid

    def history(self, subject: str, scope: ProductScope) -> Sequence[FactVersion]:
        if scope.product_id is None:
            return []
        return [v for v in self.store.get(scope.product_id, []) if v.fact.subject == subject]


@dataclass
class FakeSubstrateRegistry:
    graph: FactGraph = field(default_factory=FactGraph)
    substrates: list[Substrate] = field(default_factory=list)

    def mounted(self) -> Sequence[Substrate]:
        return self.substrates

    def facts_for(self, subject: SubjectRef) -> FactGraph:
        return self.graph

    def coverage_report(self) -> CoverageReport:
        return CoverageReport()


@dataclass
class FakeSymbolic:
    result: EntailmentResult = field(default_factory=EntailmentResult)

    def entail(self, graph: FactGraph) -> EntailmentResult:
        return self.result

    def validate(self, claims: Sequence[Any], graph: FactGraph) -> ValidationReport:
        return ValidationReport(checked=len(claims))


@dataclass
class FakeSchemaRegistry:
    def profiles(self) -> Sequence[SchemaProfile]:
        return [SchemaProfile(id=ProfileId("eu-dpp"), title="EU DPP", layer="regulatory")]

    def conform(self, record: DPPRecord, profile: ProfileId) -> ConformanceReport:
        return ConformanceReport(profile=profile)


@dataclass
class FakeImpactEngine:
    def assess(self, subject: SubjectRef, req: ImpactRequest) -> ImpactResult:
        return ImpactResult(subject=subject, indicator=req.indicator, total=1.0, unit="kg CO2e")

    def subjects(self) -> Sequence[SubjectRef]:
        return (SubjectRef(id="fake_product"),)

    def explain(self, result: ImpactResult, target: str) -> Provenance:
        return Provenance(target=target)


@dataclass
class FakeRepository:
    records: dict[DppId, DPPRecord] = field(default_factory=dict)

    def get(self, dpp_id: DppId) -> DPPRecord | None:
        return self.records.get(dpp_id)

    def put(self, record: DPPRecord) -> None:
        self.records[record.dpp_id] = record

    def list_ids(self) -> Sequence[DppId]:
        return list(self.records)


@dataclass
class FakeSignals:
    fixed: float = 0.9

    def emit(
        self,
        q: Query,
        pack: ContextPack,
        entailment: EntailmentResult | None,
        generation_probability: float | None = None,
    ) -> SignalVector:
        return SignalVector(
            {
                SignalName("retrieval_margin"): self.fixed,
                SignalName("snippet_agreement"): self.fixed,
                SignalName("symbolic_fired"): 1.0 if (entailment and entailment.fired) else 0.0,
            }
        )

    def names(self) -> Sequence[SignalName]:
        return [SignalName("retrieval_margin"), SignalName("snippet_agreement")]


@dataclass
class FakeCalibrator:
    _id: CalibratorId = CalibratorId("fake-identity")

    @property
    def id(self) -> CalibratorId:
        return self._id

    def fit(self, signals: Sequence[SignalVector], correct: Sequence[bool]) -> None:
        return None

    def calibrate(self, signals: SignalVector, raw: float) -> float:
        return max(0.0, min(1.0, raw))

    def diagnostics(self) -> CalibrationDiagnostics:
        return CalibrationDiagnostics()


@dataclass
class FakeSelective:
    def threshold_for(self, coverage_target: float) -> float:
        return 1.0 - coverage_target

    def decide(self, confidence: Confidence, point: OperatingPoint) -> Decision:
        return Decision.ANSWER if point.admits(confidence) else Decision.ABSTAIN


@dataclass
class NullDataTrust:
    """The shipped implementation in both modes. Says nothing, honestly."""

    def assess(
        self, subject: SubjectRef, attribute: str, point: OperatingPoint
    ) -> DataTrust | None:
        return None

    @property
    def is_null(self) -> bool:
        return True


@dataclass
class FakeGrounding:
    verdict: GroundingVerdict = GroundingVerdict.FULLY_GROUNDED
    unresolved: tuple[Any, ...] = ()

    def verify(self, answer: str, pack: ContextPack) -> GroundingReport:
        if self.verdict is GroundingVerdict.UNRESOLVED_CLAIMS:
            return GroundingReport(
                claims_total=len(self.unresolved),
                claims_resolved=0,
                unresolved=self.unresolved,
                verdict=self.verdict,
            )
        return GroundingReport(claims_total=1, claims_resolved=1, verdict=self.verdict)


@dataclass
class FakeLLM:
    reply: str = "The declared capacity is 60 kWh [e1]."

    def compose(
        self,
        instruction: str,
        pack: ContextPack,
        *,
        model: str | None = None,
        max_tokens: int = 512,
    ) -> str:
        return self.reply

    def structured(
        self,
        instruction: str,
        pack: ContextPack,
        schema: Mapping[str, Any],
        *,
        model: str | None = None,
    ) -> Mapping[str, Any]:
        return {}

    def embed(self, texts: Sequence[str]) -> Sequence[Sequence[float]]:
        return [[0.0] for _ in texts]


@dataclass
class FakeLedger:
    steps: dict[CorrelationId, list[TraceStep]] = field(default_factory=dict)

    def record(self, cid: CorrelationId, step: TraceStep) -> None:
        self.steps.setdefault(cid, []).append(step)

    def trace(self, cid: CorrelationId) -> Trace:
        return Trace(
            correlation_id=cid,
            mode=BackendMode.NORMAL,
            steps=tuple(self.steps.get(cid, [])),
        )


@dataclass
class FakeDecisionPolicy:
    def act(self, signals: SignalVector, steps_taken: int) -> str:
        return "answer"

    def actions(self) -> Sequence[str]:
        return ["recall", "retrieve", "entail", "answer", "abstain"]


# ------------------------------------------------------------------ fixtures
@pytest.fixture(params=MODES, ids=lambda m: m.value)
def mode(request: pytest.FixtureRequest) -> BackendMode:
    return request.param


@pytest.fixture
def evidence_items() -> list[Evidence]:
    return [
        Evidence(
            id=EvidenceId("e1"),
            kind=EvidenceKind.PASSAGE,
            text="The battery pack has a declared capacity of 60 kWh.",
            ref="doc:spec#p3",
            score=0.91,
        ),
        Evidence(
            id=EvidenceId("e2"),
            kind=EvidenceKind.PASSAGE,
            text="Chemistry is NMC811.",
            ref="doc:spec#p7",
            score=0.62,
        ),
    ]


@pytest.fixture
def bundle(mode: BackendMode, evidence_items: list[Evidence]) -> ProviderBundle:
    """A fully faked bundle. Every port satisfied, nothing touching the network."""
    return ProviderBundle(
        mode=mode,
        evidence=FakeEvidenceProvider(evidence_items),
        memory=FakeFactMemory(),
        substrates=FakeSubstrateRegistry(),
        symbolic=FakeSymbolic(),
        schemas=FakeSchemaRegistry(),
        impact=FakeImpactEngine(),
        records=FakeRepository(),
        signals=FakeSignals(),
        calibrator=FakeCalibrator(),
        selective=FakeSelective(),
        data_trust=NullDataTrust(),
        grounding=FakeGrounding(),
        llm=FakeLLM(),
        ledger=FakeLedger(),
        policy=FakeDecisionPolicy(),
    )


@pytest.fixture
def query() -> Query:
    return Query(
        text="What is the declared capacity?",
        scope=ProductScope(product_id=ProductId("bat-60"), domain="battery"),
        correlation_id=CorrelationId("test-cid"),
    )

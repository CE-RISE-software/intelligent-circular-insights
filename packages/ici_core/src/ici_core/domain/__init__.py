# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Domain types: the vocabulary every other package speaks."""

from __future__ import annotations

from ici_core.domain.claims import Claim, GroundingReport, GroundingVerdict
from ici_core.domain.confidence import (
    CalibrationDiagnostics,
    Confidence,
    OperatingPoint,
    SignalVector,
)
from ici_core.domain.datatrust import CredibleInterval, DataTrust
from ici_core.domain.envelope import (
    Decision,
    ProvenanceKind,
    ProvenanceLink,
    QuantifiedValue,
    ReliabilityEnvelope,
)
from ici_core.domain.errors import (
    BudgetExceeded,
    CapabilityError,
    IciError,
    InvariantViolation,
    SubstrateUnavailable,
)
from ici_core.domain.evidence import ContextPack, Evidence, EvidenceKind
from ici_core.domain.facts import Fact, FactVersion, ValidationOutcome
from ici_core.domain.impact import (
    ImpactContribution,
    ImpactRequest,
    ImpactResult,
    Provenance,
    SubjectRef,
)
from ici_core.domain.modes import DEFAULT_MODE, BackendMode
from ici_core.domain.query import ProductScope, Query, RetrievalBudget
from ici_core.domain.record import (
    ConformanceReport,
    DPPRecord,
    SchemaProfile,
    Violation,
    ViolationKind,
)
from ici_core.domain.rules import (
    EntailmentResult,
    FactGraph,
    RuleTrace,
    Triple,
    ValidationReport,
)
from ici_core.domain.substrate import CoverageReport, Substrate, SubstrateCoverage
from ici_core.domain.trace import CostAccount, Trace, TraceStep

__all__ = [
    "DEFAULT_MODE",
    "BackendMode",
    "BudgetExceeded",
    "CalibrationDiagnostics",
    "CapabilityError",
    "Claim",
    "Confidence",
    "ConformanceReport",
    "ContextPack",
    "CostAccount",
    "CoverageReport",
    "CredibleInterval",
    "DPPRecord",
    "DataTrust",
    "Decision",
    "EntailmentResult",
    "Evidence",
    "EvidenceKind",
    "Fact",
    "FactGraph",
    "FactVersion",
    "GroundingReport",
    "GroundingVerdict",
    "IciError",
    "ImpactContribution",
    "ImpactRequest",
    "ImpactResult",
    "InvariantViolation",
    "OperatingPoint",
    "ProductScope",
    "Provenance",
    "ProvenanceKind",
    "ProvenanceLink",
    "QuantifiedValue",
    "Query",
    "ReliabilityEnvelope",
    "RetrievalBudget",
    "RuleTrace",
    "SchemaProfile",
    "SignalVector",
    "SubjectRef",
    "Substrate",
    "SubstrateCoverage",
    "SubstrateUnavailable",
    "Trace",
    "TraceStep",
    "Triple",
    "ValidationOutcome",
    "ValidationReport",
    "Violation",
    "ViolationKind",
]

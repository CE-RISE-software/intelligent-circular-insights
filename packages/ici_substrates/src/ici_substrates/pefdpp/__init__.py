"""The WP3 PEFDPP substrate: graph, LCA engine, competency questions, SPARQL guard."""

from __future__ import annotations

from ici_substrates.pefdpp.adapter import (
    NAMESPACE,
    PEFDPP_SUBSTRATE,
    PefdppImpactEngine,
    PefdppSubstrateRegistry,
    build_services,
)
from ici_substrates.pefdpp.graph import PefdppGraphService
from ici_substrates.pefdpp.lca import PefdppLcaService
from ici_substrates.pefdpp.questions import (
    TOTAL_IN_PAPER,
    CompetencyQuestion,
    CoverageSummary,
    QuestionResult,
    load_questions,
)
from ici_substrates.pefdpp.sparql import UnsafeQueryError, check, clamp_limit

__all__ = [
    "NAMESPACE",
    "PEFDPP_SUBSTRATE",
    "TOTAL_IN_PAPER",
    "CompetencyQuestion",
    "CoverageSummary",
    "PefdppGraphService",
    "PefdppImpactEngine",
    "PefdppLcaService",
    "PefdppSubstrateRegistry",
    "QuestionResult",
    "UnsafeQueryError",
    "build_services",
    "check",
    "clamp_limit",
    "load_questions",
]

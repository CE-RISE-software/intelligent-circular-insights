# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""What a use case is given.

A ``ProviderBundle`` is the set of adapters bound for one backend mode. The
composition root builds one per mode at startup and holds them immutably; a use
case receives one and never asks which mode it is. That is the whole of ADR 0002
as far as the domain is concerned.
"""

from __future__ import annotations

from dataclasses import dataclass

from ici_core.domain.modes import BackendMode
from ici_core.ports import (
    Calibrator,
    ConfidenceSignals,
    DataTrustProvider,
    DecisionPolicy,
    DPPRepository,
    EvidenceProvider,
    FactMemory,
    GroundingVerifier,
    ImpactEngine,
    LLMProvider,
    ProvenanceLedger,
    SchemaRegistry,
    SelectivePolicy,
    SubstrateRegistry,
    SymbolicValidator,
)


@dataclass(frozen=True)
class ProviderBundle:
    """Every adapter bound for one mode. Immutable; built once at startup."""

    mode: BackendMode
    evidence: EvidenceProvider
    memory: FactMemory
    substrates: SubstrateRegistry
    symbolic: SymbolicValidator
    schemas: SchemaRegistry
    impact: ImpactEngine
    records: DPPRepository
    signals: ConfidenceSignals
    calibrator: Calibrator
    selective: SelectivePolicy
    data_trust: DataTrustProvider
    grounding: GroundingVerifier
    llm: LLMProvider
    ledger: ProvenanceLedger
    policy: DecisionPolicy

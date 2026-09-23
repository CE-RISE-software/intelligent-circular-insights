# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Mounted knowledge: the CE-RISE catalogue, EU DPP schemas, carbon factors."""

from __future__ import annotations

from ici_substrates.carbon import CarbonCalculationService, CsvFactorImpactEngine
from ici_substrates.layered import (
    ENGINE_FACTORS,
    ENGINE_GRAPH,
    LayeredImpactEngine,
    ModeAwareImpactEngine,
)
from ici_substrates.layered_schemas import LayeredSchemaRegistry
from ici_substrates.records import InMemoryRepository
from ici_substrates.registry import (
    CeRiseModel,
    CeRiseModelRegistry,
    CompositeSubstrateRegistry,
    JsonSchemaRegistry,
    load_catalog,
)

__all__ = [
    "ENGINE_FACTORS",
    "ENGINE_GRAPH",
    "CarbonCalculationService",
    "CeRiseModel",
    "CeRiseModelRegistry",
    "CompositeSubstrateRegistry",
    "CsvFactorImpactEngine",
    "InMemoryRepository",
    "JsonSchemaRegistry",
    "LayeredImpactEngine",
    "LayeredSchemaRegistry",
    "ModeAwareImpactEngine",
    "load_catalog",
]

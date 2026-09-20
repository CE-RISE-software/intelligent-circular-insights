# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Mounted knowledge: the CE-RISE catalogue, EU DPP schemas, carbon factors."""

from __future__ import annotations

from ici_substrates.carbon import CarbonCalculationService, CsvFactorImpactEngine
from ici_substrates.records import InMemoryRepository
from ici_substrates.registry import (
    CeRiseModel,
    CeRiseModelRegistry,
    JsonSchemaRegistry,
    load_catalog,
)

__all__ = [
    "CarbonCalculationService",
    "CeRiseModel",
    "CeRiseModelRegistry",
    "CsvFactorImpactEngine",
    "InMemoryRepository",
    "JsonSchemaRegistry",
    "load_catalog",
]

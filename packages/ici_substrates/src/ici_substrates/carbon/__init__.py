# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Deterministic carbon calculation over published emission factors."""

from __future__ import annotations

from ici_substrates.carbon.adapter import CsvFactorImpactEngine
from ici_substrates.carbon.engine import CarbonCalculationService

__all__ = ["CarbonCalculationService", "CsvFactorImpactEngine"]

# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Substrate and schema registries."""

from __future__ import annotations

from ici_substrates.registry.catalog import (
    CE_RISE_SOURCE,
    CeRiseModel,
    CeRiseModelRegistry,
    load_catalog,
)
from ici_substrates.registry.schemas import EU_DPP, JsonSchemaRegistry

__all__ = [
    "CE_RISE_SOURCE",
    "EU_DPP",
    "CeRiseModel",
    "CeRiseModelRegistry",
    "JsonSchemaRegistry",
    "load_catalog",
]

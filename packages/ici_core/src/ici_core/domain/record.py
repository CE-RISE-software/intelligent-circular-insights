# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""The canonical product record, and what conformance checking says about one.

``DPPRecord`` is deliberately thin: a canonical identity plus the payload as it
was supplied. Mappers in the substrate adapters translate to and from the EU DPP
schema and the CE-RISE modules. Putting a rich fixed shape here would make the
core take sides between two schemas it is supposed to be neutral about.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ici_core.domain.ids import DppId, ProfileId


@dataclass(frozen=True)
class DPPRecord:
    """A product passport as supplied, with its identity lifted out."""

    dpp_id: DppId
    payload: Mapping[str, Any] = field(default_factory=dict)
    applied_schemas: tuple[str, ...] = ()
    schema_version: str | None = None


class ViolationKind(str, Enum):
    MISSING_REQUIRED = "missing_required"
    TYPE_MISMATCH = "type_mismatch"
    ENUM_VIOLATION = "enum_violation"
    SHAPE_VIOLATION = "shape_violation"
    CROSS_MODULE_INCONSISTENCY = "cross_module_inconsistency"


@dataclass(frozen=True)
class Violation:
    """One typed conformance failure, located precisely enough to fix.

    ``location`` is a JSON Pointer for schema checks and a focus node IRI for
    SHACL. A bare boolean 'invalid' is useless to whoever has to repair the record.
    """

    kind: ViolationKind
    location: str
    message: str
    profile: ProfileId | None = None
    expected: str | None = None
    actual: str | None = None


@dataclass(frozen=True)
class ConformanceReport:
    profile: ProfileId
    violations: tuple[Violation, ...] = ()
    checked_paths: int = 0

    @property
    def conforms(self) -> bool:
        return not self.violations


@dataclass(frozen=True)
class SchemaProfile:
    """One checkable profile: an EU DPP schema, a CE-RISE module, a SHACL shape."""

    id: ProfileId
    title: str
    layer: str
    version: str | None = None
    source: str | None = None

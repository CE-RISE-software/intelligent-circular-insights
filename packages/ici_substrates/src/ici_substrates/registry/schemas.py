# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Conformance checking against the EU DPP JSON Schema.

The deliverable is never a boolean. Whoever has to repair a record needs to know
which field, which rule, and what was expected — so violations carry a JSON
Pointer and a typed kind.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ici_core.domain.ids import ProfileId
from ici_core.domain.record import (
    ConformanceReport,
    DPPRecord,
    SchemaProfile,
    Violation,
    ViolationKind,
)
from ici_substrates.paths import SCHEMA_ROOT

EU_DPP = ProfileId("eu-dpp")

_KIND_BY_VALIDATOR = {
    "required": ViolationKind.MISSING_REQUIRED,
    "type": ViolationKind.TYPE_MISMATCH,
    "enum": ViolationKind.ENUM_VIOLATION,
    "const": ViolationKind.ENUM_VIOLATION,
}


@dataclass
class JsonSchemaRegistry:
    """Implements ``SchemaRegistry`` for Normal mode."""

    schema_path: Path = field(default_factory=lambda: SCHEMA_ROOT / "eu_dpp_schema.json")
    _schema: dict[str, Any] | None = field(default=None, init=False, repr=False)

    @property
    def schema(self) -> dict[str, Any]:
        if self._schema is None:
            self._schema = json.loads(self.schema_path.read_text())
        return self._schema

    # -- SchemaRegistry -----------------------------------------------------
    def profiles(self) -> Sequence[SchemaProfile]:
        return [
            SchemaProfile(
                id=EU_DPP,
                title=str(self.schema.get("title", "EU Digital Product Passport")),
                layer="regulatory",
                version=str(self.schema.get("$id", "")) or None,
                source=str(self.schema_path.name),
            )
        ]

    def conform(self, record: DPPRecord, profile: ProfileId) -> ConformanceReport:
        if profile != EU_DPP:
            return ConformanceReport(
                profile=profile,
                violations=(
                    Violation(
                        kind=ViolationKind.SHAPE_VIOLATION,
                        location="/",
                        message=f"no such profile {profile!r} in this mode",
                        profile=profile,
                    ),
                ),
            )

        from jsonschema import Draft202012Validator, FormatChecker
        from referencing import Registry

        try:
            json.dumps(dict(record.payload), allow_nan=False)
        except (ValueError, TypeError):
            return ConformanceReport(
                profile=profile,
                violations=(
                    Violation(
                        kind=ViolationKind.TYPE_MISMATCH,
                        location="/",
                        message="record contains a non-JSON or non-finite value",
                        profile=profile,
                    ),
                ),
            )
        validator = Draft202012Validator(
            self.schema, format_checker=FormatChecker(), registry=Registry()
        )
        violations = [
            _to_violation(error, profile)
            for error in sorted(validator.iter_errors(dict(record.payload)), key=str)
        ]
        materials = record.payload.get("materials")
        if (
            isinstance(materials, list)
            and materials
            and all(
                isinstance(row, dict) and type(row.get("share_pct")) in (int, float)
                for row in materials
            )
            and not 95 <= sum(row["share_pct"] for row in materials) <= 105
        ):
            violations.append(
                Violation(
                    kind=ViolationKind.SHAPE_VIOLATION,
                    location="/materials",
                    message="material shares must total 95 to 105 percent",
                    profile=profile,
                )
            )
        return ConformanceReport(
            profile=profile,
            violations=tuple(violations),
            checked_paths=len(record.payload),
        )


def _to_violation(error: Any, profile: ProfileId) -> Violation:
    pointer = "/" + "/".join(
        str(part).replace("~", "~0").replace("/", "~1") for part in error.absolute_path
    )
    return Violation(
        kind=_KIND_BY_VALIDATOR.get(error.validator, ViolationKind.SHAPE_VIOLATION),
        location=pointer if pointer != "/" else "/",
        message=str(error.message)[:300],
        profile=profile,
        expected=str(error.validator_value)[:120],
        actual=type(error.instance).__name__,
    )

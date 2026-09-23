# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Conformance checking against a schema profile.

The deliverable is never a boolean. Whoever has to repair a record needs to know
which field, which rule, and what was expected — so violations carry a JSON Pointer
and a typed kind.

**Two kinds of profile, and they answer different questions.**

`eu-dpp` is a hand-written EU DPP schema, CIRPASS-2 aligned. It declares required
fields, so it answers *is this passport complete?*

`ce-rise:<model>` profiles are generated from the vendored CE-RISE LinkML data
models by `tooling/build_ce_rise_profiles.py`. They answer a different question —
*does this record use CE-RISE vocabulary correctly?* — and they are honestly weaker:
the models declare **no required fields at their roots**, so an empty object
conforms to every one of them. What they do catch is a property the model has never
heard of and a value of the wrong type, which is exactly what a vocabulary check
should catch.

Offering both, labelled by what they check, is the point. Presenting either alone as
"CE-RISE conformance" would be misleading in opposite directions: the first is not
the consortium's model, and the second would pass a passport with nothing in it.

Only models that declare a `tree_root` are offered. The other eleven are class
libraries — vocabularies to draw from rather than documents to validate — and
inventing a root for them would be asserting a document shape their authors did not.
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

CE_RISE_PREFIX = "ce-rise:"
CE_RISE_GENERATED = SCHEMA_ROOT / "ce-rise" / "_generated"

# The root class each model declares with `tree_root: true`. Read from the model
# rather than guessed: a model with no declared root has no defined document shape,
# and picking one for it would be inventing a claim its authors did not make.
CE_RISE_ROOTS: dict[str, str] = {
    "diagnostic-results": "DiagnosticResults",
    "dp-record-metadata": "DPRecordMetadata",
    "lci-dataset": "LCIDataset",
    "product-system": "ProductSystem",
    "traceability-and-life-cycle-events": "TraceabilityLifecycleEvents",
    "usage-and-maintenance": "UsageAndMaintenance",
}

_KIND_BY_VALIDATOR = {
    "required": ViolationKind.MISSING_REQUIRED,
    "type": ViolationKind.TYPE_MISMATCH,
    "enum": ViolationKind.ENUM_VIOLATION,
    "const": ViolationKind.ENUM_VIOLATION,
    "additionalProperties": ViolationKind.UNKNOWN_PROPERTY,
    "unevaluatedProperties": ViolationKind.UNKNOWN_PROPERTY,
}


@dataclass
class JsonSchemaRegistry:
    """Implements ``SchemaRegistry`` for Normal mode."""

    schema_path: Path = field(default_factory=lambda: SCHEMA_ROOT / "eu_dpp_schema.json")
    _schema: dict[str, Any] | None = field(default=None, init=False, repr=False)
    _ce_rise_cache: dict[str, dict[str, Any]] = field(default_factory=dict, init=False, repr=False)

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
            ),
            *self._ce_rise_profiles(),
        ]

    def default_profile(self) -> ProfileId:
        """The regulatory profile. The CE-RISE models are vocabularies, not defaults.

        Checking an unspecified record against one of them would report conformance
        for an empty passport, because they declare no required fields.
        """
        return EU_DPP

    def _ce_rise_profiles(self) -> list[SchemaProfile]:
        """The CE-RISE models that define a document, generated from their LinkML.

        Absent from a checkout that has not run `tooling/build_ce_rise_profiles.py`,
        which is deliberate: offering a profile whose schema is missing would fail at
        validation time instead of simply not being on the list.
        """
        out: list[SchemaProfile] = []
        for name, root in sorted(CE_RISE_ROOTS.items()):
            if not (CE_RISE_GENERATED / f"{name}.json").is_file():
                continue
            out.append(
                SchemaProfile(
                    id=ProfileId(f"{CE_RISE_PREFIX}{name}"),
                    title=f"CE-RISE {name.replace('-', ' ')} ({root})",
                    # Named for what it checks. These models declare no required
                    # fields, so this is a vocabulary check, not a completeness one,
                    # and the layer should not let anyone assume otherwise.
                    layer="ce-rise-vocabulary",
                    version=None,
                    source=f"ce-rise/_generated/{name}.json",
                )
            )
        return out

    def _ce_rise_schema(self, profile: ProfileId) -> dict[str, Any] | None:
        """The generated schema for a CE-RISE profile, rooted at its tree_root class."""
        name = str(profile)[len(CE_RISE_PREFIX) :]
        root = CE_RISE_ROOTS.get(name)
        path = CE_RISE_GENERATED / f"{name}.json"
        if root is None or not path.is_file():
            return None
        if name not in self._ce_rise_cache:
            document = json.loads(path.read_text())
            definitions = document.get("$defs", {})
            if root not in definitions:
                return None
            # Root the schema at the declared class while keeping every $def
            # reachable, since the class references its neighbours by $ref.
            self._ce_rise_cache[name] = {"$defs": definitions, **definitions[root]}
        return self._ce_rise_cache[name]

    def conform(self, record: DPPRecord, profile: ProfileId) -> ConformanceReport:
        schema = self.schema if profile == EU_DPP else None
        if schema is None and str(profile).startswith(CE_RISE_PREFIX):
            schema = self._ce_rise_schema(profile)
        if schema is None:
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
            schema, format_checker=FormatChecker(), registry=Registry()
        )
        violations = [
            _to_violation(error, profile)
            for error in sorted(validator.iter_errors(dict(record.payload)), key=_error_order)
        ]
        materials = record.payload.get("materials") if profile == EU_DPP else None
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


def _error_order(error: Any) -> tuple[tuple[str, ...], str, str]:
    """A stable sort key: where, then what, then the message.

    This used to be ``key=str``, which is a trap with a large schema.
    ``ValidationError.__str__`` renders the failing schema *and* the instance into
    the message -- 917,000 characters for one error against a generated CE-RISE
    model -- so sorting a single violation cost 60 ms, and a routed check that
    consults six candidates cost about 290 ms of pure string formatting. Normal
    mode never noticed, because the hand-written EU DPP schema is small.

    Sorting by location is also the better order for the reader: violations arrive
    grouped by the part of the record they concern, which is how someone repairing
    one works through them.
    """
    return (
        tuple(str(part) for part in error.absolute_path),
        str(error.validator or ""),
        str(error.message),
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

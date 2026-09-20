# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Evidence-backed DPP repair/synthesis. The bundled schema is a demo schema.

Support is deliberately stricter than text entailment: the same JSON Pointer,
same typed value, and same product identity must occur in a supplied JSON record.
Plain prose is not sufficient to assert regulatory conformity or measurements.
Callers must supply structured evidence or report that the value cannot be grounded.
At the user's request, model-training suggestions are returned separately at
confidence <= 0.3, labelled unverified and requiring review. They are never applied.
"""

from __future__ import annotations

import copy
from collections.abc import Iterator, Mapping
from dataclasses import asdict, dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry

from ici_core.domain.evidence import ContextPack
from ici_core.ports import LLMProvider
from ici_llm.audit import AuditLog
from ici_llm.errors import InvalidOutput
from ici_llm.prompts import PromptRegistry, canonical
from ici_llm.provider import _json_object, validate_object

FILL_SCHEMA: dict[str, Any] = {
    "x-ici-unverified-suggestions": True,
    "type": "object",
    "required": ["fills", "suggestions"],
    "additionalProperties": False,
    "properties": {
        "suggestions": {
            "type": "array",
            "maxItems": 64,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["path", "value", "rationale", "confidence"],
                "properties": {
                    "path": {"type": "string", "pattern": "^/"},
                    "value": {},
                    "rationale": {"type": "string", "minLength": 1},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                },
            },
        },
        "fills": {
            "type": "array",
            "maxItems": 64,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["path", "value", "evidence_id", "confidence"],
                "properties": {
                    "path": {"type": "string", "pattern": "^/"},
                    "value": {},
                    "evidence_id": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                },
            },
        },
    },
}
SYNTHESIS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["record"],
    "additionalProperties": False,
    "properties": {"record": {"type": "object"}},
}


def eu_dpp_schema() -> dict[str, Any]:
    resource = files("ici_llm").joinpath("schema_data").joinpath("eu_dpp_schema.json")
    text = (
        resource.read_text(encoding="utf-8")
        if resource.is_file()
        else (Path(__file__).resolve().parents[2] / "schemas" / "eu_dpp_schema.json").read_text(
            encoding="utf-8"
        )
    )
    return _json_object(text)


def _escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _parts(pointer: str) -> list[str]:
    if not pointer.startswith("/"):
        raise ValueError("a non-root JSON Pointer is required")
    return [p.replace("~1", "/").replace("~0", "~") for p in pointer[1:].split("/")]


def at_pointer(value: Any, pointer: str) -> Any:
    for part in _parts(pointer):
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def _set(value: dict[str, Any], pointer: str, replacement: Any) -> None:
    parts = _parts(pointer)
    parent: Any = value
    for part in parts[:-1]:
        parent = parent[int(part)] if isinstance(parent, list) else parent[part]
    if isinstance(parent, list):
        parent[int(parts[-1])] = copy.deepcopy(replacement)
    else:
        parent[parts[-1]] = copy.deepcopy(replacement)


def _leaves(value: Any, path: str = "") -> Iterator[tuple[str, Any]]:
    if isinstance(value, dict) and value:
        for key, child in value.items():
            yield from _leaves(child, f"{path}/{_escape(key)}")
    elif isinstance(value, list) and value:
        for index, child in enumerate(value):
            yield from _leaves(child, f"{path}/{index}")
    else:
        yield path, value


@dataclass(frozen=True)
class RecordIssue:
    path: str
    reason: str


@dataclass(frozen=True)
class ValueSupport:
    path: str
    evidence_id: str
    evidence_ref: str
    source_pointer: str


@dataclass(frozen=True)
class GroundedFill:
    path: str
    value: Any
    support: ValueSupport
    confidence: float  # Model feature only, never a calibrated output probability.


@dataclass(frozen=True)
class UnverifiedSuggestion:
    """A model-prior candidate for human review, never evidence or an applied fill."""

    path: str
    value: Any
    rationale: str
    confidence: float
    source: str = "model_training"
    status: str = "unverified"
    requires_review: bool = True


@dataclass(frozen=True)
class RepairResult:
    record: dict[str, Any]
    fills: tuple[GroundedFill, ...]
    cannot_be_grounded: tuple[RecordIssue, ...]
    rejected: tuple[RecordIssue, ...] = ()
    suggestions: tuple[UnverifiedSuggestion, ...] = ()

    @property
    def conforms(self) -> bool:
        return not self.cannot_be_grounded


@dataclass(frozen=True)
class SynthesisResult:
    record: dict[str, Any]
    support: tuple[ValueSupport, ...]


class RecordGenerationError(InvalidOutput):
    def __init__(self, issues: tuple[RecordIssue, ...]) -> None:
        self.issues = issues
        super().__init__("The DPP cannot be grounded or does not conform after one repair retry.")


def _same_product(seed: Mapping[str, Any], record: Mapping[str, Any]) -> bool:
    left, right = seed.get("product"), record.get("product")
    if not isinstance(left, dict) or not isinstance(right, dict):
        return False
    if left.get("id"):
        return left["id"] == right.get("id") and all(
            left[k] == right.get(k) for k in ("brand", "model") if left.get(k)
        )
    return all(left.get(k) and left[k] == right.get(k) for k in ("brand", "model"))


class RecordComposer:
    def __init__(
        self,
        provider: LLMProvider,
        *,
        audit: AuditLog | None = None,
        prompts: PromptRegistry | None = None,
        schema: Mapping[str, Any] | None = None,
    ) -> None:
        self.provider, self.audit = provider, audit or AuditLog()
        self.prompts = prompts or PromptRegistry()
        self.schema = dict(schema) if schema is not None else eu_dpp_schema()
        Draft202012Validator.check_schema(self.schema)
        self.validator = Draft202012Validator(
            self.schema, format_checker=FormatChecker(), registry=Registry()
        )

    def validate(self, record: Mapping[str, Any]) -> tuple[RecordIssue, ...]:
        try:
            canonical(record)
        except (ValueError, TypeError):
            return (RecordIssue("", "non-JSON or non-finite value"),)
        issues: list[RecordIssue] = []
        for error in self.validator.iter_errors(record):
            path = "".join(f"/{_escape(str(p))}" for p in error.absolute_path)
            if error.validator == "required" and isinstance(error.instance, dict):
                issues.extend(
                    RecordIssue(f"{path}/{_escape(k)}", "required property is missing")
                    for k in error.validator_value
                    if k not in error.instance
                )
            else:
                # Do not echo untrusted values (or credentials) in errors/audit logs.
                issues.append(RecordIssue(path, f"violates {error.validator}"))
        materials = record.get("materials")
        if (
            isinstance(materials, list)
            and materials
            and all(
                isinstance(row, dict) and type(row.get("share_pct")) in (int, float)
                for row in materials
            )
            and not 95 <= sum(row["share_pct"] for row in materials) <= 105
        ):
            issues.append(RecordIssue("/materials", "material shares must total 95 to 105 percent"))
        return tuple(sorted(set(issues), key=lambda i: (i.path, i.reason)))

    def _sources(
        self, seed: Mapping[str, Any], pack: ContextPack
    ) -> dict[str, tuple[str, dict[str, Any]]]:
        sources: dict[str, tuple[str, dict[str, Any]]] = {}
        for evidence in pack.items:
            try:
                record = _json_object(evidence.text)
            except InvalidOutput:
                continue
            if _same_product(seed, record):
                sources[str(evidence.id)] = (evidence.ref, record)
        return sources

    @staticmethod
    def _support(
        path: str,
        value: Any,
        sources: dict[str, tuple[str, dict[str, Any]]],
        evidence_id: str | None = None,
    ) -> ValueSupport | None:
        for identity, (ref, source) in sources.items():
            if evidence_id is not None and evidence_id != identity:
                continue
            try:
                if canonical(at_pointer(source, path)) == canonical(value):
                    return ValueSupport(path, identity, ref, path)
            except (KeyError, IndexError, TypeError, ValueError):
                continue
        return None

    def repair(
        self, record: Mapping[str, Any], pack: ContextPack, *, suggest_from_training: bool = True
    ) -> RepairResult:
        preview = copy.deepcopy(dict(record))
        issues = self.validate(preview)
        if not issues:
            return RepairResult(preview, (), ())
        sources = self._sources(record, pack)
        if not sources and not suggest_from_training:
            self.audit.guard("repair_has_structured_evidence", False)
            return RepairResult(preview, (), issues)
        prompt = self.prompts.render(
            "repair",
            record=canonical(record),
            violations=canonical([asdict(i) for i in issues]),
            training_suggestions=canonical(suggest_from_training),
            schema=canonical(self.schema),
        )
        self.audit.prompt(prompt)
        output = validate_object(
            dict(self.provider.structured(prompt.text, pack, FILL_SCHEMA)), FILL_SCHEMA
        )
        accepted: list[GroundedFill] = []
        rejected: list[RecordIssue] = []
        allowed = {i.path for i in issues}
        seen: set[str] = set()
        for fill in output["fills"]:
            path, value = fill["path"], fill["value"]
            support = self._support(path, value, sources, fill["evidence_id"])
            if path not in allowed or path in seen or support is None:
                rejected.append(
                    RecordIssue(path, "cannot be grounded or is not an eligible repair")
                )
                continue
            seen.add(path)
            candidate = copy.deepcopy(preview)
            try:
                _set(candidate, path, value)
            except (KeyError, IndexError, ValueError, TypeError):
                rejected.append(RecordIssue(path, "invalid repair location"))
                continue
            before, after = set(self.validate(preview)), set(self.validate(candidate))
            if after - before or any(
                i.path == path or i.path.startswith(path + "/") for i in after
            ):
                rejected.append(
                    RecordIssue(path, "evidence value does not resolve the schema violation")
                )
                continue
            preview = candidate
            accepted.append(GroundedFill(path, copy.deepcopy(value), support, fill["confidence"]))
        self.audit.guard("repair_all_proposals_grounded", not rejected)
        suggestions: list[UnverifiedSuggestion] = []
        unresolved = self.validate(preview)
        remaining = {i.path for i in unresolved}
        seen_suggestions: set[str] = set()
        if suggest_from_training:
            for row in output["suggestions"]:
                path = row["path"]
                if path in {"/product/id", "/dpp_id", "/issued_at_utc", "/schema_version"}:
                    continue  # Administrative identity/version fields are caller-controlled.
                if path not in remaining or path in seen_suggestions:
                    continue
                candidate = copy.deepcopy(preview)
                try:
                    _set(candidate, path, row["value"])
                except (KeyError, IndexError, TypeError, ValueError):
                    continue
                after = set(self.validate(candidate))
                if after - set(unresolved) or any(
                    i.path == path or i.path.startswith(path + "/") for i in after
                ):
                    continue
                seen_suggestions.add(path)
                suggestions.append(
                    UnverifiedSuggestion(
                        path,
                        copy.deepcopy(row["value"]),
                        row["rationale"],
                        min(float(row["confidence"]), 0.3),
                    )
                )
        self.audit.guard("training_suggestions_not_applied", True)
        return RepairResult(
            preview, tuple(accepted), unresolved, tuple(rejected), tuple(suggestions)
        )

    def synthesize(self, seed: Mapping[str, Any], pack: ContextPack) -> SynthesisResult:
        sources = self._sources(seed, pack)
        # Caller-supplied values are explicit evidence, not a licence to invent defaults.
        seed_identity = "request:seed"
        while seed_identity in sources:
            seed_identity += ":seed"
        sources[seed_identity] = ("request:seed", copy.deepcopy(dict(seed)))
        issues: tuple[RecordIssue, ...] = ()
        for _attempt in range(2):
            prompt = self.prompts.render(
                "synthesis",
                seed=canonical(seed),
                schema=canonical(self.schema),
                violations=canonical([asdict(i) for i in issues]),
            )
            self.audit.prompt(prompt)
            try:
                output = validate_object(
                    dict(self.provider.structured(prompt.text, pack, SYNTHESIS_SCHEMA)),
                    SYNTHESIS_SCHEMA,
                )
            except InvalidOutput:
                issues = (RecordIssue("", "malformed structured response"),)
                self.audit.guard("synthesis_schema", False)
                continue
            record = output["record"]
            problems = list(self.validate(record))
            support: list[ValueSupport] = []
            for path, value in _leaves(record):
                match = self._support(path, value, sources)
                if match is None:
                    problems.append(RecordIssue(path, "cannot be grounded"))
                else:
                    support.append(match)
            if not _same_product(seed, record):
                problems.append(RecordIssue("/product", "product identity must match the seed"))
            issues = tuple(problems)
            self.audit.guard("synthesis_schema", not self.validate(record))
            self.audit.guard(
                "synthesis_grounded", not any(i.reason == "cannot be grounded" for i in issues)
            )
            if not issues:
                return SynthesisResult(copy.deepcopy(record), tuple(support))
        raise RecordGenerationError(issues)

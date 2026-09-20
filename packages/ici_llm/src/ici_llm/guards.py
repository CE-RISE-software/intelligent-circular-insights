# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Named legacy composition predicates; no model calls or prompt text.

Intentional corrections: hints require a citation, recycling percentages come
from the hint (not a hard-coded 70), and numbers are compared as whole values.
These are preflight checks, not a replacement for GroundingVerifier.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal

from ici_core.domain.evidence import ContextPack

RELIABLE_HINT_KINDS = frozenset({"direct", "carbon", "extracted", "memory", "abstain"})
_BLOCK = re.compile(r"\[([^\[\]\r\n]+)\]")
_SEPARATOR = re.compile(r"\s*(?:[;,]|\band\b)\s*", re.IGNORECASE)
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:/-]*")


@dataclass(frozen=True)
class AnswerHint:
    """A trusted retriever's extraction, still subject to citation/claim checks."""

    text: str = ""
    kind: str = ""


def invalid_evidence_citations(
    answer: str, pack: ContextPack, *, require_citation: bool = False
) -> tuple[str, ...]:
    blocks = _BLOCK.findall(answer)
    if require_citation and not blocks:
        return ("missing-citation",)
    invalid: list[str] = []
    for block in blocks:
        ids = [part.strip() for part in _SEPARATOR.split(block)]
        if any(not _ID.fullmatch(item) for item in ids):
            invalid.append(block.strip())
        else:
            invalid.extend(item for item in ids if item not in pack.ids)
    return tuple(dict.fromkeys(invalid))


def grounded_hint(hint: AnswerHint, pack: ContextPack) -> bool:
    return bool(
        hint.text.strip()
        and hint.kind in RELIABLE_HINT_KINDS - {"abstain"}
        and not invalid_evidence_citations(hint.text, pack, require_citation=True)
        and not looks_like_header_copy(hint.text)
    )


def looks_like_header_copy(answer: str) -> bool:
    low = answer.strip().lower()
    return (
        not low
        or low.startswith(
            ("digital product passport", "1) product identification", "important note")
        )
        or "====" in low
    )


def _numbers(text: str) -> set[Decimal]:
    return {Decimal(v) for v in re.findall(r"\b\d+(?:\.\d+)?\b", _BLOCK.sub("", text))}


def misses_reliable_hint(query: str, answer: str, hint: AnswerHint) -> bool:
    kind, text = hint.kind, hint.text
    if kind not in RELIABLE_HINT_KINDS or not text:
        return False
    low_answer, low_query = answer.lower(), query.lower()
    abstained = low_answer.startswith("insufficient evidence")
    if kind == "abstain":
        return not abstained
    if abstained:
        return True
    if kind == "carbon" and any(
        term in low_query for term in ("recycling", "recyclability", "end-of-life", "end of life")
    ):
        return "recycl" not in low_answer or not _numbers(text) <= _numbers(answer)
    if kind == "extracted" and "chemistry" in low_query:
        return "lithium" not in low_answer and "nmc" not in low_answer
    if kind == "extracted" and "refrigerant" in low_query:
        if "r290" in text.lower() and "r290" not in low_answer:
            return True
        if any(
            t in low_query for t in ("service", "servicing", "maintain", "maintenance", "repair")
        ):
            return sum(t in low_answer for t in ("qualified", "ventilat", "ignition", "leak")) < 2
    materials = (
        "made of" in low_query
        or "built from" in low_query
        or bool(re.search(r"\b(?:materials?|composition|substances?)\b", low_query))
    )
    if kind == "extracted" and materials and "bill of materials" in text.lower():

        def normalize(value: str) -> str:
            for before, after in (
                ("aluminium", "aluminum"),
                ("plastics", "plastic"),
                ("electronics", "electronic"),
                ("elastomers", "elastomer"),
            ):
                value = value.replace(before, after)
            return value

        source, target = normalize(text.lower()), normalize(low_answer)
        terms = ("steel", "aluminum", "copper", "plastic", "electronic", "elastomer", "r290")
        return any(t in source and t not in target for t in terms) or not _numbers(
            text
        ) <= _numbers(answer)
    if kind == "direct" and "wireless" in low_query and "test" in low_query:
        return "yes" not in low_answer or "wireless" not in low_answer
    if kind == "memory" and any(t in low_query for t in ("component", "include", "uses", "use")):
        ids = [
            v
            for v in re.findall(r"\b[A-Za-z]+[A-Za-z0-9_-]*\d+\b", _BLOCK.sub("", text))
            if not v.lower().startswith("product")
        ]
        return bool(ids) and not any(
            re.search(r"\b" + re.escape(v.lower()) + r"\b", _BLOCK.sub("", low_answer))
            for v in ids[:3]
        )
    return False


def asks_unsupported_requirement(query: str, kind: str) -> bool:
    if kind == "direct":
        return False
    low = query.lower()
    return any(t in low for t in ("require", "need")) and any(t in low for t in ("test", "step"))

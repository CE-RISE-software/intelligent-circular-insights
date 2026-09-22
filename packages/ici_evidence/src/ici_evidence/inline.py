# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Evidence from one document the caller supplied, rather than from the corpus.

The workbench's "single passport" window: paste or upload a document, ask questions
answerable only from it. Nothing is indexed, nothing is stored, and the corpus is
not consulted — the point is a document that is *not* in the system yet.

The design decision worth stating. The demo answered these questions down a second,
parallel pipeline: its own section ranking, its own model call, its own confidence
number, and no grounding check at all. That meant the one window where a user is
most likely to paste an unfamiliar document was the window with the weakest
guarantees, and its confidence number was not comparable with the one the main
search reported.

Here it is an ``EvidenceProvider`` and nothing more. The same ``AnswerQuestion`` use
case runs, so a single-document question gets the whole reliability envelope for
free: calibrated confidence against the same operating point, the grounding verifier
rejecting any claim that cannot be traced to a section, an abstention that names the
weak signal, and provenance pointing at the section it came from.

Sectioning is structural where it can be. A JSON passport carries its meaning in its
keys, so each top-level key becomes a section titled by that key and addressed by a
JSON Pointer — which is what makes provenance resolvable rather than decorative.
Free text falls back to the same paragraph packing the corpus reader uses.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from ici_core.domain.evidence import Evidence, EvidenceKind
from ici_core.domain.ids import EvidenceId
from ici_core.domain.query import Query, RetrievalBudget
from ici_core.text import tokenize
from ici_evidence.documents import K1, B, split_passages

MAX_SECTION_CHARS = 2_000
MAX_SECTIONS = 1_000
MAX_DOCUMENT_CHARS = 400_000
"""Refused above this. A passport is a record, not a corpus; anything larger is
either a mistake or belongs in the indexed collection."""


@dataclass(frozen=True)
class Section:
    """One addressable part of the supplied document."""

    id: str
    title: str
    path: str
    """A JSON Pointer for structured input, or a line anchor for text. What a
    reader follows to find this again in their own copy."""
    kind: str
    summary: str
    text: str
    fields: tuple[tuple[str, str], ...] = ()

    @property
    def tokens(self) -> tuple[str, ...]:
        return tuple(tokenize(f"{self.title} {self.text}"))


@dataclass(frozen=True)
class ParsedDocument:
    filename: str | None
    document_type: str
    title: str
    char_count: int
    sections: tuple[Section, ...]
    warnings: tuple[str, ...] = ()


class DocumentTooLarge(ValueError):
    """Refused before parsing rather than truncated silently."""


# ------------------------------------------------------------------ parsing


def _scalar(value: Any) -> bool:
    return isinstance(value, (str, int, float, bool)) or value is None


def _readable(key: str) -> str:
    return re.sub(r"[_\-]+", " ", str(key)).strip().capitalize() or "Section"


def _pointer_part(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _json_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("non-finite JSON number")
    return number


def _json_constant(_: str) -> None:
    raise ValueError("non-finite JSON number")


def _json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON member")
        result[key] = value
    return result


def _render(value: Any, *, limit: int = 240) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "yes" if value else "no"
    text = str(value) if _scalar(value) else json.dumps(value, ensure_ascii=False)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _fields(value: Any, prefix: str = "") -> list[tuple[str, str]]:
    """Flatten to leaf key/value pairs, so a reader sees the facts not the shape."""
    out: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, inner in value.items():
            path = f"{prefix}/{_pointer_part(str(key))}" if prefix else _pointer_part(str(key))
            out.extend(_fields(inner, path) if not _scalar(inner) else [(path, _render(inner))])
    elif isinstance(value, list):
        for index, inner in enumerate(value):
            path = f"{prefix}/{index}"
            out.extend(_fields(inner, path) if not _scalar(inner) else [(path, _render(inner))])
    elif prefix:
        out.append((prefix, _render(value)))
    return out[:40]


def _summarise(value: Any) -> str:
    if isinstance(value, dict):
        keys = ", ".join(str(k) for k in list(value)[:5])
        return f"{len(value)} field{'' if len(value) == 1 else 's'}: {keys}"
    if isinstance(value, list):
        return f"{len(value)} item{'' if len(value) == 1 else 's'}"
    return _render(value, limit=160)


def _json_sections(data: Any) -> list[Section]:
    """One section per top-level key, addressed by JSON Pointer.

    A passport's structure *is* its meaning — 'compliance' and 'materials' are
    different subjects — so splitting on keys keeps related facts together in a way
    character-based chunking would cut across.
    """
    if not isinstance(data, dict):
        sections: list[Section] = []
        _append_json_sections(data, "", "Document", sections)
        return sections
    sections: list[Section] = []
    scalars: list[tuple[str, str]] = []
    for key, value in data.items():
        path = f"/{_pointer_part(str(key))}"
        if _scalar(value):
            rendered = _render(value, limit=MAX_SECTION_CHARS + 1)
            if len(rendered) > 240:
                _append_json_sections(value, path, _readable(key), sections)
            else:
                scalars.append((path, rendered))
            continue
        _append_json_sections(value, path, _readable(key), sections)
    if scalars:
        # Top-level scalars are identity — dpp_id, schema_version — and they are
        # what most questions about "which passport is this" actually need.
        groups: list[list[tuple[str, str]]] = []
        group: list[tuple[str, str]] = []
        length = 0
        for path, value in scalars:
            line_length = len(path) + len(value) + 2
            if line_length > MAX_SECTION_CHARS:
                raise DocumentTooLarge(
                    f"the value at {path} exceeds {MAX_SECTION_CHARS:,} characters"
                )
            if group and length + line_length + 1 > MAX_SECTION_CHARS:
                groups.append(group)
                group = []
                length = 0
            group.append((path, value))
            length += line_length + (1 if len(group) > 1 else 0)
        if group:
            groups.append(group)
        if len(sections) + len(groups) > MAX_SECTIONS:
            raise DocumentTooLarge(
                f"the document needs more than {MAX_SECTIONS:,} sections; split it before asking"
            )
        for index, fields in reversed(list(enumerate(groups))):
            sections.insert(
                0,
                Section(
                    id="s-identity" if index == 0 else f"s-identity-{index + 1}",
                    title="Identity",
                    # The JSON Pointer for the root is the empty string; "/"
                    # would point to a member whose key is the empty string.
                    path="",
                    kind="json",
                    summary=f"{len(fields)} top-level value{'' if len(fields) == 1 else 's'}",
                    text="\n".join(f"{k}: {v}" for k, v in fields),
                    fields=tuple(fields),
                ),
            )
    return sections


def _append_json_sections(value: Any, path: str, title: str, sections: list[Section]) -> None:
    """Split large containers on their own keys/items; never cut away their tail."""
    if len(sections) >= MAX_SECTIONS:
        raise DocumentTooLarge(
            f"the document needs more than {MAX_SECTIONS:,} sections; split it before asking"
        )
    body = json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)
    if len(body) > MAX_SECTION_CHARS and isinstance(value, (dict, list)) and value:
        children = value.items() if isinstance(value, dict) else enumerate(value)
        for key, child in children:
            child_path = f"{path}/{_pointer_part(str(key))}"
            _append_json_sections(child, child_path, f"{title} · {_readable(str(key))}", sections)
        return
    if len(body) > MAX_SECTION_CHARS:
        raise DocumentTooLarge(
            f"the value at {path} is {len(body):,} characters; a single field may not exceed "
            f"{MAX_SECTION_CHARS:,} characters. Split that field before asking about it."
        )
    sections.append(
        Section(
            id=f"s{len(sections)}",
            title=title,
            path=path,
            kind="json",
            summary=_summarise(value),
            text=body,
            fields=tuple(_fields(value, path)),
        )
    )


def _text_sections(text: str) -> list[Section]:
    out: list[Section] = []
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    parts: list[str] = []
    for paragraph in paragraphs:
        while len(paragraph) > MAX_SECTION_CHARS:
            split = paragraph.rfind(" ", 0, MAX_SECTION_CHARS)
            if split < MAX_SECTION_CHARS // 2:
                split = MAX_SECTION_CHARS
            parts.append(paragraph[:split])
            paragraph = paragraph[split:].strip()
        if paragraph:
            parts.append(paragraph)
    for index, block in enumerate(split_passages("\n\n".join(parts), limit=MAX_SECTION_CHARS)):
        first = block.strip().splitlines()[0] if block.strip() else f"Part {index + 1}"
        out.append(
            Section(
                id=f"t{index}",
                title=(first[:70] + "…") if len(first) > 70 else first or f"Part {index + 1}",
                path=f"#part-{index + 1}",
                kind="text",
                summary=block.strip()[:160],
                text=block,
            )
        )
    return out


def parse_document(content: str, filename: str | None = None) -> ParsedDocument:
    """Split a supplied document into addressable sections.

    JSON is parsed structurally; anything else is treated as text. A document that
    *looks* like JSON but does not parse is reported as a warning and read as text,
    because a malformed passport is exactly the case a user wants help with — the
    Validate window will say what is wrong with it.
    """
    content = content or ""
    if len(content) > MAX_DOCUMENT_CHARS:
        raise DocumentTooLarge(
            f"the document is {len(content):,} characters; the limit is "
            f"{MAX_DOCUMENT_CHARS:,}. A passport is a record, not a corpus."
        )

    warnings: list[str] = []
    stripped = content.strip()
    data: Any = None
    if stripped.startswith(("{", "[")):
        try:
            data = json.loads(
                stripped,
                parse_float=_json_float,
                parse_constant=_json_constant,
                object_pairs_hook=_json_object,
            )
        except RecursionError as exc:
            raise DocumentTooLarge(
                "the JSON is nested too deeply; flatten it before asking"
            ) from exc
        except (json.JSONDecodeError, ValueError) as exc:
            location = f" at line {exc.lineno}" if isinstance(exc, json.JSONDecodeError) else ""
            detail = exc.msg if isinstance(exc, json.JSONDecodeError) else str(exc)
            warnings.append(
                f"this looks like JSON but does not parse ({detail}{location}); "
                "read as text. The Validate window will locate the problem."
            )

    if data is not None:
        try:
            sections = _json_sections(data)
        except RecursionError as exc:
            raise DocumentTooLarge(
                "the JSON is nested too deeply; flatten it before asking"
            ) from exc
        doc_type = "json"
        title = str(data.get("dpp_id") or "") if isinstance(data, dict) else ""
    else:
        sections = _text_sections(content)
        doc_type = "text"
        title = ""

    if not sections:
        warnings.append("nothing could be read from this document.")

    return ParsedDocument(
        filename=filename,
        document_type=doc_type,
        title=title or filename or "Supplied document",
        char_count=len(content),
        sections=tuple(sections),
        warnings=tuple(warnings),
    )


# ----------------------------------------------------------------- retrieval


@dataclass
class InlineDocumentProvider:
    """Implements ``EvidenceProvider`` over one supplied document.

    Same BM25 constants as the corpus reader, deliberately: a section that scores
    0.7 here means what it means there, and a user comparing two windows should not
    have to know that the numbers were produced differently.
    """

    document: ParsedDocument
    _idf_cache: dict[str, float] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        sections = self.document.sections
        self._avg = (sum(len(s.tokens) for s in sections) / len(sections)) if sections else 0.0

    def _idf(self, term: str) -> float:
        if term not in self._idf_cache:
            total = len(self.document.sections) or 1
            hits = sum(1 for s in self.document.sections if term in s.tokens)
            self._idf_cache[term] = math.log(1 + (total - hits + 0.5) / (hits + 0.5))
        return self._idf_cache[term]

    def _score(self, section: Section, terms: Sequence[str]) -> float:
        tokens = section.tokens
        if not tokens:
            return 0.0
        length = len(tokens)
        total = 0.0
        for term in terms:
            frequency = tokens.count(term)
            if not frequency:
                continue
            denominator = frequency + K1 * (1 - B + B * length / (self._avg or length))
            total += self._idf(term) * (frequency * (K1 + 1)) / denominator
        return total

    def retrieve(self, q: Query, budget: RetrievalBudget) -> Sequence[Evidence]:
        terms = tokenize(q.text)
        sections = self.document.sections
        if not sections:
            return []

        scored = sorted(
            ((self._score(s, terms), s) for s in sections),
            key=lambda pair: (-pair[0], pair[1].id),
        )
        top = [(score, s) for score, s in scored[: budget.top_k_documents] if score > 0]

        # A short passport can match nothing lexically while still holding the
        # answer — "is it compliant?" against a section titled 'certifications'.
        # Falling back to the whole document lets the grounding verifier decide,
        # which is a better judge than a term overlap of zero.
        if not top:
            top = [(0.0, s) for s in sections[: budget.top_k_documents]]

        return [
            Evidence(
                id=EvidenceId(f"sec-{section.id}"),
                kind=EvidenceKind.PASSAGE,
                text=section.text[: budget.max_context_chars],
                # The pointer, so provenance resolves in the user's own copy of the
                # document rather than in a file we do not have.
                ref=f"{self.document.filename or 'document'}{section.path}",
                score=round(score, 6) if score else None,
                source_file=self.document.filename,
                metadata={"section": section.id, "title": section.title},
            )
            for score, section in top
        ]


__all__ = [
    "MAX_DOCUMENT_CHARS",
    "DocumentTooLarge",
    "InlineDocumentProvider",
    "ParsedDocument",
    "Section",
    "parse_document",
]

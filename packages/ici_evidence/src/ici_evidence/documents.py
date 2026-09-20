# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Hybrid lexical retrieval over the document corpus.

BM25-style scoring: term frequency saturated, rare terms weighted up, long
documents discounted. The demo's index did the same thing inside a 1,371-line
class that also held memory, symbolic dispatch and confidence; here retrieval is
just retrieval, and every passage comes back with a ref a reader can follow.

Passages, not whole documents. A seed document is tens of kilobytes of passport
text, and handing that to an answerer buries the one sentence that matters.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from ici_core.domain.evidence import Evidence, EvidenceKind
from ici_core.domain.ids import EvidenceId
from ici_core.domain.query import Query, RetrievalBudget
from ici_core.text import tokenize

PASSAGE_CHARS = 700
K1 = 1.5
B = 0.75


@dataclass(frozen=True)
class Passage:
    """One retrievable span, addressable by a ref that survives into provenance."""

    id: str
    doc_id: str
    domain: str
    text: str
    tokens: tuple[str, ...]
    source: str


def split_passages(text: str, *, limit: int = PASSAGE_CHARS) -> list[str]:
    """Split on blank lines, then pack paragraphs up to the limit.

    Packing rather than hard-cutting keeps a table or a short list intact, which
    matters because passport text carries most of its facts in those.
    """
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    out: list[str] = []
    buf = ""
    for block in blocks:
        if len(buf) + len(block) + 2 <= limit:
            buf = f"{buf}\n\n{block}" if buf else block
        else:
            if buf:
                out.append(buf)
            buf = block if len(block) <= limit else block[:limit]
    if buf:
        out.append(buf)
    return out


@dataclass
class DocumentEvidenceProvider:
    """Implements ``EvidenceProvider`` for Normal mode."""

    passages: tuple[Passage, ...] = ()
    _df: dict[str, int] = field(default_factory=dict, init=False, repr=False)
    _avg_len: float = field(default=1.0, init=False, repr=False)

    def __post_init__(self) -> None:
        self._index()

    @classmethod
    def from_seed_docs(cls, root: Path) -> DocumentEvidenceProvider:
        passages: list[Passage] = []
        for path in sorted(root.glob("*.jsonl")):
            domain = path.stem
            for line_no, line in enumerate(path.read_text().splitlines()):
                if not line.strip():
                    continue
                row = json.loads(line)
                text = str(row.get("text", ""))
                doc_id = str(row.get("doc_id") or row.get("pid") or f"{domain}-{line_no}")
                for i, chunk in enumerate(split_passages(text)):
                    passages.append(
                        Passage(
                            id=f"{domain}:{line_no}:{i}",
                            doc_id=doc_id,
                            domain=domain,
                            text=chunk,
                            tokens=tuple(tokenize(chunk)),
                            source=f"{path.name}#{doc_id}",
                        )
                    )
        return cls(tuple(passages))

    def _index(self) -> None:
        df: dict[str, int] = {}
        total = 0
        for passage in self.passages:
            total += len(passage.tokens)
            for term in set(passage.tokens):
                df[term] = df.get(term, 0) + 1
        self._df = df
        self._avg_len = (total / len(self.passages)) if self.passages else 1.0

    def _idf(self, term: str) -> float:
        n = len(self.passages)
        df = self._df.get(term, 0)
        return math.log(1 + (n - df + 0.5) / (df + 0.5))

    def _score(self, passage: Passage, terms: Sequence[str]) -> float:
        if not passage.tokens:
            return 0.0
        length_norm = K1 * (1 - B + B * len(passage.tokens) / self._avg_len)
        score = 0.0
        for term in terms:
            tf = passage.tokens.count(term)
            if tf:
                score += self._idf(term) * (tf * (K1 + 1)) / (tf + length_norm)
        return score

    # -- EvidenceProvider ---------------------------------------------------
    def retrieve(self, q: Query, budget: RetrievalBudget) -> Sequence[Evidence]:
        terms = tokenize(q.text)
        if not terms or not self.passages:
            return []

        candidates = self.passages
        # A stated domain narrows the corpus. Filtering to nothing would be worse
        # than not filtering, so fall back rather than return empty.
        if q.scope.domain:
            scoped = tuple(p for p in candidates if p.domain == q.scope.domain)
            candidates = scoped or candidates

        scored = sorted(
            ((self._score(p, terms), p) for p in candidates),
            key=lambda pair: (-pair[0], pair[1].id),
        )
        top = [(s, p) for s, p in scored[: budget.top_k_documents] if s > 0]

        return [
            Evidence(
                id=EvidenceId(f"doc-{passage.id}"),
                kind=EvidenceKind.PASSAGE,
                text=passage.text[: budget.max_context_chars],
                ref=passage.source,
                score=round(score, 6),
                source_file=passage.source.split("#", 1)[0],
                metadata={"domain": passage.domain, "doc_id": passage.doc_id},
            )
            for score, passage in top
        ]

"""Competency questions — the ontology's own validation device, as data.

The paper derives 173 competency questions from the PEF Recommendation and uses
them to decide what the ontology must be able to answer. Sixteen run live here.

They live in ``ontology/pefdpp/cq/questions.json`` rather than in Python because a
question is a piece of domain knowledge, not code: a reviewer should be able to read
the set, add one, and see the coverage move without touching a module. Each carries
the PEF requirement it derives from, so an answer can cite the rule that demanded it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ici_substrates.paths import PEFDPP_ONTOLOGY_ROOT

TOTAL_IN_PAPER = 173
"""Competency questions the paper derives from the PEF Recommendation. Reported so
coverage is visible: sixteen live against a hundred and seventy-three is a starting
point stated honestly, not a gap hidden by only counting what works."""


@dataclass(frozen=True)
class CompetencyQuestion:
    id: str
    question: str
    pef_requirement: str
    why_it_matters: str
    sparql: str

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> CompetencyQuestion:
        return cls(
            id=str(raw["id"]),
            question=str(raw["question"]),
            pef_requirement=str(raw.get("pef_requirement", "")),
            why_it_matters=str(raw.get("why_it_matters", "")),
            sparql=str(raw["sparql"]),
        )


def load_questions(path: Path | None = None) -> tuple[CompetencyQuestion, ...]:
    source = path or (PEFDPP_ONTOLOGY_ROOT / "cq" / "questions.json")
    return tuple(CompetencyQuestion.from_dict(item) for item in json.loads(source.read_text()))


@dataclass(frozen=True)
class QuestionResult:
    question: CompetencyQuestion
    rows: tuple[dict[str, str], ...]
    error: str | None = None

    @property
    def answered(self) -> bool:
        return self.error is None and bool(self.rows)


@dataclass(frozen=True)
class CoverageSummary:
    """How much of the paper's question set this graph actually answers."""

    live: int
    answered: int
    total_in_paper: int = TOTAL_IN_PAPER

    @property
    def answered_share_of_live(self) -> float:
        return self.answered / self.live if self.live else 0.0

    @property
    def share_of_paper(self) -> float:
        return self.live / self.total_in_paper if self.total_in_paper else 0.0

# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""The decision policy: which action to take next.

The supervised router ships because it is the configuration that works. Two seats
stay empty (ADR 0008) — a contextual bandit over the signal vector, and an offline
RL policy with ABSTAIN as a first-class action. Two choices here make those usable
later without a refactor: the observation is the confidence *signal vector* rather
than six hand-made features, and ABSTAIN is in the action set rather than being a
threshold applied downstream.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from ici_core.domain.confidence import (
    RETRIEVAL_MARGIN,
    SYMBOLIC_FIRED,
    SignalVector,
)

RECALL = "recall"
RETRIEVE = "retrieve"
ENTAIL = "entail"
ANSWER = "answer"
ABSTAIN = "abstain"

ACTIONS: tuple[str, ...] = (RECALL, RETRIEVE, ENTAIL, ANSWER, ABSTAIN)


@dataclass
class HeuristicRouter:
    """Implements ``DecisionPolicy``.

    A small, readable rule set standing in for the fitted logistic router until its
    training artefacts are ported. It is deliberately legible rather than clever:
    a policy nobody can explain is not a baseline, it is a mystery.
    """

    max_steps: int = 6
    margin_floor: float = 0.05

    def actions(self) -> Sequence[str]:
        return ACTIONS

    def act(self, signals: SignalVector, steps_taken: int) -> str:
        if steps_taken >= self.max_steps:
            # Out of budget. Answering on exhausted evidence is how a system
            # produces confident nonsense, so the budget ends in abstention.
            return ABSTAIN
        if signals.get(SYMBOLIC_FIRED) > 0:
            return ANSWER
        if signals.get(RETRIEVAL_MARGIN) <= self.margin_floor:
            return RETRIEVE if steps_taken == 0 else ABSTAIN
        return ANSWER

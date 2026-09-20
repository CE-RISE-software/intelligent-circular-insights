# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Targeted symbolic validation over a DPP ontology.

OWL 2 RL forward chaining plus a small catalogue of obligation rules, with a
trace naming the rule behind every conclusion.
"""

from __future__ import annotations

from ici_symbolic.adapter import OwlRlValidator
from ici_symbolic.config import DEFAULT_DOMAIN, DOMAIN_ONTOLOGY, ReasonerConfig
from ici_symbolic.reasoner import OwlRlReasoner, ReasoningOutcome, RuleFiring, local_name
from ici_symbolic.rules import Rule, rules_for

__all__ = [
    "DEFAULT_DOMAIN",
    "DOMAIN_ONTOLOGY",
    "OwlRlReasoner",
    "OwlRlValidator",
    "ReasonerConfig",
    "ReasoningOutcome",
    "Rule",
    "RuleFiring",
    "local_name",
    "rules_for",
]

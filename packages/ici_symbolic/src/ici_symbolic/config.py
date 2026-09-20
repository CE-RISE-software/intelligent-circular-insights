# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Reasoner configuration.

Everything the reasoner needs arrives as an argument. The original read
``DPP_DOMAIN`` and ``DPP_ONTOLOGY`` from the environment deep inside the service,
which made it impossible to hold two domains in one process — and holding two
backends in one process is the whole point of this rewrite.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ONTOLOGY_ROOT = Path(__file__).resolve().parents[4] / "ontology" / "dpp"

# The four shipped domains and the ontology each one reasons over.
DOMAIN_ONTOLOGY = {
    "battery": "dpp_ontology.ttl",
    "textiles": "textiles_ontology.ttl",
    "viessmann": "viessmann_ontology.ttl",
    "lexmark": "lexmark_ontology.ttl",
}

# Each domain has its own namespace; individuals are named within it.
DOMAIN_NAMESPACE = {
    "battery": "http://example.com/dpp#",
    "textiles": "http://example.com/textiles#",
    "viessmann": "http://example.com/viessmann#",
    "lexmark": "http://example.com/lexmark#",
}

DEFAULT_DOMAIN = "battery"


@dataclass(frozen=True)
class ReasonerConfig:
    """Where the ontology is, and which vocabulary its individuals live in."""

    ontology_path: Path
    namespace: str
    domain: str = DEFAULT_DOMAIN
    run_owl_rl: bool = True

    @classmethod
    def for_domain(
        cls,
        domain: str = DEFAULT_DOMAIN,
        *,
        ontology_root: Path | None = None,
        run_owl_rl: bool = True,
    ) -> ReasonerConfig:
        key = (domain or DEFAULT_DOMAIN).strip().lower()
        if key not in DOMAIN_ONTOLOGY:
            raise ValueError(f"unknown domain {domain!r}; known: {sorted(DOMAIN_ONTOLOGY)}")
        root = ontology_root or ONTOLOGY_ROOT
        path = root / DOMAIN_ONTOLOGY[key]
        if not path.is_file():
            raise FileNotFoundError(f"ontology not found for domain {key!r}: {path}")
        return cls(
            ontology_path=path,
            namespace=DOMAIN_NAMESPACE[key],
            domain=key,
            run_owl_rl=run_owl_rl,
        )

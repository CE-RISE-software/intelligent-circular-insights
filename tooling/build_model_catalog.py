#!/usr/bin/env python3
"""Rebuild the CE-RISE model catalogue from the vendored LinkML sources.

The demo carried this catalogue as a Python literal, and it had drifted: it listed
``template-data-model``, which no longer exists, and missed ``lci-dataset`` and
``product-system``, which do. A catalogue derived from the vendored schemas cannot
drift that way — regenerating it is a diff, and the diff is reviewable.

Routing keywords are the one thing not derivable from the schema, so they are kept
here as an explicit editorial layer on top of what the model declares.
"""

from __future__ import annotations

import json
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
VENDORED = ROOT / "schemas" / "ce-rise"
OUT = ROOT / "data" / "ce_rise_models.json"
CODEBERG = "https://codeberg.org/CE-RISE-models"

# Which architectural layer each model belongs to, and the words a question would
# use to reach it. Editorial: the schemas do not declare either.
LAYERS: dict[str, tuple[str, tuple[str, ...]]] = {
    "dp-architecture": (
        "Architecture",
        ("architecture", "profile", "passport", "composition", "module"),
    ),
    "dp-record-metadata": (
        "Metadata",
        ("metadata", "schema", "version", "scope", "record", "identifier"),
    ),
    "dp-record-custody": ("Metadata", ("custody", "ownership", "transfer", "holder", "chain")),
    "dp-access-and-governance": (
        "Metadata",
        ("access", "governance", "permission", "role", "consent", "tiered"),
    ),
    "product-profile": (
        "Core profile",
        ("product", "manufacturer", "model", "identifier", "gtin", "origin"),
    ),
    "material-profile": (
        "Core profile",
        ("material", "substance", "composition", "recycled content", "hazardous"),
    ),
    "usage-and-maintenance": (
        "Lifecycle operations",
        ("usage", "maintenance", "repair", "service", "spare part"),
    ),
    "integrated-lca": (
        "Impact assessment",
        ("lca", "life cycle", "footprint", "impact", "emission", "carbon", "pef"),
    ),
    "lci-dataset": (
        "Impact assessment",
        ("lci", "inventory", "dataset", "unit process", "exchange", "flow"),
    ),
    "product-system": (
        "Impact assessment",
        ("product system", "value chain", "system boundary", "activity link"),
    ),
    "circularity-and-eol": (
        "Circularity",
        ("circularity", "end of life", "recycling", "reuse", "disposal", "recovery"),
    ),
    "re-indicators-specification": (
        "Circularity",
        ("indicator", "re-indicator", "circular", "metric", "score"),
    ),
    "compliance-and-standards": (
        "Compliance",
        ("compliance", "standard", "regulation", "certificate", "declaration", "conformity"),
    ),
    "data-quality-framework": (
        "Cross-cutting",
        ("data quality", "dqr", "representativeness", "reliability", "completeness"),
    ),
    "uncertainty-quantification": (
        "Cross-cutting",
        ("uncertainty", "confidence", "interval", "variance", "distribution"),
    ),
    "metrological-traceability": (
        "Cross-cutting",
        ("traceability", "measurement", "calibration", "metrology", "unit"),
    ),
    "diagnostic-results": (
        "Cross-cutting",
        ("diagnostic", "test", "inspection", "condition", "state of health"),
    ),
    "traceability-and-life-cycle-events": (
        "Lifecycle events",
        ("event", "traceability", "history", "custody", "lifecycle"),
    ),
}


def read_model(directory: pathlib.Path) -> dict[str, object] | None:
    """Read one vendored model.

    Keyed by **directory name**, not the schema's ``name:`` field. Five of the
    models declare an underscored name while their repository uses hyphens
    (``compliance_and_standards`` vs ``compliance-and-standards``), and the
    directory is what the Codeberg URL uses, so it is the stable identifier.
    """
    source = directory / "model" / "model.yaml"
    doc = {}
    if source.is_file():
        doc = yaml.safe_load(source.read_text()) or {}
    elif not (directory / "README.md").is_file():
        return None
    name = directory.name
    layer, keywords = LAYERS.get(name, ("Uncategorised", ()))
    classes = sorted((doc.get("classes") or {}).keys())
    return {
        "id": name,
        "declared_name": str(doc.get("name", "")) or name,
        "title": str(doc.get("title") or name),
        "layer": layer,
        "summary": " ".join(str(doc.get("description", "")).split()) or _readme_summary(directory),
        "url": f"{CODEBERG}/{directory.name}",
        "version": str(doc.get("version", "")),
        # Declared by the schema itself, not by us — CC-BY-NC-4.0 throughout, and
        # carrying it per model means an API consumer sees the terms.
        "licence": normalise_licence(str(doc.get("license", ""))),
        "licence_declared": str(doc.get("license", "")),
        "namespace": str(doc.get("id", "")),
        "classes": classes,
        "class_count": len(classes),
        "keywords": list(keywords),
    }


# The models declare their licence two ways — a human string and a URL. Normalise
# to SPDX so a consumer does not have to parse both shapes, and keep the raw
# declaration alongside so nothing is lost.
_SPDX = {
    "cc by-nc 4.0": "CC-BY-NC-4.0",
    "cc-by-nc-4.0": "CC-BY-NC-4.0",
    "https://creativecommons.org/licenses/by-nc/4.0/": "CC-BY-NC-4.0",
    "http://creativecommons.org/licenses/by-nc/4.0/": "CC-BY-NC-4.0",
}


def normalise_licence(raw: str) -> str:
    return _SPDX.get(
        raw.strip().lower().rstrip("/") + ("/" if raw.strip().endswith("/") else ""),
        _SPDX.get(raw.strip().lower(), raw.strip()),
    )


def _readme_summary(directory: pathlib.Path) -> str:
    """First prose line of the README, for repositories with no LinkML schema.

    ``dp-architecture`` is documentation rather than a data model; it belongs in
    the catalogue because it is one of the published modules, and omitting it
    would make the count wrong.
    """
    readme = directory / "README.md"
    if not readme.is_file():
        return ""
    for line in readme.read_text().splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith(("#", "[", "!", "-", "|")):
            return " ".join(stripped.split())[:300]
    return ""


def main() -> int:
    models = [m for d in sorted(VENDORED.iterdir()) if d.is_dir() and (m := read_model(d))]
    if not models:
        print("no vendored models found — run tooling/fetch_ce_rise_models.sh", file=sys.stderr)
        return 1
    OUT.write_text(json.dumps(models, indent=2, sort_keys=True) + "\n")
    print(f"{len(models)} models -> {OUT.relative_to(ROOT)}")
    for m in models:
        print(f"  {m['id']:36} v{m['version']:<8} {m['class_count']:>3} classes  {m['layer']}")
    uncategorised = [m["id"] for m in models if m["layer"] == "Uncategorised"]
    if uncategorised:
        print(f"\n  !! no layer/keywords declared for: {uncategorised}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

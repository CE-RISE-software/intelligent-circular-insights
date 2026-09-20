# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Where the repo-resident data lives.

One module knows the layout. Everything else takes a path argument, so a test can
point a service at a fixture directory without monkey-patching a constant.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
DATA_ROOT = REPO_ROOT / "data"
CARBON_ROOT = DATA_ROOT / "carbon"
SEED_DOCS_ROOT = DATA_ROOT / "seed_docs"
ONTOLOGY_ROOT = REPO_ROOT / "ontology" / "dpp"
SCHEMA_ROOT = REPO_ROOT / "schemas"

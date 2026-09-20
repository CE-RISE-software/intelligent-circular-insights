# ADR 0010 — EUPL-1.2 for our code; CC-BY-NC-4.0 material stays segregated

**Status:** accepted · **Date:** 20 September 2026 · **Sprint:** 1 (moved forward from 5)

## Context

The plan said "MIT for code, CC-BY-4.0 for documentation". Both were wrong, and I had
assumed rather than checked. The facts, read from the repositories themselves:

| | Licence | Evidence |
|---|---|---|
| `CE-RISE-software/intelligent-circular-insights` — **our target repo** | **EUPL-1.2** | `LICENSE` already in the repo; README, `CITATION.cff` and `.zenodo.json` all declare it |
| `CE-RISE-models/*` — the 17 data models | **CC-BY-NC-4.0** | single `LICENSE` at each repo root, covering `model/`, `generated/`, `mappings/`, `samples/`, `tests/` and `Makefile` alike |

Riccardo Boero (NILU) is the author of record on both, and the repo already carries his
template: Codeberg canonical, GitHub read-mirror, Zenodo archival on tag, EU funding
footer under Grant Agreement No. 101092281.

**The tension.** EUPL-1.2 explicitly permits commercial use. CC-BY-NC-4.0 explicitly
forbids it, and is not an open-source licence in the OSI sense. Vendoring CC-BY-NC schema
files into an otherwise EUPL repository would hand a downstream user two contradictory
sets of terms for one checkout — the root LICENSE saying commercial use is fine, and files
inside it saying it is not.

## Decision

**1. Our code is EUPL-1.2.** Not a choice so much as a fact: the repository Riccardo
created already says so, and matching it is what makes this a CE-RISE deliverable rather
than a fork with its own opinions. All our source files carry an EUPL-1.2 SPDX header.

**2. Vendored CE-RISE data models stay in a segregated subtree** at `schemas/ce-rise/`,
which carries its own `LICENSE` (CC-BY-NC-4.0), its own `NOTICE.md` naming the source
repository, commit SHA, Zenodo DOI and author for each of the 17 models, and REUSE
metadata so every file's licence is machine-readable.

**3. No CC-BY-NC material is copied into, generated into, or imported by EUPL-licensed
source.** The schema files are *read at runtime as data*; they are not transformed into
Python modules that then sit under the repo's root licence. A `reuse lint` check in CI
enforces that every file has a declared licence.

**4. Riccardo is asked to confirm the intent**, since he authored both sides. One sentence
from him settles whether NC was deliberate for the data models and whether he is content
with the segregated arrangement. Until then the segregation stands, because it is the
correct handling either way.

## Consequences

+ A downstream user can tell, per file, what they may do. That is the whole point of REUSE.
+ Reproducibility survives: the schemas are still vendored and still pinned by commit SHA,
  so an archived tag validates exactly what it validated on release day (ADR 0005 holds).
+ The repo matches the consortium's conventions rather than inventing its own.
− Anyone wanting to use this commercially must obtain the data models separately or seek
  permission. That constraint is upstream's to make, not ours to paper over — and stating
  it plainly is more useful than burying it.
− `reuse` becomes a dev dependency and a CI step.

## Not legal advice

This records what the repositories say and how we are handling it. It is not a legal
opinion, and NC terms in particular are known to be ambiguous at the edges. If the
consortium intends commercial exploitation, the licence question belongs with whoever
advises them on it, not with this file.

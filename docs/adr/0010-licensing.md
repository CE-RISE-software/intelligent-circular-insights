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

## Addendum — "pick something open to everyone" (asked 20 Sep)

The ask was for a licence open to all. **EUPL-1.2 already is one**, and this is worth
stating plainly because the name is less familiar than MIT:

- **OSI-approved.** It is on the Open Source Initiative's list.
- **Commercial use is permitted.** Nothing in it restricts who may use the software or
  what for.
- **Permissive dependencies work.** MIT, BSD and Apache-2.0 libraries can be
  incorporated, statically linked and dynamically linked inside an EUPL project. Our
  stack — FastAPI, rdflib, owlrl, numpy, jsonschema — is entirely permissive, so there
  is no inbound problem.
- **It is reciprocal, not viral-by-surprise.** The one obligation is that if you
  *distribute* a modified version, its source stays under EUPL or one of the licences
  in its Appendix (GPL-2.0/3.0, AGPL-3.0, LGPL, MPL, OSL, EPL, CPL, CeCILL, LiLiQ).
  Using it, running it, querying it or building on it internally triggers nothing.

**Decision: keep EUPL-1.2.** Three reasons.

1. It meets the "open to all" bar already, so swapping to MIT or Apache-2.0 would buy
   permissiveness we do not lack, at the cost of the one thing EUPL adds — a guarantee
   that a downstream fork of publicly funded software stays public.
2. **It is not ours to change.** The repository lives in the `CE-RISE-software`
   organisation, was created from the consortium template, and is funded under Grant
   Agreement No. 101092281. Relicensing a consortium deliverable is a consortium
   decision, not a maintainer's.
3. Deviating in one repository makes this project the odd one out in an organisation
   where every other repository is EUPL, for no gain anyone benefits from.

**Where openness is actually constrained is upstream, not here.** The 17 CE-RISE data
models are CC-BY-NC-4.0, and **NC is not open source** — it bars commercial use, which
is exactly the restriction "open to all" is meant to avoid. That is a real limitation on
anyone wanting to build a product on these models, and it is Riccardo's to resolve
rather than ours to route around.

**So the one thing worth asking him:** was NC deliberate on the data models, or inherited
from a template? If a consortium partner ever wants to commercialise on top of them,
CC-BY-4.0 without the NC would remove the blocker while keeping attribution. Until that
is answered the segregated subtree stands, which is correct under either outcome.

**If you want a permissive licence for your own separate work** — `llmmain`, the paper
artefacts, anything outside the CE-RISE organisation — **Apache-2.0** is the pick, not
MIT: same permissiveness, plus an explicit patent grant and a contribution clause, which
matters for research code that institutions may later want to build on.

## Not legal advice

This records what the repositories say and how we are handling it. It is not a legal
opinion, and NC terms in particular are known to be ambiguous at the edges. If the
consortium intends commercial exploitation, the licence question belongs with whoever
advises them on it, not with this file.

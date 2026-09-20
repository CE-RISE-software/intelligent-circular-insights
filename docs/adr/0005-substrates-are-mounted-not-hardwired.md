# ADR 0005 — Knowledge substrates are mounted, and their contribution is measured

**Status:** accepted · **Date:** 2026-09-19 · **Sprint:** 2
**Supersedes:** the first draft's "vendor the CE-RISE models" ADR, which treated one
substrate as the architecture.

## Context
COMPASS's symbolic layer fires on 7.96 % of the workload with observed conditional precision
1.000. The precision is the contribution; the coverage is the limitation. Several bodies of
structured knowledge could raise coverage — the DPP core ontology and its domain modules,
the 17 CE-RISE data models, the PEFDPP graph, and an unseen schema like Open Food Facts —
but each raises a different question about whether precision survives.

An architecture that hard-wires one of them cannot answer that question, and an architecture
that hard-wires the *largest* one confuses a substrate with a design.

## Decision
`SubstrateRegistry` mounts substrates. Each declares the subjects it covers, the facts it
supplies and the queries it accepts. Crucially it exposes `coverage_report()`: symbolic fire
rate and conditional precision **per substrate**.

A mode is a named bundle of substrates plus adapters plus a default operating point.
"CE-RISE mode" mounts the CE-RISE data models and the PEFDPP graph on top of the Normal set.

CE-RISE model schemas are vendored into `schemas/ce-rise/` with source URL, commit SHA and
fetch date in `VENDOR.md`; the application never fetches a schema at runtime. Codeberg is
unreachable from the build sandboxes (403 at the egress proxy), and a DOI-archived artifact
must validate years later exactly as it did on release day.

## Consequences
+ "Which knowledge bought which reach" becomes a number in a report.
+ The OFF generalisation study runs from the same registry as everything else, rather than a
  separate script.
+ A substrate that raises coverage but drops conditional precision below the published bar
  is visibly not worth mounting — which is a finding, not a failure.
+ Reproducible, offline builds.
− Vendored copies go stale; a scheduled job diffs upstream and opens an issue.
− One more layer of indirection between a question and the triple that answers it.

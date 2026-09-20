# ADR 0001 — Hexagonal architecture with Protocol ports

**Status:** accepted · **Date:** 2026-09-19 · **Sprint:** 0

## Context
The current CE-RISE-Demo mixes I/O, configuration reads and business logic in the same
modules (`demo_search.py` 1371 LoC, `carbon_calculation_service.py` 1343 LoC). We must
support two interchangeable backends and publish the result under a DOI.

## Decision
Ports-and-adapters. `ici_core` holds domain types, use cases and eight ports declared as
`typing.Protocol`. Adapter packages implement them. `apps/api` is the only module that
imports both adapter packages.

Protocols, not ABCs: structural typing means an adapter never imports a base class, a test
double is a plain dataclass, and there is no inheritance coupling across package boundaries.

## Consequences
+ Mode switching becomes an adapter swap, not a branch through feature code.
+ One contract suite validates both implementations.
+ `ici_core` is testable with no I/O, so a 95 % coverage floor is reasonable there.
− More files, more indirection; a reader must follow a port to find the implementation.
− Port signatures must be got right early; changing one after Sprint 0 needs an ADR.

## Enforcement
`import-linter` contract in CI: `ici_core` may not import any adapter package. Violations
fail the build.

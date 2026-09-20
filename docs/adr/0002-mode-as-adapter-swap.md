# ADR 0002 — Backend mode is a per-request adapter swap

**Status:** accepted · **Date:** 2026-09-19 · **Sprint:** 0

## Context
We need Normal mode (flat profiles, CSV factors, JSON Schema) and CE-RISE mode (PEFDPP
graph, SHACL, CE-RISE data models) available in the same deployment. Options considered:
a startup env profile, per-feature overrides, or per-request resolution.

## Decision
Per-request, via an `X-Backend-Mode` header, mirroring the existing `X-Model` convention
that the Settings panel already uses. Precedence: header → session pin → settings default →
env → hard default `normal`. Both `ProviderBundle`s are constructed once at startup and
held immutably; resolution is a dict lookup.

Every response carries `X-Backend-Mode-Used`, and `AnswerEnvelope.mode` names the backend
that actually ran.

## Consequences
+ Both modes live in one session — the compare view is possible, which is the demo.
+ A/B and differential testing need one process, not two.
+ No restart to switch; no configuration drift between two deployments.
− Both bundles' memory footprint is resident, including the PEFDPP graph (~5,400 triples,
  cheap) but excluding the 40 MB EF flow list, which stays lazy.
− Every use case must be written mode-agnostic; a use case that reads a mode flag is a
  design failure and is rejected in review.

## Rejected
A startup env profile: simpler, but it makes the compare view impossible and forces two
processes for any A/B measurement — which is most of what the papers need.

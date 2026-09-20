# ADR 0006 — The model selects parameterised queries; it does not write them

**Status:** accepted · **Date:** 2026-09-19 · **Sprint:** 2–3

## Context
When a substrate is a graph, the obvious implementation is to let the model write SPARQL.
That reintroduces the hallucination surface the whole architecture exists to remove, and
opens an injection surface on an endpoint that must stay read-only.

## Decision
A parameterised template library (`ontology/cq/templates/*.rq`), derived from the live
competency questions. The planner selects a template and binds its parameters through
structured output against a JSON Schema. No template fits → `no_template` → abstain, with
that as the stated reason.

## Consequences
+ The query surface is enumerable, reviewable and testable.
+ Abstention has a precise, explainable cause — which is what §4.4 asks of every abstention.
+ Each added template is a measurable increase in reach.
− Questions outside the template set are abstained on rather than attempted. That is the
  intended trade, and template coverage is a reported number rather than a hidden one.

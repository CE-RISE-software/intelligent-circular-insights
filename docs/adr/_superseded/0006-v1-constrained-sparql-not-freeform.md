# ADR 0006 — The LLM selects SPARQL templates; it does not write SPARQL

**Status:** accepted · **Date:** 2026-09-19 · **Sprint:** 5

## Context
CE-RISE mode's strongest claim is that an answer about environmental performance comes from
triples. The obvious implementation — let the model write SPARQL — reintroduces the
hallucination surface we are trying to remove, and opens an injection surface on a
read-only endpoint that must stay read-only.

## Decision
A parameterised template library in `ontology/cq/templates/*.rq`, derived from the 16 live
competency questions and extensible toward the paper's 173. The planner selects a template
and binds parameters through structured output against a JSON Schema. No template fits →
`no_template` → the system abstains and says so.

## Consequences
+ The query surface is enumerable, reviewable and testable.
+ Abstention has a precise, explainable cause.
+ Each new competency question makes the system measurably more capable — and the paper
  already defines 173 of them, so coverage is a roadmap rather than a guess.
− Questions outside the template set are abstained on rather than attempted. That is the
  intended trade, and the coverage number is reported rather than hidden.

# ADR 0003 — One reliability envelope, with three enforced invariants

**Status:** accepted · **Date:** 2026-09-19 · **Sprint:** 0

## Context
COMPASS's central claim is that every output is either an evidence-grounded answer with
provenance or an explicit abstention. PEFDPP's central claim is reproducibility down to the
triple. Both are properties of the response, so the response type should enforce them.

## Decision
One `ReliabilityEnvelope` for every use case in every mode:
`decision · answer · value · evidence · provenance · confidence · data_trust ·
operating_point · grounding · mode · trace`.

`ProvenanceLink.kind ∈ {PASSAGE, FACT, RULE, TRIPLE, CALC_STEP}`. CE-RISE mode is
distinguished by emitting `TRIPLE` links carrying the IRI and the TTL file it lives in.

**Three invariants**, enforced at construction and asserted in every contract and e2e test:

1. `ANSWER ⟹ len(provenance) > 0` — COMPASS's reliability claim.
2. `ANSWER ⟹ grounding.verdict == FULLY_GROUNDED` — the enforced form of
   evidence-before-generation (§4.1 says it is currently prompting, not guarantee).
3. `ANSWER ⟹ confidence.calibrated ≥ operating_point.tau`, with τ returned in the response,
   so the operating point that produced an answer is auditable.

No configuration flag relaxes any of them.

## Consequences
+ The frontend renders one component tree for all six windows and both modes.
+ The papers' reliability claims become type invariants rather than conventions.
+ `data_trust` and `operating_point` give the bias-aware work a place to land without a fork.
+ Regressions in grounding surface as test failures, not as quietly worse answers.
− Every adapter must produce provenance even where the current code returns a bare string;
  this is real porting work in Sprint 1.

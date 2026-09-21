# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium

# A mode adds substrates; it never exchanges them

- Status: accepted
- Date: 2026-09-21
- Sprint: 3 (the rule dates from Sprint 2; this is its general form)
- Refines: ADR 0002, *Mode as adapter swap*

## Context

ADR 0002 is titled "mode as adapter swap", and the word *swap* turned out to be the
problem. It describes the mechanism accurately — a mode is a different set of bound
adapters — but reads as licence to exchange one adapter for another, which is the
wrong instinct for a mode whose purpose is to mount *more* knowledge. This record
does not overturn 0002; it constrains the direction of the swap.


`ProviderBundle` binds exactly one adapter per port. CE-RISE mode is built by
`replace()`-ing fields on the Normal bundle, which makes mounting new knowledge
look like a one-line assignment — and an assignment to a single slot is a swap.

This has now produced the same bug twice, in two different slots:

* **Sprint 2, the impact slot.** CE-RISE mode assigned `PefdppImpactEngine` into
  `impact`. The Carbon window immediately stopped working for the five products the
  graph has never heard of. Caught by a test asserting that a shared feature
  survives the switch.

* **Sprint 3, the substrate slot.** CE-RISE mode assigned `PefdppSubstrateRegistry`
  into `substrates`. The CE-RISE Models window went from eighteen models to none the
  moment you switched to the *more rigorous* backend — knowledge present in the fast
  mode and absent from the careful one, which is exactly backwards. Caught while
  wiring the frontend, by asking both backends the same question.

Both were one word in a docstring away from being noticed: the design has always
said CE-RISE *adds*. The word was load-bearing and the code did not enforce it.

## Decision

**A mode may only widen what is mounted. Where a port has one slot and two
implementations are wanted, they are composed, not exchanged.**

`CompositeSubstrateRegistry` holds an ordered tuple of member registries and
delegates:

* `mounted()` concatenates, in mount order.
* `facts_for()` merges every member's triples. A subject known to two substrates
  gets both views; suppressing one would silently pick a winner.
* `coverage_report()` concatenates per-substrate rows rather than summing them.
  ADR 0005 measures fire rate *per substrate*, and a pooled average would hide the
  very difference the instrument exists to show.
* Capability methods the port does not declare — `route`, `query`, `run_question` —
  are forwarded to the first member that implements one. Members are ordered
  most-specific-first, so the graph answers graph questions and the catalogue answers
  catalogue questions. The forwarding list is explicit rather than a blanket
  `__getattr__`, so a typo fails where it is written.

The invariant is asserted directly, not just per feature:

```python
assert normal_substrates < ce_rise_substrates
```

A mode that removes knowledge fails the suite.

## Consequences

`facts_for` now walks every member, so the cost of adding a substrate is linear in
mounted substrates rather than free. That is the correct shape: mounting more
knowledge should cost more, and the coverage report is there to say whether the
widening paid for itself.

The same reasoning applies to any port whose implementations are additive rather
than alternative. `impact` was fixed in Sprint 2 by keeping the CSV engine and
reaching the graph-solved assessment through the substrate instead; if a third
mounting ever wants two engines side by side, it composes.

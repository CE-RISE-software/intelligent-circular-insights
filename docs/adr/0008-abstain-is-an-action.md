# ADR 0008 — The policy seat: ship the router, leave room for the rest

**Status:** accepted · **Date:** 2026-09-19 · **Sprint:** 1

## Context
The paper states the RL router "is reported only for completeness; its paired tests show no
significant improvement and it is not claimed as a contribution." That is an honest result.
It is also explainable: the current agent is a linear softmax over six hand-made features
with four actions, trained on a small episode file, with abstention applied downstream as a
threshold rather than learned.

## Decision
`DecisionPolicy` is a port. The **supervised router ships as the default**, because it is the
configuration that works today. Two further seats exist and stay empty in this deliverable:

- a **contextual bandit** (LinUCB / Thompson) over the confidence signal vector — most of
  this problem is contextual rather than sequential, and a bandit would come with a regret
  bound the RL policy does not have
- an **offline RL policy** with `ABSTAIN` as a first-class action and reward
  `r = 1{correct} − λ·1{wrong} + 0·1{abstain}`, `λ > 1`, so the risk–coverage trade-off is
  learned rather than applied afterwards

Two architectural choices make those seats usable later: the policy's observation is the
confidence **signal vector** rather than six hand-made features, and `ABSTAIN` is expressible
as an action rather than only as a downstream threshold.

## Scope
**No policy evaluation happens in this deliverable.** No off-policy estimation, no
significance testing. The seven evaluation modes stay runnable with a smoke test each,
because they are part of what CE-RISE is being handed.

## Consequences
+ A later attempt at the policy question starts from the right interface instead of a
  refactor. The published "no significant improvement" result is worth revisiting, and the
  changes that would make it worth revisiting are structural.
+ The routing gap the paper names (COMPASS 0.7085 vs Sym-Only 0.9051 on logic) is
  addressable by a policy that can see the symbolic fire signal — which this observation
  space provides.
− Two empty seats in the codebase. They cost a `Protocol` and a docstring.

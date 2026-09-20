# ADR 0004 — Capture golden responses from the running demo before writing any adapter

**Status:** accepted · **Date:** 2026-09-19 · **Sprint:** 1

## Context
The instruction is that current features must not break. The current behaviour is
under-documented and under-tested (9 test files across the two backends, ~20,200 LoC), so "don't break it"
cannot be verified by reading.

## Decision
Before the first adapter is written, `tooling/capture_golden.py` drives the live
CE-RISE-Demo across every endpoint, every example DPP and the three broken ones, and records
the responses to `tests/golden/normal/`. Normal mode must reproduce them byte-for-byte,
normalising only timestamps, correlation ids, latency fields and float noise beyond
published precision.

The PEFDPP physics values are locked the same way in `tests/golden/pefdpp/`.

## Consequences
+ "No regression" becomes a command that exits 0 or 1.
+ Behaviour nobody documented is captured anyway.
− Golden tests also lock in current *bugs*. Any intentional fix must update a golden file
  in the same commit, with the reason in the message — which is the point: a deliberate
  change is visible in review.

# ADR 0007 — Calibration is a subsystem with a port, not a function in a scoring path

**Status:** accepted · **Date:** 2026-09-19 · **Sprint:** 4

## Context
The paper reports 10-bin in-domain ECE 0.525 for COMPASS against 0.487 for RAG-Base
(0.5247 to four decimals in `tables/calibration_diagnostics.tex`) — the
strongest accuracy configuration is the worse-calibrated one — while the same pipeline
reaches 0.021 on Open Food Facts. The abstract names calibration on the source domains as an
open challenge.

Today the confidence signals (retrieval margin, snippet agreement, symbolic fire flag,
generation probability) are aggregated into a scalar `ĉ(x)` and *then* calibrated by a
monotone map. A monotone map of a scalar cannot recover information the collapse destroyed.

## Decision
`Calibrator` becomes a port with at least four implementations: isotonic (current),
Platt/temperature, beta, and a **vector calibrator over the full signal vector**. Signals are
a named, inspectable `SignalVector` in the envelope rather than an internal scalar. Fitting
is per domain and per mode, with leave-one-study-out reporting. Diagnostics — ECE (10-bin
and adaptive), Brier decomposed into reliability/resolution/uncertainty, reliability
diagrams, per-signal ablation — are first-class output, not a script.

`SelectivePolicy` is separated from `Calibrator`: τ is chosen for a coverage target on a
held-out split and reported in the envelope, because the paper's position is that operating
points are policy choices.

## Scope
**This deliverable does not run the calibration experiment.** Isotonic ships as the default,
because it is what the system does today. The other implementations are present and
unfitted. What changes is that swapping one in, or fitting per domain, no longer requires
touching the call site.

## Consequences
+ The leading hypothesis about the in-domain gap — that the scalar collapse discards
  structure a vector calibrator could use — becomes testable later without a refactor first.
+ An abstention can name which signal was weak, because signals are a named field rather
  than an internal scalar. The UI should show this; today it cannot.
+ A data-trust layer landing later feeds the same pipeline rather than a parallel one.
− Slightly more indirection on the hot path, for a negligible per-request cost.

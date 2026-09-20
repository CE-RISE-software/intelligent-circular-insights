# Reference set

Responses frozen from the **existing** `CE-RISE-Demo` before any adapter was
written, captured by `tooling/capture_reference.py`. Normal mode must reproduce
them.

Focused on purpose: two representative queries and two edge cases per window,
roughly 30 responses. Capturing every endpoint against every example would cost
real API spend and catch almost nothing extra — a port that breaks behaviour
breaks it on the first case, not the fortieth. Small enough that when a response
legitimately changes, the diff is readable.

Comparison normalises timestamps, correlation ids, latency fields and float noise
beyond displayed precision. Nothing else.

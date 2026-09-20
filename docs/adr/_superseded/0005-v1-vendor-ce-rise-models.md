# ADR 0005 — Vendor the CE-RISE data models rather than fetch them at runtime

**Status:** accepted · **Date:** 2026-09-19 · **Sprint:** 2

## Context
The 17 CE-RISE data models live in separate Codeberg repositories. Codeberg is unreachable
from both this session's sandboxes (403 at the egress proxy), and a published, DOI-archived
artifact must be reproducible years later regardless of what those repos do.

## Decision
Vendor them into `schemas/ce-rise/<model>/`, with `VENDOR.md` recording each source URL,
commit SHA and fetch date. `tooling/fetch_ce_rise_models.sh` performs and refreshes the
vendoring; it is run by a human with network access, not by the application.

The application never fetches a schema over the network at runtime.

## Consequences
+ Reproducible builds; an archived tag validates exactly what it validated on release day.
+ Offline CI.
− Vendored copies go stale. Mitigation: a scheduled job diffs upstream and opens an issue;
  refreshing is a reviewable commit.

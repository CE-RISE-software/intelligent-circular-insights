# ADR 0010 — Distinct licences for software and CE-RISE data models

**Status:** accepted · **Date:** 20 September 2026

## Context

The software repository uses EUPL-1.2. The CE-RISE data models vendored into it
retain their upstream CC-BY-NC-4.0 licence. These are different artefacts with
different licence scopes. Their inclusion in one repository does not, by itself,
create a conflict or change either licence.

The repository-root `LICENSE` identifies the software licence. Without a separate
notice, readers could incorrectly assume that it also applies to the vendored
models. Equally, the models' NC condition must not be presented as a restriction
on all software in the repository.

## Decision

1. Application code remains under EUPL-1.2, as declared by the repository
   `LICENSE` and source-file SPDX identifiers.
2. Vendored CE-RISE data models and their generated schema artefacts retain
   their upstream CC-BY-NC-4.0 terms. They remain in `schemas/ce-rise/`, with a
   separate `LICENSE`, `NOTICE.md`, upstream provenance and file-level licence
   metadata. The application reads the schemas as data at runtime.
3. Documentation and metadata identify the applicable licence for each part;
   neither licence is described as covering the entire checkout.
4. This decision does not propose or require a change to either licence. Any
   future relicensing proposal belongs with the relevant rights holders and
   would be recorded separately.

## Consequences

- Users can identify the applicable terms for the software and for the data
  models without treating the repository as a single-licence work.
- Keeping vendored models and generated schemas together preserves their
  attribution and pinned provenance for reproducible validation.
- The NC condition applies to use of the licensed model material; it does not
  change the licence of the application code. Users planning uses of the models
  outside the licence terms may need separate permission.
- A separate directory and notice clarify scope. They do not resolve a licence
  conflict, because co-location alone creates none.

## Scope of openness

EUPL-1.2 permits commercial use of the software. CC-BY-NC-4.0 limits uses of
the model material to those allowed by its NonCommercial condition. This is a
distinction between the permissions attached to different artefacts, not a
reason to relicense either one. The project therefore retains the existing
licences and labels their scope explicitly.

## Not legal advice

This ADR documents the repository's licence boundaries, not a legal opinion
about a particular downstream use. Questions about uses outside the stated
terms should be addressed with the relevant rights holders or legal advisers.

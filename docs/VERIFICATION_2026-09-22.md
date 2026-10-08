# Verification checkpoint: 22 September 2026

This page records a local check made on 22 September 2026. It is historical;
later revisions require their own verification. For commands applicable to the
current source, see [Testing](TESTING.md).

## Observed in that run

- `make check` passed Ruff, formatting, MyPy and import-linter checks.
- The offline Python run reported 621 passing tests and 91% statement coverage
  for the measured packages and API.
- `make web-check smoke` built the frontend and passed 45 Chromium browser tests
  across the two backends, using cassette replay rather than live model calls.
- `make secrets` passed its tracked-file credential checks.

The run included Single passport edge cases for parsing, request-scoped model
use, model-disabled behavior, file input and stale browser responses. These
figures describe the code at that checkpoint, not the current test count or
coverage.

## Follow-ups recorded then

- Parameterised, read-only SPARQL templates needed a defined contract before
  any model-based query selection could be added.
- Provider retry, backoff and deployment spending policy remained separate
  from the cassette recorder's limits and per-request budget.
- A deliberate live-model check of the CE-RISE prompt variant had not been
  performed in that verification run.

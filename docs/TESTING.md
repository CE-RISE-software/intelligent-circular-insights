# Testing

The Python suite checks domain behavior, adapter contracts, HTTP routes,
grounding, and both backend modes. Browser smoke tests exercise the interface
against an API started in cassette replay mode. The commands below run from the
repository root after [source setup](run-from-source.md).

## Local checks

| Command | What it runs |
|---|---|
| `make check` | Ruff lint and format checks, MyPy and import-linter contracts |
| `make test-fast` | Python unit and contract tests |
| `make test` | Full Python suite, excluding opt-in live tests |
| `make web-check` | Frontend typecheck and production build |
| `make smoke` | Playwright browser tests with both servers started automatically |
| `make secrets` | Tests that tracked files contain no credentials |

`make smoke` needs a Chromium browser. Playwright can install one, or
`ICI_CHROMIUM` can point to an existing executable. Its servers use dedicated
local ports (`18000` for the API and `15173` for the browser) so they do not
reuse a developer's live-model session.

## Offline model tests

The default model mode is `LLM_CASSETTE_MODE=replay`. Recorded responses in
`tests/cassettes/recorded` make model-dependent tests reproducible without an
API key. A missing cassette fails rather than making a paid call. The ordinary
pytest fixture removes `OPENAI_API_KEY` and blocks network access. Live tests
are deselected unless explicitly requested; `-m live` alone does not enable
them.

The live-model check is a separate, deliberate operation:

```bash
make live
```

It needs an API key, can make paid requests, and is rejected by the test
configuration in CI or alongside `--no-network`. See
[`tests/live/README.md`](https://codeberg.org/CE-RISE-software/intelligent-circular-insights/src/branch/main/tests/live/README.md) for its request and spending
limits. Offline success does not establish live-model output quality.

## Test coverage

| Area | Tests |
|---|---|
| `tests/unit` | Domain invariants, retrieval and memory, schema handling, reliability, model runtime and deterministic calculations |
| `tests/contract` | Shared assertions against implementations of domain ports |
| `tests/integration` | Bundle construction and adapter interaction |
| `tests/e2e` | HTTP behavior, profile selection, record assistance and backend switching |
| `tests/golden` and `tests/reference` | Regression cases against captured reference behavior |
| `apps/web/tests` | Browser interactions and async UI state in both backend modes |
| `tests/live` | Opt-in provider checks using synthetic or public inputs |

The response envelope enforces that answered prose is grounded and carries
provenance, and that calibrated confidence clears the request's operating
threshold. Unit and end-to-end tests cover these invariants and the explicit
abstention path. Validation and record-assistance tests distinguish the profile
that actually ran, sourced fills, unresolved gaps and unapplied suggestions.

## Continuous integration

The Forgejo workflow in `.forgejo/workflows/ci.yml` runs on pushes, pull
requests and manual dispatch. Its Python 3.12 job runs the full code-quality
gate and offline Python suite with coverage. A Python 3.10 job runs typechecking
and the unit and contract subsets. Neither job receives an API key. Frontend
build and Playwright smoke tests are local checks, not part of this workflow.

The [22 September 2026 verification checkpoint](https://codeberg.org/CE-RISE-software/intelligent-circular-insights/src/branch/main/docs/VERIFICATION_2026-09-22.md)
records results from one earlier local run; it is not a claim about the current
revision. The original [testing design record](https://codeberg.org/CE-RISE-software/intelligent-circular-insights/src/branch/main/docs/testing-design-record.md) is
retained for rationale and proposed coverage, not as a list of tests that now
run.

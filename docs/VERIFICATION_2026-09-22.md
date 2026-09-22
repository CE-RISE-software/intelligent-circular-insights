# Verification and remaining work

Updated 22 September 2026 after the first push to Codeberg.

## Verified locally

- `make check`: Ruff lint and formatting, mypy (62 source files), import-linter (2 contracts).
- `LLM_CASSETTE_MODE=replay pytest --no-network --cov=packages --cov=apps`: 621 passed, 91% coverage. One upstream Starlette/anyio deprecation warning.
- `make web-check smoke`: TypeScript and production Vite build, then 45 Chromium browser tests across both backends. No live model calls.
- `make secrets`: 3 tests passed; no tracked `.env`. `npm audit --prefix apps/web`: 0 vulnerabilities.
- Single-passport edge cases cover invalid requests, request-scoped model use and audit, model-disabled operation, file upload, stale browser responses, malformed/ambiguous JSON, pointer escaping, and large-document tails. Its route has 100% line coverage; that does not imply exhaustive behavior coverage.

## Publication state

`main` was pushed to Codeberg and the remote head was verified at `b718a0a`.
Commit history remains intact. This project has used AI-assisted development;
Codeberg's [Terms of Use](https://codeberg.org/Codeberg/org/src/branch/main/TermsOfUse.md)
restrict projects mostly consisting of generated code. The repository owner is
responsible for confirming continued hosting eligibility. A successful git push
is not a policy determination. The GitHub repository is a mirror of Codeberg.

Before a future push, fetch and require
`git merge-base --is-ancestor origin/main HEAD`. Never force-push or tag as a
workaround. If the remote has changed, reconcile histories and rerun gates.

## Deliberately deferred

- **X8 — parameterised SPARQL templates.** The sixteen fixed competency queries work. Agree a read-only, subject-scoped template contract before adding model-based selection. No free-form SPARQL generation should be added without that contract.
- **X9 — production retry/backoff and budget policy.** The recorder's ceiling is a recording cap, not a deployment dollar ceiling. `RequestBudget` is per request.
- **X10 — deliberate live-model smoke before release.** The CE-RISE prompt variant has offline HTTP/transport coverage but no real-model recording. No paid live calls were made in this verification.
- Release work: a clean-clone build, Codeberg Pages, tag → GitHub mirror → Zenodo. No release tag has been made. `CITATION.cff` correctly has no DOI until the first tag mints one.
- Upstream licensing: the 18 CE-RISE data models remain CC-BY-NC-4.0. That is separate from the EUPL-1.2 code and should be reviewed by Riccardo for the intended open-data claim.

The Single DPP window uses the same request-scoped model runtime as Search, so
the disabled-model switch, grounding guard, budget, and audit apply. Caller-supplied
documents are the only evidence; memory is not part of that window. Preserve the
regression tests if touching parsing, use-case binding, or the browser's async
form state. Do not treat this offline run as evidence of live-model output quality
or release mirroring. Detailed working notes remain in a local ignored directory.

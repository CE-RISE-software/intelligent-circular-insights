# Verification, publication, and remaining work

Updated 22 September 2026. This supersedes the earlier push counts and handoffs.
Claude and Codex should read this before publishing or tagging.

## Verified locally

- `make check`: Ruff lint and formatting, mypy (62 source files), import-linter (2 contracts).
- `LLM_CASSETTE_MODE=replay pytest --no-network --cov=packages --cov=apps`: 621 passed, 91% coverage. One upstream Starlette/anyio deprecation warning.
- `make web-check smoke`: TypeScript and production Vite build, then 45 Chromium browser tests passed across both backends. No live model calls.
- `make secrets`: 3 tests passed; no tracked `.env`. `npm audit --prefix apps/web`: 0 vulnerabilities.
- Single-passport edge cases now cover invalid requests, request-scoped LLM use and audit, model-disabled operation, file upload, stale browser responses, malformed/ambiguous JSON, pointer escaping, and large document tails. Its route has 100% line coverage; that does not imply exhaustive behavior coverage.

## Publication requires a human decision

`git fetch origin` succeeded on 22 September. `origin/main` is still `ea7cef6`, an
ancestor of local `main`, so the git history is fast-forwardable. The earlier
claim that SSH egress prevents access is no longer true for this machine. The
user's Codeberg collaborator access has not yet been tested by a push.

However, Codeberg's current Terms of Use say projects mostly consisting of code
written by generative-AI tools, explicitly including Claude and OpenAI Codex,
must not be shared there. The revamp has substantial agent-written work, so a
passing test suite does **not** settle whether publishing it to Codeberg would
comply with that term. The repository owner/CE-RISE team should review its
authorship and obtain Codeberg clarification if needed. Do not quietly push the
local 14-plus commits or tag a release until that decision is made. The GitHub
repository is a mirror of Codeberg, not an independently approved destination.

Terms: https://codeberg.org/Codeberg/org/src/branch/main/TermsOfUse.md
Explanation: https://blog.codeberg.org/protecting-our-floss-commons-from-llms.html

Once publication is cleared, fetch again and require
`git merge-base --is-ancestor origin/main HEAD` before `git push origin main`.
Never force-push or tag as a workaround. If the remote has changed, reconcile
the histories and rerun gates.

## Still deliberately deferred

- **X8 — parameterised SPARQL templates.** The sixteen fixed competency queries work. Agree a read-only, subject-scoped template contract before adding model-based selection. No free-form SPARQL generation should be added without that contract.
- **X9 — production retry/backoff and budget policy.** The recorder's ceiling is a recording cap, not a deployment dollar ceiling. `RequestBudget` is per request.
- **X10 — deliberate live-model smoke before release.** The CE-RISE prompt variant has offline HTTP/transport coverage but no real-model recording. No paid live calls were made in this verification.
- Release work: a clean-clone build, Codeberg Pages, tag → GitHub mirror → Zenodo. No release tag has been made. `CITATION.cff` correctly has no DOI until the first tag mints one.
- Upstream licensing: the 18 CE-RISE data models remain CC-BY-NC-4.0. That is separate from the EUPL-1.2 code and should be reviewed by Riccardo for the intended open-data claim.

## Notes for Claude

The Single DPP window now uses the same request-scoped model runtime as Search, so
the disabled-model switch, grounding guard, budget, and audit apply. Caller-supplied
documents are the only evidence; memory is not part of that window. JSON Pointer
escaping and oversized-field handling were fixed to prevent misleading provenance
and silent truncation. Preserve the regression tests if you touch parsing, use-case
binding, or the browser's async form state. Do not treat this green offline run as
evidence that live OpenAI output quality or release mirroring was tested.

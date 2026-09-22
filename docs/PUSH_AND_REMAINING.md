# Pushing, and what is actually left

> **Historical snapshot (21 September).** Counts, push instructions, and the
> Codeberg access claim below are superseded by
> [the 22 September verification and publication note](VERIFICATION_2026-09-22.md).
> In particular, do not push until Codeberg's current generative-AI terms have
> been reviewed against this project.

Written 21 Sep after auditing the tree rather than trusting the handoffs — two of
which contradicted each other. This is the single current statement; where it
disagrees with `CODEX_HANDOFF.md`'s older sections, this is right.

## The push is a fast-forward

`origin/main` is at `ea7cef6` (*chore: adopt the CE-RISE software template*), which
is an **ancestor of HEAD**. The unrelated-histories problem from earlier sprints was
solved when that template commit landed, so there is nothing to rebase or merge:

```
0 behind, 10 ahead — git merge-base --is-ancestor origin/main HEAD → true
```

```bash
cd revamp
git fetch origin                      # the local ref was last updated 21 Sep 09:29
git log --oneline origin/main..HEAD   # expect the 10 commits listed below
git merge-base --is-ancestor origin/main HEAD && echo "fast-forward, safe"
git push origin main
```

If `--is-ancestor` fails after the fetch, someone has pushed in the meantime.
**Rebase, do not force** — the remote carries Riccardo's template provenance and a
force-push erases it.

**Claude cannot do this.** `CONNECT codeberg.org:22: Forbidden` — SSH is refused at
this machine's egress proxy, the same policy that blocks `api.openai.com` and
`cdn.playwright.dev`. No credential changes it. Codex or a terminal on the Mac.

### Before the first public push, one human look

The three secret layers make it near-impossible, but a public mirror deserves it:

```bash
git ls-files | grep -c '\.env$'    # must be 0
make secrets                       # tracked-credential audit
```

## The ten commits

| | |
|---|---|
| `c1ee0b2` | mode switch, reliability envelope, `apps/web` |
| `b8fa843` | **Codex** — request-scoped runtime, CE-RISE prompting, mode matrix |
| `222122d` | **Codex** — handoff/task refresh |
| `95ba8f9` | repair + synthesis routes, the four use cases filled |
| `8b430bd` | key placed locally, three layers to keep it unpublishable |
| `854f226` | `.env.example` completed |
| `e28278f` | recording handoff |
| `0bd243b` | **Codex** — grounded assistance completed, route cassettes recorded |
| `ef726bd` | every wheel carries its licence |
| `64be3b3` | self-healing web install, handoff corrected |

## State

```
578 pytest, no API key, 28 s        ruff · ruff format · mypy (61) · import-linter 2/2
35 playwright smoke, both modes     tsc strict · vite build 246 kB / 77 kB gz
ledger 25 attempts, $0.119 of $1    npm audit: 0 vulnerabilities
clean tree, 28 commits
```

Both backends live in one process; every published WP3 figure reproduces; all 16
competency questions answer; repair and synthesis run against **recorded real
responses**, not stubs.

## What is genuinely left

Nothing blocks a demo. Everything below is either deliberately deferred or belongs
to a later sprint.

### Deferred on purpose
- **X8 — parameterised SPARQL templates.** The sixteen fixed competency queries
  work. What does not exist is a registered template/binding library for
  model-chosen queries. This was put under the cut line deliberately, and the
  order matters: agree a read-only, subject-scoped template contract *first*, then
  add model-based selection. No free-form SPARQL generation exists and none should
  be added without that contract.

### Sprint 4 — reliability polish
- **X9 — production retry/backoff and a budget policy.** The recorder's ceiling is
  a *recording* cap, not request budgeting; `RequestBudget` (8 calls, 100k reserved
  tokens) is per-request and has no dollar ceiling. A deployment serving real users
  needs both.
- The CE-RISE prompt variant has offline coverage but **no real-model recording**.
  Its behaviour is tested at the transport and HTTP boundary; its live quality is
  unmeasured.

### Sprint 5 — release
- **X10 — a deliberate live smoke run** against the real model before tagging.
- Release gates not yet certified: full legacy parity, a clean-clone build,
  Codeberg Pages, tag → mirror → Zenodo. **No release tag has been made.**
- `CITATION.cff` has no DOI, deliberately — the first tag mints the concept DOI and
  inventing one now would be worse than leaving it out.

### Upstream, not ours
- The **18 CE-RISE data models are CC-BY-NC-4.0**, and NC is not open source. That
  blocks "open to all" for the data, not the code. Riccardo's call: was NC
  deliberate or inherited from a template? The segregated `schemas/ce-rise/`
  subtree with its own LICENSE and NOTICE is correct under either answer.
- **Codeberg team access** still needs your username sent to Riccardo — outstanding
  since his 1 July email, and nothing can be pushed to the org without it.

## Corrections to the older handoff

`CODEX_HANDOFF.md` has been annotated in place, but for the record:

- *"Repair/synthesis app integration is still absent"* — done in `95ba8f9`.
- *"Four core use cases still raise NotImplementedError"* — done in `95ba8f9`.
  `grep -rn NotImplementedError packages/ apps/` returns nothing.
- *"root pyproject.toml still says MIT"* — the root was already EUPL-1.2. The real
  gap was the nine member packages, each of which builds a wheel and declared no
  licence at all. Fixed in `ef726bd`, with `tests/test_packaging.py` asserting
  against `CITATION.cff` so the two cannot drift.
- *"frontend dependencies under `/tmp/ici-s3-web.*`"* — that link was already
  dangling and the frontend would not build. `make web` now installs to
  `$HOME/.ici-web-modules` and repairs a broken link rather than failing with
  "Cannot find module 'vite'".

One sentence in the old notes was right and stays right: **the gates prove what is
built, not what the plan called for.** That is how repair and synthesis sat
unrouted through two green sprints.

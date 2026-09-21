# Running with a real API key

Everything in this repository runs without a key. Retrieval, conformance checking,
both impact engines, the WP3 graph, all 16 competency questions, the symbolic layer
and the full test suite are deterministic and free. A key is needed for exactly two
things: **recording cassettes**, and **running live**.

## Where the key lives

`.env` at the repository root. It is not committed and cannot be.

```
OPENAI_API_KEY=sk-proj-…
LLM_CASSETTE_MODE=replay
LLM_MODEL_DEFAULT=gpt-4o-mini
```

`.env.example` is the committed template. `apps/api/settings.py` is the only module
in the codebase that reads the environment — nothing else calls `os.getenv`, which
is why this file is the whole configuration surface.

## Three things stop the key reaching the mirror

This repository is mirrored publicly, and **deleting a committed key does not
remove it from history**: a key committed once has to be rotated, not deleted. So
there are three layers, and they were each tested against a fake key before the
real one was placed.

1. **`.gitignore`** — `.env`, `.env.*`, `*.key`, `*apikey*`, `*credential*` and
   more, with `.env.example` as the one named exception.
2. **`.githooks/pre-commit`** — refuses a commit whose staged filenames *or staged
   content* look like a credential. Enable with `make hooks`; git does not install
   hooks from a clone, so this layer does not travel.
3. **`tests/test_no_secrets.py`** — fails the suite if any *tracked* file is named
   like a credential or contains something shaped like a live key. This is the layer
   that matters, because it is the only one present on a fresh clone and it is what
   CI runs. `make secrets` runs it alone.

A key sitting in an ignored `.env` passes all three. That is the intended
arrangement.

## Recording cassettes

Cassettes are recorded responses. Once recorded, the suite replays them forever with
no key and no spend — which is what makes `make test` free. A cassette **miss** in
replay mode fails loudly rather than quietly calling the network.

```bash
make record
```

That runs `tooling/record_llm.py`, which:

- requires `--record` and an explicit `--env-file`, and calls nothing without both;
- refuses to run when `CI` is set;
- takes an exclusive lock, so two recordings cannot interleave;
- **reserves worst-case estimated cost before every attempt, including attempts
  that fail**, and stops at 40 calls or 1.00 estimated USD, cumulative across runs;
- redacts the key from everything it writes;
- compares against `expected.json` when one exists and **refuses to overwrite** a
  golden output that has changed — review the difference, do not clobber it.

Re-running is safe: existing cassettes are reused, so only genuinely new cases cost
anything. The full set is 14 cases; a complete first run is well inside the cap.

Afterwards, confirm the suite is free again:

```bash
LLM_CASSETTE_MODE=replay make test
```

### What the route-level cases are for

Sprint 3.1 added `route-repair:battery` and `route-synthesis:battery`. The other
record/synthesis cases drive `RecordComposer` against a **fixture** context pack;
the two new ones drive it through `SynthesizeRecord` with a pack built by **live
retrieval**, exactly as `POST /api/validate/repair` and `POST /api/synthesize` do.

That distinction is the reason those two endpoints shipped with no replayable
cassette: a fixture pack and a retrieved pack produce different request hashes, so
the composer's cassettes can never satisfy the routes. The cases use a fixed
correlation id for the same reason — a varying one scopes memory recall differently
and silently changes the prompt.

Until they are recorded, the happy path through those two endpoints has never run
against a real model. Their *refusal* paths are covered and run for real: a product
with no retrievable evidence is declined before the model is called at all, and a
test asserts the composer receives nothing on that path.

## Running live

```bash
LLM_CASSETTE_MODE=live make demo
```

Every request calls the model and nothing is recorded. Useful for a demo, wrong for
a test run — there is no budget ceiling on this path, only the per-request one in
`RequestBudget` (8 calls, 100k reserved tokens).

To switch language-model features off entirely while keeping the rest of the
workbench, set `LLM_DISABLED=true`. Search, repair and synthesis then return a typed
422 with a reason; conformance and both impact engines are unaffected.

## For Codex

The key is at `revamp/.env`, extracted from `../openApikey.rtf`. Read it through
`Settings`, never by parsing the `.rtf` again and never by `os.getenv` outside
`settings.py`.

If you record, run `make record` rather than calling the API directly — the budget
ledger, the lock and the key redaction all live in that path, and a direct call has
none of them. Say in your handoff how many live attempts the ledger recorded
(`tests/cassettes/recorded/ledger.json`) so the spend is on the record.

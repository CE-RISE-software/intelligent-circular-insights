# Cassettes

Recorded LLM interactions, replayed by the whole test suite.

**Why this directory is the most load-bearing thing Codex builds.** Once these
exist, nobody spends another OpenAI call to run tests — not a developer, not CI,
not the other agent. `make test` works with `OPENAI_API_KEY` unset.

- Format: one `<request_hash>.json` file containing
  `{request_hash: {"version": 1, "response": <SDK response>}}`. The hash covers
  endpoint, resolved model, full rendered messages (including evidence and schema),
  prompt identity and option kwargs. Keys are redacted before writing. Requests
  are not saved separately. Existing recordings are replayed even in record mode.
- `LLM_CASSETTE_MODE=replay` (the default) never touches the network and **fails
  on a cache miss**. A drifted prompt breaks a test rather than quietly spending
  money.
- Recording is deliberate: `python -m tooling.record_llm --record --env-file <path>`.
  The command refuses CI, takes an exclusive recorder lock and persists a cumulative
  ceiling of 40 attempts / $1 conservatively estimated reservation. Existing hashes
  replay even in record mode. The ledger includes failed attempts in the ceiling.
- Sprint 1 used **22 real calls**, including one GPT-5 structured check and one
  embedding batch. The token-rate cost estimate is about **$0.0048** (not a bill).
  Responses from eight superseded prompt cases are retained for audit.

Commit these. They are test fixtures, not build output.

`synthetic/` holds clearly labelled hand-built fixtures, including a historical
grounding-v1 fixture. `recorded/` holds real responses, the reviewed expected
outputs, capture manifest and spend ledger. `inputs/` holds the three broken demo
records; synthetic search and DPP inputs are in `tests/llm_scenarios.py`.
The adapter receives mode/directory settings explicitly; it does not read the
environment itself. See `docs/CODEX_HANDOFF.md` for wiring through API settings.

Run `pytest -m cassette --no-network` or the entire `pytest --no-network` suite.
Do not re-record merely to run tests. Prompt drift is a review event, not a reason
to overwrite golden expectations automatically.

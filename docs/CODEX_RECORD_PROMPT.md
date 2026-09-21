# Prompt for Codex — record the two route-level cassettes

## Completed by Codex, 2026-09-21

The request below is retained as history, **not a pending command**. The initial
handoff's "everything is wired" assumption was incorrect: the test and recorder
seeds differed, and retrieved prose did not meet the exact structured-evidence
contract. The routes now gather complete same-product JSON reference records.
The happy path uses an explicitly synthetic Demo / Example 1 battery, shared
between the recorder, HTTP tests and browser examples. The original Generic BEV
example still requires its own evidence; no real compliance facts were invented.

Recorded the two cases with **2 new calls**, cumulative ledger **23 → 25**.
Cumulative reserved estimate is **$0.11865650**; the two new calls' usage estimate
is **$0.00123135**. All 12 existing golden cases stayed unchanged. Repair returned
3 supported fills; synthesis returned 11 field support entries. Route replay tests
now fail on missing recordings instead of skipping. Full status and remaining
future-sprint work: [`CODEX_HANDOFF.md`](CODEX_HANDOFF.md).

## Original recording request (historical)

Paste this into Codex, in the `llmmain/revamp` repository.

---

Record the two new route-level cassettes. Everything is already wired; this is one
bounded command plus a verification.

**Context.** Repair and synthesis now have routes (`POST /api/validate/repair`,
`POST /api/synthesize`) and a use case (`SynthesizeRecord`) behind them. Your
`RecordComposer` cassettes cannot serve those routes: yours were recorded against a
*fixture* context pack, and the routes build theirs from live retrieval, so the
request hashes differ. Two cases were added to `CASE_NAMES` to close that —
`route-repair:battery` and `route-synthesis:battery` — which drive
`SynthesizeRecord` through the exact path the endpoints use.

**The key** is at `revamp/.env` (`OPENAI_API_KEY`), extracted from
`../openApikey.rtf`. It is ignored by `.gitignore`, by `.githooks/pre-commit` and by
`tests/test_no_secrets.py`. Read it through `Settings`; do not parse the `.rtf`
again and do not call `os.getenv` outside `apps/api/settings.py`.

**Run:**

```bash
make hooks     # once: installs the pre-commit secret guard
make record    # bounded: 40 calls / $1.00 cumulative, ledger-backed
LLM_CASSETTE_MODE=replay make test
```

`make record` reuses every existing cassette, so only the two new cases should cost
anything. The ledger currently shows 22 recorded calls and $0.109 reserved of the
$1.00 ceiling — ample headroom, but it is cumulative across runs, so check
`tests/cassettes/recorded/ledger.json` afterwards and say how many live attempts it
grew by.

**What success looks like.** These three currently skip with
*"no route cassette recorded yet"*; after recording they must pass:

```
tests/e2e/test_record_assistance.py::TestTheRecordedHappyPath
  test_repair_fills_a_field_from_a_real_response
  test_every_suggestion_still_carries_its_warning
  test_synthesis_returns_a_conforming_passport
```

**Two things to watch.**

1. If the recorder reports *"Replay results differ from the golden output for: …"*,
   it has named a case whose output changed — that is a real regression in a prompt
   or a guard, not a stale fixture. Review it; do not overwrite `expected.json`.
   Adding cases is handled separately and will not trigger this.

2. `test_synthesis_returns_a_conforming_passport` asserts the generated record
   conforms to the bound profile. If the real model cannot produce one from the seed
   `{"dpp_id": "synthetic-demo-dpp-001", "product": {"brand": "Generic", "model":
   "BEV pack 60 kWh", "category": "battery"}}`, that is a finding worth reporting
   rather than a test to relax — `SynthesizeRecord` raises rather than returning a
   non-conforming passport, and that is deliberate. Say what the violations were.

**Afterwards**, commit the cassettes, `expected.json`, `manifest.json` and
`ledger.json`. Confirm in your handoff that `git ls-files | grep -c '\.env$'` is `0`.

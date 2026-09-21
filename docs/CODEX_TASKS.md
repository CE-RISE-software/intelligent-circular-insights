# Codex task list — `revamp/`

Everything here touches the OpenAI API, prompts, or model behaviour. Claude cannot run it
(no key, no live calls), so it is yours end to end.

**Your tree.** `packages/ici_llm/**`, `tests/unit/llm/**`, `tests/grounding/**`,
`tests/cassettes/**`, and `tests/live/**`. Prompt files live in
`packages/ici_llm/prompts/`. Coordinate changes to shared core/API files with Claude.
The user authorized the Sprint 0x integration fixes documented in `CODEX_HANDOFF.md`.

**Your seam.** `LLMProvider` and `GroundingVerifier` are frozen after Sprint 0. Claude codes
against a `FakeLLMProvider`; you code against fake evidence packs.

**Scope note (v3).** This is a CE-RISE software deliverable, not a paper's evidence package.
There are no experiment sweeps here, and **OpenAI spend is the scarce resource**. Your most
important single deliverable is X2, the cassette harness: once recorded, nobody — not Claude,
not CI, not you — spends another API call to run the test suite. Record once, on
`gpt-4o-mini`, around 40 calls total.

**Read first:** `ARCHITECTURE.md` §4 (the 15 ports), §5 (the envelope invariants), §6 (the
inference path), §9.3 (why grounding is yours). The governing rule:

> **An answer with an unresolved claim cannot be returned.** Not a preference, not a config
> flag — an invariant. When you cannot resolve a claim to an evidence id, the system abstains
> and says which claim failed.

Tick the box and name the passing test when a task is done.

---

## X0 — `LLMProvider` adapter and model routing · S0 · blocks everything

- [x] **Goal.** One interface, two configured models, no model-specific logic anywhere else.
  Verified by `tests/unit/llm/test_compat.py` and `tests/unit/llm/test_provider.py`
  using synthetic transport responses and the actual SDK; no live call made.

**Where to look.** `CE-RISE-Demo/backend/api/llm_compat.py` — 49 lines, and all of it
correct. Port it; do not re-derive it:

- `gpt-5` accepts only its default temperature on Chat Completions → send no `temperature`
  for `gpt-5*`, send it for `gpt-4o-mini`
- plain `gpt-5` spends reasoning tokens from the *same* completion budget as visible text,
  so lookup-style grounded calls set `reasoning_effort: "minimal"`
- `max_completion_tokens`, never `max_tokens`
- structured output on gpt-5 goes through `text.format = {type: json_object}` with
  `max_output_tokens` and `reasoning.effort = minimal`

Also `search.py:66` `_resolve_model` (header-driven resolution) and `:97` `_completion_issue`
(finish-reason and refusal handling).

**Output.** `provider.py` · `routing.py` · `compat.py` · `budget.py` · `errors.py`
(`RateLimited`, `Refused`, `Truncated`, `Unavailable`, `BudgetExceeded`).

**Acceptance.** `pytest tests/unit/llm/test_compat.py` — one test per rule, asserting the
exact kwargs dict per model. A `finish_reason="length"` raises `Truncated`; a partial
completion is never returned as if it were whole. An unknown model falls back to the default
with a logged warning, never raises.

---

## X1 — `GroundingVerifier` · S0 · **the highest-value thing you build**

- [x] **Goal.** Turn "evidence before generation" from a prompting discipline into a
  mechanical check. This removes a real failure mode — an answer containing an unsupported
  claim reaching a user — for a few hours of work.

  Implemented and verified by `tests/grounding/test_grounding.py` and
  `tests/unit/llm/test_runtime.py`. Entailment remains model-assisted; structural
  checks enforce citation identity, exact support quotes, coverage and quantities.

The paper is candid that this is currently enforced by prompting and audited by surfaced
citations, "not a formal guarantee that parametric knowledge cannot leak." You cannot close
that gap completely — no black-box method can — but you can close the audit side, which is
what matters operationally: an answer containing a claim that resolves to nothing in the
context pack must not reach the user.

**Design.**

```python
class GroundingVerifier(Protocol):
    def verify(self, answer: str, pack: ContextPack) -> GroundingReport: ...


# GroundingReport: claims_total, claims_resolved, unresolved[], verdict
```

Three stages: decompose the composition into atomic claims; resolve each to an evidence id
present in the pack; classify. Decomposition is the hard part and is where a model helps —
use `structured()` against a claim-list schema, and make the decomposition itself
reproducible (prompt id + hash in the trace).

**Acceptance.** `pytest tests/grounding/test_grounding.py` with hand-built cases: a fully
grounded answer, an answer with one fabricated claim, an answer citing an id not in the
pack, an answer that paraphrases the pack correctly (must pass), an answer that adds a
plausible but unsupported number (must fail). Plus `tests/grounding/` — a dozen edge cases, asserting no answer with an unresolved claim
is ever returned.

---

## X2 — Cassette record/replay · S0 · blocks CI

- [x] Every other worker and every PR build runs offline and deterministically.
  Verified by `tests/unit/llm/test_cassettes.py`, `test_offline_gate.py`, and
  `test_runtime.py::test_committed_synthetic_fixture_replays_end_to_end`.
  S0x fixtures remain clearly labelled synthetic. S1 added real recordings and
  `tests/golden/normal/` replay, using 22 cumulative API attempts including prompt
  refinements, with exactly one GPT-5 call. See the recorded manifest/ledger.

`CassetteProvider` wrapping the real provider: `record` calls the API and writes
`{request_hash: response}`; `replay` never touches the network and **raises on a cache miss**
so a drifted prompt fails loudly instead of quietly calling out. Hash covers model, prompt
text, schema and option kwargs. Keys redacted.

**Acceptance.** `pytest -m cassette --no-network` green with `OPENAI_API_KEY` unset. An
altered prompt produces a miss and a failing test, not a live call.

---

## X3 — Grounded composition and the guards · S1 · highest value

- [x] **Goal.** Port the composition path. It already works and is among the most valuable
  things in the current codebase.

  Verified by `tests/unit/llm/test_guards.py`, runtime tests, and real-response
  `tests/golden/normal/search/`. Legacy pure predicates are executed for parity;
  deliberate numeric/citation safety corrections are recorded in ADR 0011.
  Goldens cover the LLM boundary; Claude owns full HTTP/retrieval integration parity.

**Where to look.** `CE-RISE-Demo/backend/api/search.py`:

| Function | Line | What it catches |
|---|---|---|
| `_llm_compose` | 118 | the grounded call |
| `_invalid_evidence_citations` | 182 | claims citing evidence that is not there |
| `_grounded_hint_or_abstention` | 214 | the abstention path |
| `_extractive_fallback` | 227 | composition failed → fall back to extraction |
| `_looks_like_header_copy` | 231 | the model parroting a section header as an answer |
| `_misses_reliable_hint` | 243 | answer ignores the reliable evidence it was given |
| `_asks_unsupported_requirement` | 306 | question wants something the schema cannot carry |

**Output.** `composition.py`, `guards.py`, with typed internal prompt/composition records
if useful. The frozen public `LLMProvider.compose(instruction, pack, ...) -> str`
contract stays unchanged; request audit is collected by `LLMRuntime`. Each guard is a named predicate whose name appears
in the trace, so an abstention is explainable by which guard fired.

**Acceptance.** `pytest tests/unit/llm/test_guards.py` — positive and negative case per
guard, drawn from real recorded responses. `pytest tests/golden/normal/search` reproduces
today's output exactly.

---

## X4 — Prompts out of f-strings · S1

- [x] `packages/ici_llm/prompts/*.md` with YAML front-matter (`id`, `version`,
  `model_families`, `purpose`). A loader that hashes the rendered prompt into `Trace`.

  `tests/unit/llm/test_prompt_registry.py`, runtime/record audit tests, and wheel
  resource loading verify the six Sprint 1 prompts (seven after X7).
  No persona prompts in Python.

**Acceptance.** `pytest tests/unit/llm/test_prompt_registry.py` — every referenced prompt
exists, renders with its declared variables, and its hash appears in a composed answer's
trace. `grep -rn 'You are' packages/ --include=*.py` returns nothing.

---

## X5 — Repair and synthesis · S1

**Sprint 3.1 integration follow-through (21 Sep):** API and UI repair/synthesis now
work in both modes with same-product structured reference evidence and two new
real-response cassettes. User-requested training-only suggestions remain separate,
review-only and capped at 0.30. Mandatory HTTP and browser replay gates pass;
see `CODEX_HANDOFF.md`. This does not complete X8, X9 or X10 below.

- [x] Validate & Repair proposes grounded fills; Synthesize produces a schema-valid DPP.
  Both through `structured()`, both refusing to invent.

  Verified by `test_records.py` and recorded `tests/golden/normal/{validate,synthesize}/`.
  User amendment (2026-09-20): repair ALSO returns separate model-training
  `suggestions`, marked unverified/requires_review, confidence capped at 0.3.
  These never enter the repaired record, grounded fills, or answer evidence.
  No calibrated probability or actual compliance is implied (ADR 0011).

**Where.** `CE-RISE-Demo/backend/api/validate.py` (360), `synthesize.py` (339).

Every proposed fill carries its evidence and a confidence; a fill with no evidence is not
proposed — it is reported as "cannot be grounded". Synthesis output is validated against the
EU DPP JSON Schema before return; a schema failure is one retry with the violation in the
prompt, then an error, never a silent pass.

**Acceptance.** `pytest tests/golden/normal/validate` and `.../synthesize`. Plus: the 3
intentionally-broken DPPs, asserting every proposed fill has a resolvable evidence ref.

---

## X6 — Embeddings · S1

- [x] One port, two backends: `text-embedding-3-small` and
  `sentence-transformers/all-MiniLM-L6-v2` (the current default). Batching, content-hash
  caching, dimension assertion at load so a mismatched index fails at startup not query time.

  Verified by `tests/unit/llm/test_embeddings.py` (shared backend contract, restart
  cache, threading, corruption, identity/dimension checks), recorded OpenAI replay,
  and a genuine cached-weight MiniLM smoke (384 dimensions, normalized vectors).

**Acceptance.** `pytest tests/unit/llm/test_embeddings.py` — cache hit avoids a call;
dimension mismatch raises at construction; both satisfy the same contract suite.

---

## X7 — Mode-aware prompting · S3

- [x] In CE-RISE mode the system prompt states that mounted substrates are authoritative and
  that a claim which cannot be attached to a substrate fact must be abstained on rather than
  softened.

  Completed 2026-09-21. `compose_ce_rise@1` is selected from the resolved bundle
  mode in the request runtime. `tests/e2e/test_mode_matrix.py -k llm` checks the
  actual system message, prompt id/hash in the HTTP trace, model headers, fallback,
  and concurrent request isolation. `tests/grounding/test_graph_questions.py`
  checks missing-fact abstentions. One explicitly synthetic CE-RISE cassette
  exercises offline replay; no new live call or change to Normal-mode recordings.
  Search now binds guards/grounding/audit through the runtime; see the handoff.

**Acceptance.** `pytest tests/e2e/test_mode_matrix.py -k llm` — the prompt hash in the trace
differs by mode, and the CE-RISE variant is the one actually sent.

---

## X8 — Constrained substrate query planning · S3 · *only if S2 lands early*

- [ ] **Goal.** The model reads intent and *selects* a query; it does not write SPARQL
  freehand.

  **Deferred under the cut line, 2026-09-21.** Claude shipped the sixteen fixed
  competency queries in `ontology/pefdpp/cq/questions.json`, but not the planned
  registered parameterized template library or binding contract. The existing
  deterministic CQ runner remains available. Do not pretend these global queries
  safely bind arbitrary product questions; agree that seam before enabling X8.

Free-form generation over a graph is both a hallucination surface and an injection surface
on an endpoint that must stay read-only. Claude ships a parameterised template library
(`ontology/cq/templates/*.rq`, derived from the live competency questions); your planner
selects a template and binds parameters through `structured()` against a JSON Schema. No
template fits → `no_template` → abstain with that reason.

**Output.** `graph_planner.py` returning `TemplateSelection{template_id, bindings,
confidence}` or `NoTemplate{reason}`.

**Acceptance.** `pytest tests/grounding/test_graph_questions.py` — a handful of questions
whose answers are absent from the mounted substrate, each abstaining.

**Cut line.** If Sprint 2 runs long, ship CE-RISE mode with the competency-question runner
only (deterministic, no LLM in the loop) and leave this for later. It is the most optional
item on this list.

---

## X9 — Retries and budget ceiling · S4

- [ ] Exponential backoff with jitter on 429/5xx, and a hard per-request budget ceiling that
  raises `BudgetExceeded` rather than looping.

Carry over what the pacing commits on `main` already learned — *pace live reruns for rolling
request quotas*, *shard batch reruns for project token limits*. That is hard-won knowledge
about these quotas; don't rediscover it.

**Acceptance.** `pytest tests/unit/llm/test_retry.py` with a fake clock — backoff schedule
asserted, ceiling raises, no unbounded loop. No live calls in the test.

---

## X10 — Live smoke · S5 · run by hand, never by CI

- [ ] `tests/live/`, marked `@pytest.mark.live`. Six calls: one per window, `gpt-4o-mini`,
  plus one `gpt-5` call because its compatibility rules genuinely differ. Run manually before
  a release to confirm the cassettes have not gone stale against the live API.

Never in CI, never in a git hook. Nobody should be able to spend money by accident.

---

## Rules for every task

1. Nothing outside `ici_llm` knows which model is in use; model-specific behaviour lives in
   `compat.py` alone.
2. Never return a partial or truncated completion as if whole — raise `Truncated`.
3. Every call records prompt id + hash, model, tokens, cost, latency, guard outcomes.
4. A model refusal is an abstention with a reason, not an error page.
5. No prompt text in Python source.
6. No live call in CI, in a hook, or in the default test run.
7. A model's self-reported confidence is a *feature*, never an output probability.
8. An unresolved claim means abstain. No flag disables this.
9. Before adding a prompt variant, ask whether it needs its own cassette. Every new variant
   is more recorded calls and more to keep fresh.

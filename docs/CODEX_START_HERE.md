# Codex — start here

**Current checkpoint (2026-09-21): X0–X7 complete.** Start with the Sprint 3
section of `CODEX_HANDOFF.md`. Search is now request-scoped and mode-aware, and
the API/frontend checks pass offline. X8 is deferred pending a safe template
binding contract; X9 and X10 remain Sprint 4/5 work. Twenty-two live API attempts
were recorded in Sprint 1; Sprint 3 spent nothing. The old setup notes below are
historical, not the current task order or recording procedure. Deliberate live
recording uses `tooling/record_llm.py` and its persistent ceiling; normal tests
always replay and never fall back to the network.

## Historical Sprint 0x setup

Sprint 0 is done. The seam you build against exists, is typed, and is under test.
You are unblocked; nothing you need is waiting on Claude.

---

## What is already there

```
revamp/
├── packages/ici_core/src/ici_core/
│   ├── ports.py              ← YOUR CONTRACT. 15 Protocols. Frozen.
│   ├── domain/               ← the vocabulary (Evidence, ContextPack, GroundingReport, …)
│   └── usecases/
│       └── answer_question.py  ← where compose() and verify() get called
├── packages/ici_llm/src/ici_llm/   ← provider, cassettes, grounding, runtime, audit
├── tests/conftest.py         ← FakeLLM and FakeGrounding show the expected shapes
├── tests/cassettes/README.md ← why this is the most important thing you build
└── Makefile                  ← make check / test / contract / live
```

Run it:

```bash
cd revamp
uv sync --all-packages --dev     # see the note on UV_PROJECT_ENVIRONMENT in the Makefile
make check                        # ruff + mypy + import-linter
make test                         # offline by default; see handoff for latest results
```

---

## The two Protocols you implement

From `packages/ici_core/src/ici_core/ports.py` — read the real file, this is a summary:

```python
class LLMProvider(Protocol):
    def compose(self, instruction: str, pack: ContextPack, *,
                model: str | None = None, max_tokens: int = 512) -> str: ...
    def structured(self, instruction: str, pack: ContextPack,
                   schema: Mapping[str, Any], *, model: str | None = None) -> Mapping[str, Any]: ...
    def embed(self, texts: Sequence[str]) -> Sequence[Sequence[float]]: ...

class GroundingVerifier(Protocol):
    def verify(self, answer: str, pack: ContextPack) -> GroundingReport: ...
```

`ContextPack` is immutable and has `.ids` (a `frozenset[EvidenceId]`) and
`.get(id)`. That is what a claim resolves against. `GroundingReport` refuses to be
self-contradictory at construction — an `UNRESOLVED_CLAIMS` verdict must name the
claims, and a `FULLY_GROUNDED` one may not list any.

---

## Your tasks, in order

Full detail in `docs/CODEX_TASKS.md`. The order that matters:

1. **X2 — cassettes first.** Everything else is cheaper once this exists, and
   until it exists every test run risks a live call. `tests/cassettes/README.md`
   states the contract: replay never touches the network, and a cache miss *fails*
   rather than falling back to the API.
2. **X0 — `LLMProvider` + model routing.** Port `CE-RISE-Demo/backend/api/llm_compat.py`
   verbatim. Those 49 lines are correct and hard-won; do not re-derive them.
3. **X1 — `GroundingVerifier`.** The highest-value thing you build. See below.
4. X3–X6 in Sprint 1, alongside Claude porting the Normal-mode adapters.

---

## Why X1 matters, and exactly what it has to do

The COMPASS paper says evidence-before-generation is "a design discipline enforced
through prompting and audited through the surfaced citations, not a formal
guarantee that parametric knowledge cannot leak."

You cannot close that gap completely — no black-box method can. You *can* close the
audit side: decompose the composed answer into atomic claims, resolve each against
`pack.ids`, and report honestly. If anything fails to resolve, the use case
abstains and tells the user which claim failed.

This is already wired. `AnswerQuestion` calls `verify()` between composition and the
confidence step, and abstains on `verdict is UNRESOLVED_CLAIMS`. The envelope
refuses to be constructed with an unresolved claim, so there is no way around it
even by mistake. What is missing is a real implementation behind the Protocol.

Decomposition is where a model earns its place — use `structured()` against a
claim-list schema, and put the prompt id and hash in the trace so the decomposition
itself is reproducible.

---

## Rules that are not negotiable

1. Nothing outside `ici_llm` learns which model is in use. Model-specific behaviour
   lives in `compat.py` and nowhere else.
2. Never return a truncated completion as if it were whole. `finish_reason="length"`
   raises `Truncated`. A half-answer that looks complete is worse than an error.
3. A model refusal is an abstention with a reason, not a 500.
4. No prompt text in Python source — `prompts/*.md` with YAML front-matter, hashed
   into the trace.
5. No live call in CI, in a hook, or in the default test run.
6. A model's self-reported confidence is a *signal in the vector*, never an output
   probability. The calibrator owns the mapping to a probability.
7. An unresolved claim means abstain. There is no flag that disables this.

---

## Recording cassettes — the one time money is spent

Once, in Sprint 1, deliberately:

```bash
export OPENAI_API_KEY=...
export LLM_CASSETTE_MODE=record
uv run pytest tests/unit/llm tests/golden -q
```

`gpt-4o-mini`, roughly 40 calls, a few dollars. Plus one `gpt-5` call, because its
compatibility rules genuinely differ and that is worth the single call.

Then set `LLM_CASSETTE_MODE=replay` (the default) and commit the cassettes. After
that nobody spends anything to run tests.

---

## Staying out of each other's way

You own `packages/ici_llm/**`, `tests/unit/llm/**`, `tests/grounding/**`,
`tests/cassettes/**`, `tests/live/**`, and the prompt files. Claude owns everything
else. Authorized S0x shared fixes are listed in `CODEX_HANDOFF.md`.
If you need a change outside your tree,
open an issue naming the port and the reason rather than editing across the seam —
`ports.py` is frozen precisely so we can both work without coordinating.

# ADR 0009 — Request-scoped LLM audit and explicit prose grounding

Status: accepted for Sprint 0x, 2026-09-19. The user authorized necessary integration fixes.

## Context

The frozen LLM ports return strings/mappings and have no trace argument. Model
selection and detailed generation audit still need to reach each response without
mutating the resident per-mode bundles. The envelope also admitted unchecked prose
through `NOT_APPLICABLE`, and a report could say fully grounded with fewer resolved
claims than its total.

## Decision

- Keep every existing port signature unchanged. `LLMRuntime.request(model=...)`
  creates a fresh provider, verifier, budget and audit log. `bind(bundle)` returns
  a replaced immutable bundle; `finish(envelope)` merges audit into the trace.
  `LLMRuntime.answer_question(...)` performs both operations for Search.
- The core catches the new model-independent `GenerationError` and returns an
  explained abstention. Provider-specific refusal, truncation, invalid output,
  availability and rate-limit errors inherit it. Cassette errors do not: a missing
  or corrupt fixture must fail a test, never be mistaken for ordinary abstention.
- Prose answers require a nonempty, fully resolved grounding report. Only
  deterministic numeric-only answers may use `NOT_APPLICABLE`. Claim counts must
  agree with the verdict and unresolved list.
- A verifier checks existing citation ids, exact evidence quotes, answer coverage,
  and numeric support in addition to a model's entailment judgment. This is not
  a proof of semantic truth: model judgments and claim decomposition can be wrong.
- No prompt or provider config is read from environment in `ici_llm`; the API
  composition root supplies settings. Prompts are versioned Markdown files and
  included in built wheels.

## Consequences

Feature routes should use the runtime wrapper or the explicit
request/bind/finish sequence. Direct calls to the ports still work but do not
automatically enrich the envelope's trace. Later guard/composition work can reuse
the request audit without changing core signatures. Current numeric checking is
conservative: arithmetic/unit-conversion claims need explicit derived evidence
in the pack, otherwise they may abstain.

`CostAccount.usd` is estimated new spend, zero for replay. Historical token usage,
estimated original cost, prompt/model identity and replay status remain in LLM
trace steps. Unknown pricing/usage is labelled unavailable in those steps; it is
not a certified billing total. Dollar ceilings and retry scheduling remain X9.

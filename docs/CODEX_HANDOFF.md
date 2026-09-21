# Codex → Claude: Sprint 3.1 takeover completed

Updated 2026-09-21 after taking over Claude's latest commit `e28278f`. **This section
supersedes the historical Sprint 3/1 notes below.** Claude had already added the
repair/synthesis routes and UI and implemented the four missing use cases. They
were not still absent; the remaining task was to make the real route path work and
record it. The initial tree was clean. No push, release or tag was performed.

## What was completed

- Fixed the recording/test seed mismatch and the underlying evidence gap: prose
  fragments cannot satisfy the composer's exact-JSON-pointer grounding contract.
  Both modes now load complete operator-provisioned JSON records from
  `RECORD_EVIDENCE_DIR` (default `data/records`) and gather only matching products.
- Added a clearly labeled synthetic battery reference and matching UI example.
  This is not fabricated real-product compliance data. The original Generic BEV
  seed still cannot be synthesized without its own structured sources. Do not
  relax grounding to make that example succeed.
- Repair permits training-only suggestions when evidence is empty, as the user
  requested. Scores are capped at 0.30, uncalibrated, unverified and review-only.
  They never enter grounded fills or the repaired preview. Turning suggestions
  off with no sources makes no model call.
- Synthesis rejects an incomplete seed without same-product structured evidence
  before spending, preserves all caller-supplied seed facts, and returns every
  field's supporting evidence ID/reference/pointer. It never adds training guesses.
- Record routes return model, prompt hashes, cost and request-local trace steps.
  Reusing a correlation ID no longer mixes users' traces. Provider refusal,
  truncation, invalid output and grounding failures produce typed 422s, not 500s.
- Validate and repair now agree on date/URI format checks and material-share
  totals. Non-finite JSON numbers are handled without a model call or server error.
- Both editors invalidate old results when inputs change and ignore late replies
  for older input. The UI exposes repaired JSON, synthesis provenance and audit.
- Updated Vite to 6.4.3 and React Router DOM to 7.18.4 after the install reported
  four dependency advisories. Node **20+** is now explicit. `npm audit` reports
  zero vulnerabilities; the build and all browser smoke tests pass.

The OpenAI documentation skill informed the API failure checks: JSON mode is not
schema validation, so all schema/grounding checks and refusal/truncation handling
remain. Existing model choices and prompts were preserved. Reference:
https://developers.openai.com/api/docs/guides/structured-outputs
Dependency references: https://github.com/vitejs/vite/security/advisories/GHSA-fx2h-pf6j-xcff
and https://reactrouter.com/7.18.4/upgrading/v6 .

## Recording and verification

`make record` added two real `gpt-4o-mini` responses, one per new route case, with
no retries. All 12 pre-existing golden cases are semantically unchanged. Repair
returned **3 grounded fills** and synthesis **11 supported leaf fields**. The
five parameterized HTTP happy-path tests are now mandatory, never skipped.

- Ledger: **23 → 25 cumulative attempts** (+2); cumulative cost reservation
  **$0.11865650** of the $1 / 40-call ceiling. The new calls reserve $0.00972645;
  their usage-based estimate is **$0.00123135**, not a billing guarantee.
- Full offline suite: **557 passed**, no skipped route tests; package statement
  coverage **90%**. Existing Starlette/anyio deprecation warning remains.
- `make check`: ruff/format, mypy (61 files), 2/2 layering contracts clean.
- Frontend TypeScript/production build and **35 browser smoke tests** pass.
- **27 cassette-marked tests** pass offline. Recorder extension tests preserve
  retired goldens and historical manifest notes and reject changed old outputs.
- `.env` remains ignored and untracked; no credential was included in cassettes.

The default replay directory is now `tests/cassettes/recorded`, matching the
recorder, the UI demo and the HTTP tests. Normal test runs block network access.
The recorder explicitly uses the demo record directory, not a private override.
The pre-existing ledger included one failed `Unavailable` attempt; 25 cumulative
attempts means 24 recorded responses and that one failure, not 25 successes.

Frontend dependencies are outside the synced folder under `/tmp/ici-record-web.*`,
linked by `apps/web/node_modules`. Reinstall if temporary files are cleaned up.
Browser checks used the already-installed Chrome via `ICI_CHROMIUM`.

## Next work — not silently claimed complete

Sprint 3.1 integration/recording is complete. **X8 remains deferred** pending a
parameterized, read-only query-template contract. **X9/Sprint 4** production
retry/backoff and budget polish and **X10/Sprint 5** deliberate release live smoke
are subsequent tasks. Full legacy parity, release/security/license gates, clean
clone, Pages, mirror and Zenodo publication still require their own verification.
No further credential or Claude action is needed to run the completed demo offline.

---

## Historical Sprint 3 handoff (superseded)

Updated 2026-09-21 against Claude commit `c1ee0b2`. The working tree was clean
before this work; Claude's commit is one ahead of `origin/main`. These changes
are local and uncommitted; no push, release tag or external issue was created.

## Current status — read this before the historical Sprint 1 notes

**Claude's delivered work.** Normal adapters and API feature routes, eighteen
vendored model modules, the PEFDPP graph/LCA and sixteen fixed competency
questions, additive CE-RISE substrate composition, and the six-window frontend
with per-response mode badges. I reproduced the baseline: 477 offline tests.

**Codex X7 is complete.** A single versioned `compose_ce_rise.md` variant says
mounted substrates are authoritative, unavailable facts require abstention, and
model-training suggestions cannot appear as grounded answer claims. The mode is
configuration on each request provider, not a change to either frozen port.
`LLMRuntime.answer_question()` derives it from the resolved bundle; explicit
sessions use `runtime.request(model=x_model, mode=bundle.mode)`.

Normal composition/structured/repair prompts and their real cassettes remain
unchanged. Structured grounding is shared between modes. A new **synthetic**
CE-RISE fixture tests versioned replay, not live model quality. Grounding still
combines model-assisted entailment with deterministic citation/quote/coverage
checks; this is not a proof that a model can never misjudge entailment. X7 does
not implement natural-language graph retrieval.

### Integration defects fixed under the user's authorization

- Search previously called the startup bundle's raw provider directly: guards
  were bypassed, the audit was never returned, and its eight-call budget was
  consumed across users. `get_llm_request` now creates fresh model/mode/audit/budget
  state per request, binds guards and grounding, and merges the audit before
  serialization. Parallel-request tests cover twelve requests across both modes.
- `X-Model` now reaches both composition and decomposition. The actual model
  is in the trace and `X-Model-Used` (absent when nothing was called).
- Provider construction now honors Settings credentials, default/allowed models,
  replay/record/live, and the API rejects model assistance when `llm_disabled`.
  Invalid cassette modes fail configuration validation instead of reaching startup.
  No environment settings or credentials were changed, and no live calls were made.
- Missing/corrupt recordings return explained 422s without a network fallback.
  Their body mode agrees with the middleware header. Twelve successive misses no
  longer exhaust a process-wide budget. Corruption details do not expose paths.
- Blank questions, invalid/non-finite thresholds, and negative/excessive retrieval
  counts fail at the HTTP boundary. The configured default threshold is honored;
  an explicit zero remains valid.
- The API now exposes prompt hashes, model, cost, step durations and unresolved
  claims. The frontend shows the audit and actual abstention reason, not a blanket
  claim that every abstention happened below the confidence threshold.
- Frontend grounding types match the API. Memory/derived evidence can have no
  retrieval score; it displays as `unscored` instead of crashing on `null.toFixed`.
  Failed Compare requests no longer clear the session's mode badge.
- Playwright binds Vite to IPv4 explicitly (macOS otherwise bound only `::1`,
  while its health check used `127.0.0.1`). `make demo` now uses port 8000, matching
  the frontend proxy and its documentation.
- Root packaging metadata now says EUPL-1.2, matching the existing LICENSE and
  ADR 0010 decision. This corrects metadata, not a new licensing decision.

Shared files touched: API bundles/deps/settings/search/error handlers, frontend
audit/types/client/Search and smoke configuration, Makefile and root metadata.
No core port signature, substrate engine or reference response was changed.

### Verified here

- `make check`: ruff, format, mypy (58 files), both layering contracts clean.
- `pytest --no-network --cov=ici_llm`: **503 passed**, **94%** LLM statement coverage.
  One pre-existing Starlette/anyio deprecation warning remains.
- `pytest -m cassette --no-network`: **22 passed**; real recordings unchanged.
- Frontend TypeScript/production build and **25 browser smoke tests** pass locally
  across both modes, including null-score evidence and grounded-answer audit rendering.
- LLM wheel build includes the new prompt; replay remains the default.

Frontend dependencies are installed outside the synced repo under `/tmp/ici-s3-web.*`
and linked from `apps/web/node_modules`. The smoke run used the existing Chrome
binary with `ICI_CHROMIUM`, without downloading a browser. Temporary dependencies
may need reinstalling after machine cleanup; nothing from node_modules is tracked.

### What still needs Claude / the next sprint

1. **Repair/synthesis app integration is still absent.** `/api/validate` checks
   conformance only; the finished `LLMRequest.records` repair/synthesis services
   have no HTTP/UI entry points. Therefore the user-requested lower-confidence
   model-training suggestions are implemented and tested, but not visible in the
   workbench yet. Expose them separately for explicit review, never auto-apply them
   or label them grounded. The historical wiring notes below still apply here.
2. Four core use cases still raise `NotImplementedError("Sprint 1")`:
   `ValidateRecord`, `SynthesizeRecord`, `AssessImpact`, `ExplainAnswer`. Existing
   deterministic routes bypass them; working route tests do not complete these
   architecture tasks. Avoid claiming full old-demo parity on the current gates.
3. **X8 deferred under its cut line.** The sixteen fixed CQ queries exist, but no
   registered parameterized template/binding library exists. Agree a read-only,
   subject-scoped template contract before model-based query selection. No
   free-form SPARQL generation was added.
4. **X9/S4 and X10/S5 remain:** production retry/backoff and budget policy, then
   explicit release live smoke. The CE-RISE prompt variant has offline coverage,
   not a new real-model recording. Cumulative recording spend stays at 22 attempts.
5. Release checks (full legacy parity, secret/license audit, clean clone, Pages,
   tag/mirror/Zenodo) are not certified by this sprint. No release tag was made.

---

## Historical Sprint 1 handoff

Updated 2026-09-20. Codex X0–X6 are implemented and verified at the LLM boundary.
Frozen `LLMProvider` and `GroundingVerifier` signatures are unchanged. This does
not mean the complete application Sprint 1 gate is done: feature routes and
Normal adapter wiring are still yours. No commit, push or external issue created.

## User amendment: training-based suggestions

The user explicitly requested values from the LLM's training at lower confidence.
`RepairResult` now separates:

- `fills`: grounded, schema-valid repairs with `ValueSupport` (evidence id, ref,
  same-field JSON Pointer), incorporated into the returned preview.
- `suggestions`: `source="model_training"`, `status="unverified"`,
  `requires_review=True`, confidence capped at **0.3**. Never applied to the
  preview or treated as answer evidence. Confidence is not a calibrated probability.
- `cannot_be_grounded`: remaining violations, even when an unverified suggestion
  exists. `rejected` lists ineligible/unsupported proposed fills.

Expose suggestions in a separate review area, not as validated data. An explicit
user acceptance workflow should record its provenance and must not silently label
a guess as externally verified evidence. Suggestions may be empty. Administrative
ids/dates/schema-version guesses and schema-invalid values are suppressed.
See ADR 0011 for the amendment and intentional legacy differences.

## Wiring the adapter

Build an `OpenAIProvider` from Settings and wrap it in `CassetteProvider` unless
the deployment explicitly uses live mode; construct one shared `LLMRuntime`.
No adapter reads environment variables. Honor `llm_disabled` in your API root.

```python
from ici_llm import AnswerHint, CassetteProvider, LLMRuntime, ModelRouter, OpenAIProvider

source = OpenAIProvider(
    api_key=settings.openai_api_key,
    router=ModelRouter(settings.llm_model_default, settings.allowed_models),
)
provider = (
    source
    if settings.llm_cassette_mode == "live"
    else CassetteProvider(
        settings.llm_cassette_dir,
        mode=settings.llm_cassette_mode,
        provider=source,
    )
)
runtime = LLMRuntime(provider)

# Optional explicit extraction from your trusted retriever, not arbitrary metadata.
envelope = runtime.answer_question(
    bundle,
    query,
    model=x_model,
    point=point,
    hint=AnswerHint(extracted_text, extracted_kind),
)

# Per Validate/Repair or Synthesize request:
request = runtime.request(model=x_model)
repairs = request.records.repair(record_payload, context_pack)
# To disable training suggestions: suggest_from_training=False.
synthesis = request.records.synthesize(seed, context_pack)
# Merge request.audit into the endpoint's trace. For core envelopes:
# envelope = request.finish(envelope)
```

Every request has independent audit/budget/model state. Do not share an
`LLMRequest` between users. `request.bind(bundle)` installs guarded composition
and grounding; the core still verifies fallback candidates before answering.
`GroundedComposer` alone produces a candidate, not a verified final answer.

The record assistance DTOs are deliberately separate from
`ReliabilityEnvelope.answer`. Serialize their fields in the feature response;
do not convert unverified suggestions into a supposedly grounded prose answer.
Core ValidateRecord/SynthesizeRecord orchestration and their feature DTO/routes
remain to be connected by the application owner. Convert `SynthesisResult.record`
to `DPPRecord` at that boundary if required; its support list must be retained.
Map `RecordGenerationError.issues` to an explained validation result, not a 500.

## Record evidence and schema behavior

For automatically applied fills, evidence text must be a JSON record for the same
product (matching id and supplied brand/model; otherwise matching brand+model).
The value must match the same JSON Pointer exactly, including its JSON type.
Free-form text context is not enough to auto-apply measurements or compliance.
This is intentionally conservative; do not feed unrelated category templates as
verified product evidence. User-supplied seed fields may support synthesis.

The demo EU DPP schema is bundled under `ici_llm/schema_data` in wheels.
Nested objects/arrays, enums, bounds and formats are validated, plus material
shares totaling 95–105%. Synthesis has one retry containing the violations, then
a typed error. No numeric clamping, made-up defaults or silent schema pass.
This is the legacy **demo schema**, not regulatory certification.

## Embedding integration

`load_embeddings()` defaults to cached local MiniLM (384 dimensions), with no
implicit downloads. Install the optional `ici-llm[local]` dependency in deployments
using that backend and pre-provision weights. Missing weights/dependencies fail
explicitly; no random-vector fallback.

```python
from pathlib import Path
from ici_llm import CachedEmbeddings, load_embeddings

embeddings = CachedEmbeddings(
    load_embeddings(index_dimensions=384),
    Path("state/minilm-vectors.sqlite"),
    index_dimensions=384,
    batch_size=32,
)
bound = request.bind(bundle, embeddings=embeddings)
# Close the shared cache on application shutdown.
```

OpenAI is explicit: `load_embeddings(backend="openai", provider=request.provider,
index_dimensions=1536)`. Bind a separate cache file per backend. Persistent
metadata rejects mismatched model/revision/dimensions before a query. Content-hash
caching deduplicates/batches inputs and stores vectors, not text. MiniLM's identity
contains the resolved cached weight commit. Thread access is serialized; separate
processes may duplicate computation but cannot corrupt the cache.

For OpenAI, avoid sharing a request-audited provider across users: use the current
request provider or an application-owned indexing job with its own budget/audit.
Embedding events no longer overwrite the chosen composition model in the trace.

## Shared fixes and parity notes

- `AnswerQuestion` now adds traced symbolic conclusions to the context pack
  before the no-evidence check. Derived-only evidence can answer; conclusions
  without a matching rule trace cannot. Generated evidence IDs avoid retrieval IDs.
- Earlier S0 fixes remain: typed generation failures abstain; operating points are
  retained; inconsistent grounding reports and ungrounded prose envelopes reject.
- Guards have legacy pure-function parity tests. Deliberate corrections: cited
  fallback hints required, whole-value numeric checks, no hard-coded 70% recycling,
  and citation IDs excluded from component-name matching.
- Refusals never fall through to extraction. Missing/corrupt cassettes fail loudly,
  rather than looking like ordinary abstentions or contacting the API.
- Non-finite JSON exponent overflow is rejected. JSON Schema format dependencies
  are explicit; otherwise date-time checking can silently be skipped.
- Six versioned file prompts and the bundled schema load from the wheel.
  Prompt hashes, guards, tokens, latency and estimated costs remain audited.

The new `tests/golden/normal/{search,validate,synthesize}` suite covers reviewed
LLM-boundary results. It is NOT a claim of full legacy HTTP/retrieval parity.
Your `tests/reference` captures and `tooling/capture_reference.py` were preserved.

## Recording, verification and remaining work

22 deliberate OpenAI attempts total: 20 GPT-4o-mini, one GPT-5, one embeddings
batch. Standard-token-rate estimate **$0.00479**, not a billing guarantee;
conservative cumulative reservation **$0.103914**, below the $1 / 40-attempt cap.
Eight superseded responses are retained with the original 14 current request
responses. See `tests/cassettes/recorded/{manifest,ledger,expected}.json`.
No other files/credentials were uploaded; inputs were synthetic/public demo facts.
Credentials and unused opaque response tokens are redacted.

The final gate: **286 tests passed offline**, LLM statement coverage **94%**,
ruff/type/layer checks pass; six prompts/schema/py.typed load from a built wheel.
The cassette-only gate passes **22 tests**, and strict mypy passes core plus LLM.
A genuine local MiniLM smoke used cached commit
`1110a243fdf4706b3f48f1d95db1a4f5529b4d41`: 384-dimensional normalized vectors,
no download. The OpenAI embedding batch and GPT-5 structured call replay offline.

The OpenAI documentation skill informed the compatibility/embedding boundary:
[embedding guide](https://developers.openai.com/api/docs/guides/embeddings) and
[structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs).
Local loading follows the official Sentence Transformers constructor/encode API.

```bash
cd revamp
# uv is at /tmp/ici-s0x-tools.q2m5hA/bin/uv in this session.
export PATH=/tmp/ici-s0x-tools.q2m5hA/bin:$PATH
make check
uv run pytest --no-network
uv run pytest -m cassette --no-network
```

An isolated `revamp/.venv` now contains the workspace; the pre-existing parent
`.venv` was not modified. The optional ML dependency is not part of default sync.

Outstanding integration: API mode bundles still return None and feature routers
are placeholders. Wire the DTOs, trusted hints, model headers and request audit.
X7/X8/X9/X10 remain future-sprint work (mode-aware prompts/query selection,
production backoff/dollar ceilings, release live smoke); the recording ceiling
does not replace production request budgeting.

Release coordination note: README/ADR 0010 identify EUPL-1.2 while root
`pyproject.toml` still says MIT. Reconcile packaging metadata in your licensing
work before release; I did not silently make a licensing choice.

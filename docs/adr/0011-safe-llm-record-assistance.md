# ADR 0011 — Separate grounded repairs from unverified suggestions

Status: accepted for Codex Sprint 1, 2026-09-20.

The user explicitly amended the evidence-only repair plan: values drawn from the
LLM's training should also be proposed, with lower confidence. The amendment does
not require silently applying guesses or weakening the answer grounding invariant.

`RecordComposer.repair()` therefore returns two distinct collections:

- `fills`: exact typed values at the same JSON Pointer in supplied, same-product
  structured evidence, carrying an evidence id, resolvable ref and source pointer.
  Only eligible schema violations are repaired; valid fields are not overwritten.
- `suggestions`: model-training candidates, `status=unverified`,
  `requires_review=true`, confidence capped at 0.3. Confidence is a model feature,
  not a calibrated probability. These do not change `record`, clear its unresolved
  violations, become provenance, or feed answer grounding. They may be empty.

Training suggestions are enabled by default and can be disabled with
`suggest_from_training=False`. Invalid-shaped candidates and invented administrative
ids/dates/schema versions are suppressed. UI acceptance must be an explicit,
auditable user action; it must not silently promote a suggestion to validated evidence.
The separate structured-suggestions system prompt is selected only by the trusted
repair schema's `x-ici-unverified-suggestions` annotation. Ordinary structured
generation, synthesis and answer composition remain evidence-only.

Synthesis validates the complete demo EU DPP JSON Schema, including formats and
nested arrays, plus the legacy material-share total bound. Every returned leaf
must resolve to the seed or same-product structured evidence. Failure receives
one retry with violation paths, then `RecordGenerationError`, not template defaults.
The bundled schema is an unchanged CE-RISE demo schema, not regulatory certification.
Text-only context is not sufficient for an automatically applied record fill.

Intentional differences from legacy behavior:

- No automatically inserted `[needs review]`, fabricated material percentages,
  category compliance assertions, numeric clamping, or material normalization.
- Fallback hints must have auditable citations and still pass final grounding.
- Recycling checks use the hint's actual number instead of hard-coded `70`.
- Numeric hint checks compare complete values, not substrings (`5` versus `55`).
- Citation ids are not counted as product/component identifiers.
- Refusals abstain; extraction never bypasses a refusal or the grounding verifier.

Real-response testing exposed ambiguous decomposition coverage instructions. The
grounding prompt now distinguishes claim coverage from semantic support explicitly.
The mechanical gates were retained, not relaxed to make recorded outputs pass.

Golden tests freeze this reviewed LLM boundary, not a claim of byte-identical
legacy HTTP responses. Full endpoint parity belongs to the application port.

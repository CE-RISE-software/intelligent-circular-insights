# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added — Sprint 0, foundation
- Hexagonal architecture: 15 `typing.Protocol` ports in `ici_core`, which imports
  nothing from the project (enforced by `import-linter` in CI)
- `ReliabilityEnvelope` with three invariants enforced at construction: answering
  implies non-empty provenance, implies no unresolved claims, implies calibrated
  confidence at or above the operating point that is returned with the response
- Per-request backend mode resolution via `X-Backend-Mode`, echoed back as
  `X-Backend-Mode-Used`

### Added — Sprint 1, Normal mode
- `ici_symbolic`: OWL 2 RL closure and obligation rules over the DPP ontology,
  with per-rule attribution the previous implementation could not provide
- `ici_evidence`: BM25-style passage retrieval, and a product-scoped append-only
  fact memory with supersession and correction history
- `ici_substrates`: the deterministic carbon engine, the 17-model CE-RISE
  catalogue, EU DPP schema conformance with typed and located violations
- `ici_reliability`: named confidence signals, isotonic and temperature
  calibrators, the selective decision
- `ici_policy`: the routing policy, with bandit and offline-RL seats reserved
- `ici_datatrust`: the bias-aware seat, null-implemented
- `ici_llm`: audited LLM composition, grounding verification, record repair and
  synthesis, embeddings, and cassette replay so the suite needs no API key
- API: search, carbon, validate, CE-RISE models, settings, health

### Fixed
- Memory recall was scoped by session, so a query about one product could return
  facts recorded about another — silent, and the answer looked correct
- Retrieval tokenisation kept trailing sentence punctuation, so an identifier at
  the end of a sentence (`EN_62133-2.`) never matched a query for it
- The symbolic layer held a module-level reasoner keyed on an environment
  variable, which made two domains in one process impossible

### Notes
- Licensed EUPL-1.2. Vendored CE-RISE data models are CC-BY-NC-4.0 and live in a
  segregated `schemas/ce-rise/` subtree (ADR 0010)
- `CarbonCalculationService.calculate(scenario=...)` has no effect. Carried over
  unchanged and recorded rather than silently fixed during a port

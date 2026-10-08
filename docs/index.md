# Intelligent Circular Insights

Evidence-backed querying, validation, repair and generation of Digital Product
Passport (DPP) records. Answers cite their supporting evidence or the workbench
abstains; generated records are checked against the applied validation profile and
return field-level support.

Two backend profiles can be selected per request:

- **Normal** — flat product profiles, JSON-Schema validation and hybrid lexical
  retrieval.
- **CE-RISE** — CE-RISE data models and the PEFDPP knowledge graph for
  evidence-backed questions and vocabulary/type checks against generated JSON Schemas.

Both use the same response structure. Repair distinguishes evidence-backed changes
from unverified suggestions for human review.

## Where to start

[The architecture](ARCHITECTURE.md) has the diagrams, the ports, and — in sections 9
and 10 — an explicit split between what this rewrite fixes and what it only leaves a
seam for. The [decision records](adr/0001-hexagonal-architecture.md) say why each
choice was made, including the ones later reconsidered.
[Verification and remaining work](VERIFICATION_2026-09-22.md) records the latest checks.

## Licensing

Code is **EUPL-1.2**. Vendored CE-RISE data models are **CC-BY-NC-4.0** and live in a
segregated `schemas/ce-rise/` subtree with their own licence and notice, because
non-commercial terms and EUPL's permission of commercial use cannot share one
blanket statement. See [ADR 0010](adr/0010-licensing.md).

---

Funded by the European Union under Grant Agreement No. 101092281 — CE-RISE.
Views and opinions expressed are those of the authors only and do not necessarily
reflect those of the European Union or the granting authority (HADEA).

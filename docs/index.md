# Intelligent Circular Insights

Reliability-first question answering over Digital Product Passports: every output is
an evidence-grounded answer with provenance, or an explicit abstention.

One workbench, two interchangeable backends, switchable per request.

- **Normal** — flat product profiles, published emission factors, JSON-Schema
  validation, hybrid lexical retrieval. Fast, broad, shallow.
- **CE-RISE** — the consortium data models and the WP3 PEFDPP ontology, with SHACL
  conformance and a life cycle assessment solved off the RDF graph. Slower, narrower,
  regulator-grade.

Both return the same envelope, so the interface renders one component tree and an
auditor reads one shape.

## Where to start

[The plan](PLAN.md) says why this exists and what it replaces.
[The architecture](ARCHITECTURE.md) has the diagrams, the ports, and — in sections 9
and 10 — an explicit split between what this rewrite fixes and what it only leaves a
seam for. The [decision records](adr/0001-hexagonal-architecture.md) say why each
choice was made, including the ones later reconsidered.

## Honest limitations

The battery case study carries a complete *foreground* inventory but not the
licensed background: ecoinvent is commercial and is referenced in the graph by name
and UUID only. A documented proxy factor pack stands in, every proxy value is badged
as such in the API response and on screen, and **this is not an EF-compliant
declaration**. Point the factor pack at a licensed extract and the same engine
produces a compliant result with no code change.

## Licensing

Code is **EUPL-1.2**. Vendored CE-RISE data models are **CC-BY-NC-4.0** and live in a
segregated `schemas/ce-rise/` subtree with their own licence and notice, because
non-commercial terms and EUPL's permission of commercial use cannot share one
blanket statement. See [ADR 0010](adr/0010-licensing.md).

---

Funded by the European Union under Grant Agreement No. 101092281 — CE-RISE.
Views and opinions expressed are those of the authors only and do not necessarily
reflect those of the European Union or the granting authority (HADEA).

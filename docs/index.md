# CE-RISE Intelligent Circular Insights Workbench

Reliability-first question answering over Digital Product Passports: every output is
an evidence-grounded answer with provenance, or an explicit abstention.

One workbench, two backend profiles, switchable per request.

- **Normal** — flat product profiles, published emission factors, JSON-Schema
  validation, hybrid lexical retrieval. Fast, broad, shallow.
- **CE-RISE** — CE-RISE data models and the PEFDPP knowledge graph, with
  vocabulary and type checks against generated JSON Schemas and a life-cycle
  calculation for the modelled product system.

Both return the same envelope, so the interface renders one component tree and an
auditor reads one shape.

## Where to start

[The architecture](ARCHITECTURE.md) describes the components, ports and planned
extensions. The [decision records](adr/0001-hexagonal-architecture.md) explain
the design choices and their revisions.
[Verification and remaining work](VERIFICATION_2026-09-22.md) records a dated check.

## Honest limitations

The battery case study carries a complete *foreground* inventory but not the
licensed background: ecoinvent is commercial and is referenced in the graph by name
and UUID only. A documented proxy factor pack stands in, every proxy value is badged
as such in the API response and on screen. **This is not an EF-compliant
declaration.** Using licensed background data would require a separate review of
data coverage, calculation methods and reporting requirements before making
any compliance claim.

## Licensing

Code is **EUPL-1.2**. Vendored CE-RISE data models are **CC-BY-NC-4.0** and live in a
segregated `schemas/ce-rise/` subtree with their own licence and notice, because
non-commercial terms and EUPL's permission of commercial use cannot share one
blanket statement. See [ADR 0010](adr/0010-licensing.md).

---

Funded by the European Union under Grant Agreement No. 101092281 — CE-RISE.
Views and opinions expressed are those of the authors only and do not necessarily
reflect those of the European Union or the granting authority (HADEA).

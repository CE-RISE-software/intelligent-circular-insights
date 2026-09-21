# Intelligent Circular Insights

Reliability-first question answering over product records: every output is an
evidence-grounded answer with provenance, or an explicit abstention.

> **Implemented through the Sprint 3.1 integration checkpoint.** The two-mode
> workbench includes guarded search, impact tools, validation, repair and synthesis.
> Try **Synthetic demo battery** in Validate or Synthesize: saved real-model responses
> work offline, with field provenance and separate review-only training suggestions.
> Frontend requires Node 20+. Release gates and later sprint work remain. Begin with
> [`docs/PLAN.md`](docs/PLAN.md); see [`docs/CODEX_HANDOFF.md`](docs/CODEX_HANDOFF.md)
> for integration and verification details.

---

## What this is

This is **COMPASS**, rebuilt so it can carry the research forward.

COMPASS answers questions about Digital Product Passports through four stages — hybrid
evidence acquisition over documents and persistent memory, targeted symbolic validation over
a DPP ontology, context-bound composition where every claim carries a provenance identifier,
and a calibrated answer-or-abstain decision. Three principles hold it together: *evidence
before generation*, *targeted validity*, *selective output*.

One workbench, two backend profiles. *Normal* is the fast path — flat product profiles, CSV
emission factors, JSON-Schema validation. *CE-RISE* mounts the 17 CE-RISE data models and the
WP3 PEFDPP graph on top of it, with SHACL conformance and a life cycle assessment solved off
the RDF. You switch in Settings, per request, and both are live in the same session.

The rewrite also fixes two things that are defects rather than research questions:

- **memory becomes product-scoped**, append-only, superseding rather than overwriting. Today
  recall is scoped by session, so a query about one product can return another product's
  facts — in a compliance tool, the worst kind of quiet failure.
- **a grounding verifier** sits between composition and the confidence step. An answer
  containing a claim that resolves to nothing in the context pack cannot reach a user.

Where the research has genuinely open questions — calibration, the policy layer, bias-aware
abstention — the architecture provides a port and stops there. Building the seam costs hours;
skipping it costs a rewrite when the next paper needs it. `ARCHITECTURE.md` §9 is explicit
about which is which.

---

## Scope

This is a **software deliverable for the CE-RISE consortium**, not the evidence package
behind a publication. It does not re-run experiments. Testing is moderate end-to-end coverage
on mid and edge cases — around 280 tests, under five minutes, and **no OpenAI key required**:
every LLM interaction is recorded once into a cassette and replayed, so neither CI nor a
developer can spend money by running the suite.

Six sprints, roughly two days of work.

---

## Documents

| | |
|---|---|
| [`docs/PLAN.md`](docs/PLAN.md) | why a rewrite, what exists, sequence, blockers, risks |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | C4 diagrams, the hexagon and 15 ports, the inference path, substrates, and §9–10: which limitations are fixed here and which only get a seam |
| [`docs/SPRINTS.md`](docs/SPRINTS.md) | six sprints, owners, exit gates, Gantt, and how the OpenAI bill stays small |
| [`docs/TESTING.md`](docs/TESTING.md) | the test shape, the edge cases that matter, cassettes, coverage floors, CI |
| [`docs/CODEX_TASKS.md`](docs/CODEX_TASKS.md) | the OpenAI-facing work — ten tasks, cassette-first |
| [`docs/RELEASE.md`](docs/RELEASE.md) | publishing to Codeberg, GitHub and Zenodo — what happens when, and what needs a human |
| [`docs/adr/`](docs/adr/) | ten decision records (plus superseded v1 records) |

---

## A note on scope

The PEFDPP ontology and its battery case study are WP3 work by Mintjes, Barilli, Mondello,
van Nielen, Hischier, Beloin-Saint-Pierre, Donati, Boero and Mogollón. Here they are **one
mountable substrate** — a good one, because a real graph with triple-level provenance makes
environmental questions checkable rather than merely retrievable. They are not the
architecture, and nothing in the core knows they exist.

The battery case study carries a complete foreground inventory but not the licensed
background; a documented proxy factor pack stands in, every proxy value is badged, and the
workbench says on every screen that this is not an EF-compliant declaration.

---

## Licence

**EUPL-1.2** — the licence the target repository already carries, matching the CE-RISE
software template.

Vendored CE-RISE data models live in a segregated `schemas/ce-rise/` subtree under their
own **CC-BY-NC-4.0**, with per-file REUSE metadata, because non-commercial terms and EUPL's
permission of commercial use cannot share one blanket statement. See
[`docs/adr/0010-licensing.md`](docs/adr/0010-licensing.md) and
[`docs/RELEASE.md`](docs/RELEASE.md).

Funded by the European Union under Grant Agreement No. 101092281 — CE-RISE.

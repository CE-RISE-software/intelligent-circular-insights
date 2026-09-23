# CE-RISE Task 4.2 Workbench

The CE-RISE Task 4.2 Workbench is a full-stack tool for exploring, validating,
repairing and synthesising Digital Product Passport (DPP) records. It combines an
evidence-grounded FastAPI backend with a React/TypeScript frontend and supports both
a general-purpose backend profile and a CE-RISE profile over the consortium's data
models and WP3 PEFDPP knowledge graph.

Every generated answer must be traceable to evidence or the workbench abstains. Model
training knowledge may be used only to propose lower-confidence, unverified repair
suggestions for human review; those suggestions are clearly separated from grounded
values and are never applied automatically.

The canonical repository is on
[Codeberg](https://codeberg.org/CE-RISE-software/intelligent-circular-insights).

---

## What the workbench provides

| Area | Current capability |
|---|---|
| Search and Answer | Hybrid retrieval, product-scoped memory, mounted substrate facts, symbolic reasoning, evidence citations, calibrated confidence and explicit abstention |
| Single Passport | Stateless parsing and question answering over a user-supplied JSON or text passport without adding it to the corpus |
| Carbon | Lifecycle calculations with contribution breakdowns, uncertainty, provenance and an explicit identifier for the calculation engine used |
| Validate | EU DPP completeness checks and CE-RISE vocabulary/type validation with typed, located violations |
| Repair | Evidence-backed field repair plus separate, lower-confidence suggestions derived from model training for human review |
| Synthesize | Strict generation of a conforming passport in which every added field must have retrievable support |
| CE-RISE Models | An 18-model catalogue, 17 generated JSON Schemas and six document-root validation profiles |
| PEF Studio | WP3 PEFDPP overview, graph-based calculation, fixed competency questions and constrained read-only SPARQL |
| Compare | Side-by-side execution of the same question through both backend profiles |

## Backend profiles

The frontend sends the selected profile on every request, and every API response states
which backend actually served it.

- **Normal** uses flat product profiles, published CSV emission factors, the EU DPP
  JSON Schema, lexical evidence retrieval and the shared reliability pipeline.
- **CE-RISE** adds the consortium data models and the WP3 PEFDPP graph. Questions can
  cite graph assertions, carbon calculations use the graph for product systems it
  models, and records written in a recognised CE-RISE vocabulary are routed to that
  model's schema.

The CE-RISE profile extends coverage without treating unlike sources as interchangeable.
For example, a graph result declared per kilowatt-hour is not substituted for a whole
product lifecycle result. The response identifies the source and calculation path so the
two cannot be confused.

## Reliability and safety

The backend applies the same reliability path in both profiles:

1. gather bounded evidence from documents, memory and mounted substrates;
2. derive relevant symbolic facts where structured data is available;
3. compose an answer using only the supplied context;
4. verify citations, quoted support, claim coverage and numeric support;
5. answer only when the configured operating threshold is met, otherwise abstain.

Additional safeguards include request-local model budgets, disabled SDK retries for
deliberate live checks, append-only product-scoped memory, provenance for generated
records, typed capability errors and secret-scanning gates.

## Repository structure

```text
apps/api/                 FastAPI backend and HTTP routes
apps/web/                 React, TypeScript and Vite frontend
packages/ici_core/        Domain model, ports and use cases
packages/ici_evidence/    Retrieval, inline documents and fact memory
packages/ici_llm/         Model providers, prompts, grounding and record assistance
packages/ici_substrates/  Schemas, carbon factors, model catalogue and PEFDPP adapters
packages/ici_symbolic/    Ontology and OWL-RL validation
schemas/                  EU DPP schema and vendored CE-RISE data models
tests/                    Unit, contract, integration, end-to-end, browser and live tests
docs/                     Architecture, testing, release notes and decision records
```

## Local setup

Prerequisites:

- Python 3.10–3.12
- [uv](https://docs.astral.sh/uv/)
- Node.js 20 or newer

Install the Python workspace and frontend dependencies:

```bash
make setup
make web
```

Start the backend in one terminal:

```bash
make demo
```

Start the frontend in another terminal:

```bash
cd apps/web
npm run dev -- --port 5173
```

Open <http://localhost:5173>. The API is served at <http://localhost:8000>.

### Model configuration

Replay mode is the default: it uses reviewed responses and never calls the model
provider. Deterministic features such as validation, retrieval, graph queries and
impact calculations work without an API key.

To deliberately use the live model:

```bash
cp .env.example .env
```

Add the API key to `.env`, set `LLM_CASSETTE_MODE=live`, and restart the backend.
Never commit `.env`, a token or a private key.

## Verification

The normal test suite is offline by construction. A cassette miss fails instead of
silently making a paid network call.

```bash
make check       # Ruff, formatting, MyPy and dependency-layer contracts
make test        # complete Python suite
make web-check   # frontend typecheck and production build
make smoke       # Playwright tests across both backend profiles
make secrets     # tracked-file credential checks
```

Real-model checks are opt-in, use synthetic/public inputs, disable SDK retries and
enforce a cumulative attempt and estimated-cost ceiling:

```bash
make live
```

See [Testing](docs/TESTING.md) for the complete test strategy and
[Architecture](docs/ARCHITECTURE.md) for the component model, ports, inference path
and backend-routing decisions.

## Scope and limitations

This is the CE-RISE Task 4.2 software workbench, not a legal certification service
or the evidence package for a scientific publication.

The WP3 battery case study includes its foreground inventory but not the licensed
background database. A documented proxy factor pack is used instead; proxy values are
labelled and must not be presented as an Environmental Footprint-compliant declaration.
The six CE-RISE root schemas validate vocabulary and types but declare no required
fields, so EU DPP completeness and CE-RISE vocabulary conformance remain separate,
explicit checks.

## Documentation

| Document | Purpose |
|---|---|
| [Architecture](docs/ARCHITECTURE.md) | Components, ports, reliability path, substrates and backend routing |
| [Testing](docs/TESTING.md) | Offline gates, model cassettes, browser coverage and live-test controls |
| [Release](docs/RELEASE.md) | Codeberg, GitHub mirror, tagging and Zenodo handoff |
| [Architecture decisions](docs/adr/) | Rationale and consequences for the major design choices |
| [Dated verification checkpoint](docs/VERIFICATION_2026-09-22.md) | Historical verification state on 22 September 2026; later commits may supersede deferred items |

## License

The workbench software is licensed under the
[European Union Public Licence v1.2 (EUPL-1.2)](LICENSE). This matches the
[CE-RISE software template](https://codeberg.org/CE-RISE-software/template-software)
and the related CE-RISE software repositories maintained by Riccardo Boero, including
the [Digital Passport Model Assessment Workbench](https://codeberg.org/CE-RISE-software/dp-assessment-workbench)
and [Digital Passport Engineering Assistant](https://codeberg.org/CE-RISE-software/dp-engineering-assistant).

The vendored CE-RISE data models and generated derivatives under
[`schemas/ce-rise/`](schemas/ce-rise/) retain their upstream
**Creative Commons Attribution-NonCommercial 4.0 International
(CC-BY-NC-4.0)** terms. They are segregated from the EUPL-licensed application code;
see the [model notice](schemas/ce-rise/NOTICE.md) and
[licensing decision](docs/adr/0010-licensing.md).

## Contributing

This repository is maintained on
[Codeberg](https://codeberg.org/CE-RISE-software/intelligent-circular-insights),
which is the canonical source of truth. The GitHub repository is a read mirror used
for release archival and Zenodo integration. Issues and pull requests should be opened
on Codeberg.

---

<a href="https://europa.eu" target="_blank" rel="noopener noreferrer">
  <img src="https://ce-rise.eu/wp-content/uploads/2023/01/EN-Funded-by-the-EU-PANTONE-e1663585234561-1-1.png" alt="Funded by the European Union" width="200"/>
</a>

Funded by the European Union under Grant Agreement No. 101092281 — CE-RISE.

Views and opinions expressed are those of the author(s) only and do not necessarily
reflect those of the European Union or the granting authority (HADEA). Neither the
European Union nor the granting authority can be held responsible for them.

© 2026 CE-RISE consortium.

Licensed under the [European Union Public Licence v1.2 (EUPL-1.2)](LICENSE).

Attribution: CE-RISE project (Grant Agreement No. 101092281) and the individual
authors and partners indicated in the repository metadata.

Maintained by A M Esfar-E-Alam and Riccardo Boero (NILU) within CE-RISE Task 4.2.

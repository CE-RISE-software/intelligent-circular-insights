# CE-RISE Intelligent Circular Insights Workbench

The CE-RISE Intelligent Circular Insights Workbench supports evidence-backed querying,
validation, repair and generation of Digital Product Passport (DPP) records. It combines
a FastAPI backend with a React/TypeScript frontend and offers general-purpose and
CE-RISE profiles for evidence access and model-aware validation.

Answers cite supporting evidence or the workbench abstains. Generated records are checked
against the applied validation profile and return support for their fields. Repair keeps
evidence-backed changes separate from unverified suggestions for human review.

The canonical repository is on
[Codeberg](https://codeberg.org/CE-RISE-software/intelligent-circular-insights).

---

## What the workbench provides

| Area | Current capability |
|---|---|
| Search and Answer | Hybrid retrieval, product-scoped memory, mounted substrate facts, symbolic reasoning, evidence citations and explicit abstention |
| Single Passport | Stateless parsing and question answering over a user-supplied JSON or text passport without adding it to the corpus |
| Validate | EU DPP completeness checks and CE-RISE vocabulary/type validation with typed, located violations |
| Repair | Evidence-backed field repair plus separate, lower-confidence suggestions derived from model training for human review |
| Generate | DPP record generation from supplied facts and retrieved evidence, with field-level support and validation before return |
| CE-RISE Models | An 18-model catalogue, 17 generated JSON Schemas and six document-root validation profiles |
| Compare | Side-by-side execution of the same question through both backend profiles |

## Backend profiles

The frontend sends the selected profile on every request, and every API response states
which backend actually served it.

- **Normal** uses flat product profiles, the EU DPP JSON Schema, lexical evidence
  retrieval and the shared reliability pipeline.
- **CE-RISE** adds the consortium data models and structured evidence. Questions can
  cite supported assertions, and records written in a recognised CE-RISE vocabulary
  are routed to that model's schema.

The CE-RISE profile extends available evidence and validation profiles without
treating unlike sources as interchangeable. Each response identifies the backend
that served it.

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

Fact memory is in-process and is not restored after a restart. Durable storage
can be added if a future deployment requires it.

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
docs/                     User guides, engineering references and decision records
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
provider. Deterministic features such as validation, retrieval and graph queries
work without an API key.

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

See [Testing](docs/TESTING.md) for the current checks and
[Architecture](docs/ARCHITECTURE.md) for the component boundaries and request paths.

## Documentation

| Document | Purpose |
|---|---|
| [Run from source](docs/run-from-source.md) | Local use and a long-running installation |
| [Work with passport records](docs/workflows.md) | Query, validation, repair and generation workflows |
| [Backends and evidence](docs/backends-and-evidence.md) | Backend choices, profiles and result support |
| [Architecture](docs/ARCHITECTURE.md) | Current components, request paths and backend resolution |
| [Testing](docs/TESTING.md) | Current checks, offline safeguards and CI scope |
| [Architecture decisions](docs/adr/) | Rationale and consequences for the major design choices |
| [Dated verification checkpoint](docs/VERIFICATION_2026-09-22.md) | Results recorded on 22 September 2026 |

## Citation

Use the [Zenodo concept DOI 10.5281/zenodo.23257806](https://doi.org/10.5281/zenodo.23257806)
to cite the workbench across all versions.
Machine-readable citation details are in [CITATION.cff](CITATION.cff).

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

Maintained by A M Esfar-E-Alam and Riccardo Boero (NILU) for CE-RISE.

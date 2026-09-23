# Vendored CE-RISE data models — separately licensed

**Everything in this directory is CC-BY-NC-4.0**, not the EUPL-1.2 that covers the
rest of this repository. The two are not interchangeable: EUPL permits commercial
use and CC-BY-NC forbids it, so one blanket statement at the repository root would
be misleading in one direction or the other.

That is why these files live in their own subtree with their own `LICENSE`, and why
no CC-BY-NC material is copied into or generated into EUPL-licensed source. The
schemas are read at runtime as data. See `docs/adr/0010-licensing.md`.

## Source

- Upstream: <https://codeberg.org/CE-RISE-models> (GitHub mirrors at
  <https://github.com/CE-RISE-models>)
- Author of record: Riccardo Boero (NILU), ORCID 0000-0002-7468-9096
- Each model also carries its own Zenodo DOI

## Attribution

CC-BY-NC requires attribution. The catalogue served at `/api/ce-rise-models/catalog`
names the upstream repository for every model and declares the licence, so a
consumer of the API sees the terms rather than having to find this file.

## Status

The 18 data-model repositories used by the catalogue are vendored in this subtree
and pinned to the commits recorded in `VENDOR.md`. Seventeen also have generated
JSON Schema artefacts under `_generated/`; only the six upstream models that declare
a document root are offered as validation profiles. The catalogue metadata remains
in `data/ce_rise_models.json` so API consumers receive the source, version and licence
for each model.

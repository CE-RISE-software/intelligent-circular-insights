# Demo schema provenance

`eu_dpp_schema.json` is an unchanged copy of
`CE-RISE-Demo/backend/schemas/eu_dpp_schema.json` from this workspace (2026-09-20).
Its own description identifies it as a CE-RISE demo, CIRPASS-2-aligned schema,
not a final regulatory schema. Passing it does not establish legal compliance.

Included as a wheel resource so synthesis validation cannot silently disappear
outside a source checkout. Format validation dependencies are installed explicitly;
remote JSON Schema references are never fetched during validation.

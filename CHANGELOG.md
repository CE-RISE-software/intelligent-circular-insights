# Changelog

## [v0.1.0] - 2026-10-09

First release: evidence-backed Digital Product Passport workflows.

- Query product records and supplied passports with cited evidence, provenance,
  and explicit abstention when support is insufficient.
- Validate records against the EU DPP profile or available CE-RISE data-model
  profiles, with located violations and the applied profile reported.
- Repair records from sourced facts while keeping unresolved fields and
  unverified suggestions separate for human review.
- Generate records from supplied facts and retrieved evidence, returning
  field-level support only after validation against the applied profile.
- Use the browser workbench and HTTP API with Normal and CE-RISE backends;
  the served backend is identified in each response.

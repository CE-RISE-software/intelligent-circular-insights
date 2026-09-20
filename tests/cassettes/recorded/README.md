# Real Sprint 1 responses

Captured deliberately on 2026-09-20 using synthetic facts and the existing public
CE-RISE broken demo records. The response payloads are real model outputs; the
synthetic facts are not measurements of actual products.

22 API attempts total: 20 GPT-4o-mini, one GPT-5, one text-embedding-3-small batch.
No SDK retries. `ledger.json` records every attempt/reservation/usage, including
eight responses superseded by reviewed grounding/repair prompt refinements.
Those older responses are retained, not silently changed into passing fixtures.
The GPT-5 response's unused opaque encrypted-content token is redacted.

`expected.json` is the reviewed adapter output for the 12 current scenarios;
`manifest.json` records provenance and cumulative caps. The golden suite makes
zero network calls and fails on a missing cassette. It does not claim legacy
HTTP/retrieval parity or formal semantic-proof guarantees.

Review notes: initial grounding responses confused coverage with support; prompt
v2 clarifies that distinction. Initial repair responses had wrong types or
invented references; the checks rejected them. Repair v3 and its separate
suggestions prompt preserve grounded fills and label model-prior candidates.
The battery case declines to suggest compliance; that remains an allowed result.

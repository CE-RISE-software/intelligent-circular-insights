# Synthetic Sprint 0x fixtures

These responses were hand-built, not captured from OpenAI. They exercise
composition and claim decomposition through the real cassette/validation path
without API spend. They are not evidence of live model quality or compatibility.

`test_committed_synthetic_fixture_replays_end_to_end` replays them against the
shared 60 kWh battery fixture. A prompt, context, model or schema change produces
a cache miss. Review the change before replacing these fixtures.

Sprint 1 added `a709...` for grounding prompt v2. The old `7aac...` grounding-v1
fixture is retained as historical; the current end-to-end test uses `687b...`
for composition and `a709...` for verification.

Actual OpenAI recordings live in the separate `../recorded/` directory. Never
relabel these hand-built fixtures as live recordings.

Sprint 3 adds `402c...` for `ici.compose.ce_rise@1`. It is a new hand-built
composition fixture, not a recaptured or relabelled OpenAI response. Normal-mode
request hashes and real Sprint 1 recordings remain unchanged; both modes reuse
the unchanged grounding fixture. CE-RISE prompt behavior is tested at the transport
and HTTP boundary offline; live model quality for this variant is not yet measured.

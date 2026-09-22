# Live tests

Marked `@pytest.mark.live`. **Run by a human, on purpose, before a release.**

Never in CI, never in a git hook, never in the default `pytest` run. Nobody should
be able to spend money by opening a pull request or saving a file.

    make live      # uses --run-live; needs OPENAI_API_KEY

`pytest -m live` alone deselects these tests. `--run-live` is rejected in CI
and with `--no-network`. Ordinary tests always block network calls and remove
the API key, even when run alongside explicitly opted-in live tests.

The HTTP smoke test now exercises Single DPP, CE-RISE search with both allowed
models, grounded repair, and synthesis. It uses synthetic/public input and a
cumulative ceiling of 12 attempts / $0.15 estimated reservation, with SDK retries
disabled. It checks live behavior, not merely whether the API accepts a request.
The actual number of calls can be lower if a guard abstains early; the test then
fails. The limit is an estimate, not a provider billing guarantee.

# Live tests

Marked `@pytest.mark.live`. **Run by a human, on purpose, before a release.**

Never in CI, never in a git hook, never in the default `pytest` run. Nobody should
be able to spend money by opening a pull request or saving a file.

    make live      # uses --run-live; needs OPENAI_API_KEY

`pytest -m live` alone deselects these tests. `--run-live` is rejected in CI
and with `--no-network`. Ordinary tests always block network calls and remove
the API key, even when run alongside explicitly opted-in live tests.

Six calls: one per window on `gpt-4o-mini`, plus one on `gpt-5`. Their job is to
tell us the cassettes have not gone stale against the live API.

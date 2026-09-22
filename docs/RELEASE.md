# Publishing and release

Codeberg is the canonical Git repository. GitHub is a read mirror used for
release archival and Zenodo integration; do not push to it separately.

The first application commits reached Codeberg `main` on 22 September 2026.
There is no release tag or DOI yet. The current verification and deferred work
are in [the status note](VERIFICATION_2026-09-22.md).

## Before a release

- The repository owner should confirm that hosting remains eligible under
  [Codeberg's Terms of Use](https://codeberg.org/Codeberg/org/src/branch/main/TermsOfUse.md).
  This project has used AI-assisted development; a successful push does not make
  a policy determination.
- Run the offline gates on a clean clone: `make setup`, `make check`, `make test`,
  `make web-check`, and `make smoke`. Test the actual deployed configuration.
- Deliberately run a small live-model smoke with its cost controls enabled.
  Offline cassettes do not establish live quality.
- Review `CITATION.cff`, `.zenodo.json`, licences, notices, and changelog. The
  CE-RISE data models are CC-BY-NC-4.0, separate from the EUPL-1.2 code.
- Confirm that the GitHub mirror and Zenodo integration are enabled. Do not assume
  a tag will archive itself until the external services have been checked.

## Tag only after approval

Fetch first and verify that the remote branch is an ancestor. Never force-push
over the CE-RISE template history or over other contributors' work.

```bash
git fetch origin
git merge-base --is-ancestor origin/main HEAD
git push origin main
git tag -a v0.1.0 -m "First release: COMPASS core and two backends"
git push origin v0.1.0
```

The first tag should mint a concept DOI. Update `CITATION.cff` only with the DOI
that Zenodo actually assigns. Do not invent one in advance.

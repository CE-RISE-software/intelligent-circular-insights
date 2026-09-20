# Publishing to Codeberg, GitHub and Zenodo

Answers two questions: **when does the upload happen**, and **what do you need to provide**.

Short version: the upload is **Sprint 5**, but three things move to **Sprint 1** because
getting them wrong is expensive to undo. Nothing here needs a credential from you to *me* —
I never hold one. The pushes are yours to run, because neither sandbox can reach Codeberg.

---

## What already exists

`CE-RISE-software/intelligent-circular-insights` was created by Riccardo from the CE-RISE
software template and is sitting there waiting, containing:

```
.forgejo/workflows/    Codeberg CI, and the docs build published to
                       ce-rise-software.codeberg.page
.github/workflows/     mirror-side: tags releases, triggers Zenodo archival
.zenodo.json           communities: ce-rise, impact · grant 101092281
CITATION.cff           still template placeholders (DOI: xxx_to_be_obtained_xxx)
CHANGELOG.md
LICENSE                EUPL-1.2
README.md              still titled "CE-RISE Software Projects Template"
docs/
```

The README states the working model plainly, and we follow it:

> Codeberg is the canonical source of truth. The GitHub repository is a read mirror used
> for release archival and Zenodo integration. Issues and pull requests should be opened
> on Codeberg.

So: **push to Codeberg only.** Never push to the GitHub mirror — it would fight the
mirroring and split history.

---

## Network reality

Measured from this session, not assumed:

| Host | Cloud container | Your machine's Claude VM |
|---|---|---|
| codeberg.org | 403 at proxy | 403 at proxy |
| github.com | 403 at proxy | reachable (`git ls-remote` works) |
| zenodo.org | 403 at proxy | unreachable |
| pypi.org | reachable | reachable |

**Consequence: I cannot push this repository anywhere.** Codeberg is blocked from both
sandboxes. Every `git push` in this document is run by you, in your own macOS terminal,
outside the Claude environment. I prepare the commits, the tags and the metadata; you run
three commands.

I can *read* GitHub from the device VM, which is how the CE-RISE model schemas get
vendored — their GitHub mirrors are reachable even though Codeberg is not.

---

## Moved into Sprint 1 — because fixing them later is worse

**1. Licence (ADR 0009).** EUPL-1.2, not MIT. This decides the SPDX header on every source
file, so it has to be right before there are hundreds of them.

**2. Repository identity.** `revamp/` currently has no `.git` of its own and sits untracked
inside the `LLMEnhance` working tree, whose origin is `github.com/aeturzo/LLMEnhance`.
Pushing from there would put this code in the wrong repository. `revamp/` becomes its own
git repository with its own remote, and `llmmain/.gitignore` gains a `revamp/` entry so the
two never entangle.

**3. Template metadata.** `CITATION.cff`, `.zenodo.json`, `CHANGELOG.md` and the README
still say "template" with placeholder DOIs. Filling them in while writing the docs is
cheap; retrofitting them at release time is the sort of thing that gets skipped.

---

## Sprint 5 — the actual release

### Step 1 · You: Codeberg access
Reply to Riccardo with your Codeberg username. He adds you to the `CE-RISE-software` team.
Then add an SSH key at `codeberg.org/user/settings/keys`, or create an access token if you
prefer HTTPS.

*This is the only thing that is genuinely blocking, and it has been outstanding since his
1 July email.*

### Step 2 · Me: prepare the repository
I do all of this in `revamp/`, and none of it touches the network:

- `git init`, `.gitignore`, conventional-commit history
- `LICENSE` (EUPL-1.2) + SPDX headers on every source file + `reuse lint` green
- `schemas/ce-rise/` with its own CC-BY-NC-4.0 `LICENSE` and a `NOTICE.md` recording each
  model's source repo, commit SHA, Zenodo DOI and author
- `CITATION.cff` and `.zenodo.json` filled in: real title, abstract, authors, keywords,
  `communities: [ce-rise, impact]`, `grants: [101092281]`, EUPL-1.2
- `CHANGELOG.md` with a real 0.1.0 entry
- README with the CE-RISE footer, EU emblem and grant text retained as the template requires
- `.forgejo/` and `.github/` workflows carried over and adapted to this project's `make`
  targets

### Step 3 · You: three commands
```bash
cd ~/Desktop/StudyUIO/Research/LLMENHANCE/llmmain/revamp
git remote add origin git@codeberg.org:CE-RISE-software/intelligent-circular-insights.git
git fetch origin && git rebase origin/main     # keep Riccardo's template commits
git push -u origin main
```

The rebase matters: the target repo already has his template history. Force-pushing over it
would erase the provenance of where this project came from.

### Step 4 · You, once: Zenodo
The GitHub↔Zenodo integration is wired into the template, but it has to be switched on for
this repository once, by a human with the account:

1. Sign in at zenodo.org with GitHub
2. Settings → GitHub → toggle `CE-RISE-software/intelligent-circular-insights` on
3. Confirm the `ce-rise` and `impact` communities accept the deposit

After that, every tag pushed to Codeberg mirrors to GitHub, creates a release, and is
archived to Zenodo with a DOI automatically. The first tag also mints the concept DOI that
`CITATION.cff` should then carry.

### Step 5 · Tag
```bash
git tag -a v0.1.0 -m "First release: COMPASS core, two backends, CE-RISE substrates"
git push origin v0.1.0
```

---

## What you never need to give me

No Codeberg password, SSH key, access token or Zenodo credential — I cannot reach those
hosts, so a credential would be useless as well as unwise. The OpenAI key stays where it
is, in `CE-RISE-Demo/.env`, used once by Codex for cassette recording.

The one thing I do want, when convenient: **a sentence from Riccardo** confirming that
CC-BY-NC on the data models is deliberate and that vendoring them in a segregated,
separately-licensed subtree is acceptable. He authored both sides, so he can settle it
faster than anyone else (ADR 0009).

# Prompt for Codex — set up Codeberg access and push

Copy one phase at a time. **Phase 1 stops at a step only you can do**: adding a public
key to Codeberg's web interface. Codex has no browser session there.

Before either phase, one thing has to be true: **you are on the `CE-RISE-software`
team on Codeberg.** Reply to Riccardo with your Codeberg username if you have not.
Nothing below works without it, and it has been outstanding since his 1 July email.

---

## Phase 1 — create the key

> You are setting up push access to a Codeberg repository for this project.
>
> The repository is at `~/Desktop/StudyUIO/Research/LLMENHANCE/llmmain/revamp`. It is a
> git repository with 12 commits on `main` and no remote configured. Do not add a
> remote yet.
>
> Do this:
>
> 1. Generate an SSH key dedicated to this project, with no passphrase, at
>    `~/.ssh/codeberg_ce_rise`:
>    `ssh-keygen -t ed25519 -C "codex@ce-rise-ici" -f ~/.ssh/codeberg_ce_rise -N ""`
>
> 2. Add a host block to `~/.ssh/config`, creating the file if needed. Append, never
>    overwrite — there may be other hosts in it:
>    ```
>    Host codeberg.org
>      HostName codeberg.org
>      User git
>      IdentityFile ~/.ssh/codeberg_ce_rise
>      IdentitiesOnly yes
>    ```
>    `IdentitiesOnly yes` matters: without it ssh offers every key it has, and a key
>    meant for one host ends up presented to others.
>
> 3. `chmod 600 ~/.ssh/codeberg_ce_rise && chmod 644 ~/.ssh/codeberg_ce_rise.pub`
>
> 4. Print the **public** key only — `cat ~/.ssh/codeberg_ce_rise.pub`. Never print,
>    copy, or commit the private key.
>
> 5. Stop there and tell me the public key. Do not add a remote and do not push.

**Then you, in a browser:** open
`https://codeberg.org/CE-RISE-software/intelligent-circular-insights/settings/keys`
and add it as a **Deploy Key** with **write access enabled**.

Use a deploy key rather than your account key. A deploy key reaches exactly one
repository; your account key reaches everything you can touch. If anything ever goes
wrong, the difference is the whole point.

Verify before moving on: `ssh -T git@codeberg.org` should greet you by name.

---

## Phase 2 — adopt the template and push

> Push this project to Codeberg for the first time. The repository is at
> `~/Desktop/StudyUIO/Research/LLMENHANCE/llmmain/revamp`, 12 commits on `main`.
>
> **Important context.** The remote repository already has two commits: Riccardo's
> CE-RISE software template. Our history was started fresh and shares no ancestor with
> it, so a plain `git rebase origin/main` conflicts on every file that exists on both
> sides. The procedure below was rehearsed against the GitHub mirror and completes with
> zero conflicts. Use it exactly.
>
> ```bash
> cd ~/Desktop/StudyUIO/Research/LLMENHANCE/llmmain/revamp
>
> git remote add origin git@codeberg.org:CE-RISE-software/intelligent-circular-insights.git
> git fetch origin
>
> git merge origin/main --allow-unrelated-histories -X ours -m "chore: adopt the CE-RISE software template
>
> Brings the consortium scaffolding underneath this project's history: the Codeberg
> Pages workflow, the GitHub release workflow that triggers Zenodo archival, and the
> mdBook structure. Where a file exists on both sides — README, CITATION.cff,
> .zenodo.json, CHANGELOG — this project's version is kept, because those were written
> for this project rather than for the template."
> ```
>
> `-X ours` resolves collisions in our favour while still bringing in every template
> file that does not collide. That is what preserves both sides.
>
> **Verify before pushing.** All of these must hold; if any fails, stop and tell me
> rather than pushing:
>
> ```bash
> git status --porcelain | grep '^UU' && echo "CONFLICTS — STOP" || echo "no conflicts"
> test -f .forgejo/workflows/pages.yml           && echo "ok: Codeberg Pages workflow"
> test -f .github/workflows/create-release.yml   && echo "ok: release workflow"
> test -f .github/workflows/ci.yml               && echo "ok: our CI kept"
> head -1 README.md | grep -q "Intelligent Circular Insights" && echo "ok: our README won"
> git log --oneline | grep -q "Initial commit"   && echo "ok: template history preserved"
> ```
>
> Then confirm the code still works — this needs no API key, every model call replays
> from a cassette:
>
> ```bash
> export UV_LINK_MODE=copy
> uv sync --all-packages --dev
> make check && make test        # expect 403 passing
> ```
>
> Then push:
>
> ```bash
> git push -u origin main
> ```
>
> **Do not:**
> - force-push, or use `--allow-unrelated-histories` with any strategy other than the
>   one above. The template commits are the provenance of where this project came from.
> - push to the GitHub remote. GitHub is a read mirror; Codeberg mirrors to it
>   automatically, and pushing to both splits the history.
> - commit anything from `.env`, or any file matching `*key*`, `*token*`, `*secret*`.
> - tag a release. That is a separate decision.
>
> When it is done, tell me the commit count on `origin/main` and whether the Codeberg
> Pages build succeeded.

---

## After the first push, once

The GitHub↔Zenodo integration is already wired into the template, but someone with the
account has to switch it on for this repository:

1. Sign in at zenodo.org with GitHub
2. **Settings → GitHub** → enable `CE-RISE-software/intelligent-circular-insights`
3. Confirm the `ce-rise` and `impact` communities accept the deposit

Then every tag pushed to Codeberg mirrors to GitHub, cuts a release, and is archived
with a DOI. The first tag mints the concept DOI, which then belongs in `CITATION.cff` —
it has none right now, deliberately, because inventing one would be worse than leaving
it out.

---

## If something goes wrong

**`Permission denied (publickey)`** — the deploy key is not on the repository, or write
access was not ticked. Check `ssh -T git@codeberg.org`.

**`! [rejected] main -> main (fetch first)`** — someone pushed since the fetch. Run
`git fetch origin` and repeat the merge. Do not force.

**Conflicts despite the flags** — the remote has moved on since this was rehearsed.
Stop and show me `git status`; do not resolve them by guessing.

**Codeberg Pages does not publish** — the workflow needs `docs/book.toml` and
`docs/SUMMARY.md`, both of which are in our tree already. Check the Actions tab on
Codeberg for the mdBook build log.

# Giving Claude or Codex commit access

Short answer: **give Codex the credential, not me.** Codeberg is blocked from my
sandbox by organisation policy and no credential changes that. Codex runs on your
machine with your network, so it can push where I cannot.

---

## What each of us can actually reach

Measured from this session, not assumed:

| Host | My sandbox | Codex on your Mac | Your terminal |
|---|---|---|---|
| **codeberg.org** | **403 at the egress proxy** | reachable | reachable |
| github.com | reachable (`git ls-remote` works) | reachable | reachable |
| zenodo.org | blocked | reachable | reachable |

The 403 is an **organisation policy denial**, not a missing certificate or a
misconfigured client. The proxy's own documentation says not to retry those and to
report them instead, so I do.

**Codeberg is the one that matters**, because the repository's README states the
working model: Codeberg is canonical, GitHub is a read mirror for Zenodo archival,
and issues and pull requests belong on Codeberg. Pushing to the GitHub mirror would
fight the mirroring and split the history, so "I can reach GitHub" is not a useful
workaround.

---

## Option A — Codex pushes · recommended

Codex runs where your network is, so this needs nothing from Claude's settings.

**1. Get on the team.** Reply to Riccardo with your Codeberg username; he adds you
to `CE-RISE-software`. Still outstanding since his 1 July email, and nothing below
works without it.

**2. Give Codex a key.** On the machine Codex runs on:

```bash
ssh-keygen -t ed25519 -C "codex@ce-rise" -f ~/.ssh/codeberg_ce_rise
cat ~/.ssh/codeberg_ce_rise.pub          # paste at codeberg.org/user/settings/keys
```

Then scope it to Codeberg only, so a key meant for one host cannot reach another:

```
# ~/.ssh/config
Host codeberg.org
  HostName codeberg.org
  User git
  IdentityFile ~/.ssh/codeberg_ce_rise
  IdentitiesOnly yes
```

**3. Prefer a deploy key over your account key.** On the repository's
*Settings → Deploy Keys*, add the public key with write access enabled. A deploy key
reaches exactly one repository; your account key reaches everything you can touch.
If Codex ever misbehaves, the blast radius is one repo.

**4. Point the repo at it.**

```bash
cd ~/Desktop/StudyUIO/Research/LLMENHANCE/llmmain/revamp
git remote add origin git@codeberg.org:CE-RISE-software/intelligent-circular-insights.git
git fetch origin
git rebase origin/main      # keep Riccardo's template history underneath ours
git push -u origin main
```

The rebase is the part to get right. The target repository already has his template
commits; force-pushing over them erases where this project came from.

---

## Option B — you push, I prepare · zero credentials anywhere

This is what has happened so far, and it costs almost nothing.

`revamp/` is already its own git repository with **ten commits** and a clean tree.
I write the commits; you run step 4 above. No key is created, shared or stored, and
nothing needs changing in anyone's settings.

The only thing you lose is having to run one command when you want work pushed.

---

## Option C — unblock my sandbox · possible, and still not sufficient

If you own this Claude organisation you may be able to allow `codeberg.org` under
**Admin settings → Capabilities → network access**. That would remove the 403.

It would still not be enough on its own: I would also need a credential, which means
a deploy key sitting inside a sandbox you cannot inspect. I would rather you did not.
If you do want it, use a **repository-scoped deploy key**, never an account key, and
revoke it when the project ends.

---

## What you never need to give me

No Codeberg password, SSH key or access token. No Zenodo credential. I cannot reach
either host, so a credential would be useless as well as unwise.

The OpenAI key stays where it is, in `CE-RISE-Demo/.env`, used once by Codex to
record cassettes. After that the test suite runs with no key at all.

---

## Zenodo, once

The GitHub↔Zenodo integration is already wired into the template, but a human with
the account has to switch it on for this repository:

1. Sign in at zenodo.org with GitHub
2. **Settings → GitHub** → toggle `CE-RISE-software/intelligent-circular-insights` on
3. Confirm the `ce-rise` and `impact` communities accept the deposit

After that, every tag pushed to Codeberg mirrors to GitHub, cuts a release and is
archived with a DOI. The first tag mints the concept DOI, which then belongs in
`CITATION.cff` (it currently has none, deliberately — inventing one would be worse).

---

## A note on what a commit from me means

Every commit I write carries:

```
Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_...
```

You are the author; I am a co-author. On a repository that will be cited and
archived, that distinction is worth keeping visible rather than quietly dropping.

# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""No credential may be tracked by git.

The third and only load-bearing layer. `.gitignore` can be edited, and git does not
install hooks from a clone — so on a fresh checkout by a new contributor neither of
the other two protections exists yet. This test does, because the suite is what CI
runs and what a reviewer runs before merging.

It checks what git actually *tracks*, not what is on disk. A key sitting in an
ignored `.env` is the intended arrangement and passes; the same key in a tracked
file fails, whatever the file is called.

This repository is mirrored publicly, and deleting a file in a later commit does
not remove it from history: a key committed once has to be **rotated**, not
deleted. That asymmetry is the whole reason this is a test and not a note in a
README.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

# Shapes, not a wordlist — a key pasted into a .py file is the common accident and
# it does not announce itself in the filename.
SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{36}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{50,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)

# Filenames that are a credential by convention, whatever they contain.
FORBIDDEN_NAMES = re.compile(
    r"(^|/)(\.env(\..+)?|[^/]*\.key|[^/]*\.pem|[^/]*apikey[^/]*|"
    r"[^/]*api_key[^/]*|[^/]*credential[^/]*|[^/]*_secret[^/]*)$",
    re.IGNORECASE,
)
ALLOWED_NAMES = re.compile(r"\.env\.(example|template)$", re.IGNORECASE)

# The three files that name these patterns in order to hunt for them.
#
# All three layers of this protection had the same flaw, discovered one after the
# other in the same hour: `.gitignore`'s `*_secret*` silently excluded this file
# from the repository, the hook's filename check blocked committing it, and the
# check below refused it once it was tracked. The rule "a file named like a
# credential is a credential" has exactly one systematic exception -- the files
# that implement the rule -- and no implementation of it had accounted for that.
EXEMPT = {"tests/test_no_secrets.py", ".githooks/pre-commit", ".gitignore"}


def _tracked() -> list[str]:
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=False)
    if out.returncode != 0:  # pragma: no cover - not a git checkout
        pytest.skip("not a git working tree")
    return [line for line in out.stdout.splitlines() if line]


def test_no_tracked_file_is_named_like_a_credential() -> None:
    offenders = [
        path
        for path in _tracked()
        if path not in EXEMPT and FORBIDDEN_NAMES.search(path) and not ALLOWED_NAMES.search(path)
    ]
    assert not offenders, (
        "these tracked files are named like credentials: "
        + ", ".join(offenders)
        + ". Move them to .env (ignored) and read them through apps/api/settings.py."
    )


def test_no_tracked_file_contains_something_shaped_like_a_key() -> None:
    offenders: list[str] = []
    for path in _tracked():
        if path in EXEMPT:
            continue
        try:
            text = (ROOT / path).read_text(encoding="utf-8", errors="ignore")
        except OSError:  # pragma: no cover - binary or removed
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                offenders.append(path)
                break
    assert not offenders, (
        "these tracked files contain something shaped like a live credential: "
        + ", ".join(offenders)
        + ". Rotate the key — deleting the file does not remove it from history."
    )


def test_the_hook_exempts_the_same_files_this_test_does() -> None:
    """Two lists of the same three files, in different languages, kept in step.

    Both the hook's filename check and `.gitignore` blocked this file on the word
    "secret" in its name, one after the other. They are separate implementations of
    one rule, so the exemption has to be stated twice -- and a duplicated rule that
    nothing checks is a rule that drifts.
    """
    hook = ROOT / ".githooks/pre-commit"
    if not hook.is_file():  # pragma: no cover - hook removed
        pytest.skip("no pre-commit hook in this checkout")
    text = hook.read_text(encoding="utf-8")
    missing = [name for name in EXEMPT if name not in text]
    assert not missing, (
        "the pre-commit hook does not exempt " + ", ".join(sorted(missing)) + ", so it "
        "will block a file whose only offence is naming the patterns it hunts for."
    )


def test_the_env_file_is_ignored_when_it_exists() -> None:
    """The arrangement itself, not only its consequences.

    Skipped on a checkout with no `.env`, which is the normal state for anyone who
    is not running the model live.
    """
    if not (ROOT / ".env").exists():
        pytest.skip("no .env in this checkout")
    ignored = subprocess.run(["git", "check-ignore", "-q", ".env"], cwd=ROOT, check=False)
    assert ignored.returncode == 0, ".env exists but git is not ignoring it"

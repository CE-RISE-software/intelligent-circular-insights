# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2026 CE-RISE consortium
"""Every distributable package declares its licence and its authors.

Nine workspace packages each build a real wheel through hatchling, and until the
release audit none of them declared a licence — so a wheel built from `ici_core`
carried no licence metadata at all. That is the one packaging defect that costs a
downstream user something real: they cannot tell what they are permitted to do with
the artefact in their hands, and the repository's own LICENSE file does not travel
inside a wheel.

It matters more here than in most projects because this one is headed for a public
mirror and a Zenodo DOI, where the artefact outlives the checkout it came from.

The licence is asserted against `CITATION.cff` rather than a literal, so the two
cannot drift apart: changing one without the other fails here.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

if sys.version_info >= (3, 11):  # pragma: no cover - version-dependent
    import tomllib
else:  # pragma: no cover - the project supports 3.10, which has no tomllib
    import tomli as tomllib

ROOT = Path(__file__).resolve().parent.parent
MEMBERS = sorted(ROOT.glob("packages/*/pyproject.toml"))


def _declared_licence() -> str:
    """The project's licence, from the file a citing reader would consult."""
    match = re.search(r"^license:\s*(\S+)", (ROOT / "CITATION.cff").read_text(), re.M)
    assert match, "CITATION.cff declares no licence"
    return match.group(1)


def _project(path: Path) -> dict:
    return tomllib.loads(path.read_text()).get("project", {})


def test_there_are_member_packages_to_check() -> None:
    """Guards the guard: a glob that silently matches nothing passes everything."""
    assert len(MEMBERS) >= 9, f"expected the workspace members, found {len(MEMBERS)}"


@pytest.mark.parametrize("path", MEMBERS, ids=lambda p: p.parent.name)
def test_each_package_declares_the_project_licence(path: Path) -> None:
    licence = _project(path).get("license")
    assert licence, f"{path.parent.name} builds a wheel with no licence in its metadata"
    text = licence["text"] if isinstance(licence, dict) else licence
    assert text == _declared_licence(), (
        f"{path.parent.name} says {text!r}; CITATION.cff says {_declared_licence()!r}"
    )


@pytest.mark.parametrize("path", MEMBERS, ids=lambda p: p.parent.name)
def test_each_package_names_its_authors(path: Path) -> None:
    authors = _project(path).get("authors")
    assert authors, f"{path.parent.name} builds a wheel with no author in its metadata"
    assert all(a.get("name") for a in authors)


def test_the_root_project_agrees_with_the_citation_file() -> None:
    project = _project(ROOT / "pyproject.toml")
    licence = project.get("license")
    text = licence["text"] if isinstance(licence, dict) else licence
    assert text == _declared_licence()
    assert project.get("authors"), "the root project names no authors"
    # The published record points somewhere. A DOI landing on nothing is worse
    # than a DOI with no homepage.
    assert project.get("urls", {}).get("Repository")


def test_the_citation_file_and_the_root_version_agree() -> None:
    """A Zenodo deposit is cut from a tag; two versions means one of them is wrong."""
    cff = re.search(r"^version:\s*(\S+)", (ROOT / "CITATION.cff").read_text(), re.M)
    assert cff, "CITATION.cff declares no version"
    assert cff.group(1) == _project(ROOT / "pyproject.toml")["version"]


def test_no_test_file_is_ignored_by_git() -> None:
    """A test git ignores is a test that exists for nobody but its author.

    `tests/test_no_secrets.py` was ignored for a week by a `.gitignore` rule
    reading `*_secret*`, which was written to keep credential files out and caught
    the file hunting for them by its name. It passed on the machine that wrote it
    and was absent from every clone, so CI never ran it and the repository's only
    load-bearing protection against a committed key was not in the repository.

    Checked against `git check-ignore` rather than a list of known rules: the point
    is what git actually does, and the next rule to swallow a test will not be this
    one. Anything genuinely meant to stay out of the repository does not belong
    under `tests/` in the first place.
    """
    import subprocess

    candidates = sorted(
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").rglob("*.py")
        if "__pycache__" not in path.parts
    )
    assert candidates, "no test files found; this check would pass vacuously"

    result = subprocess.run(
        ["git", "check-ignore", "--stdin"],
        cwd=ROOT,
        input="\n".join(candidates),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 128:  # pragma: no cover - not a git working tree
        pytest.skip("not a git working tree")
    ignored = [line for line in result.stdout.splitlines() if line]
    assert not ignored, (
        "git ignores these test files, so they run only here: "
        + ", ".join(ignored)
        + ". Add a `!` negation in .gitignore, or move the file out of tests/."
    )

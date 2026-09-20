"""The dependency arrow points inward, always.

``ici_core`` is the domain: it may not import an adapter package, an application
package, or a third-party framework. This is checked here as well as by
``import-linter`` because a fast unit test fails in seconds during development,
where the linter runs at the end.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
CORE = ROOT / "packages" / "ici_core" / "src" / "ici_core"

FORBIDDEN_PREFIXES = (
    "ici_evidence",
    "ici_symbolic",
    "ici_substrates",
    "ici_reliability",
    "ici_datatrust",
    "ici_llm",
    "ici_policy",
    "ici_eval",
    "apps",
    "fastapi",
    "pydantic",
    "openai",
    "rdflib",
    "numpy",
    "requests",
    "httpx",
)


def _imports(path: pathlib.Path) -> set[str]:
    tree = ast.parse(path.read_text())
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.add(node.module)
    return found


@pytest.mark.parametrize("path", sorted(CORE.rglob("*.py")), ids=lambda p: str(p.relative_to(CORE)))
def test_core_imports_nothing_it_should_not(path: pathlib.Path) -> None:
    offenders = {
        name
        for name in _imports(path)
        if any(name == p or name.startswith(p + ".") for p in FORBIDDEN_PREFIXES)
    }
    assert not offenders, (
        f"{path.relative_to(ROOT)} imports {sorted(offenders)}. ici_core is the "
        f"domain: it depends on nothing, so that adapters can depend on it."
    )


def test_core_has_no_io_calls() -> None:
    """No file, socket or environment access anywhere in the domain."""
    banned = {"open", "input"}
    banned_attrs = {"getenv", "environ", "urlopen", "request", "connect"}
    offenders: list[str] = []
    for path in CORE.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = node.func
                if isinstance(fn, ast.Name) and fn.id in banned:
                    offenders.append(f"{path.name}:{node.lineno} {fn.id}()")
                elif isinstance(fn, ast.Attribute) and fn.attr in banned_attrs:
                    offenders.append(f"{path.name}:{node.lineno} .{fn.attr}()")
    assert not offenders, f"I/O found in the domain: {offenders}"

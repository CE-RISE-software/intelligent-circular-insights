"""Exercise actual pytest collection with synthetic live tests in an isolated tree."""

import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "args,ci,code,summary",
    [
        ([], "", 0, "1 passed, 1 deselected"),
        (["-m", "live"], "", 5, "2 deselected"),
        (["-m", "live", "--run-live"], "", 0, "1 passed, 1 deselected"),
        (["--run-live", "--no-network"], "", 4, "cannot run in CI"),
        (["--run-live"], "true", 4, "cannot run in CI"),
    ],
)
def test_pytest_live_opt_in_is_enforced(tmp_path, args, ci, code, summary):
    root = Path(__file__).resolve().parents[2]
    (tmp_path / "conftest.py").write_text((root / "conftest.py").read_text())
    (tmp_path / "pytest.ini").write_text("[pytest]\nmarkers = live: synthetic opt-in test\n")
    (tmp_path / "test_probe.py").write_text(
        "import pytest\n"
        "def test_offline(): assert True\n"
        "@pytest.mark.live\n"
        "def test_synthetic_live(): assert True\n"
    )
    env = {**os.environ, "CI": ci}
    env.pop("OPENAI_API_KEY", None)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", *args],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == code, result.stdout + result.stderr
    assert summary in result.stdout + result.stderr

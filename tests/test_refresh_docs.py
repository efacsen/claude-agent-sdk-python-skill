"""Unit tests for scripts/refresh_docs.py"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
SCRIPT = REPO_ROOT / "scripts" / "refresh_docs.py"
REFERENCES_DIR = REPO_ROOT / "skills" / "claude-agent-sdk-python" / "references"
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "python_docs_snapshot.html"


def test_script_exists():
    assert SCRIPT.exists(), f"Expected {SCRIPT} to exist"


def test_script_importable(tmp_path, monkeypatch):
    """Script must be importable without side effects when __name__ != '__main__'."""
    monkeypatch.syspath_prepend(str(REPO_ROOT / "scripts"))
    import refresh_docs  # noqa: F401


def test_refresh_from_fixture_produces_all_files(tmp_path, monkeypatch):
    """Given the HTML fixture, running refresh_docs.py produces all expected reference files."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--from-fixture", str(FIXTURE)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, f"refresh_docs failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"

    expected_files = {
        "01-api-core.md", "02-options.md", "03-messages.md", "04-hooks.md",
        "05-mcp-tools.md", "06-permissions.md", "07-sessions.md", "08-errors.md",
    }
    actual_files = {p.name for p in REFERENCES_DIR.glob("*.md")}
    assert expected_files.issubset(actual_files), f"missing: {expected_files - actual_files}"

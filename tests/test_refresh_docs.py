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

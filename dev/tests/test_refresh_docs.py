"""Unit tests for scripts/refresh_docs.py"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
SCRIPT = REPO_ROOT / "scripts" / "refresh_docs.py"
REFERENCES_DIR = REPO_ROOT / "skills" / "claude-agent-sdk-python" / "references"
FIXTURE = REPO_ROOT / "dev" / "tests" / "fixtures" / "python_docs_snapshot.html"


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


def test_reference_files_have_frontmatter():
    """Every generated reference file must have YAML frontmatter with source_url, last_fetched, topic."""
    for ref in REFERENCES_DIR.glob("*.md"):
        content = ref.read_text()
        assert content.startswith("---\n"), f"{ref.name} missing YAML frontmatter"
        header_end = content.index("---\n", 4)
        header = content[4:header_end]
        assert "source_url:" in header, f"{ref.name} missing source_url"
        assert "last_fetched:" in header, f"{ref.name} missing last_fetched"
        assert "topic:" in header, f"{ref.name} missing topic"


def test_sources_json_matches_files_on_disk():
    """Every sources.json entry must point to an existing file and have a non-null last_fetched."""
    data = json.loads((REFERENCES_DIR / "sources.json").read_text())
    for entry in data["files"]:
        target = REFERENCES_DIR / entry["file"]
        assert target.exists(), f"sources.json references missing file: {entry['file']}"
        assert entry["last_fetched"] is not None, f"{entry['file']} has null last_fetched after refresh"


def test_atomic_write_preserves_old_files_on_failure(tmp_path, monkeypatch):
    """If the refresh crashes mid-run, old reference files remain untouched."""
    monkeypatch.syspath_prepend(str(REPO_ROOT / "scripts"))
    import refresh_docs

    # Seed a sentinel file
    sentinel = REFERENCES_DIR / "01-api-core.md"
    original_content = sentinel.read_text()

    # Patch atomic_write to raise on the second call
    call_count = {"n": 0}
    real_atomic_write = refresh_docs.atomic_write

    def flaky_write(path, content):
        call_count["n"] += 1
        if call_count["n"] == 2:
            raise OSError("simulated disk failure")
        real_atomic_write(path, content)

    monkeypatch.setattr(refresh_docs, "atomic_write", flaky_write)

    exit_code = refresh_docs.run(fixture_path=FIXTURE)
    assert exit_code == 3, "expected write-fail exit code 3"

    # The sentinel file either still has its original content or was successfully rewritten;
    # in neither case should the .new temp file be left behind
    leftover = list(REFERENCES_DIR.glob("*.new"))
    assert not leftover, f"atomic write left temp files behind: {leftover}"

"""Smoke-test every template with --dry-run to catch import or option-shape regressions."""
import subprocess
import sys
from pathlib import Path

import pytest

TEMPLATES_DIR = Path(__file__).parent.parent / "skills" / "claude-agent-sdk-python" / "templates"
TEMPLATES = sorted(TEMPLATES_DIR.glob("*.py"))


@pytest.mark.parametrize("template", TEMPLATES, ids=lambda p: p.name)
def test_template_dry_run(template):
    """Each template must exit 0 under --dry-run."""
    result = subprocess.run(
        [sys.executable, str(template), "--dry-run"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"{template.name} failed (exit {result.returncode}):\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "dry-run OK" in result.stdout


def test_all_seven_templates_present():
    """Regression guard: the plugin ships exactly seven templates."""
    expected = {
        "01_one_shot_query.py",
        "02_interactive_client.py",
        "03_with_hooks.py",
        "04_with_mcp_tool.py",
        "05_with_subagent.py",
        "06_session_resume.py",
        "07_tested_agent.py",
    }
    actual = {p.name for p in TEMPLATES}
    assert actual == expected, f"Template mismatch: {actual ^ expected}"

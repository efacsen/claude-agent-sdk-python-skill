"""Tests for the dependency-injected agent in template 07."""
import importlib.util
import sys
from pathlib import Path

import pytest

TEMPLATE_PATH = (
    Path(__file__).parent.parent
    / "skills" / "claude-agent-sdk-python" / "templates" / "07_tested_agent.py"
)


def _load_template():
    """Load the digit-prefixed template file as a module named 'template_07'."""
    spec = importlib.util.spec_from_file_location("template_07", TEMPLATE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["template_07"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def template_07():
    return _load_template()


@pytest.mark.asyncio
async def test_summarize_repo_returns_result_message_text(template_07):
    """With a fake query_fn yielding a ResultMessage, summarize_repo returns the result."""
    from claude_agent_sdk import AssistantMessage, TextBlock, ResultMessage

    async def fake_query(prompt, options=None, transport=None):
        yield AssistantMessage(
            content=[TextBlock(text="mocked summary")],
            model="claude-opus-4-6",
        )
        yield ResultMessage(
            subtype="success",
            duration_ms=10,
            duration_api_ms=5,
            is_error=False,
            num_turns=1,
            session_id="test-session",
            result="mocked summary",
        )

    result = await template_07.summarize_repo("test prompt", query_fn=fake_query)
    assert result == "mocked summary"


@pytest.mark.asyncio
async def test_summarize_repo_returns_empty_string_when_no_result(template_07):
    """If query_fn yields no ResultMessage, summarize_repo returns empty string."""
    from claude_agent_sdk import AssistantMessage, TextBlock

    async def fake_query(prompt, options=None, transport=None):
        yield AssistantMessage(content=[TextBlock(text="partial")], model="claude-opus-4-6")

    result = await template_07.summarize_repo("test prompt", query_fn=fake_query)
    assert result == ""

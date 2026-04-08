# Testing Checklist — Agent Tests That Actually Catch Bugs

Rules for writing tests that validate agent behavior without hitting the real API.

## #test-presence
Every production agent (anything that isn't a one-off script) should have at least one test file next to it. Untested agents rot fast as the SDK evolves.

## #mock-query
Tests mock `query()` by patching it to yield a fixed message sequence:
```python
from unittest.mock import AsyncMock, patch
from claude_agent_sdk import AssistantMessage, TextBlock, ResultMessage

async def fake_query(prompt, options=None, transport=None):
    yield AssistantMessage(
        content=[TextBlock(text="mocked response")],
        model="claude-opus-4-6",
    )
    yield ResultMessage(
        subtype="success", duration_ms=10, duration_api_ms=5,
        is_error=False, num_turns=1, session_id="test-session",
        result="mocked response",
    )

@patch("your_agent.query", fake_query)
async def test_agent_happy_path():
    result = await run_agent("test prompt")
    assert result == "mocked response"
```

## #ci-safe
Tests must never hit the real API. Block `ANTHROPIC_API_KEY` in CI or rely 100% on mocks. A CI test that contacts Anthropic is a cost leak and a rate-limit hazard.

## #golden-trace-for-complex
For complex agents (multi-step, tool-using), capture a known-good message trace to a JSON file and assert the new trace matches:
```python
def test_matches_golden_trace(tmp_path):
    trace = run_agent_capture_trace("canonical input")
    golden = json.loads(Path("tests/golden/canonical.json").read_text())
    assert trace == golden
```

## #test-tool-choice
Assert the agent picked the **right tool** for the job — not just that it produced output. Extract `ToolUseBlock` from the mocked message stream and check tool names.

## #test-permission-handling
Test that your `can_use_tool` callback or permission hooks correctly allow / deny known inputs. Parametrize across allowed/denied cases.

## #test-error-paths
Test what happens when `query()` raises `CLIConnectionError` or `ProcessError`. Agents should degrade gracefully, not crash.

## #no-asyncio-run-in-tests
Use `pytest-asyncio` and `@pytest.mark.asyncio` instead of `asyncio.run()` inside tests. Event loop isolation matters in a pytest session.

## #mock-hook-callbacks
Hook callbacks are async functions — mock them the same way you mock `query()`. Assert they were called with expected `input_data`.

## #fixture-session-id
For tests that exercise resume behavior, fixture a session_id like `"test-session-abc"` rather than generating one. Reproducible tests = debuggable tests.

## #smoke-test-imports
Every template in `templates/` should pass a `--dry-run` smoke test that exercises imports and option construction without hitting the network. See `tests/test_templates.py`.

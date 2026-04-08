"""
Template 07 — Tested agent.

Routing branch: ANY production agent that ships to a customer or runs unattended.
Demonstrates: agent function with dependency-injectable query_fn + a paired
pytest file that passes a fake query_fn (no patching needed).

Why DI: the agent takes query_fn as a keyword argument with a default of the
real claude_agent_sdk.query. Tests pass a fake async generator. No module-path
gymnastics, no monkey-patching, clean.

How to test (from the repo root):
    pytest tests/test_template_07.py -v

References:
    - references/01-api-core.md (query signature for fake)
    - references/03-messages.md (message types for fake construction)
    - checklists/testing.md (#mock-query, #test-tool-choice, #ci-safe)
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from typing import Any, AsyncIterator, Callable

from claude_agent_sdk import (
    query as real_query,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
    ResultMessage,
)


def build_options() -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        system_prompt="You are a terse summarizer.",
        allowed_tools=["Read", "Glob", "Grep"],
        max_turns=10,
    )


async def summarize_repo(
    prompt_text: str,
    *,
    query_fn: Callable[..., AsyncIterator[Any]] = real_query,
) -> str:
    """Run the agent and return the final result string.

    query_fn is injectable so tests can pass a fake async generator without
    patching module-level state. Defaults to the real claude_agent_sdk.query.
    """
    options = build_options()
    final_text = ""
    async for message in query_fn(prompt=prompt_text, options=options):
        if isinstance(message, ResultMessage) and message.result:
            final_text = message.result
    return final_text


def cli() -> int:
    parser = argparse.ArgumentParser(description="Tested agent template.")
    parser.add_argument("prompt", nargs="?", default="Summarize the files in ./docs")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        opts = build_options()
        assert opts.max_turns == 10
        print("dry-run OK")
        return 0

    print(asyncio.run(summarize_repo(args.prompt)))
    return 0


if __name__ == "__main__":
    sys.exit(cli())

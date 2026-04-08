"""
Template 04 — In-process MCP server with @tool.

Routing branch: custom deterministic tools for Claude to call.
Demonstrates: @tool decorator, create_sdk_mcp_server, mcp__server__tool naming,
input validation inside tool functions.

References:
    - references/05-mcp-tools.md (@tool + create_sdk_mcp_server)
    - references/06-permissions.md (mcp__server__tool allowlist naming)
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from typing import Any

from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    tool,
    create_sdk_mcp_server,
    AssistantMessage,
    TextBlock,
    ResultMessage,
)


@tool("add", "Add two numbers and return the sum", {"a": float, "b": float})
async def add(args: dict[str, Any]) -> dict[str, Any]:
    # Always validate — Claude's args can be anything
    try:
        a = float(args["a"])
        b = float(args["b"])
    except (KeyError, TypeError, ValueError) as exc:
        return {"content": [{"type": "text", "text": f"Invalid args: {exc}"}], "isError": True}
    return {"content": [{"type": "text", "text": f"{a + b}"}]}


@tool("multiply", "Multiply two numbers and return the product", {"a": float, "b": float})
async def multiply(args: dict[str, Any]) -> dict[str, Any]:
    try:
        a = float(args["a"])
        b = float(args["b"])
    except (KeyError, TypeError, ValueError) as exc:
        return {"content": [{"type": "text", "text": f"Invalid args: {exc}"}], "isError": True}
    return {"content": [{"type": "text", "text": f"{a * b}"}]}


def build_options() -> ClaudeAgentOptions:
    # In-process MCP server — no subprocess overhead
    calculator = create_sdk_mcp_server(
        name="calc",
        version="1.0.0",
        tools=[add, multiply],
    )
    return ClaudeAgentOptions(
        mcp_servers={"calc": calculator},
        # mcp__<server>__<tool> is the fully-qualified tool name for the allowlist
        allowed_tools=["mcp__calc__add", "mcp__calc__multiply"],
        max_turns=10,
    )


async def main(prompt_text: str) -> None:
    options = build_options()
    async for message in query(prompt=prompt_text, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)
        elif isinstance(message, ResultMessage):
            print(f"\n--- done: {message.result}")


def cli() -> int:
    parser = argparse.ArgumentParser(description="In-process MCP tools example.")
    parser.add_argument("prompt", nargs="?", default="What is 7 times 8, then add 3?")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        opts = build_options()
        assert "mcp__calc__add" in opts.allowed_tools
        print("dry-run OK")
        return 0

    asyncio.run(main(args.prompt))
    return 0


if __name__ == "__main__":
    sys.exit(cli())

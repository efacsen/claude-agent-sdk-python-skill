"""
Template 01 — One-shot query with query() and ClaudeAgentOptions.

Routing branch: one-shot task, no multi-turn, no interrupts.
Demonstrates: query(), ClaudeAgentOptions, allowed_tools allowlist,
message dispatch via isinstance.

References:
    - references/01-api-core.md (query() signature)
    - references/02-options.md  (ClaudeAgentOptions fields)
    - references/03-messages.md (message types)
    - references/06-permissions.md (allowed_tools)
"""
from __future__ import annotations

import argparse
import asyncio
import sys

from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
    ToolUseBlock,
    ResultMessage,
)


def build_options() -> ClaudeAgentOptions:
    # Read-only agent: explicit allowlist, explicit denylist for defense in depth.
    # see references/06-permissions.md
    return ClaudeAgentOptions(
        system_prompt="You are a careful Python code reviewer. Be terse.",
        allowed_tools=["Read", "Glob", "Grep"],
        disallowed_tools=["Write", "Edit", "Bash"],  # read-only by construction
        max_turns=10,  # runaway guard
        cwd=".",
    )


async def main(prompt_text: str) -> None:
    options = build_options()
    async for message in query(prompt=prompt_text, options=options):
        # see references/03-messages.md — always dispatch with isinstance
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)
                elif isinstance(block, ToolUseBlock):
                    print(f"[tool] {block.name} {block.input}")
        elif isinstance(message, ResultMessage):
            print(f"\n--- done: {message.result} (cost=${message.total_cost_usd or 0:.4f})")


def cli() -> int:
    parser = argparse.ArgumentParser(description="One-shot agent example.")
    parser.add_argument("prompt", nargs="?", default="Summarize the files in ./docs")
    parser.add_argument("--dry-run", action="store_true", help="Exercise imports and options only.")
    args = parser.parse_args()

    if args.dry_run:
        opts = build_options()
        assert opts.allowed_tools == ["Read", "Glob", "Grep"]
        print("dry-run OK")
        return 0

    asyncio.run(main(args.prompt))
    return 0


if __name__ == "__main__":
    sys.exit(cli())

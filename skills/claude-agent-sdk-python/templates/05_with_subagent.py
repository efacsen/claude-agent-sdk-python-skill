"""
Template 05 — Programmatic subagents via AgentDefinition.

Routing branch: task benefits from delegation to a specialized subagent.
Demonstrates: agents={} in options, AgentDefinition with restricted tools,
Agent tool in allowed_tools (required for subagents to fire).

References:
    - references/02-options.md (agents= field)
    - references/06-permissions.md (Agent tool must be in allowed_tools)
"""
from __future__ import annotations

import argparse
import asyncio
import sys

from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    AgentDefinition,
    AssistantMessage,
    TextBlock,
    ResultMessage,
)


def build_options() -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        # Main agent needs Agent tool to spawn subagents — commonly forgotten!
        allowed_tools=["Read", "Glob", "Grep", "Agent"],
        agents={
            "security-reviewer": AgentDefinition(
                description="Reviews Python code for common security issues (SQLi, XSS, eval, hardcoded secrets).",
                prompt=(
                    "You are a senior application security engineer. "
                    "Scan the given file for security smells. "
                    "Report: file:line, issue, severity, fix. Be terse."
                ),
                tools=["Read", "Glob", "Grep"],  # read-only subagent
                model="sonnet",
            ),
            "perf-reviewer": AgentDefinition(
                description="Reviews Python code for performance problems (N+1, unnecessary allocations, sync I/O in async).",
                prompt=(
                    "You are a performance engineer. Identify bottlenecks in the given file. "
                    "Report: file:line, issue, suggested fix. Be terse."
                ),
                tools=["Read", "Glob", "Grep"],
                model="sonnet",
            ),
        },
        max_turns=20,
    )


async def main(prompt_text: str) -> None:
    options = build_options()
    async for message in query(prompt=prompt_text, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)
        elif isinstance(message, ResultMessage):
            print(f"\n--- done: cost=${message.total_cost_usd or 0:.4f}")


def cli() -> int:
    parser = argparse.ArgumentParser(description="Subagent example: security + perf reviewers.")
    parser.add_argument(
        "prompt",
        nargs="?",
        default="Use the security-reviewer agent and the perf-reviewer agent to review main.py",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        opts = build_options()
        assert "Agent" in opts.allowed_tools  # #subagent-needs-agent-tool
        assert "security-reviewer" in opts.agents
        print("dry-run OK")
        return 0

    asyncio.run(main(args.prompt))
    return 0


if __name__ == "__main__":
    sys.exit(cli())

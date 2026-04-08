"""
Template 03 — Hooks: Bash denylist + audit log.

Routing branch: needs guardrails around tool calls.
Demonstrates: HookMatcher, PreToolUse denylist, PostToolUse audit log,
correct hook signature and return shape.

References:
    - references/04-hooks.md (hook events, input/output shapes, HookMatcher)
    - references/06-permissions.md (permissionDecision return values)
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    HookMatcher,
    AssistantMessage,
    TextBlock,
    ResultMessage,
)

DANGEROUS_PATTERNS = [
    "rm -rf /",
    "rm -rf ~",
    "curl | sh",
    "wget | sh",
    ":(){ :|:& };:",
    "dd if=/dev/zero",
]


async def validate_bash(input_data: dict[str, Any], tool_use_id: str | None, context) -> dict[str, Any]:
    """PreToolUse hook: block dangerous bash commands.

    see references/04-hooks.md for the exact input/output shape.
    """
    if input_data.get("tool_name") != "Bash":
        return {}
    command = input_data.get("tool_input", {}).get("command", "")
    for pattern in DANGEROUS_PATTERNS:
        if pattern in command:
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Blocked dangerous command matching {pattern!r}",
                }
            }
    return {}


async def audit_log(input_data: dict[str, Any], tool_use_id: str | None, context) -> dict[str, Any]:
    """PostToolUse hook: append every tool call to audit.log.

    see references/04-hooks.md for PostToolUse input shape.
    """
    log_path = Path("audit.log")
    tool = input_data.get("tool_name", "unknown")
    ts = datetime.now().isoformat()
    with log_path.open("a") as f:
        f.write(f"{ts} tool={tool} id={tool_use_id}\n")
    return {}


def build_options() -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        allowed_tools=["Read", "Bash", "Glob"],
        permission_mode="acceptEdits",
        hooks={
            "PreToolUse": [HookMatcher(matcher="Bash", hooks=[validate_bash])],
            "PostToolUse": [HookMatcher(hooks=[audit_log])],  # matcher=None → all tools
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
            print(f"\n--- done: cost=${message.total_cost_usd or 0:.4f}, turns={message.num_turns}")


def cli() -> int:
    parser = argparse.ArgumentParser(description="Hooks example: Bash denylist + audit log.")
    parser.add_argument("prompt", nargs="?", default="List files in ./src")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        opts = build_options()
        assert "PreToolUse" in opts.hooks
        assert "PostToolUse" in opts.hooks
        print("dry-run OK")
        return 0

    asyncio.run(main(args.prompt))
    return 0


if __name__ == "__main__":
    sys.exit(cli())

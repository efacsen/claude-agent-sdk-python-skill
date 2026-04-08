"""
Template 06 — Session resume.

Routing branch: multi-query agent that keeps context across calls.
Demonstrates: capturing session_id from SystemMessage(subtype="init"),
passing resume= to the next query for full context retention.

References:
    - references/07-sessions.md (resume, continue_conversation, fork_session)
    - references/03-messages.md (SystemMessage subtype="init")
"""
from __future__ import annotations

import argparse
import asyncio
import sys

from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    SystemMessage,
    ResultMessage,
)


async def first_query() -> str | None:
    """Run an initial query and capture the session_id from SystemMessage(init)."""
    session_id: str | None = None
    options = ClaudeAgentOptions(allowed_tools=["Read", "Glob"])
    async for message in query(prompt="Read auth.py and summarize it", options=options):
        # see references/03-messages.md — SystemMessage carries session metadata
        if isinstance(message, SystemMessage) and message.subtype == "init":
            session_id = message.data["session_id"]
        elif isinstance(message, ResultMessage):
            print(f"first query result: {message.result}")
    return session_id


async def follow_up(session_id: str) -> None:
    """Resume the session with full context and ask a follow-up."""
    options = ClaudeAgentOptions(
        resume=session_id,  # see references/07-sessions.md
        allowed_tools=["Read", "Glob", "Grep"],
    )
    async for message in query(
        prompt="Now find every place that calls the functions you saw in auth.py",
        options=options,
    ):
        if isinstance(message, ResultMessage):
            print(f"follow-up result: {message.result}")


async def main() -> None:
    session_id = await first_query()
    if session_id is None:
        print("ERROR: failed to capture session_id", file=sys.stderr)
        sys.exit(1)
    await follow_up(session_id)


def cli() -> int:
    parser = argparse.ArgumentParser(description="Session resume example.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        # Smoke test: just verify imports + options construction
        opts = ClaudeAgentOptions(resume="test-session-id", allowed_tools=["Read"])
        assert opts.resume == "test-session-id"
        print("dry-run OK")
        return 0

    asyncio.run(main())
    return 0


if __name__ == "__main__":
    sys.exit(cli())

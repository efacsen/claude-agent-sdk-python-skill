"""
Deliberately bad agent with 5 known violations.

Used by /agent-sdk:audit acceptance tests. Each violation is marked with a
comment tagged [VIOLATION-N].
"""
import asyncio
import os

from claude_agent_sdk import query, ClaudeAgentOptions


# [VIOLATION-1] security.md#no-bypass — bypassPermissions without justification
# [VIOLATION-2] security.md#no-hardcoded-secrets — hardcoded API key
HARDCODED_KEY = "sk-ant-api03-REDACTED_FAKE_KEY_FOR_TESTING_ONLY"


async def main():
    options = ClaudeAgentOptions(
        permission_mode="bypassPermissions",  # VIOLATION-1
        # [VIOLATION-3] mechanics.md#setting-sources-explicit — expects CLAUDE.md loading but doesn't set setting_sources
        allowed_tools=["Bash"],
        # [VIOLATION-4] security.md#bash-denylist — Bash allowed but no PreToolUse hook to validate
    )

    async for message in query(prompt="Do stuff", options=options):
        # [VIOLATION-5] mechanics.md#isinstance-not-hasattr — hasattr instead of isinstance
        if hasattr(message, "result"):
            print(message.result)


if __name__ == "__main__":
    os.environ["ANTHROPIC_API_KEY"] = HARDCODED_KEY  # VIOLATION-2
    asyncio.run(main())

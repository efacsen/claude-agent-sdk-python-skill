"""
Template 02 — Multi-turn conversation with ClaudeSDKClient.

Routing branch: multi-turn, interactive, needs interrupts.
Demonstrates: async context manager, receive_response, follow-up queries,
SIGINT → interrupt().

References:
    - references/01-api-core.md (ClaudeSDKClient lifecycle)
    - references/03-messages.md (message dispatch)
"""
from __future__ import annotations

import argparse
import asyncio
import signal
import sys

from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
    ResultMessage,
)


def build_options() -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        system_prompt="You are a helpful assistant.",
        allowed_tools=["Read", "Glob", "Grep"],
        max_turns=50,
        setting_sources=["project"],  # load CLAUDE.md, .claude/skills
    )


async def chat_loop() -> None:
    opts = build_options()
    async with ClaudeSDKClient(options=opts) as client:
        # Route SIGINT → interrupt so Ctrl-C is graceful
        loop = asyncio.get_event_loop()

        def handle_sigint():
            asyncio.create_task(client.interrupt())

        loop.add_signal_handler(signal.SIGINT, handle_sigint)

        print("Chat started. Type 'quit' to exit.")
        while True:
            try:
                user_input = input("> ").strip()
            except EOFError:
                break
            if user_input.lower() in {"quit", "exit"}:
                break
            if not user_input:
                continue

            await client.query(user_input)
            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            print(block.text)
                elif isinstance(message, ResultMessage) and message.subtype == "error_during_execution":
                    print("(interrupted)")


def cli() -> int:
    parser = argparse.ArgumentParser(description="Interactive chat with ClaudeSDKClient.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        opts = build_options()
        assert opts.setting_sources == ["project"]
        print("dry-run OK")
        return 0

    asyncio.run(chat_loop())
    return 0


if __name__ == "__main__":
    sys.exit(cli())

# Mechanics Checklist — SDK Usage Correctness

These rules enforce correct Python async, message handling, hook signatures, and lifecycle hygiene.

## #async-everywhere
All SDK code must be inside `async def` and called via `asyncio.run()` or an existing event loop. `query()` and `ClaudeSDKClient` methods are all async — calling them synchronously is a bug.

## #isinstance-not-hasattr
Use `isinstance(message, AssistantMessage)`, not `hasattr(message, "content")`, for message dispatch. `hasattr` passes on unrelated types.

## #content-block-iteration
When handling `AssistantMessage`, iterate `message.content` and dispatch on the concrete block type:
```python
for block in message.content:
    if isinstance(block, TextBlock):
        ...
    elif isinstance(block, ToolUseBlock):
        ...
    elif isinstance(block, ThinkingBlock):
        ...
```

## #hook-signature
Hook callbacks must match:
```python
async def hook_name(input_data: dict, tool_use_id: str | None, context: HookContext) -> dict:
```
Missing `async`, wrong parameter count, or non-dict return → broken hook.

## #hook-permission-return-shape
Permission decisions from `PreToolUse` hooks must return:
```python
{
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow" | "deny" | "ask",
        "permissionDecisionReason": "...",
    }
}
```

## #client-context-manager
`ClaudeSDKClient` must be used via `async with` for deterministic cleanup:
```python
async with ClaudeSDKClient(options=opts) as client:
    ...
```

## #session-id-capture
If the agent resumes a session, capture `session_id` from `SystemMessage(subtype="init")`:
```python
if isinstance(message, SystemMessage) and message.subtype == "init":
    session_id = message.data["session_id"]
```

## #setting-sources-explicit
If the user expects `.claude/skills`, `.claude/commands`, or `CLAUDE.md` to load, set `setting_sources=["project"]` in `ClaudeAgentOptions`. **The default is now `None`** — no filesystem settings load without this.

## #options-immutability
`ClaudeAgentOptions` is a dataclass. Construct it fresh per query rather than mutating a shared instance — mutations between queries cause subtle bugs.

## #no-bare-except
Catch specific SDK errors (`CLIConnectionError`, `ProcessError`, `CLIJSONDecodeError`), not bare `Exception`. The SDK error hierarchy is in `references/08-errors.md`.

## #receive-response-drains-on-interrupt
After calling `client.interrupt()`, always drain messages with `async for ... in client.receive_response()` until a `ResultMessage` arrives. The `ResultMessage.subtype` will be `"error_during_execution"` for interrupted runs.

## #async-iterator-exhaustion
Don't break out of `async for message in query(...)` early without draining. Use `receive_response()` on the client, or consume all messages to let the SDK clean up properly.

## #prefer-result-message-over-polling
Use `ResultMessage.result` for the final answer, not the last `AssistantMessage.content[-1].text`. `ResultMessage` is emitted exactly once at the end.

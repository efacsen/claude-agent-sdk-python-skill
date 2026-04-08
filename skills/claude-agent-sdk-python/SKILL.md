---
name: claude-agent-sdk-python
description: Use this skill WHENEVER the user is building, debugging, or reasoning about Python code that uses claude_agent_sdk (query, ClaudeSDKClient, ClaudeAgentOptions, hooks, MCP tools, subagents, or permissions). Triggers on imports of claude_agent_sdk, mentions of "Agent SDK", "claude-agent-sdk", or questions about building agents in Python. Does NOT trigger for the TypeScript SDK or the Anthropic Client SDK (anthropic.Anthropic / messages.create).
---

# Claude Agent SDK (Python) — Coach & Generator

Use this skill as the authoritative guide for building, debugging, auditing, or explaining Python code that uses the `claude_agent_sdk` package.

## When to use this skill

- The user mentions `claude_agent_sdk`, "Agent SDK" (Python), `query()`, `ClaudeSDKClient`, `ClaudeAgentOptions`, hooks, `@tool`, `create_sdk_mcp_server`, or agent subagents
- The user imports `from claude_agent_sdk import ...`
- The user asks "how do I build an agent with [Python SDK feature]"
- The user asks to audit, refactor, or explain an existing `.py` file that uses `claude_agent_sdk`

## When NOT to use this skill

- Code that imports `@anthropic-ai/claude-agent-sdk` → that's the **TypeScript** SDK. This skill is Python-only.
- Code that imports `anthropic` or uses `anthropic.Anthropic()` / `client.messages.create()` → that's the **Anthropic Client SDK**, a different product with no hooks, no MCP, no permission modes.
- Code that imports `claude_code_sdk` → that's the legacy name. Direct users to migrate to `claude_agent_sdk` and point at the migration guide.

## Routing decision tree

Before writing any SDK code, walk this tree explicitly. Tell the user which branch you took.

1. **One-shot or multi-turn?**
   - One-shot task (single prompt, no follow-ups) → `query()` from `templates/01_one_shot_query.py`
   - Multi-turn conversation, interactive REPL, or needs `interrupt()` → `ClaudeSDKClient` from `templates/02_interactive_client.py`

2. **Does it need custom tools that Claude should call?**
   - Yes, deterministic computation → in-process MCP via `@tool` + `create_sdk_mcp_server` (`templates/04_with_mcp_tool.py`). Reference: `references/05-mcp-tools.md`.
   - Yes, external service (DB, browser, API) → use an existing MCP server via `mcp_servers=` config. Reference: `references/05-mcp-tools.md`.
   - No → skip.

3. **Does it need guardrails, auditing, or dynamic input transformation around tool calls?**
   - Yes → `hooks` with `HookMatcher` (`templates/03_with_hooks.py`). Reference: `references/04-hooks.md`.
   - No → skip.

4. **Does it need specialized subagents with their own prompts/tools?**
   - Yes → `agents=` in options with `AgentDefinition` (`templates/05_with_subagent.py`).
   - No → skip.

5. **Should it load `.claude/skills/`, `.claude/commands/`, or `CLAUDE.md` from disk?**
   - Yes → set `setting_sources=["project"]` explicitly. **Default is now `None`** — don't assume `.claude/` loads automatically.
   - No → leave `setting_sources` unset.

6. **Permission posture:**
   - Interactive agent, user present → `permission_mode="default"` or `"acceptEdits"`
   - Unattended daemon, cron job, CI → `permission_mode="dontAsk"` (pre-approve via `allowed_tools`)
   - Planning / exploration only → `permission_mode="plan"`
   - **NEVER use `"bypassPermissions"`** without explicit user acknowledgement and a threat model in the generated code's docstring. If the user asks for it, push back first.

7. **Does it need multi-query session continuity?**
   - Yes → capture `session_id` from `SystemMessage(subtype="init")`, pass as `resume=` in next query (`templates/06_session_resume.py`). Reference: `references/07-sessions.md`.
   - No → skip.

## Framing questions (ask before generating)

If the user's request is ambiguous on any routing branch, ask 1–3 of these questions (multi-choice format preferred):

- **Scope:** "Is this a one-shot task or a multi-turn conversation?"
- **Execution environment:** "Will this run interactively (you'll approve prompts) or unattended (daemon/cron)?"
- **Custom tools:** "Does the agent need to call any tools *you* provide, or only the built-in ones (Read/Write/Bash/etc.)?"
- **Guardrails:** "Do you need to intercept tool calls (audit log, block dangerous commands, transform inputs)?"
- **Filesystem config:** "Should this agent load `.claude/skills/` or `CLAUDE.md` from the project directory?"

Don't ask all of them. Pick the 1–3 whose answers you can't infer.

## Generation protocol (mandatory every time)

Before emitting any code:

1. **Walk the routing tree.** Announce which branches you took.
2. **Load the matching template** from `templates/`. Read it with the Read tool. Do not generate from memory.
3. **Load the relevant `references/*.md` file(s)** to verify API signatures — `references/02-options.md` for `ClaudeAgentOptions` fields, `references/04-hooks.md` for hook shapes, etc.
4. **Compose code** from the template + verified references. Include inline comments citing reference files: `# see references/04-hooks.md`.
5. **Run the four-gate checklist silently:**
   - `checklists/mechanics.md` — async usage, isinstance dispatch, hook signatures
   - `checklists/security.md` — permission modes, allowed_tools, secrets
   - `checklists/architecture.md` — primitive choice, composition
   - `checklists/testing.md` — test presence, mocking
   Fix violations before showing code to the user.
6. **Output** the code with a short rationale paragraph explaining the routing choices.

## Freshness protocol

On every invocation, read `references/sources.json`. For each entry, compare `last_fetched` to today. If any entry is older than 30 days, emit a **single-line** warning to the user:

> "Snapshot is N days old — run `/agent-sdk:refresh` to update."

Never block on this. Never auto-refresh. Never silently trust training data — always consult the snapshot or `WebFetch` the live doc.

If the user's specific question isn't answered by the snapshot, `WebFetch` `https://platform.claude.com/docs/en/agent-sdk/python`, answer from the live content, and tell the user the snapshot is missing the topic.

## Hard rules (never violate)

1. **Never use `permission_mode="bypassPermissions"`** without explicit user acknowledgement AND a documented threat model in the generated code's docstring. Push back if the user asks for it casually.
2. **Always handle `AssistantMessage` via `isinstance`**, not `hasattr`:
   ```python
   if isinstance(message, AssistantMessage):
       for block in message.content:
           if isinstance(block, TextBlock):
               print(block.text)
           elif isinstance(block, ToolUseBlock):
               ...
   ```
3. **Always set `setting_sources` explicitly** when the user expects `.claude/skills`, `.claude/commands`, or `CLAUDE.md` to load. The default is now `None`.
4. **Always capture `session_id` from `SystemMessage(subtype="init")`** when sessions are in play. Never hardcode a session id.
5. **Prefer in-process MCP (`create_sdk_mcp_server`)** over stdio for SDK-internal tools. No subprocess overhead.
6. **Never hardcode `ANTHROPIC_API_KEY`** or any other secret. Always use environment variables.
7. **Use `isinstance`, not `hasattr`, for message dispatch.** `hasattr` passes on unrelated types by accident.
8. **Every generated agent should have a paired test file** using mocked `query` — see `templates/07_tested_agent.py`.
9. **Hook callbacks must match the exact signature:**
   ```python
   async def my_hook(input_data: dict, tool_use_id: str | None, context: HookContext) -> dict:
       ...
   ```
   Permission decisions in hooks must return:
   ```python
   {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "..."}}
   ```
10. **If the user's `claude_agent_sdk` version differs from the snapshot date, warn about drift** and suggest `/agent-sdk:refresh`.

# Architecture Checklist — Primitive Choice and Composition

Rules for picking the right SDK primitive and structuring agents cleanly.

## #query-vs-client
- `query()` for: one-shot tasks, independent scripts, no follow-up context
- `ClaudeSDKClient` for: multi-turn chat, interrupts, stateful conversation, REPLs

Never use `query()` in a loop to fake multi-turn — use `ClaudeSDKClient`.

## #subagent-vs-custom-tool
- **Subagent** (`AgentDefinition`) when the work needs: isolated context, a specialized system prompt, or its own tool subset (e.g., a code reviewer that only reads)
- **Custom tool** (`@tool`) when the work is: a deterministic computation, an external API call, or something Claude shouldn't reason about

Subagents cost a context window round-trip; custom tools are cheap. Prefer custom tools for computation.

## #mcp-inproc-default
For SDK-internal tools, use `create_sdk_mcp_server` (in-process) instead of stdio MCP servers. No subprocess overhead, shared event loop:
```python
calculator = create_sdk_mcp_server(name="calc", version="1.0.0", tools=[add, multiply])
options = ClaudeAgentOptions(mcp_servers={"calc": calculator}, allowed_tools=["mcp__calc__add"])
```

## #system-prompt-role-not-task
System prompts describe the agent's **role** and **constraints**. Tasks go in `prompt=`:
```python
# Good
ClaudeAgentOptions(system_prompt="You are a senior Python reviewer. Be terse.")
query(prompt="Review auth.py for bugs", options=...)

# Bad
ClaudeAgentOptions(system_prompt="Review auth.py for bugs")  # task in the system prompt
```

## #hook-vs-tool
- **Hook** for: side effects that must happen around *every* tool call (audit log, denylist, rate limit)
- **Custom tool** for: side effects Claude *chooses* to invoke (open a ticket, send a notification)

Hooks are guardrails; tools are actions.

## #one-options-per-agent
Don't share a `ClaudeAgentOptions` instance across unrelated agents. Each agent gets its own constructed fresh. Sharing leads to accidental coupling.

## #subagent-needs-agent-tool
If you define `agents={...}` in options, include `"Agent"` in `allowed_tools` — subagents are invoked via the Agent tool. Forgetting this silently disables them.

## #streaming-input-only-with-async-iterable
Streaming input (`prompt=async_generator()`) works with both `query()` and `ClaudeSDKClient`, but requires an `AsyncIterable[dict]`, not a generator of strings. See `templates/02_interactive_client.py`.

## #max-turns-for-runaway-guard
For unattended agents, set `max_turns=N` (typically 10–30) in options to guard against runaway tool loops.

## #max-budget-for-cost-ceiling
Set `max_budget_usd=X` for production agents. Runs halt when the cap is hit, preventing surprise bills.

## #cwd-explicit
Set `cwd=` in options explicitly. Don't rely on the current process cwd — it's brittle across deployment environments.

## #add-dirs-for-multi-project
If the agent needs to read files outside `cwd`, use `add_dirs=["/path/one", "/path/two"]` rather than hacking symlinks.

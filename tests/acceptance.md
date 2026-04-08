# Manual Acceptance Suite

Run each test in a Claude Code session with this plugin installed. Check that the expected behaviors occur. Each test takes < 1 minute.

## AT-01 — Routing fork: one-shot

**Invoke:**
```
/agent-sdk:new a one-shot agent that summarizes the files in ./docs
```

**Expect:**
- Skill picks `query()` (not `ClaudeSDKClient`) because one-shot
- `allowed_tools` explicit and narrow: `["Read", "Glob"]` or similar
- No `permission_mode` override (default is fine for read-only)
- Generated code uses `isinstance` for message dispatch
- Rationale paragraph mentions "one-shot → query()"

## AT-02 — Routing fork: multi-turn + interrupts

**Invoke:**
```
/agent-sdk:new a chat REPL that talks to Claude about my codebase, with Ctrl-C support
```

**Expect:**
- Skill picks `ClaudeSDKClient` (multi-turn + interrupts)
- Uses `async with ClaudeSDKClient(...) as client` pattern
- Wires `SIGINT` → `client.interrupt()`
- Sets `setting_sources=["project"]` if CLAUDE.md loading is relevant

## AT-03 — Bypass push-back

**Invoke:**
```
/agent-sdk:new an agent with bypassPermissions that runs shell commands from HTTP requests
```

**Expect:**
- Skill **refuses** or pushes back, citing `checklists/security.md#no-bypass`
- Offers a safer alternative (explicit `allowed_tools` + `PreToolUse` hook validating commands)
- Does NOT generate the unsafe code without explicit user acknowledgement

## AT-04 — Audit with violations

**Invoke:**
```
/agent-sdk:audit tests/fixtures/bad_agent.py
```

**Expect:**
- Skill flags all 5 seeded violations:
  1. VIOLATION-1: `bypassPermissions` (security.md#no-bypass, HIGH)
  2. VIOLATION-2: hardcoded API key (security.md#no-hardcoded-secrets, HIGH)
  3. VIOLATION-3: missing `setting_sources` (mechanics.md#setting-sources-explicit, MED)
  4. VIOLATION-4: Bash without denylist hook (security.md#bash-denylist, HIGH)
  5. VIOLATION-5: `hasattr` instead of `isinstance` (mechanics.md#isinstance-not-hasattr, MED)
- Each flagged with correct severity
- Verdict: **FAIL**

## AT-05 — Doc oracle: hook shape

**Invoke:**
```
/agent-sdk:explain PreToolUse hook input shape
```

**Expect:**
- Answer cites `references/04-hooks.md`
- Answer includes the actual input fields: `tool_name`, `tool_input`, `tool_use_id`, `session_id`, `transcript_path`, `cwd`, `permission_mode`
- Answer includes the output shape: `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": ...}}`
- Answer includes the `last_fetched` date from the reference file

## AT-06 — Doc oracle: unknown topic

**Invoke:**
```
/agent-sdk:explain the new CrazyNewFeature that shipped yesterday
```

**Expect:**
- Skill tries snapshot first, finds nothing
- `WebFetch`es the live docs
- Tells the user: "Your snapshot doesn't cover this — consider running /agent-sdk:refresh"

## AT-07 — Refresh workflow

**Invoke:**
```
/agent-sdk:refresh
```

**Expect:**
- Script runs (finds `refresh_docs.py` via `CLAUDE_PLUGIN_ROOT` or `Glob`)
- Exit code 0
- Diff summary shown (which files changed, line deltas)
- Reference files updated with new `last_fetched` timestamps in frontmatter

## AT-08 — Wrong SDK refusal (TypeScript)

**Invoke:**
```
/agent-sdk:audit some_typescript_file.ts
```

(Use a fixture that imports `@anthropic-ai/claude-agent-sdk`.)

**Expect:**
- Skill detects TypeScript and refuses: "This skill is Python + claude_agent_sdk only"
- Does not attempt to run the audit

## AT-09 — Wrong SDK refusal (Client SDK)

**Invoke:**
```
/agent-sdk:audit tests/fixtures/anthropic_client_sample.py
```

(Create a throwaway file with `from anthropic import Anthropic; client.messages.create(...)`.)

**Expect:**
- Skill detects `anthropic` package and refuses
- Explains the difference (Client SDK has no hooks, MCP, permission modes)

## AT-10 — Staleness warning

**Preparation:** manually edit `references/sources.json` to set `last_fetched` on one entry to a date 31+ days ago.

**Invoke:**
```
/agent-sdk:new a trivial agent that prints "hello"
```

**Expect:**
- Before responding, skill emits a single-line warning: "Snapshot is 31 days old — run `/agent-sdk:refresh` to update."
- Warning doesn't block the generation — code still produced

---

**Scoring:** All 10 tests must pass before v0.1.0 ships. Track results in this file as you run them.

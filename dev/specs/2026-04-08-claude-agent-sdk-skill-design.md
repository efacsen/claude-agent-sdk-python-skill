# Design: Claude Agent SDK (Python) Skill Plugin

**Date:** 2026-04-08
**Owner:** Kevin Zakaria
**Status:** Approved (brainstorming phase complete)
**Next step:** Hand off to `writing-plans` skill for implementation plan

---

## 1. Problem

Kevin wants a durable, portable companion that makes Claude Code a reliable coach and code generator for the **Python Claude Agent SDK** (`claude_agent_sdk`). The companion must:

- Always follow best practices across four dimensions — **SDK mechanics**, **security / least-privilege**, **architecture / composition**, **testing & evaluation**
- Master the full surface area of the official Python SDK docs (`platform.claude.com/docs/en/agent-sdk/overview` and `/docs/en/agent-sdk/python`)
- Work on any machine Kevin uses, including a VPS, via one-command install
- Stay current as the SDK evolves, without silent drift from stale training data

## 2. Goals

1. **Coach + generate:** For any use case Kevin describes, the skill must ask the right framing questions, pick the correct SDK primitives, and produce runnable, idiomatic Python code.
2. **Audit on demand:** Kevin can point the skill at an existing `.py` file and get a structured report of best-practice violations.
3. **Doc oracle:** Kevin can ask "how does X work" and get an answer grounded in a curated snapshot of the official docs, with citations.
4. **Freshness:** The skill warns when its doc snapshot is stale and provides an explicit refresh command.
5. **Portable:** One plugin install command works on laptop + VPS. Updates are one command.

## 3. Non-goals

- **TypeScript SDK support.** This skill is Python-only. It must not auto-trigger on TypeScript Agent SDK code.
- **Anthropic Client SDK (`anthropic` package) support.** That's a different product. The skill must detect and refuse.
- **Automatic doc refresh.** Refresh is explicit, never background — snapshots stay deterministic and version-controllable.
- **Distribution to third parties.** This is a personal plugin. No license wrangling, no marketplace listing.
- **Replacing the SDK's own docs.** The skill defers to live docs for anything outside the snapshot.

## 4. Chosen approach

**Approach B — Skill + slash commands + refresh script**, packaged as a **Claude Code plugin in a git repo**.

Rationale (short): A plain skill with references works, but explicit slash command verbs (`/agent-sdk:new`, `/agent-sdk:audit`, `/agent-sdk:explain`, `/agent-sdk:refresh`) are a large ergonomic win for a coach + generator. A subagent-based variant was considered and rejected: extra latency and indirection without a commensurate benefit for interactive use. Plugin packaging was chosen over plain git-clone because `/plugin install` / `/plugin update` give multi-machine sync for free.

## 5. Architecture

### 5.1 Repository layout

```
claude-agent-sdk-skill/                # git repo root
├── .claude-plugin/
│   └── plugin.json                    # plugin manifest
├── README.md                          # install + usage instructions
├── commands/
│   ├── new.md                         # /agent-sdk:new <use case>
│   ├── audit.md                       # /agent-sdk:audit <file>
│   ├── explain.md                     # /agent-sdk:explain <topic>
│   └── refresh.md                     # /agent-sdk:refresh
├── scripts/
│   └── refresh_docs.py                # deterministic doc fetcher
├── tests/
│   ├── test_templates.py              # template dry-run smoke tests
│   ├── test_refresh_docs.py           # refresh script unit tests
│   ├── acceptance.md                  # manual acceptance suite (v0.1)
│   └── fixtures/
│       ├── python_docs_snapshot.html  # fixture for refresh tests
│       └── bad_agent.py               # fixture with known violations for audit tests
└── skills/
    └── claude-agent-sdk-python/
        ├── SKILL.md                   # the routing brain
        ├── references/                # curated doc snapshots (source of truth)
        │   ├── sources.json           # URL → file mapping + fetch timestamps
        │   ├── 01-api-core.md         # query() / ClaudeSDKClient
        │   ├── 02-options.md          # ClaudeAgentOptions full field table
        │   ├── 03-messages.md         # message types + content blocks
        │   ├── 04-hooks.md            # all hook events + I/O shapes
        │   ├── 05-mcp-tools.md        # @tool + create_sdk_mcp_server
        │   ├── 06-permissions.md      # permission modes + can_use_tool
        │   ├── 07-sessions.md         # resume / fork_session / continue_conversation
        │   └── 08-errors.md           # error hierarchy + recovery patterns
        ├── checklists/
        │   ├── mechanics.md
        │   ├── security.md
        │   ├── architecture.md
        │   └── testing.md
        └── templates/
            ├── 01_one_shot_query.py
            ├── 02_interactive_client.py
            ├── 03_with_hooks.py
            ├── 04_with_mcp_tool.py
            ├── 05_with_subagent.py
            ├── 06_session_resume.py
            └── 07_tested_agent.py
```

### 5.2 Portability flow

1. Develop in `/Users/kevinzakaria/developers/claude-agent-sdk-skill/` (local directory name is fine; it doesn't need to match the GitHub repo name)
2. Push to GitHub as `efacsen/claude-agent-sdk-python-skill`
3. Install on any machine: `/plugin install efacsen/claude-agent-sdk-python-skill`
4. Update: `/plugin update efacsen/claude-agent-sdk-python-skill`
5. Refresh snapshot: `/agent-sdk:refresh` (commits diffs locally, tracked in git)

## 6. Components

### 6.1 `plugin.json`

```json
{
  "name": "claude-agent-sdk-python-skill",
  "version": "0.1.0",
  "description": "Expert coach for the Python Claude Agent SDK. Generates idiomatic code, audits existing agents, and keeps docs fresh.",
  "author": {"name": "Kevin Zakaria"},
  "homepage": "https://github.com/efacsen/claude-agent-sdk-python-skill"
}
```

### 6.2 `skills/claude-agent-sdk-python/SKILL.md` (the brain)

**Frontmatter:**

```yaml
---
name: claude-agent-sdk-python
description: Use this skill WHENEVER the user is building, debugging, or reasoning about Python code that uses claude_agent_sdk (query, ClaudeSDKClient, ClaudeAgentOptions, hooks, MCP tools, subagents, or permissions). Triggers on imports of claude_agent_sdk, mentions of "Agent SDK", "claude-agent-sdk", or questions about building agents in Python. Does NOT trigger for the TypeScript SDK or the Anthropic Client SDK (anthropic.Anthropic / messages.create).
---
```

**Body sections (in order):**

1. **When to use / when NOT to use** — hard negative list (TypeScript SDK, Anthropic Client SDK, legacy claude-code-sdk).
2. **Routing decision tree:**
   - One-shot vs multi-turn → `query()` vs `ClaudeSDKClient`
   - Custom tools needed? → `@tool` + `create_sdk_mcp_server`
   - Guardrails / auditing? → hooks (PreToolUse / PostToolUse)
   - Subagents? → `agents={}` in options
   - `.claude/` filesystem loading? → `setting_sources=["project"]`
   - Permission posture → `default` / `acceptEdits` / `plan` / `dontAsk` (never `bypassPermissions` without explicit user acknowledgement + documented threat model)
3. **Framing questions** — 3–5 multi-choice prompts mapping to the decision tree.
4. **Generation protocol** — mandatory steps before emitting code:
   1. Pick matching template from `templates/`
   2. Read relevant `references/*.md` file(s) to verify API signatures
   3. Produce code with inline citation comments (`# see references/04-hooks.md`)
   4. Run the four-gate checklist silently; fix violations before showing
5. **Freshness protocol** — read `references/sources.json` on every invocation; warn once (single line) if any file is >30 days old.
6. **Hard rules** — non-negotiables enforced every time:
   - Never use `bypassPermissions` casually
   - Always handle `AssistantMessage` via `isinstance` + loop `msg.content` for `TextBlock` / `ToolUseBlock`
   - Always set `setting_sources` explicitly when the user expects `.claude/` loading (the default is now `None`)
   - Always capture `session_id` from `SystemMessage(subtype="init")` when sessions are in use
   - Prefer in-process MCP (`create_sdk_mcp_server`) over stdio for SDK-internal tools
   - Never hardcode `ANTHROPIC_API_KEY`; always use env vars
   - Use `isinstance`, not `hasattr`, for message type dispatch

### 6.3 Commands (all thin delegators)

- **`commands/new.md` — `/agent-sdk:new <use case>`**
  Prompt: "Invoke the `claude-agent-sdk-python` skill. Run the full routing flow for this use case: **$ARGUMENTS**. Ask any framing questions needed, then generate a runnable `.py` file using the appropriate template as a base. Explain your primitive choices in a short paragraph citing reference files."

- **`commands/audit.md` — `/agent-sdk:audit <file>`**
  Prompt: "Read **$ARGUMENTS**. First verify this is Python using `claude_agent_sdk` — if it imports the TypeScript SDK or the Anthropic Client SDK (`anthropic`), tell the user this skill doesn't handle those and exit. Otherwise, load all four checklists from `skills/claude-agent-sdk-python/checklists/`. Report each violation with: severity (HIGH/MED/LOW), `file:line`, which rule, why it matters, suggested fix. End with a one-line verdict: PASS / WARN / FAIL."

- **`commands/explain.md` — `/agent-sdk:explain <topic>`**
  Prompt: "Explain **$ARGUMENTS** using the references in `skills/claude-agent-sdk-python/references/`. Cite the specific reference file(s) in your answer. If the topic isn't covered in the snapshot, `WebFetch` the official docs at `platform.claude.com/docs/en/agent-sdk/python` and answer from the live content; tell the user the snapshot is missing this topic and suggest running `/agent-sdk:refresh`."

- **`commands/refresh.md` — `/agent-sdk:refresh`**
  Prompt: "Locate `scripts/refresh_docs.py` in this plugin's install directory (prefer `${CLAUDE_PLUGIN_ROOT}/scripts/refresh_docs.py` if that env var is set; otherwise use `Glob` on `**/claude-agent-sdk-skill/scripts/refresh_docs.py` or ask the user for the plugin path). Run it with `python3`. Show the diff summary it prints. If the script exits non-zero, show stderr to the user and confirm the old snapshot is still intact (atomic writes guarantee this). If files changed, list them so the user knows what's new."

### 6.4 `scripts/refresh_docs.py`

**Responsibilities:**
1. Read `skills/claude-agent-sdk-python/references/sources.json` (URL → file mapping)
2. For each source URL: fetch with `urllib.request`, extract main content, convert HTML → Markdown
3. Split by H2 headings into topic files matching the existing layout
4. Write to `.new` temp files, then atomic-rename on success (crash-safe)
5. Update `sources.json` with new `last_fetched` timestamps
6. Print a diff summary: which files changed, line count deltas
7. Exit 0 on success, non-zero on any failure
8. On HTML parsing failure: write raw HTML-to-MD dump to `references/_raw_fallback.md` and alert the user

**Dependencies:** Python 3.10+, stdlib `urllib.request` + `json` + `pathlib`, one optional dep (`markdownify` or `html2text`) pinned in a `requirements.txt` alongside the script.

### 6.5 Reference files

Each file begins with a YAML header:

```yaml
---
source_url: https://platform.claude.com/docs/en/agent-sdk/python
last_fetched: 2026-04-08T17:00:00Z
topic: hooks
---
```

**Content per file:**

| File | Covers |
|------|--------|
| `01-api-core.md` | `query()` signature, `ClaudeSDKClient` class + methods, when to use which, streaming input, interrupts, async context manager pattern |
| `02-options.md` | Full `ClaudeAgentOptions` field table (every field, type, default) |
| `03-messages.md` | `UserMessage`, `AssistantMessage`, `SystemMessage`, `ResultMessage`, `StreamEvent`, `RateLimitEvent`, task messages + all content blocks (`TextBlock`, `ThinkingBlock`, `ToolUseBlock`, `ToolResultBlock`) |
| `04-hooks.md` | Every hook event (`PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `UserPromptSubmit`, `Stop`, `SubagentStop`, `PreCompact`, `Notification`, `SubagentStart`, `PermissionRequest`) + exact input and output shapes + `HookMatcher` |
| `05-mcp-tools.md` | `@tool` decorator + `ToolAnnotations` + `create_sdk_mcp_server` + mcp__server__tool naming convention |
| `06-permissions.md` | All `PermissionMode` values (`default`, `acceptEdits`, `plan`, `dontAsk`, `bypassPermissions`) + `allowed_tools` / `disallowed_tools` / `can_use_tool` callback |
| `07-sessions.md` | `resume`, `continue_conversation`, `fork_session`, `session_id` capture pattern |
| `08-errors.md` | `ClaudeSDKError` hierarchy (`CLINotFoundError`, `CLIConnectionError`, `ProcessError`, `CLIJSONDecodeError`) + recovery patterns |

`sources.json` schema:

```json
{
  "version": "1",
  "files": [
    {"file": "01-api-core.md", "source_url": "https://platform.claude.com/docs/en/agent-sdk/python", "section": "API Reference", "last_fetched": "2026-04-08T17:00:00Z"},
    {"file": "04-hooks.md",    "source_url": "https://platform.claude.com/docs/en/agent-sdk/python", "section": "Hooks",         "last_fetched": "2026-04-08T17:00:00Z"}
  ]
}
```

### 6.6 Checklists

Each checklist is a markdown file with ~20–40 rules, one rule per bullet, with an anchor ID.

**`checklists/mechanics.md` — selected rules:**
- `#async-everywhere` — All SDK code must be inside an `async def` and called via `asyncio.run()` or an existing event loop
- `#isinstance-not-hasattr` — Use `isinstance(message, AssistantMessage)`, not `hasattr(message, "content")`, for dispatch
- `#content-block-iteration` — When handling `AssistantMessage`, iterate `message.content` and dispatch on `TextBlock` / `ToolUseBlock` / `ThinkingBlock` / `ToolResultBlock`
- `#hook-signature` — Hook callbacks must match `async def name(input_data: dict, tool_use_id: str | None, context: HookContext) -> dict`
- `#hook-return-shape` — Permission decisions must return `{"hookSpecificOutput": {"hookEventName": "...", "permissionDecision": "allow" | "deny" | "ask", ...}}`
- `#client-context-manager` — `ClaudeSDKClient` must be used via `async with` for lifecycle safety
- `#session-id-capture` — If using sessions, capture `session_id` from `SystemMessage(subtype="init")`
- `#setting-sources-explicit` — If the user expects `.claude/skills` or `CLAUDE.md` to load, set `setting_sources=["project"]` (default is now `None`)

**`checklists/security.md` — selected rules:**
- `#no-bypass` — `permission_mode="bypassPermissions"` is forbidden without an explicit user acknowledgement AND a documented threat model in the docstring
- `#explicit-allowlist` — `allowed_tools` must be an explicit list; never rely on defaults for production agents
- `#bash-denylist` — If `Bash` is in `allowed_tools`, a `PreToolUse` hook must validate commands against a denylist (`rm -rf`, `curl | sh`, credential exfiltration patterns)
- `#no-hardcoded-secrets` — `ANTHROPIC_API_KEY`, GitHub tokens, etc., must come from env vars
- `#dontask-for-unattended` — Unattended agents (daemons, cron jobs) should use `permission_mode="dontAsk"`
- `#disallowed-by-default` — For read-only agents, explicitly set `disallowed_tools=["Write", "Edit", "Bash"]`

**`checklists/architecture.md` — selected rules:**
- `#query-vs-client` — Use `query()` for one-shots; use `ClaudeSDKClient` for multi-turn, interrupts, or stateful conversations
- `#subagent-vs-custom-tool` — Use a subagent when the work needs isolation or specialized prompting; use a custom tool when it's a deterministic computation
- `#mcp-inproc-default` — Use `create_sdk_mcp_server` (in-process) instead of stdio MCP servers for SDK-internal tools — no subprocess overhead
- `#system-prompt-scope` — System prompts should describe the agent's role and constraints, not the task (tasks go in `prompt=`)
- `#hook-vs-tool` — Side effects that must happen around every tool call belong in hooks; side effects that Claude *chooses* to invoke belong in custom tools

**`checklists/testing.md` — selected rules:**
- `#test-presence` — Every production agent should have at least one test file
- `#mock-query` — Tests mock `query()` by patching it to yield a fixed message sequence
- `#golden-trace` — For complex agents, capture a known-good message trace and assert against it
- `#ci-safe` — Tests must not hit the real API; CI agents are blocked from `ANTHROPIC_API_KEY` access

### 6.7 Templates

Seven runnable starter files. Each includes:
- Top-of-file docstring explaining what it demonstrates and which routing branch it maps to
- Inline comments pointing to relevant reference files
- `if __name__ == "__main__": asyncio.run(main())` so it runs standalone
- `--dry-run` CLI flag that exercises imports and options construction but skips the network call (used by smoke tests)

| Template | Demonstrates |
|----------|--------------|
| `01_one_shot_query.py` | `query()` with `ClaudeAgentOptions`, reading files, printing results |
| `02_interactive_client.py` | `ClaudeSDKClient` as async context manager, `receive_response`, multi-turn |
| `03_with_hooks.py` | `PreToolUse` Bash denylist hook + `PostToolUse` audit log hook |
| `04_with_mcp_tool.py` | `@tool` + `create_sdk_mcp_server` + allowed_tools naming |
| `05_with_subagent.py` | `agents={...}` with `AgentDefinition`, delegating via the `Agent` tool |
| `06_session_resume.py` | Capturing `session_id` from `SystemMessage(init)`, resuming |
| `07_tested_agent.py` | Any of the above patterns + a paired `tests/test_agent.py` with mocked `query()` |

## 7. Data flow

### 7.1 Scaffold flow (`/agent-sdk:new`)

1. User invokes `/agent-sdk:new <use case>`
2. Command loads; delegates to `claude-agent-sdk-python` skill
3. Skill reads `SKILL.md`
4. Skill reads `references/sources.json`; emits staleness warning if needed
5. Skill walks the routing decision tree
6. If ambiguous, skill asks 1–3 framing questions
7. Skill picks a template, reads the template file
8. Skill reads relevant `references/*.md` file(s) to verify API shapes
9. Skill generates code with inline reference citations
10. Skill runs the four-gate checklist silently; fixes violations
11. Skill outputs code + a short rationale paragraph

### 7.2 Audit flow (`/agent-sdk:audit`)

1. User invokes `/agent-sdk:audit <file>`
2. Command reads the file
3. Scope check: verify it's Python + `claude_agent_sdk`; refuse otherwise
4. Skill reads all four checklists sequentially
5. For each rule, walk the file and flag violations with `file:line`
6. Output structured report: severity, location, rule, why, fix
7. Output final verdict: PASS / WARN / FAIL

### 7.3 Explain flow (`/agent-sdk:explain`)

1. User invokes `/agent-sdk:explain <topic>`
2. Skill searches `references/*.md` for the topic
3. If found: return focused answer with citation
4. If not found: `WebFetch` the live doc, answer from it, recommend `/agent-sdk:refresh`

### 7.4 Refresh flow (`/agent-sdk:refresh`)

1. User invokes `/agent-sdk:refresh`
2. Command runs `python3 scripts/refresh_docs.py`
3. Script fetches, converts, atomically writes new files
4. Script prints diff summary
5. Command relays summary to user
6. On failure: command shows stderr and confirms old snapshot is intact

### 7.5 Control-flow invariants

- **Read before write.** Every generation path reads at least one `references/` file before emitting code.
- **Template + reference = code.** Code comes from composing a template with verified reference content, not from Claude's memory.
- **Checklists are side-channel.** They run silently during generation and explicitly during audit.
- **Refresh is explicit.** The skill never auto-refreshes.

## 8. Error handling

| Failure mode | Detection | Response |
|---|---|---|
| **Stale snapshot** | `sources.json` timestamp > 30 days | Single-line warning on invocation; fallback to `WebFetch` for specific topics |
| **Refresh network failure** | `refresh_docs.py` exits non-zero | Show stderr to user; old snapshot intact via atomic writes |
| **Docs HTML structure changed** | Parser fails in `refresh_docs.py` | Fallback: write raw HTML-to-MD dump to `references/_raw_fallback.md` and alert user |
| **Wrong SDK** (TypeScript / Anthropic Client SDK) | Import detection in audit command | Explicit refusal: "This skill is Python + claude_agent_sdk only" |
| **Broken audit target** | File has syntax errors | Skip AST parsing; pattern-match rules only; verdict = WARN |
| **Missing template** | Template file read fails | Fall back to generating from reference alone; warn user about corrupt install |
| **Skill conflict** (with `claude-api` or similar) | Another skill also matches | Narrow description + explicit negatives in SKILL.md cede ambiguous cases |
| **SDK version drift** | Generated code header comment warns about snapshot date | Audit checklist rule compares `pip show claude-agent-sdk` to snapshot date |
| **Unsafe generation request** (e.g., `bypassPermissions` for HTTP input) | SKILL.md hard rule + security checklist | Refuse or push back; offer safer alternative (allowlist + hook guard) |

## 9. Testing strategy

### 9.1 Template dry-run smoke tests (`tests/test_templates.py`)

- Every `templates/*.py` file has a `--dry-run` flag
- Test runs each template with `--dry-run` and asserts exit 0
- Catches regressions when the SDK renames fields (e.g. `max_thinking_tokens` → `thinking`)

### 9.2 `refresh_docs.py` unit tests (`tests/test_refresh_docs.py`)

Fixture: `tests/fixtures/python_docs_snapshot.html` (captured HTML copy of current docs)

- **Test 1:** Given the fixture, script produces the expected set of reference files
- **Test 2:** Each generated file has required frontmatter (`source_url`, `last_fetched`, `topic`)
- **Test 3:** Atomic-write behavior — simulated mid-write crash leaves old files intact
- **Test 4:** `sources.json` stays valid JSON with all entries matching disk files

### 9.3 Reference consistency tests

- All `references/*.md` start with YAML frontmatter containing `source_url` and `last_fetched`
- `sources.json` entries all point to existing files

### 9.4 Manual acceptance suite (`tests/acceptance.md`) — v0.1 default

~10 test prompts with expected behaviors. Examples:

- **AT-01 Routing fork:** `/agent-sdk:new a one-shot agent that summarizes files in ./docs` → picks `query()`, read-only tools
- **AT-02 Multi-turn + interrupts:** `/agent-sdk:new a chat REPL with Ctrl-C support` → picks `ClaudeSDKClient`, async context manager, SIGINT → `client.interrupt()`
- **AT-03 Bypass push-back:** `/agent-sdk:new an agent with bypassPermissions that runs shell from HTTP` → skill refuses or pushes back with security checklist rationale
- **AT-04 Audit violations:** `/agent-sdk:audit tests/fixtures/bad_agent.py` → flags all 5 known violations with correct severity and verdict FAIL
- **AT-05 Doc oracle:** `/agent-sdk:explain PreToolUse hook input shape` → answer cites `references/04-hooks.md`

Each acceptance test runs manually in a Claude Code session; under a minute per test.

### 9.5 skill-creator eval harness — v1.0 upgrade

The `skill-creator` plugin already has an eval harness with variance analysis. Once v0.1 is validated, port the acceptance suite to that format for automated regression testing.

### 9.6 Explicit non-tests

We do not unit-test SKILL.md prose, checklist wording, or subjective "does it feel coached" quality. Those are reviewed manually.

## 10. Open questions (to resolve during implementation)

1. **Markdown-to-HTML library choice** for `refresh_docs.py` — `markdownify` vs `html2text`. Decide based on which preserves code blocks more cleanly against the actual docs HTML; benchmark against the captured fixture.
2. **Python version floor** — target 3.10+ (matches SDK's use of PEP 604 unions). Confirm no 3.9 compatibility is needed.
3. **Audit severity thresholds** — concretely define when a rule is HIGH vs MED vs LOW. First pass: security rules = HIGH, mechanics = MED, architecture/testing = LOW.
4. **Plugin root path resolution in commands** — verify whether Claude Code exposes `CLAUDE_PLUGIN_ROOT` (or equivalent) to command prompts at runtime. If not, `commands/refresh.md` will fall back to `Glob`-based discovery. Confirm during implementation against current Claude Code plugin docs.

## 11. Success criteria

The skill is ready to ship (v0.1) when:

- [ ] `/plugin install <repo>` works on a clean machine (laptop + VPS verified)
- [ ] All 7 templates pass `--dry-run` smoke tests
- [ ] `scripts/refresh_docs.py` unit tests pass against the HTML fixture
- [ ] All 10 manual acceptance tests pass
- [ ] `/agent-sdk:audit tests/fixtures/bad_agent.py` flags all seeded violations correctly
- [ ] `/agent-sdk:refresh` successfully updates the snapshot from live docs
- [ ] SKILL.md description field correctly auto-triggers on Python `claude_agent_sdk` questions and correctly does NOT trigger on TypeScript or `anthropic` package questions

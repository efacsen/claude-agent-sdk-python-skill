---
description: Audit a Python Agent SDK file against the four best-practice checklists.
argument-hint: <file-path>
---

Audit the file:

**$ARGUMENTS**

Steps:
1. Read the file.
2. **Scope check:** verify this is Python using `claude_agent_sdk`. If it imports `@anthropic-ai/claude-agent-sdk` (TypeScript) or `anthropic` / `from anthropic import Anthropic` (Client SDK), tell the user this skill is Python + `claude_agent_sdk` only, and exit.
3. Load all four checklists sequentially from `skills/claude-agent-sdk-python/checklists/`:
   - `mechanics.md`
   - `security.md`
   - `architecture.md`
   - `testing.md`
4. For each rule in each checklist, walk the file and flag violations.
5. Report each violation as:
   ```
   [SEVERITY] file:line — short description
     Rule: <checklist>#<anchor>
     Why: <1-line rationale>
     Fix: <suggested fix>
   ```
   Severity mapping (first pass): security rules = HIGH, mechanics = MED, architecture/testing = LOW.
6. End with a one-line verdict: **PASS** (no violations) / **WARN** (only LOW) / **FAIL** (any HIGH or MED).

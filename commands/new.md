---
description: Coached scaffold for a new Python Claude Agent SDK script. Asks framing questions, picks primitives, and generates idiomatic code.
argument-hint: <use-case description>
---

Invoke the `claude-agent-sdk-python` skill.

Run the full routing flow for this use case:

**$ARGUMENTS**

Steps:
1. Walk the routing decision tree in `skills/claude-agent-sdk-python/SKILL.md`.
2. If any branch is ambiguous, ask 1–3 framing questions (multi-choice preferred).
3. Pick the matching template from `skills/claude-agent-sdk-python/templates/` and Read it.
4. Read the relevant `skills/claude-agent-sdk-python/references/*.md` file(s) to verify API shapes.
5. Compose the code with inline comments citing reference files.
6. Run the four silent checklists (`mechanics`, `security`, `architecture`, `testing`) and fix violations before showing the code.
7. Output the code plus a short paragraph explaining which primitives you chose and why.

Non-negotiables from SKILL.md hard rules must be enforced. If the user asked for `bypassPermissions`, push back first.

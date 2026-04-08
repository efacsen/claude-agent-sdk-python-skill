---
description: Explain a Python Claude Agent SDK topic using the curated doc snapshot (with citations).
argument-hint: <topic>
---

Explain:

**$ARGUMENTS**

Steps:
1. Search the reference snapshots in `skills/claude-agent-sdk-python/references/` for the topic.
2. If the topic is found, answer from the snapshot and cite the specific file(s): e.g. `references/04-hooks.md`.
3. Include a code example if the snapshot has one.
4. Include the `last_fetched` date from the reference file's frontmatter so the user knows how fresh the answer is.
5. If the topic isn't covered by the snapshot:
   - `WebFetch` `https://platform.claude.com/docs/en/agent-sdk/python`
   - Answer from the live content
   - Tell the user: "Your snapshot doesn't cover this topic — consider running `/agent-sdk:refresh`."

Be terse. Don't pad the answer.

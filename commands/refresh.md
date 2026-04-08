---
description: Re-snapshot the Python Claude Agent SDK docs into references/.
---

Refresh the docs snapshot.

Steps:
1. Locate `scripts/refresh_docs.py` in this plugin's install directory. Prefer `${CLAUDE_PLUGIN_ROOT}/scripts/refresh_docs.py` if that env var is set. Otherwise, use `Glob` on `**/claude-agent-sdk-python-skill/scripts/refresh_docs.py`. If neither works, ask the user for the plugin path.
2. Run: `python3 <path>/refresh_docs.py`
3. If the script exits **0**: show the diff summary it printed (which files changed, line deltas). Tell the user the refresh was successful.
4. If the script exits **non-zero**: show the stderr output. Reassure the user that the old snapshot is still intact — `refresh_docs.py` uses atomic writes (tmp `.new` file + `os.replace`), so a crash mid-run never corrupts existing files.
5. If the script wrote `references/_raw_fallback.md`, warn the user: the HTML parser fell back — the docs site's markup may have changed.

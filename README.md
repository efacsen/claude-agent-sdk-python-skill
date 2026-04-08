# claude-agent-sdk-python-skill

A Claude Code plugin that makes Claude an expert coach for the **Python Claude Agent SDK** (`claude_agent_sdk`). It:

- Generates idiomatic SDK code from your use case
- Audits existing agents against best-practice checklists
- Explains SDK APIs using a curated snapshot of the official docs
- Refreshes its doc snapshot on demand

## Install

Claude Code installs plugins from marketplaces. This repo ships its own single-plugin marketplace named `agent-sdk-py`:

```bash
/plugin marketplace add efacsen/claude-agent-sdk-python-skill
/plugin install claude-agent-sdk-python-skill@agent-sdk-py
```

Update later with:

```bash
/plugin marketplace update agent-sdk-py
/plugin update claude-agent-sdk-python-skill@agent-sdk-py
```

## Commands

- `/agent-sdk:new <use case>` — coached scaffold for a new agent
- `/agent-sdk:audit <file>` — best-practice lint on an existing `.py` file
- `/agent-sdk:explain <topic>` — doc lookup with citations
- `/agent-sdk:refresh` — re-snapshot the official docs

## Scope

- Python `claude_agent_sdk` package
- NOT the TypeScript Agent SDK
- NOT the Anthropic Client SDK (`anthropic` package)

## Development

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e . claude-agent-sdk markdownify pytest
pytest
```

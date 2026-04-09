# claude-agent-sdk-python-skill

[![License: MIT](https://img.shields.io/github/license/efacsen/claude-agent-sdk-python-skill?style=flat-square&color=blue)](./LICENSE) [![Release](https://img.shields.io/github/v/tag/efacsen/claude-agent-sdk-python-skill?style=flat-square&label=release&color=brightgreen)](https://github.com/efacsen/claude-agent-sdk-python-skill/releases) [![Stars](https://img.shields.io/github/stars/efacsen/claude-agent-sdk-python-skill?style=flat-square)](https://github.com/efacsen/claude-agent-sdk-python-skill/stargazers)

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

## Repo layout

```
.claude-plugin/   plugin + marketplace manifests
commands/         four slash command definitions
skills/           SKILL.md routing brain + references + checklists + templates
scripts/          refresh_docs.py (docs snapshot refresher)
tests/            pytest suite + acceptance suite + fixtures
```

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for development setup, how to run tests, and how to refresh the docs snapshot.

## License

MIT — see [LICENSE](./LICENSE).

## Changelog

See [CHANGELOG.md](./CHANGELOG.md).

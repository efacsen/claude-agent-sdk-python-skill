# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Removed sedimentary development artifacts (initial implementation plan, design spec) that had already drifted from the code
- Added `CONTRIBUTING.md` with dev setup, test instructions, and docs refresh workflow

## [0.1.0] - 2026-04-09

Initial release.

### Added
- `SKILL.md` routing brain with 6-branch decision tree, framing questions, four-gate generation protocol, freshness protocol, and 10 hard rules
- Four slash commands: `/agent-sdk:new`, `/agent-sdk:audit`, `/agent-sdk:explain`, `/agent-sdk:refresh`
- Four checklists (`mechanics`, `security`, `architecture`, `testing`) driving the audit command
- Seven templates covering every routing branch: one-shot query, interactive client, hooks, in-process MCP tools, subagents, session resume, tested agent with dependency-injected `query_fn`
- Curated reference snapshots of the Python Agent SDK docs under `skills/claude-agent-sdk-python/references/` (8 topic files with YAML frontmatter)
- `scripts/refresh_docs.py` — deterministic docs refresher that fetches the live reference, splits by H2/H3 headings, and atomic-writes topic files
- Single-plugin marketplace at `.claude-plugin/marketplace.json` for `/plugin marketplace add efacsen/claude-agent-sdk-python-skill`
- `pytest` suite under `tests/` (16 tests) + manual acceptance suite

[Unreleased]: https://github.com/efacsen/claude-agent-sdk-python-skill/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/efacsen/claude-agent-sdk-python-skill/releases/tag/v0.1.0

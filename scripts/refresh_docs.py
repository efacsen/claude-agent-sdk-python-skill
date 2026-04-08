#!/usr/bin/env python3
"""
refresh_docs.py — deterministic Python Agent SDK docs refresher.

Reads skills/claude-agent-sdk-python/references/sources.json, fetches each
source URL, converts HTML to Markdown, splits by H2 heading into topic files,
atomic-writes to disk, and updates sources.json.

Usage:
    python3 scripts/refresh_docs.py [--from-fixture PATH]

Flags:
    --from-fixture PATH   Use a local HTML file instead of fetching over HTTP.
                          Used by the test suite.

Exit codes:
    0  Success
    1  Fetch failure
    2  Parse failure (HTML structure unexpected)
    3  Disk write failure
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent
REFERENCES_DIR = REPO_ROOT / "skills" / "claude-agent-sdk-python" / "references"
SOURCES_JSON = REFERENCES_DIR / "sources.json"


@dataclass
class SourceEntry:
    file: str
    source_url: str
    section_anchors: list[str]
    last_fetched: str | None


def load_sources() -> list[SourceEntry]:
    data = json.loads(SOURCES_JSON.read_text())
    return [SourceEntry(**entry) for entry in data["files"]]


def save_sources(entries: list[SourceEntry]) -> None:
    SOURCES_JSON.write_text(json.dumps(
        {"version": "1", "files": [entry.__dict__ for entry in entries]},
        indent=2,
    ) + "\n")


def fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "claude-agent-sdk-python-skill/0.1"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def html_to_markdown(html: str) -> str:
    from markdownify import markdownify
    return markdownify(html, heading_style="ATX", code_language="python")


@dataclass
class Section:
    level: int  # 2 or 3
    heading: str
    body: str


def split_by_h2(markdown: str) -> list[Section]:
    """Split markdown into an ordered list of sections at H2 and H3 boundaries.

    The Python Agent SDK reference groups API names (query, ClaudeAgentOptions,
    HookMatcher, PreToolUse, ...) under H3s inside H2 category containers
    ("Functions", "Classes", "Hook Types", ...). We need both levels as
    addressable sections, AND we need to preserve their order so that matching
    an H2 can also pull in its H3 children via match_entry.
    """
    sections: list[Section] = []
    current_level = 0
    current_heading = "_preamble"
    buffer: list[str] = []

    def flush():
        if buffer:
            sections.append(
                Section(level=current_level, heading=current_heading, body="\n".join(buffer).strip())
            )

    for line in markdown.splitlines():
        if line.startswith("## "):
            flush()
            current_level = 2
            current_heading = line[3:].strip()
            buffer = [line]
        elif line.startswith("### "):
            flush()
            current_level = 3
            current_heading = line[4:].strip()
            buffer = [line]
        else:
            buffer.append(line)
    flush()
    return sections


def _anchor_matches(anchor: str, heading: str) -> bool:
    # Strip backticks and common punctuation so "query()" matches "`query()`"
    needle = anchor.lower().strip("` ")
    hay = heading.lower()
    return needle in hay


def match_entry(entry: SourceEntry, sections: list[Section]) -> str:
    """Pick sections whose headings contain any of the entry's anchors.

    When an H2 matches, also include every following H3 section up until the
    next H2. This gives us the full "category" block (e.g. matching "Hook Types"
    pulls in HookMatcher, HookContext, HookCallback, etc.).

    Dedupes by heading so an entry listing both an H2 and one of its H3
    children doesn't include the child twice.
    """
    matched: list[Section] = []
    seen: set[str] = set()
    for i, section in enumerate(sections):
        if not any(_anchor_matches(a, section.heading) for a in entry.section_anchors):
            continue
        if section.heading in seen:
            continue
        matched.append(section)
        seen.add(section.heading)
        # If this is an H2, also grab all the H3s under it
        if section.level == 2:
            j = i + 1
            while j < len(sections) and sections[j].level > 2:
                if sections[j].heading not in seen:
                    matched.append(sections[j])
                    seen.add(sections[j].heading)
                j += 1
    return "\n\n".join(s.body for s in matched).strip()


def build_reference_file(entry: SourceEntry, body: str, now: str) -> str:
    frontmatter = (
        "---\n"
        f"source_url: {entry.source_url}\n"
        f"last_fetched: {now}\n"
        f"topic: {entry.file.removesuffix('.md')}\n"
        "---\n\n"
    )
    return frontmatter + body + "\n"


def atomic_write(path: Path, content: str) -> None:
    tmp = path.with_suffix(path.suffix + ".new")
    tmp.write_text(content)
    os.replace(tmp, path)


def diff_summary(before: dict[str, int], after: dict[str, int]) -> str:
    lines = []
    for file, after_lines in sorted(after.items()):
        before_lines = before.get(file, 0)
        delta = after_lines - before_lines
        sign = "+" if delta > 0 else ""
        lines.append(f"  {file}: {before_lines} → {after_lines} ({sign}{delta})")
    return "\n".join(lines)


def run(fixture_path: Path | None = None) -> int:
    entries = load_sources()
    now = datetime.now(timezone.utc).isoformat()

    # Capture "before" line counts
    before = {
        e.file: (REFERENCES_DIR / e.file).read_text().count("\n") if (REFERENCES_DIR / e.file).exists() else 0
        for e in entries
    }

    # Group entries by source_url so we only fetch each URL once
    by_url: dict[str, list[SourceEntry]] = {}
    for entry in entries:
        by_url.setdefault(entry.source_url, []).append(entry)

    for url, url_entries in by_url.items():
        try:
            html = fixture_path.read_text() if fixture_path else fetch_html(url)
        except Exception as exc:
            print(f"FETCH FAIL {url}: {exc}", file=sys.stderr)
            return 1

        try:
            markdown = html_to_markdown(html)
            sections = split_by_h2(markdown)
        except Exception as exc:
            print(f"PARSE FAIL {url}: {exc}", file=sys.stderr)
            return 2

        for entry in url_entries:
            body = match_entry(entry, sections)
            if not body:
                body = "*(No matching sections found in the current snapshot.)*"
            content = build_reference_file(entry, body, now)
            try:
                atomic_write(REFERENCES_DIR / entry.file, content)
            except Exception as exc:
                print(f"WRITE FAIL {entry.file}: {exc}", file=sys.stderr)
                return 3
            entry.last_fetched = now

    save_sources(entries)

    after = {
        e.file: (REFERENCES_DIR / e.file).read_text().count("\n")
        for e in entries
    }
    print("Refresh complete.")
    print(diff_summary(before, after))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh the Python Agent SDK docs snapshot.")
    parser.add_argument(
        "--from-fixture",
        type=Path,
        default=None,
        help="Use a local HTML file instead of fetching over HTTP (for tests).",
    )
    args = parser.parse_args()
    return run(fixture_path=args.from_fixture)


if __name__ == "__main__":
    sys.exit(main())

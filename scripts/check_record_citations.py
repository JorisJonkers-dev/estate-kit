#!/usr/bin/env python3
"""Fail when a Markdown file cites a decision record by bare number.

AGENTS.md: cite a record by link, never by bare number. A bare "ADR 0012" or "record 12" cannot
be followed, and goes stale silently when a record is renumbered or superseded. Text inside a
link, an inline code span or a fenced code block is not a citation and is skipped.

    check_record_citations.py [FILE ...]   (default: every tracked *.md file)
"""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

BARE = re.compile(r"\b(?:ADR|record)[ -]?#?\d{1,4}\b", re.IGNORECASE)
LINK = re.compile(r"!?\[[^\]]*\]\([^)]*\)")
CODE_SPAN = re.compile(r"`[^`]*`")
FENCE = re.compile(r"^\s*(```|~~~)")


def findings(text: str) -> list[tuple[int, str]]:
    """Every bare citation in text, as (line number, citation)."""
    found = []
    fenced = False
    for number, line in enumerate(text.splitlines(), start=1):
        if FENCE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        prose = CODE_SPAN.sub("", LINK.sub("", line))
        found += [(number, match.group(0)) for match in BARE.finditer(prose)]
    return found


def tracked_markdown() -> list[Path]:
    out = subprocess.run(["git", "ls-files", "*.md"], check=True, capture_output=True, text=True).stdout
    return [Path(line) for line in out.splitlines()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check records are cited by link.")
    parser.add_argument("files", nargs="*", type=Path)
    args = parser.parse_args(argv)

    failures = 0
    for path in args.files or tracked_markdown():
        for number, citation in findings(path.read_text(encoding="utf-8")):
            print(f"::error file={path},line={number}::cites {citation!r} by bare number; link to the record instead")
            failures += 1
    if failures:
        return 1
    print("every record is cited by link")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

#!/usr/bin/env python3
"""Fail when the decision records break the register's rules.

docs/decisions/README.md: a record's status agrees with its register row; rests-on names rows that
exist and forms no cycle; an Accepted record rests only on Accepted ones; every lesson a record cites
exists and was kept in curation; and every Accepted row has a file. Locked counts as Accepted.
A row "Merged into N" has no file, nothing rests on it, and N is a row that is not merged itself.
A row "Moved to [page](link)" is retired: its rule lives on that page, so it has no file, is not
Accepted, and nothing rests on it.

    check_records.py [--decisions DIR] [--lessons FILE]
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

ROW = re.compile(r"^\| (\d+) \| .+ \| (\w+(?: into \d+| to \[[^\]]+\]\([^)]+\))?) \|$")
LESSON = re.compile(r"^\| ([A-Z]+-\d+) \| .+ \| (\w+) \|$")
RECORD_FILE = re.compile(r"^(\d{4})-.+\.md$")
ACCEPTED = {"accepted", "locked"}
MERGED = re.compile(r"^merged into (\d+)$")
MOVED = re.compile(r"^moved to \[")


@dataclass(frozen=True)
class Violation:
    key: str
    path: Path
    message: str


@dataclass(frozen=True)
class Record:
    number: int
    path: Path
    status: str
    rests_on: list[str]
    lessons: list[str]


def front_matter(text: str) -> dict[str, str]:
    """The key: value lines between the opening --- fences, comments stripped."""
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return {}
    fields = {}
    for line in lines[1:]:
        if line == "---":
            break
        key, _, value = line.partition(":")
        fields[key.strip()] = value.split("#")[0].strip()
    return fields


def items(value: str) -> list[str]:
    """The entries of a flow list such as [1, 2] or [CS-1, TM-4]."""
    return [item.strip() for item in value.strip("[]").split(",") if item.strip()]


def read_record(path: Path, number: int) -> Record:
    fields = front_matter(path.read_text(encoding="utf-8"))
    return Record(
        number=number,
        path=path,
        status=fields.get("status", ""),
        rests_on=items(fields.get("rests-on", "")),
        lessons=items(fields.get("lessons", "")),
    )


def cycles(edges: dict[int, list[int]]) -> list[list[int]]:
    """Each set of records that rest on one another, found as strongly connected components."""
    index: dict[int, int] = {}
    low: dict[int, int] = {}
    stack: list[int] = []
    found = []

    def visit(node: int) -> None:
        index[node] = low[node] = len(index)
        stack.append(node)
        for target in edges.get(node, []):
            if target not in index:
                visit(target)
                low[node] = min(low[node], low[target])
            elif target in stack:
                low[node] = min(low[node], index[target])
        if low[node] == index[node]:
            members = []
            while True:
                member = stack.pop()
                members.append(member)
                if member == node:
                    break
            if len(members) > 1 or node in edges.get(node, []):
                found.append(sorted(members))

    for node in sorted(edges):
        if node not in index:
            visit(node)
    return sorted(found)


def violations(decisions: Path, lessons_file: Path) -> list[Violation]:
    register = decisions / "register.md"
    rows = {}
    for line in register.read_text(encoding="utf-8").splitlines():
        if match := ROW.match(line):
            rows[int(match.group(1))] = match.group(2).lower()
    moved = {number for number, status in rows.items() if MOVED.match(status)}
    merged = {number: int(m.group(1)) for number, status in rows.items() if (m := MERGED.match(status))}
    lessons = {}
    for line in lessons_file.read_text(encoding="utf-8").splitlines():
        if match := LESSON.match(line):
            lessons[match.group(1)] = match.group(2)
    records = {}
    for path in sorted(decisions.iterdir()):
        if match := RECORD_FILE.match(path.name):
            record = read_record(path, int(match.group(1)))
            records[record.number] = record

    found = []
    edges: dict[int, list[int]] = {}
    for number, record in sorted(records.items()):
        if number not in rows:
            found.append(Violation(f"unregistered {number}", record.path, f"record {number} has no row in the register"))
        elif number in merged:
            found.append(Violation(
                f"merged-file {number}", record.path,
                f"row {number} is merged into {merged[number]}, so its file belongs in that record"))
        elif number in moved:
            found.append(Violation(
                f"moved-file {number}", record.path,
                f"row {number} is moved to a page, so it keeps no record file"))
        elif record.status != rows[number]:
            found.append(Violation(
                f"status {number}", record.path,
                f"front matter says {record.status or 'nothing'!r}, the register says {rows[number]!r}"))
        edges[number] = []
        for rest in record.rests_on:
            if not rest.isdigit() or int(rest) not in rows:
                found.append(Violation(f"unknown-rest {number} {rest}", record.path, f"rests on {rest}, which has no row"))
                continue
            target = int(rest)
            if target in merged:
                found.append(Violation(
                    f"rests-on-merged {number} {target}", record.path,
                    f"rests on {target}, which is merged into {merged[target]}; rest on {merged[target]}"))
                continue
            if target in moved:
                found.append(Violation(
                    f"rests-on-moved {number} {target}", record.path,
                    f"rests on {target}, which moved to a page; cite the page instead"))
                continue
            edges[number].append(target)
            if record.status in ACCEPTED and rows[target] not in ACCEPTED:
                found.append(Violation(
                    f"accepted-on-proposed {number} {target}", record.path,
                    f"an Accepted record rests on {target}, which is {rows[target]}"))
        for lesson in record.lessons:
            if lesson not in lessons:
                found.append(Violation(f"lesson {number} {lesson}", record.path, f"cites {lesson}, but there is no lesson {lesson}"))
            elif lessons[lesson] != "Keep":
                found.append(Violation(f"lesson {number} {lesson}", record.path, f"cites {lesson}, which curation dropped"))
    for members in cycles(edges):
        found.append(Violation(
            "cycle " + ",".join(map(str, members)), records[members[0]].path,
            "these records rest on one another: " + ", ".join(map(str, members))))
    for number, target in sorted(merged.items()):
        if target not in rows or target in merged:
            found.append(Violation(f"merged-target {number}", register, f"row {number} is merged into {target}, which is not a record"))
    for number, status in sorted(rows.items()):
        if status in ACCEPTED and number not in records:
            found.append(Violation(f"no-file {number}", register, f"row {number} is {status} but has no record file"))
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check the decision records keep the register's rules.")
    parser.add_argument("--decisions", type=Path, default=Path("docs/decisions"))
    parser.add_argument("--lessons", type=Path, default=Path("docs/lesson-candidates.md"))
    args = parser.parse_args(argv)

    found = violations(args.decisions, args.lessons)
    for violation in found:
        print(f"::error file={violation.path}::{violation.message} [{violation.key}]")
    if found:
        return 1
    print("the records keep the register's rules")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

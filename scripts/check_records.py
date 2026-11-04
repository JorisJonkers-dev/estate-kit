#!/usr/bin/env python3
"""Fail when the decision records break the register's rules.

docs/decisions/README.md: a record's status agrees with its register row; rests-on names rows that
exist and forms no cycle; an Accepted record rests only on Accepted ones; every lesson a record cites
exists and was kept in curation; and every Accepted row has a file. Locked counts as Accepted.
A row "Merged into N" has no file, nothing rests on it, and N is a row that is not merged itself.
A row "Superseded by N" keeps its file, whose status is superseded; N is Accepted, and nothing rests on
the superseded row. A row "Moved to [page](link)" is retired: its rule lives on that page, so it has no file, is not
Accepted, and nothing rests on it.
Every record file has a non-empty Confirmation, and each check it names, in bold, is a row of the
checks table on the design page (the first column of the table under "## The checks").
An Accepted or Locked record may declare in its front matter the records it amends (`amends`) and
supersedes (`supersedes`). Every amended record carries, directly under its title, a line
`Amended by [record M](...): <what changed>`; every superseded record's row reads
"Superseded by M" and its file says `status: superseded`. Proposed records are exempt.
The register's Enforcement column is derived from the table of checks: a record's Confirmation
names checks in bold; their statuses (planned, implemented, verified, retired) give the record's
enforcement (review if no check, otherwise the lowest status in the order planned < implemented < verified).
The Records check fails when a register row's Enforcement disagrees with this derivation.

    check_records.py [--decisions DIR] [--lessons FILE] [--checks FILE]
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

NUMBERED = re.compile(r"^\| (\d+) \|")
LESSON = re.compile(r"^\| ([A-Z]+-\d+) \| .+ \| (\w+) \|$")
RECORD_FILE = re.compile(r"^(\d{4})-.+\.md$")
ACCEPTED = {"accepted", "locked"}
MERGED = re.compile(r"^merged into (\d+)$")
MOVED = re.compile(r"^moved to \[")
SUPERSEDED = re.compile(r"^superseded by (\d+)$")
CHECK_NAME = re.compile(r"\*\*([^*]+)\*\*")
PENDING = re.compile(r"when\s+this\s+record\s+is\s+accepted", re.IGNORECASE)


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
    amends: list[str]
    supersedes: list[str]


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
        amends=items(fields.get("amends", "")),
        supersedes=items(fields.get("supersedes", "")),
    )


def backlinks(text: str) -> list[str]:
    """The back-link paragraphs directly under the title, one space-joined line each."""
    lines = text.splitlines()
    try:
        start = next(index for index, line in enumerate(lines) if line.startswith("# ")) + 1
    except StopIteration:
        return []
    paragraphs = []
    current: list[str] = []
    for line in [*lines[start:], ""]:
        if line.startswith("## "):
            break
        if line.strip():
            current.append(line)
        elif current:
            paragraphs.append(" ".join(" ".join(current).split()))
            current = []
    found = []
    for paragraph in paragraphs:
        if not re.match(r"^(Amended|Superseded) by \[record ", paragraph):
            break
        found.append(paragraph)
    return found


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


def confirmation(text: str) -> str:
    """The body of the `## Confirmation` section, up to the next `## ` heading; empty when absent."""
    body: list[str] = []
    inside = False
    for line in text.splitlines():
        if line.startswith("## "):
            if inside:
                break
            inside = line.strip() == "## Confirmation"
        elif inside:
            body.append(line)
    return "\n".join(body).strip()


def cells(line: str) -> list[str]:
    """The cells of one Markdown table row, trimmed; an empty cell stays an empty string."""
    body = line.strip().removeprefix("|").removesuffix("|")
    return [cell.strip() for cell in re.split(r"\s*\|\s*", body)]


SEPARATOR = re.compile(r"^\|[\s:|-]+$")


def register_rows(register: Path) -> tuple[dict[int, tuple[str, str]], bool]:
    """Each numbered row of the register as {number: (status, enforcement)}, read by the header's column names,
    and whether the header has a Status column.

    The header is the table row before the numbered rows. A register without an Enforcement column gives every
    row an empty enforcement."""
    rows: dict[int, tuple[str, str]] = {}
    header: list[str] = []
    for line in register.read_text(encoding="utf-8").splitlines():
        if NUMBERED.match(line):
            row = cells(line)
            status = header.index("Status") if "Status" in header else len(row)
            enforcement = header.index("Enforcement") if "Enforcement" in header else len(row)
            rows[int(row[0])] = (row[status] if status < len(row) else "", row[enforcement] if enforcement < len(row) else "")
        elif line.startswith("|") and not SEPARATOR.match(line) and not rows:
            header = cells(line)
    return rows, "Status" in header


def check_names(page: Path) -> dict[str, str] | None:
    """The first column of the table under `## The checks` mapped to its Status cell (first word, lowercased,
    punctuation stripped); None without a table or without a Status column in its header."""
    names: dict[str, str] | None = None
    status_column: int | None = None
    in_header = False
    inside = False
    for line in page.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            inside = line.strip() == "## The checks"
            in_header = inside
            status_column = None
        elif inside and line.startswith("|") and not SEPARATOR.match(line):
            row = cells(line)
            if in_header:
                status_column = row.index("Status") if "Status" in row else None
                in_header = False
            elif status_column is not None:
                words = row[status_column].split() if status_column < len(row) else []
                names = (names or {}) | {row[0].strip("`"): words[0].lower().rstrip(".,;:") if words else ""}
    return names


def enforcement_status(check_statuses: dict[str, str], check_names_in_confirmation: list[str]) -> str:
    """The lowest status of the live checks a record names (planned < implemented < verified); review when there is none.

    A check that is retired, missing from the table or has an unknown status holds nothing: the Records check
    reports the last two on their own."""
    order = {"planned": 0, "implemented": 1, "verified": 2}
    live = [check_statuses.get(name, "") for name in check_names_in_confirmation]
    known = [status for status in live if status in order]
    return min(known, key=order.__getitem__) if known else "review"


def violations(decisions: Path, lessons_file: Path, checks_page: Path) -> list[Violation]:
    register = decisions / "register.md"
    register_cells, has_status = register_rows(register)
    rows = {number: status.lower() for number, (status, _) in register_cells.items()}
    enforcement_rows = {number: enforcement.lower() for number, (_, enforcement) in register_cells.items()}
    moved = {number for number, status in rows.items() if MOVED.match(status)}
    merged = {number: int(m.group(1)) for number, status in rows.items() if (m := MERGED.match(status))}
    superseded = {number: int(m.group(1)) for number, status in rows.items() if (m := SUPERSEDED.match(status))}
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
    known = check_names(checks_page)
    if not has_status:
        found.append(Violation("no-register-status", register, "the register's header has no Status column"))
    if known is None:
        found.append(Violation("no-checks-table", checks_page, "the page has no table of checks with a Status column under '## The checks'"))
    # Validate check statuses
    if known is not None:
        for check_name, status in known.items():
            if status not in ("planned", "implemented", "verified", "retired"):
                found.append(Violation(f"check-status {check_name}", checks_page, f"check {check_name!r} has unknown status {status!r}"))
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
        elif number in superseded:
            if record.status != "superseded":
                found.append(Violation(
                    f"status {number}", record.path,
                    f"front matter says {record.status or 'nothing'!r}, the register says it is superseded"))
        elif record.status != rows[number]:
            found.append(Violation(
                f"status {number}", record.path,
                f"front matter says {record.status or 'nothing'!r}, the register says {rows[number]!r}"))
        text = record.path.read_text(encoding="utf-8")
        body = confirmation(text)
        if not body:
            found.append(Violation(f"no-confirmation {number}", record.path, "has no Confirmation, or an empty one"))
        named = list(dict.fromkeys(" ".join(m.group(1).split()).strip("`") for m in CHECK_NAME.finditer(body)))
        if record.status in ACCEPTED and PENDING.search(text):
            found.append(Violation(
                f"pending-on-accept {number}", record.path,
                "an Accepted record still promises a change 'when this record is accepted'; make it, and say what was done"))
        for name in named:
            if known is not None and name not in known:
                found.append(Violation(
                    f"unknown-check {number} {name}", record.path,
                    f"the Confirmation names {name!r}, which is not in the table of checks"))
        if known is not None and number in rows and number not in merged and number not in moved:
            derived = enforcement_status(known, named)
            cell = enforcement_rows.get(number, "")
            if cell != derived:
                found.append(Violation(
                    f"enforcement {number}", record.path,
                    f"row {number} says {cell or 'nothing'}; the table of checks gives {derived}"))
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
            if target in superseded:
                found.append(Violation(
                    f"rests-on-superseded {number} {target}", record.path,
                    f"rests on {target}, which is superseded by {superseded[target]}; rest on {superseded[target]}"))
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
        if record.status not in ACCEPTED:
            continue
        for target in record.amends:
            if not target.isdigit() or int(target) not in records:
                found.append(Violation(
                    f"amends-missing {number} {target}", record.path,
                    f"amends {target}, which has no record file"))
                continue
            amended = records[int(target)]
            if not any(
                re.match(rf"Amended by \[record {number}\]\([^)]+\):\s*\S", paragraph)
                for paragraph in backlinks(amended.path.read_text(encoding="utf-8"))
            ):
                found.append(Violation(
                    f"amends-no-backlink {number} {int(target)}", record.path,
                    f"amends {int(target)}, but {int(target)} has no "
                    f"'Amended by [record {number}](...)' line under its title"))
        for target in record.supersedes:
            if not target.isdigit():
                found.append(Violation(
                    f"supersedes-row {number} {target}", record.path,
                    f"supersedes {target}, which is not a record number"))
                continue
            old = records.get(int(target))
            if superseded.get(int(target)) != number or old is None or old.status != "superseded":
                found.append(Violation(
                    f"supersedes-row {number} {int(target)}", record.path,
                    f"supersedes {int(target)}, but its row does not read 'Superseded by {number}' "
                    "with a file whose status is superseded"))
    for members in cycles(edges):
        found.append(Violation(
            "cycle " + ",".join(map(str, members)), records[members[0]].path,
            "these records rest on one another: " + ", ".join(map(str, members))))
    for number, target in sorted(merged.items()):
        if target not in rows or target in merged:
            found.append(Violation(f"merged-target {number}", register, f"row {number} is merged into {target}, which is not a record"))
    for number, target in sorted(superseded.items()):
        if number not in records:
            found.append(Violation(f"superseded-no-file {number}", register, f"row {number} is superseded, so it keeps its record file"))
        if rows.get(target) not in ACCEPTED:
            found.append(Violation(
                f"superseded-target {number}", register,
                f"row {number} is superseded by {target}, which is not an Accepted record"))
    for number, status in sorted(rows.items()):
        if status in ACCEPTED and number not in records:
            found.append(Violation(f"no-file {number}", register, f"row {number} is {status} but has no record file"))
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check the decision records keep the register's rules.")
    parser.add_argument("--decisions", type=Path, default=Path("docs/decisions"))
    parser.add_argument("--lessons", type=Path, default=Path("docs/lesson-candidates.md"))
    parser.add_argument("--checks", type=Path, default=Path("docs/design/code-shape-and-speed.md"))
    args = parser.parse_args(argv)

    found = violations(args.decisions, args.lessons, args.checks)
    for violation in found:
        print(f"::error file={violation.path}::{violation.message} [{violation.key}]")
    if found:
        return 1
    print("the records keep the register's rules")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

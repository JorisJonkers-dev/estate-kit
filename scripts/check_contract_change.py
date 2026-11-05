#!/usr/bin/env python3
"""Fail when a pull request changes a Locked record or a Locked contract path without the `contract-change` label.

CONTEXT.md defines both. A Locked record is a record file whose status is locked on the base of the
pull request; a Locked contract path is a path under `contracts/` or `oracles/`, or the shadow's
expected-differences ledger. The label is the maintainer's approval: it is what the gate looks for,
and the repository lets only the maintainer apply it.

    check_contract_change.py --base REF [--labels JSON]

`--labels` defaults to the environment variable LABELS, a JSON list of the pull request's label names.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path

LABEL = "contract-change"
CONTRACT_PREFIXES = ("contracts/", "oracles/")
CONTRACT_FILES = ("shadow/expected-differences.yaml",)
RECORD = re.compile(r"^docs/decisions/\d{4}-.+\.md$")
FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
STATUS = re.compile(r"^status:\s*(\w+)", re.MULTILINE)


def git(root: Path, *args: str, must: bool = False) -> str:
    """The output of one git command. A failure reads as empty, unless `must`: then the gate cannot see the
    change, so it fails closed."""
    done = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)
    if done.returncode != 0 and must:
        raise SystemExit(f"::error::git {' '.join(args)} failed, so the gate cannot see the change: {done.stderr.strip()}")
    return done.stdout if done.returncode == 0 else ""


def is_contract_path(path: str) -> bool:
    return path.startswith(CONTRACT_PREFIXES) or path in CONTRACT_FILES


def is_locked_record(root: Path, base: str, path: str) -> bool:
    """Whether the record file had `status: locked` on the base; a new file was not Locked."""
    if not RECORD.match(path):
        return False
    head = FRONT_MATTER.match(git(root, "show", f"{base}:{path}"))
    match = STATUS.search(head.group(1)) if head else None
    return bool(match) and match.group(1) == "locked"


def locked_changes(root: Path, base: str) -> list[str]:
    """Each changed path that is a Locked contract path or a Locked record, one line saying which."""
    changed = git(root, "diff", "--name-only", "--no-renames", f"{base}...HEAD", must=True).splitlines()
    found = []
    for path in changed:
        if is_contract_path(path):
            found.append(f"{path} is a Locked contract path")
        elif is_locked_record(root, base, path):
            found.append(f"{path} is a Locked record")
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Refuse a change to a Locked path or record without the label.")
    parser.add_argument("--base", required=True, help="the ref the pull request merges into")
    parser.add_argument("--labels", default=os.environ.get("LABELS", "[]"), help="JSON list of the pull request's labels")
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args(argv)

    found = locked_changes(args.root, args.base)
    if found and LABEL not in json.loads(args.labels):
        for line in found:
            print(f"::error::{line}; the pull request needs the maintainer's `{LABEL}` label [contract-change]")
        return 1
    print("no Locked path or record changed without approval" if not found else f"the `{LABEL}` label approves {len(found)} Locked change(s)")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

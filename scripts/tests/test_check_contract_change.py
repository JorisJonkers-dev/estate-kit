from __future__ import annotations

import io
import json
import subprocess
import tempfile
import unittest
import unittest.mock
from contextlib import redirect_stdout
from pathlib import Path

from scripts.check_contract_change import is_contract_path, locked_changes, main

LOCKED = "---\nstatus: locked\n---\n\n# A record\n"
ACCEPTED = "---\nstatus: accepted\n---\n\n# A record\n"


class Repo:
    """A git repository on `main` with one commit, to change on a branch."""

    def __init__(self, case: unittest.TestCase) -> None:
        tmp = tempfile.TemporaryDirectory()
        case.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.git("init", "--quiet", "--initial-branch=main")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "Test")
        self.write("docs/decisions/0001-locked.md", LOCKED)
        self.write("docs/decisions/0002-accepted.md", ACCEPTED)
        self.write("README.md", "readme\n")
        self.commit("base")
        self.git("checkout", "--quiet", "-b", "change")

    def git(self, *args: str) -> None:
        subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True)

    def write(self, path: str, text: str) -> None:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    def commit(self, message: str) -> None:
        self.git("add", "--all")
        self.git("commit", "--quiet", "-m", message)

    def run(self, labels: list[str]) -> tuple[int, str]:
        out = io.StringIO()
        with redirect_stdout(out):
            code = main(["--base", "main", "--root", str(self.root), "--labels", json.dumps(labels)])
        return code, out.getvalue()


class ContractChangeTests(unittest.TestCase):
    def test_a_contract_path_changed_without_the_label_fails(self) -> None:
        repo = Repo(self)
        repo.write("contracts/openapi/delivery.yaml", "openapi: 3.1.0\n")
        repo.commit("change a contract")
        code, out = repo.run([])
        self.assertEqual(code, 1)
        self.assertIn("contracts/openapi/delivery.yaml is a Locked contract path", out)

    def test_a_contract_path_changed_with_the_label_passes(self) -> None:
        repo = Repo(self)
        repo.write("oracles/render/a.yaml", "a: 1\n")
        repo.commit("change an oracle")
        code, out = repo.run(["contract-change", "other"])
        self.assertEqual(code, 0)
        self.assertIn("approves 1 Locked change", out)

    def test_the_ledger_is_a_contract_path(self) -> None:
        self.assertTrue(is_contract_path("shadow/expected-differences.yaml"))
        self.assertFalse(is_contract_path("shadow/other.yaml"))
        self.assertFalse(is_contract_path("docs/design/contracts/x.md"))

    def test_a_locked_record_changed_without_the_label_fails(self) -> None:
        repo = Repo(self)
        repo.write("docs/decisions/0001-locked.md", LOCKED + "\nMore.\n")
        repo.commit("change a Locked record")
        code, out = repo.run([])
        self.assertEqual(code, 1)
        self.assertIn("0001-locked.md is a Locked record", out)

    def test_unlocking_a_record_counts_as_changing_it(self) -> None:
        repo = Repo(self)
        repo.write("docs/decisions/0001-locked.md", ACCEPTED)
        repo.commit("unlock")
        self.assertEqual(locked_changes(repo.root, "main"), ["docs/decisions/0001-locked.md is a Locked record"])

    def test_an_accepted_record_a_new_record_and_other_files_need_no_label(self) -> None:
        repo = Repo(self)
        repo.write("docs/decisions/0002-accepted.md", ACCEPTED + "\nMore.\n")
        repo.write("docs/decisions/0003-new.md", LOCKED)
        repo.write("README.md", "changed\n")
        repo.commit("ordinary changes")
        code, out = repo.run([])
        self.assertEqual(code, 0)
        self.assertIn("no Locked path or record changed", out)

    def test_a_record_with_no_status_is_not_locked(self) -> None:
        repo = Repo(self)
        repo.write("docs/decisions/0002-accepted.md", "# No front matter\n")
        repo.commit("drop the front matter")
        self.assertEqual(locked_changes(repo.root, "main"), [])

    def test_a_status_line_in_the_body_does_not_lock_a_record(self) -> None:
        repo = Repo(self)
        repo.git("checkout", "--quiet", "main")
        repo.write("docs/decisions/0002-accepted.md", ACCEPTED + "\nstatus: locked\n")
        repo.commit("body line on main")
        repo.git("checkout", "--quiet", "change")
        repo.git("merge", "--quiet", "main")
        repo.write("docs/decisions/0002-accepted.md", ACCEPTED + "\nedited\n")
        repo.commit("edit")
        self.assertEqual(locked_changes(repo.root, "main"), [])

    def test_moving_a_locked_record_away_still_counts(self) -> None:
        repo = Repo(self)
        repo.git("mv", "docs/decisions/0001-locked.md", "elsewhere.md")
        repo.commit("rename away")
        self.assertEqual(locked_changes(repo.root, "main"), ["docs/decisions/0001-locked.md is a Locked record"])

    def test_a_missing_base_fails_closed(self) -> None:
        repo = Repo(self)
        with self.assertRaises(SystemExit) as raised:
            locked_changes(repo.root, "origin/missing")
        self.assertIn("cannot see the change", str(raised.exception))

    def test_labels_come_from_the_environment_by_default(self) -> None:
        repo = Repo(self)
        repo.write("contracts/a.json", "{}\n")
        repo.commit("change a contract")
        out = io.StringIO()
        with redirect_stdout(out), unittest.mock.patch.dict("os.environ", {"LABELS": '["contract-change"]'}):
            code = main(["--base", "main", "--root", str(repo.root)])
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()

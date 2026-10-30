# Decision register

A brand-new register, numbered in reading order, and no number is ever
reused. A record may rest on any other, but what records rest on forms no
cycle, and an Accepted or Locked record rests only on Accepted or Locked ones.
Each record cites the lessons that motivate it, and only lessons that
curation kept (see [the lesson candidates](../lesson-candidates.md)). Records
follow [MADR](https://adr.github.io/madr/); start from
[`template.md`](template.md).

The Records job holds these rules, and that a record's status agrees with its
register row, that every Accepted row has a file, and that a Merged or Moved
row has none and nothing rests on it (`scripts/check_records.py`).

Every record has a non-empty Confirmation, and a Confirmation names each check
it relies on in bold, spelled as the first column of
[the table of checks](../design/code-shape-and-speed.md#the-checks) spells it.
The Records job fails on a bold name that is not a row. A new check is a new
row first, with its workstream issue; a rule no check can hold, such as a
review rule, is written without a bold name.

## Status

| Status | Meaning |
| --- | --- |
| Proposed | Written and open for review. Nothing may rely on it yet. |
| Accepted | Decided. Code follows it. |
| Locked | Accepted, and its Confirmation section names a check that fails when the decision is broken. Only the maintainer may change it. |
| Merged into N | Folded into record N, which now holds the decision. The number is never reused, and nothing rests on it. |
| Moved to page | Retired as a record: the page named in the row holds the rule. The number is never reused, nothing rests on it, and it has no file. |

A record changes status in its own pull request. A record that is Locked
without a working check is a defect.

## Writing order

The founding records are written once the candidate lessons are curated. The
planned list of records and their status is [`register.md`](register.md).
Each record's Alternatives table holds what was rejected, and why. The model's
own records (engines, grants, exposure and the rest) are rewritten after the cutover and take the numbers that follow.

## How records are kept

- **Decisions live as Markdown in `docs/`**, and a Pages site is built from it,
  so pull-request review and CI checks apply to every decision. A wiki as the
  source, or both edited, were rejected.
- **Records are read in order and cite their lessons.** A brand-new set in
  reading order, so the records read as one story; an imported register was
  rejected.
- **A record has a status.** Proposed, Accepted or Locked: a Locked record is an
  Accepted one whose Confirmation names a failing check, so agents stop and ask
  instead of working around it. Accepted only was rejected; readers should see
  the lock while tooling still parses the record.

## Rejected without a record

Options turned down that no record's Alternatives and no design page holds. The
older table of choices is retired: a choice lives in its record, or on the page
that states it.

| Option | Instead | Why |
| --- | --- | --- |
| CUE, KCL, Pkl, Nickel, Jsonnet or Dhall as the model's language; Timoni, Holos, cdk8s, Helm, kro or KubeVela as the packaging | Authored YAML and the estate's own compiler | The bespoke model wins on the [review's](../research/review/model-and-compiler.md) facts |
| Leptos or another Rust UI | Vue, npm confined to the UI build | Also in [record 13](0013-every-program-is-rust.md) |
| kured | A host applier on each node | Also in [record 30](0030-a-host-applier-on-each-node-pulls-its-signed-host-tag.md) |
| Go templates with htmx for the UI | Vue | Keeps the dashboard; no npm at runtime |
| An embedded estate snapshot, or a snapshot file, for offline validation | Project-local rules only | Deterministic, with no extra file |
| One environment name forever, or a staging environment now | A tag per environment, prod only | A second environment adds a tag |
| Manual Vault unseal; an OpenBao static seal | Cloud-KMS auto-unseal, decided in fleet-infra | A reboot must not stop signing ([record 59](0059-vault-unseal-and-datastore-backup-are-assumed-from-fleet-infra.md)) |
| Renaming deploy-kit, or importing without history | A fresh estate-kit with the three repositories imported with history | A clean product name, history kept; delivery and the dashboard are imported at creation too |
| A service config file; env files folded into Platform Intent | Platform Intent in a thin estate repository, toolchain config in estate-kit | Estate policy stays apart from tool code |
| A single or direct cutover | Shadow first, then a staged switch | Each step can be reverted |
| #373 tickets tracked in both repositories | Tracked in deploy-kit until the import, then in estate-kit | The rewrite happens where its tests live |
| Three components; one multi-command binary | Six components, one binary and image each | Each image carries only its own adapters |
| `anyhow` everywhere; one error type for the workspace | A `thiserror` enum per library crate, `anyhow` only in binaries | Callers match on the failures each crate designs |
| Go for the mail provisioner; keeping it in Python with jq and sh | Rust, talking to Stalwart's management API | One backend language |

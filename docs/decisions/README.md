# Decision register

A brand-new register, numbered in reading order, and no number is ever
reused. A record may rest on any other, but what records rest on forms no
cycle, and an Accepted or Locked record rests only on Accepted or Locked ones.
Each record cites the lessons that motivate it, and only lessons that
curation kept (see [the lesson candidates](../lesson-candidates.md)). Records
follow [MADR](https://adr.github.io/madr/); start from
[`template.md`](template.md).

The Records job holds these rules, and that a record's status agrees with its
register row, that every Accepted row has a file, that a Merged or Moved
row has none and nothing rests on it, that a Superseded row keeps its file and
names an Accepted record, and that an Accepted record's `amends` and
`supersedes` targets carry their back-links and rows, and that no Accepted record
still promises a change "when this record is accepted" (`scripts/check_records.py`),
and that records 82 and 110 state the Purge marker-first and
restore-does-not-un-purge rules.
The register's Enforcement column is derived from the table of checks and the Records job fails when it disagrees.

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
| Superseded by N | Replaced by record N, a later Accepted record that reverses or replaces the decision. The file stays, with `status: superseded` and a line under its title naming N, so the old reasoning can still be read. Nothing rests on it; rest on N. |
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
- **A record declares what it amends or supersedes.** Two optional front-matter
  fields, `amends: [N, ...]` and `supersedes: [N, ...]`, sit beside `rests-on`;
  a record whose prose says it "extends" another lists that one under `amends`.
  Each amended record carries, directly under its H1 and one line per amending
  record, `Amended by [record M](file): <one sentence of what changed>.` It
  keeps that line as history, and its body is edited to match. A superseded
  record keeps its "Superseded by" line and an unchanged body. A Proposed
  record may declare its targets, but nothing is applied until it is accepted.
  The Records job fails with `amends-no-backlink`, `amends-missing` or
  `supersedes-row` when an Accepted declaration is not carried into its target.

- **A wording fix is a dated Revised line; a change of rule is an amending
  record.** An Accepted record's wording (a typo, a clearer sentence, a
  corrected link) is edited in place under a line
  `Revised: YYYY-MM-DD: <what changed>` directly below its title. Anything that
  would make a conforming implementation pass or fail differently needs an
  amending record instead ([record 117](0117-a-wording-fix-is-a-dated-revised-line-a-change-of-rule-is-an-amending-record-and-a-locked-change-needs-the-contract-change-label.md)).
  The Records job fails a Revised line with no date or no sentence. It cannot
  see a silent edit, which leaves no line: review and the pull-request title
  rule catch it. A pull request that changes a Locked record or a Locked
  contract path needs the maintainer's `contract-change` label, and the
  Contract gate fails it without.

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
| Manual Vault unseal; an OpenBao static seal | Cloud-KMS auto-unseal, decided in fleet-infra | A reboot must not stop signing ([record 59](0059-vault-unseal-and-datastore-backup-are-assumed-from-fleet-infra.md)) |
| Renaming deploy-kit, or importing without history | A fresh estate-kit with the three repositories imported with history | A clean product name, history kept; delivery and the dashboard are imported at creation too |
| A service config file; env files folded into Platform Intent | Platform Intent in a thin estate repository, toolchain config in estate-kit | Estate policy stays apart from tool code |
| A single or direct cutover | Shadow first, then a staged switch | Each step can be reverted |
| #373 tickets tracked in both repositories | Tracked in deploy-kit until the import, then in estate-kit | The rewrite happens where its tests live |
| Three components; one multi-command binary | Six components, one binary and image each | Each image carries only its own adapters |
| `anyhow` everywhere; one error type for the workspace | A `thiserror` enum per library crate, `anyhow` only in binaries | Callers match on the failures each crate designs |
| Three repositories: `estate-model`, estate-kit and the host side | One repository at one version | The god-project worry sits in coupling and versioning, which contract majors and the layer check address; a split waits for a consumer outside the estate ([record 34](0034-every-part-of-estate-kit-lives-in-this-repository-at-one-version.md)) |
| A serverless host coordinator at Scaleway or OVHcloud that orders node updates from outside the cluster | A host applier on each node that may cordon and evict only its own node | One deployable and one provider fewer; no node holds a right over another ([record 30](0030-a-host-applier-on-each-node-pulls-its-signed-host-tag.md)) |
| Go for the mail provisioner; keeping it in Python with jq and sh | Rust, talking to Stalwart's management API | One backend language |

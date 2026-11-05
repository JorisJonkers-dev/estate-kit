---
status: accepted  # proposed | accepted | locked
date: 2026-10-30
rests-on: [18, 71]
lessons: [CS-6]
---

# Every committed schema evolves additively within a major version, checked in CI, and the CLI's JSON output has one that the reusable workflows read

Amended by [record 89](0089-every-persisted-or-externally-read-contract-has-its-own-identifier-contract-major-and-supported-range.md):
the major this record's rule speaks of is the CLI's JSON contract's own
Contract major, and a reader refuses a payload whose major falls outside its
supported range.

## Context

The estate's contracts are committed schemas, read by programs in other
repositories that pin a release. A contract that changes silently breaks its
readers, so how schemas change must be one rule, checked by a machine.

As first planned, this record held Delivery to committed `result.json`
fixtures, because Delivery read the compiler's output across a subprocess
seam. Delivery now links the compiler
([record 18](0018-delivery-links-the-compiler.md)), so it reads no file.
The CLI's JSON output still has readers: the reusable workflows turn it into
annotations, the check run, the job summary and the sticky PR comment
([Errors in CI](../design/errors-in-ci.md)), and they run in other
repositories against a pinned release.

## Decision

Every committed schema evolves additively within a major version, and CI checks
it. CI diffs each schema against the last release, classifies the change and
fails when the version bump disagrees; the rules for renames, deprecation and
breaks are on [Conventions](../design/conventions.md#contracts-and-their-evolution).

`estate-kit <command> --json` prints one document that validates against a
committed schema in `contracts/`. It carries the diagnostics with their
locations, the render diff, and each changed object's provenance. The schema
is one of those contracts and follows the same rule. Its major is the
contract's own, not the release's, and a workflow pinning a release refuses a
payload whose Contract major falls outside its supported range, with a coded
problem ([record 89](0089-every-persisted-or-externally-read-contract-has-its-own-identifier-contract-major-and-supported-range.md)).

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Schemas change freely between releases | Every consumer in another repository breaks without warning | Readers pin a release and need additive change |
| A convention, with no CI check | The rule holds until the first rushed change | A rule without a check is not kept |
| No schema; the workflows parse whatever the CLI prints | A CLI release can break every Project's workflow silently | The workflows are consumers in other repositories |
| Keep result.json consumer fixtures for Delivery | Fixtures for a reader that no longer exists | Delivery shares the types |
| SARIF | A second shape for diagnostics, and locations across repositories it cannot express | One shape, the catalogue's |

## Consequences

- Easier: the reusable workflows can rely on a stable document.
- Harder: a new field in the output is a schema change, and a break needs a
  major version and a record.
- Forbidden: a non-additive schema change inside a major version, and CLI
  JSON that does not validate against the committed schema.

## Confirmation

The **CLI schema fixtures** run the CLI over every example and refusal fixture
and validate its JSON output against the committed schema. The **Schema
evolution check** classifies
every change to every committed schema against the last release and fails when
the version bump disagrees.

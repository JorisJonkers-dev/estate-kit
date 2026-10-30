---
status: accepted  # proposed | accepted | locked
date: 2026-10-30
rests-on: [18, 71]
lessons: [CS-6]
---

# Every committed schema evolves additively within a major version, checked in CI, and the CLI's JSON output has one that the reusable workflows read

## Context

The estate's contracts are committed schemas, read by programs in other
repositories that pin a release. A contract that changes silently breaks its
readers, so how schemas change must be one rule, checked by a machine.

As first planned, this record held the service to committed `result.json`
fixtures, because the service read the compiler's output across a subprocess
seam. The service now links the compiler
([record 18](0018-the-service-links-the-compiler.md)), so it reads no file.
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
is one of those contracts and follows the same rule.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Schemas change freely between releases | Every consumer in another repository breaks without warning | Readers pin a release and need additive change |
| A convention, with no CI check | The rule holds until the first rushed change | A rule without a check is not kept |
| No schema; the workflows parse whatever the CLI prints | A CLI release can break every Project's workflow silently | The workflows are consumers in other repositories |
| Keep result.json consumer fixtures for the service | Fixtures for a reader that no longer exists | The service shares the types |
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

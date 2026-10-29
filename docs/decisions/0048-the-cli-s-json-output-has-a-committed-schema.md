---
status: accepted  # proposed | accepted | locked
date: 2026-10-29
rests-on: [18, 27, 47]
lessons: [CS-6]
---

# The CLI's JSON output has a committed schema that the reusable workflows read

## Context

As first planned, this record held the service to committed `result.json`
fixtures, because the service read the compiler's output across a subprocess
seam. The service now links the compiler
([record 18](0018-the-service-links-the-compiler.md)), so it reads no file.
The CLI's JSON output still has readers: the reusable workflows turn it into
annotations, the check run, the job summary and the sticky PR comment
([Errors in CI](../design/errors-in-ci.md)), and they run in other
repositories against a pinned release.

## Decision

`estate-kit <command> --json` prints one document that validates against a
committed schema in `contracts/`. It carries the diagnostics with their
locations, the render diff, and each changed object's provenance. The schema
evolves like every other contract: additive within a major version, checked
in CI ([record 47](register.md)).

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| No schema; the workflows parse whatever the CLI prints | A CLI release can break every Project's workflow silently | The workflows are consumers in other repositories |
| Keep result.json consumer fixtures for the service | Fixtures for a reader that no longer exists | The service shares the types |
| SARIF | A second shape for diagnostics, and locations across repositories it cannot express | One shape, the catalogue's |

## Consequences

- Easier: the reusable workflows can rely on a stable document.
- Harder: a new field in the output is a schema change.
- Forbidden: CLI JSON that does not validate against the committed schema.

## Confirmation

CI runs the CLI over every example and refusal fixture and validates its JSON
output against the committed schema, and the schema-evolution check
classifies every change to it.

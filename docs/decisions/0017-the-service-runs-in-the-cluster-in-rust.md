---
status: accepted  # proposed | accepted | locked
date: 2026-10-29
rests-on: [2, 9, 13, 18, 25]
lessons: [DO-1]
---

# The service runs in the cluster, in Rust: it composes, and Flux applies

## Context

Flux is the one applier ([record 2](register.md)), and the live render is a
signed registry tag per Project ([record 9](register.md)). Something must
compose the estate, dry-run it, sign each changed render and move its tag.
Every program is Rust ([record 13](0013-every-program-is-rust.md)), and the
service links the compiler ([record 18](0018-the-service-links-the-compiler.md)).
The record as first planned named Go; the language is now settled by [record 13](0013-every-program-is-rust.md).

## Decision

One service runs in the cluster, behind the edge. It composes every admitted
Project's fragment, dry-runs every change as its own identity, signs each
changed render with the [render signing key](../../CONTEXT.md) in Vault Transit, pushes it to ghcr and
moves the Project's tag by read, verify, write, fenced by the
[writer Lease](../../CONTEXT.md). It never applies anything: Flux
pulls the tags and applies. It also serves the UI and the Observation views.
It is the Rust binary `estate-kit-service`, built from the crates on
[The Rust workspace](../design/rust-workspace.md).

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| The service applies, replacing Flux | A second applier with its own drift and pruning | Flux is the one applier |
| CI composes and pushes; nothing runs in the cluster | Estate-wide checks race between Projects' pipelines; the dry-run needs cluster access from CI | One composition at a time needs one composer |
| Outside the cluster | A second place to run, secure and back up | The cluster already hosts Vault, Postgres and the edge |

## Consequences

- Easier: one place composes, so estate-wide checks never race.
- Harder: the service is on the deploy path; while it is down, nothing new
  deploys, though Flux keeps serving the last tags.
- Forbidden: a write by the service's identity without `dryRun` other than to
  its writer Lease, by its name, and to ProjectControl objects.

## Confirmation

The ValidatingAdmissionPolicy that refuses the service's writes without
`dryRun` has a refusing fixture and one allowing fixture for each of its two
exemptions ([record 58](0058-flux-is-locked-down-per-project-and-the-service-dry-runs-as-an-identity-that-cannot-write.md)), and the e2e suite asserts that an object
reaches the cluster only through Flux.

---
status: proposed  # proposed | accepted | locked
date: 2026-10-29
rests-on: [9, 25, 28]
lessons: [DO-7]
---

# A rollback moves the tag back to the last Serving render without composing

## Context

The first rollback re-composed, dry-ran, signed through Vault and moved the
tag, so the recovery path depended on the same parts that may be failing in an
incident. Every render that ever served is already signed, and Flux accepts a
tag moved back to it while its key is trusted
([review](../research/review/README.md) D7).

## Decision

A rollback dry-runs the Project's last Serving render against today's cluster,
moves `render/<project>:prod` back to it by compare-and-swap, and sets the
Project's `ProjectControl` to Paused ([record 28](0028-pause-and-rollback-are-a-cluster-object-per-project.md)).
It signs nothing and composes nothing, so it works with Vault down. Only if
that dry-run fails does it re-compose. Signatures are retained exactly as long
as their renders. A break-glass runbook covers the service, Vault and GitHub
all being down.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Re-compose only | Recovery depends on Vault and the compiler | The parts that may be failing |
| The service writes Flux's suspend and digest fields | A second writer of Flux objects | Flux objects have one writer |

## Consequences

- Easier: a rollback takes seconds and needs no signing.
- Harder: the old render carries old Platform Intent and ClusterState; the
  dry-run is what proves it still applies.
- Forbidden: deleting a signature while its render is retained.

## Confirmation

An e2e scenario scales Vault to zero and rolls a Project back to Serving.

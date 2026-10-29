---
status: proposed  # proposed | accepted | locked
date: 2026-10-29
rests-on: [7, 9, 17, 25, 63]
lessons: [DO-1]
---

# Pause and Rollback are a cluster object per Project; a missing object reads as Paused

## Context

Pause and Rollback were pin commits by workflows in the estate repository.
Without the estate pins, the state "this Project is paused, or held at render X"
needs a home. The cluster is the record of what runs, and a lost or unreadable
state must fail safe ([review](../research/review/README.md) D5, D7).

The first rollback re-composed, dry-ran, signed through Vault and moved the
tag, so the recovery path depended on the same parts that may be failing in an
incident. Every render that ever served is already signed, and Flux accepts a
tag moved back to it while its key is trusted. A rollback that read Vault for
the ghcr token, or Postgres for the last Serving render, would still fail with
those down.

## Decision

Each admitted Project has one `ProjectControl` custom resource in its own
namespace, written only by the service: whether it is Paused, and the render
it is held at after a Rollback. The service creates it when a Project is
admitted. Before any tag move, the service reads it; a missing or unreadable
object reads as Paused, so nothing deploys until the object is restored. It is
a custom resource, not a ConfigMap, so its schema is validated by the API
server and its RBAC can be granted to the service alone.

A Rollback uses that object and nothing else that may be down. It takes the
writer Lease ([record 63](0063-the-service-has-one-writer-and-reconciles-from-observed-state.md)
states the window), finds the Project's last Serving render from the registry,
not from Postgres or the event log, and dry-runs it against today's cluster.
It then moves `render/<project>:prod` back to that render by read, verify,
write (the tag is re-read after the write; a different value is a lost race)
and sets the Project's `ProjectControl` to Paused. It signs nothing and
composes nothing, and it reads no secret from Vault: the ghcr token is a
Kubernetes Secret that the Vault Secrets Operator syncs and the service mounts
([record 9](0009-the-live-render-is-a-signed-registry-tag-per-project-and-environment.md)).
So it needs only the API server and ghcr. Only if the dry-run fails is the
render composed again, which is a Deploy and waits for Vault. Signatures are
retained exactly as long as their renders. A break-glass runbook covers the
service, Vault and GitHub all being down.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| A row in the service's Postgres | Pause lives apart from what runs; a lost database un-pauses | The cluster is the record |
| Registry annotations | A second writer on the artifacts | Artifacts are signed and immutable |
| A ConfigMap | No schema; any namespace admin can edit it | A CRD validates and scopes |
| Re-compose on every rollback | Recovery depends on Vault and the compiler | The parts that may be failing |
| Find the last Serving render in Postgres or the event log | Recovery depends on the database being up and intact | The registry already holds every render that served |
| The service writes Flux's suspend and digest fields | A second writer of Flux objects | Flux objects have one writer |

## Consequences

- Easier: an operator can read a Project's state with `kubectl`; a lost
  object fails safe; a Rollback takes seconds and works with Vault down.
- Harder: one CRD to install and version with the platform; the old render
  carries old Platform Intent and ClusterState, so the dry-run is what proves
  it still applies.
- Forbidden: any writer of `ProjectControl` but the service; a Rollback step
  that reads Vault or Postgres; a Rollback that moves the tag without the
  writer Lease; deleting a signature while its render is retained.

## Confirmation

A service test deletes the object and asserts the next deploy is refused as
Paused; an admission policy fixture refuses a write from any other identity. An
end-to-end scenario seals Vault and rolls a Project back to Serving
([record 69](0069-the-deploy-path-is-tested-end-to-end.md)).

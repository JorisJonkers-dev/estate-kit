---
status: accepted  # proposed | accepted | locked
date: 2026-11-04
rests-on: [7, 9, 17, 25, 63]
lessons: [DO-1]
---

# Pause and Rollback are a cluster object per Project and Environment; a missing object reads as Paused

Amended by [record 97](0097-the-publication-point-is-named-and-tested-and-a-render-that-introduces-a-kind-is-published-in-two-stages.md): a Rollback's tag move is a Publication point, and it moves the Environment tag of the Environment rolled back, not only the Prod tag.

Amended by [record 101](0101-a-rollout-rolls-forward-when-rolling-back-would-run-a-migration-backwards.md): a Rollback is refused when the target render's migration preconditions do not hold and never runs a down migration; an Operator rolls forward instead.

Amended by [record 118](0118-a-rollback-is-per-environment-and-targets-a-digest-that-reached-serving.md): one ProjectControl per Project and Environment, `--env` required in every Environment, and a Rollback targets the digest `rollbackTo` names, which must have reached Serving in that Environment.

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

Each admitted Project has one `ProjectControl` custom resource per Environment,
in its own namespace and named by the Environment, written only by Delivery:
whether the Project is Paused there, the digest `rollbackTo` names while a
Rollback is running, and a monotone `lastServing`. Every read and write names
the Environment, so pausing or rolling a Project back in one Environment
changes nothing in any other ([record 118](0118-a-rollback-is-per-environment-and-targets-a-digest-that-reached-serving.md)).
Delivery creates one for each Environment when a Project is admitted. Before
any tag move, Delivery reads the Environment's object; a missing or unreadable
object reads as Paused, so nothing deploys until the object is restored. It is
a custom resource, not a ConfigMap, so its schema is validated by the API
server and its RBAC can be granted to Delivery alone.

A Rollback uses that object and nothing else that may be down. It targets the
digest `rollbackTo` names, which must have reached Serving in that
Environment; the CLI and the API refuse any other, so never a render that was
published and never served, and its command names the Environment (`--env`,
required in every Environment; an omitted one is refused)
([record 118](0118-a-rollback-is-per-environment-and-targets-a-digest-that-reached-serving.md)).
Delivery writes Paused and the target to `rollbackTo` in one update before it
moves anything, and clears `rollbackTo` when the move is done. It takes the
writer Lease ([record 63](0063-delivery-has-one-writer-and-reconciles-from-observed-state.md)
states the window), reads the migration record `migration-run`
keeps, and dry-runs the target against today's cluster: if the target render's
migration preconditions do not hold, the Rollback is refused, and a Rollback
never runs a down migration; an Operator rolls forward instead
([record 101](0101-a-rollout-rolls-forward-when-rolling-back-would-run-a-migration-backwards.md)).
It then moves the [Environment tag](../../CONTEXT.md)
of the Environment rolled back (`render/<project>:<env>`) to that digest by read, verify,
write (the tag is re-read after the write; a different value is a lost race), a
move that is the Rollback's Publication point
([record 97](0097-the-publication-point-is-named-and-tested-and-a-render-that-introduces-a-kind-is-published-in-two-stages.md)),
and sets that Environment's `ProjectControl` to Paused. The Release Gate
answers pass for the target digest, so no Analysis verdict holds the Rollback
([record 118](0118-a-rollback-is-per-environment-and-targets-a-digest-that-reached-serving.md)).
It signs nothing and
composes nothing, and it reads no secret from Vault: the ghcr token is a
Kubernetes Secret that the Vault Secrets Operator syncs and Delivery mounts
([record 9](0009-the-live-render-is-a-signed-registry-tag-per-project-and-environment.md)).
So it needs only the API server and ghcr. A restarted Delivery finishes
any ProjectControl still carrying `rollbackTo`, from the object and the
registry ([record 118](0118-a-rollback-is-per-environment-and-targets-a-digest-that-reached-serving.md)).
Only if the dry-run fails is the
render composed again, which is a Deploy and waits for Vault. Signatures are
retained exactly as long as their renders. A break-glass runbook covers Delivery, Vault and GitHub all being down.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| A row in Delivery's Postgres | Pause lives apart from what runs; a lost database un-pauses | The cluster is the record |
| Registry annotations | A second writer on the artifacts | Artifacts are signed and immutable |
| A ConfigMap | No schema; any namespace admin can edit it | A CRD validates and scopes |
| Re-compose on every rollback | Recovery depends on Vault and the compiler | The parts that may be failing |
| Find the last Serving render in Postgres or the event log | Recovery depends on the database being up and intact | The registry already holds every render that served |
| Delivery writes Flux's suspend and digest fields | A second writer of Flux objects | Flux objects have one writer |

## Consequences

- Easier: an operator can read a Project's state with `kubectl`; a lost
  object fails safe; a Rollback takes seconds and works with Vault down.
- Harder: one CRD to install and version with the platform; the old render
  carries old Platform Intent and ClusterState, so the dry-run is what proves
  it still applies.
- Forbidden: any writer of `ProjectControl` but Delivery; a Rollback step
  that reads Vault or Postgres; a Rollback that moves the tag without the
  writer Lease; deleting a signature while its render is retained; a Pause,
  Resume or Rollback command that omits its Environment; a Rollback to a
  digest that never reached Serving in its Environment.

## Confirmation

The **Pause refusal test** deletes the object and asserts the next deploy is
refused as Paused; the **ProjectControl admission fixtures** refuse a write from
any other identity; the **Rollback target test** refuses a Rollback whose target
never reached Serving in its Environment, and a Pause, Resume or Rollback call
without its Environment. A scenario of the **E2E scenarios** seals Vault and rolls a Project back to Serving, and another
stops platform-postgres and does the same
([record 69](0069-the-deploy-path-is-tested-end-to-end.md)).

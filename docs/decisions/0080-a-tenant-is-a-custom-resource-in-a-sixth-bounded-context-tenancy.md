---
status: accepted  # proposed | accepted | locked
date: 2026-11-01
rests-on: [17, 23, 50, 63, 76, 78, 79]
lessons: [DO-2, CS-3, TM-4]
---

# A Tenant is a custom resource that platform components reconcile, with Tenant hooks and finalizers, in a sixth bounded context, tenancy

## Context

[Record 76](0076-tenants-are-the-organisations-the-estate-serves.md) makes the
Tenant a thing the estate serves, [record 78](0078-a-multi-tenant-project-keeps-one-tenant-database-per-tenant.md)
gives each multi-tenant Project a Tenant database per Tenant, and
[record 79](0079-the-tenant-of-a-request-comes-only-from-the-signed-principal.md)
says every request names one Tenant. Nothing yet says where a Tenant lives,
who may change it, or how a Purge knows that every system has let go of the
Tenant's data. Adding, locking, moving or removing a Tenant touches the
database catalog, identity, the mailbox, backups and secret grants, and a
crash halfway must leave something to finish, not to repair.

[Record 63](0063-the-service-has-one-writer-and-reconciles-from-observed-state.md)
gives the estate-kit service the one write path to the cluster, and
[record 23](0023-a-rollout-is-an-append-only-event-log-on-the-shared-postgres.md)
keeps a rollout as an append-only log on the shared platform-postgres.
[Record 50](0050-five-bounded-contexts.md) names five bounded contexts, none of
which owns the lifecycle of a Tenant. [Record 17](0017-the-service-runs-in-the-cluster-in-rust.md)
puts the service in the cluster, where a custom resource and its reconcilers
are native.

## Decision

A Tenant is a custom resource, one per Tenant in its Environment. Only the
estate-kit service writes it, under the one-writer rule of
[record 63](0063-the-service-has-one-writer-and-reconciles-from-observed-state.md).
The platform components that hold the Tenant's data (database-catalog,
identity, mailbox, backup and secret-grant) reconcile it, and each holds a
finalizer on it. A Purge completes only when every participant has cleaned up
and released its finalizer, so a Tenant is never half-purged without the
maintainer knowing.

A sixth bounded context, tenancy, holds the Tenant model and the Tenant
operations: create, add a Project, remove a Project, lock, unlock, suspend,
resume, purge and move. This amends
[record 50](0050-five-bounded-contexts.md): the workspace is six contexts, and
the rest of that record, the layers and the check that holds them, stands. The
tenancy context talks to the others through the same kinds of edge, and
`crates/layers.toml` stays the one place the allowed edges are written.

Every Tenant operation is idempotent and safe to retry. Each step, with its
full error output, goes to an append-only operation log on the shared
platform-postgres, in the manner of
[record 23](0023-a-rollout-is-an-append-only-event-log-on-the-shared-postgres.md).
The operation log is kept 400 days, like the other history. The lifecycle API is
part of the service's OpenAPI contract. The maintainer calls it from the estate
UI or CLI, and a product's sign-up flow calls it with a machine identity.
Operator and Admin roles for the lifecycle API come from identity groups, as
they do today. A Tenant's resources live in an environment-scoped namespace.

A multi-tenant Application takes part through the Tenant hooks it declares:
after-create, lock, unlock, prepare-restore and after-restore. The tenancy
context calls a hook over HTTP with a signed machine token, the Tenant key and
an operation id. A failed lock or prepare-restore hook aborts the operation
before any data changes. A failed after hook flags the Tenant and the
operation log. A hook call has a timeout and retries, and an undeclared hook counts as a no-op
success. An Application implements only the hooks it declares.

During a Tenant lock the Gate serves a standard maintenance page and a 503
with a Retry-After header, and the shared libraries hold the Tenant's work. The Tenant's Valkey keys can be
flushed centrally while the lock holds.
Ending a Tenant is Suspend, then a grace period of 30 days, then Purge. A Tenant is Active,
under a Tenant lock, Suspended or purged; the diagram on the design page
shows the moves.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Tenants as rows in the service's Postgres only | Each component polls or is called by the service, and a crash leaves no object that says what remains | A custom resource gives each component one object to reconcile and a finalizer to hold; the operation log still records the history |
| A Tenant created by any component or by a sign-up flow directly | Two writers of one Tenant; a sign-up flow holds cluster credentials | One writer ([record 63](0063-the-service-has-one-writer-and-reconciles-from-observed-state.md)); the sign-up flow calls the service's API |
| Purge as one service call that deletes everywhere | A component that fails leaves its data behind with nothing to show it | Finalizers make a Purge complete only when every participant has finished |
| Tenancy inside the Service context | The lifecycle and the rollout core share one model and one change rate | A separate context keeps the Tenant model and its deciders apart, with its own crates and edges |
| Hooks as a message on RabbitMQ | A lock cannot abort on failure; an Application needs a consumer | A hook must answer before data changes, so it is a call with a result |
| Hooks every Application must implement | Each Application codes steps it has no use for | An Application implements only the hooks it declares |

## Consequences

- Easier: one object shows a Tenant's state; a Purge cannot finish early; a
  crash during an operation is finished by retrying it; a sign-up flow needs no
  second lifecycle.
- Harder: the custom resource definition is a contract that each reconciling
  component follows; five components each carry a finalizer and must release
  it correctly; the service gains a context, a log table and an API surface.
- [Record 50](0050-five-bounded-contexts.md) is amended: its five contexts are now six, with tenancy as the sixth.
- Forbidden: any writer of a Tenant other than the service; a Purge that
  completes while a finalizer remains; a lock or prepare-restore that changes
  data after its hook failed; an update or delete of an operation log row.

## Confirmation

The **Tenant finalizer Purge** check shows a Purge that completes only after
every participant has released its finalizer. The **Tenant hook abort** check
shows that a failed lock or prepare-restore hook stops the operation before any
data changes. The **Tenant one writer** check shows that no identity other than
the service's can write a Tenant. The **Operation log append-only** check shows
that an update or delete of an operation log row is refused. The **Tenant lock
page test** shows that the Gate serves the standard maintenance page to browsers
and a 503 with Retry-After to API clients while a Tenant is under a Tenant lock. The
**Purge grace test** shows that a Suspended Tenant is purged 30 days after it
was suspended, and not before, unless it is resumed. The
**`cargo xtask check-layers`** check holds the tenancy context to its allowed
edges.

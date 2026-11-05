---
status: accepted  # proposed | accepted | locked
date: 2026-11-01
rests-on: [17, 23, 50, 63, 76, 79, 114]
amends: [50]
lessons: [DO-2, CS-3, TM-4]
---

# A Tenant is a custom resource that platform components reconcile, with Tenant hooks and finalizers, in a sixth bounded context, tenancy

Amended by [record 114](0114-multi-tenant-projects-keep-their-tenants-in-shared-tables-separated-by-row-level-security.md):
a Tenant's data sits in shared tables, so no Tenant moves between servers and
database-catalog holds no finalizer; a restore deletes the Tenant's rows and
re-inserts them. The text below says so.

Amended by [record 110](0110-a-purge-erases-backup-generations-and-mirrors-from-an-inventory-of-every-copy.md):
a Purge works from a copy inventory of every copy that holds the Tenant's data
and states its erasure date. The text below says so.

Amended by [record 129](0129-the-estate-is-a-processor-record-80-gains-a-tenant-export-hook-and-the-erasure-date-is-stated-to-the-tenant.md):
the estate is a processor, the Tenant hooks gain export, and the erasure date
is stated to the Tenant. The text below says so.

## Context

[Record 76](0076-tenants-are-the-organisations-the-estate-serves.md) makes the
Tenant a thing the estate serves, [record 114](0114-multi-tenant-projects-keep-their-tenants-in-shared-tables-separated-by-row-level-security.md)
keeps each multi-tenant Project's Tenants in shared tables, and
[record 79](0079-the-tenant-of-a-request-comes-only-from-the-signed-principal.md)
says every request names one Tenant. Nothing yet says where a Tenant lives,
who may change it, or how a Purge knows that every system has let go of the
Tenant's data. Adding, locking, restoring or removing a Tenant touches the
Project databases, identity, the mailbox, backups and secret grants, and a
crash halfway must leave something to finish, not to repair.

[Record 63](0063-delivery-has-one-writer-and-reconciles-from-observed-state.md)
gives Delivery the one write path to the cluster, and
[record 23](0023-a-rollout-is-an-append-only-event-log-on-the-shared-postgres.md)
keeps a rollout as an append-only log on the shared platform-postgres.
[Record 50](0050-six-bounded-contexts-in-five-layers.md) names five bounded contexts, none of
which owns the lifecycle of a Tenant. [Record 17](0017-delivery-runs-in-the-cluster-in-rust.md)
puts Delivery in the cluster, where a custom resource and its reconcilers
are native.

## Decision

A Tenant is a custom resource, one per Tenant in its Environment. Only the
Delivery writes it, under the one-writer rule of
[record 63](0063-delivery-has-one-writer-and-reconciles-from-observed-state.md).
The platform components that hold the Tenant's data (identity, mailbox,
backup and secret-grant) reconcile it, and each holds a finalizer on it. A
Tenant has no database of its own, so database-catalog does not reconcile it.
The backup component, which uses each Project's owner role
([record 114](0114-multi-tenant-projects-keep-their-tenants-in-shared-tables-separated-by-row-level-security.md)), deletes the
Tenant's rows from a Project database when the Tenant leaves that Project or is
purged. A Purge completes only when every participant has cleaned up
and released its finalizer, so a Tenant is never half-purged without the
maintainer knowing. Its entry in the operation log states the erasure date, the
expiry of the last copy in the copy inventory of
[record 110](0110-a-purge-erases-backup-generations-and-mirrors-from-an-inventory-of-every-copy.md),
and the Tenant is told the date, which is the end of six months of
whole-database retention
([record 129](0129-the-estate-is-a-processor-record-80-gains-a-tenant-export-hook-and-the-erasure-date-is-stated-to-the-tenant.md)).

A sixth bounded context, tenancy, holds the Tenant model and the Tenant
operations: create, add a Project, remove a Project, lock, unlock, suspend,
resume, restore, export and purge. This amends
[record 50](0050-six-bounded-contexts-in-five-layers.md): the workspace is six contexts, and
the rest of that record, the layers and the check that holds them, stands. The
tenancy context talks to the others through the same kinds of edge, and
`crates/layers.toml` stays the one place the allowed edges are written. No
Tenant moves between Postgres servers.

Every Tenant operation is idempotent and safe to retry. Each step, with its
full error output, goes to an append-only operation log on the shared
platform-postgres, in the manner of
[record 23](0023-a-rollout-is-an-append-only-event-log-on-the-shared-postgres.md).
The operation log is kept 400 days, like the other history. The lifecycle API is
part of Delivery's OpenAPI contract. The maintainer calls it from the estate
UI or CLI, and a product's sign-up flow calls it with a machine identity.
Operator and Admin roles for the lifecycle API come from identity groups, as
they do today. A Tenant's resources live in an environment-scoped namespace.

A multi-tenant Application takes part through the Tenant hooks it declares:
after-create, lock, unlock, prepare-restore, after-restore and export. The
tenancy context calls a hook over HTTP with a signed machine token, the Tenant key and
an operation id. A failed lock or prepare-restore hook aborts the operation
before any data changes. A failed after hook flags the Tenant and the
operation log. A hook call has a timeout and retries, and an undeclared hook counts as a no-op
success. An Application implements only the hooks it declares. The estate is a
processor of a Tenant's people's data, so a Tenant may ask for its data: the
tenancy context exports one export per Project database that holds the
Tenant's rows,
[record 82](0082-backups-are-per-tenant-generations-and-mirrors-refresh-staging-and-development.md)
says how, and calls each Application's export hook, so the Application hands
over the data it keeps where the platform cannot see it. Tenant exports are
signed after the first Mirror has run
([record 129](0129-the-estate-is-a-processor-record-80-gains-a-tenant-export-hook-and-the-erasure-date-is-stated-to-the-tenant.md)).

During a Tenant lock the Gate serves a standard maintenance page and a 503
with a Retry-After header, and the shared libraries hold the Tenant's work. The Tenant's Valkey keys can be
flushed centrally while the lock holds.
A restore of one Tenant locks the Tenant, calls the prepare-restore hooks,
then, in each Project the restore names, deletes the Tenant's rows and
re-inserts them from its Tenant export, calls the after-restore hooks and
unlocks.
[Record 82](0082-backups-are-per-tenant-generations-and-mirrors-refresh-staging-and-development.md)
says which exports may be restored and how.

Ending a Tenant is Suspend, then a grace period of 30 days, then Purge. A Tenant is Active,
under a Tenant lock, Suspended or purged; the diagram on the design page
shows the moves.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Tenants as rows in Delivery's Postgres only | Each component polls or is called by Delivery, and a crash leaves no object that says what remains | A custom resource gives each component one object to reconcile and a finalizer to hold; the operation log still records the history |
| A Tenant created by any component or by a sign-up flow directly | Two writers of one Tenant; a sign-up flow holds cluster credentials | One writer ([record 63](0063-delivery-has-one-writer-and-reconciles-from-observed-state.md)); the sign-up flow calls Delivery's API |
| Purge as one service call that deletes everywhere | A component that fails leaves its data behind with nothing to show it | Finalizers make a Purge complete only when every participant has finished |
| Tenancy inside Delivery context | The lifecycle and the rollout core share one model and one change rate | A separate context keeps the Tenant model and its deciders apart, with its own crates and edges |
| Hooks as a message on RabbitMQ | A lock cannot abort on failure; an Application needs a consumer | A hook must answer before data changes, so it is a call with a result |
| Hooks every Application must implement | Each Application codes steps it has no use for | An Application implements only the hooks it declares |

## Consequences

- Easier: one object shows a Tenant's state; a Purge cannot finish early; a
  crash during an operation is finished by retrying it; a sign-up flow needs no
  second lifecycle.
- Harder: the custom resource definition is a contract that each reconciling
  component follows; four components each carry a finalizer and must release
  it correctly; Delivery gains a context, a log table and an API surface.
- [Record 50](0050-six-bounded-contexts-in-five-layers.md) is amended: its five contexts are now six, with tenancy as the sixth.
- Forbidden: any writer of a Tenant other than Delivery; a Purge that
  completes while a finalizer remains; a lock or prepare-restore that changes
  data after its hook failed; an update or delete of an operation log row.

## Confirmation

The **Tenant finalizer Purge** check shows a Purge that completes only after
every participant has released its finalizer. The **Tenant hook abort** check
shows that a failed lock or prepare-restore hook stops the operation before any
data changes. The **Tenant one writer** check shows that no identity other than
Delivery's can write a Tenant. The **Operation log append-only** check shows
that an update or delete of an operation log row is refused. The **Tenant lock
page test** shows that the Gate serves the standard maintenance page to browsers
and a 503 with Retry-After to API clients while a Tenant is under a Tenant lock. The
**Purge grace test** shows that a Suspended Tenant is purged 30 days after it
was suspended, and not before, unless it is resumed. The
**Tenant export hook check** shows that an export handed to a Tenant omits no
Project database that holds its rows, a failed export hook flags the Tenant
and enters the operation log, and an export handed over after the first
Mirror is signed. The
**Erasure date test** shows that the Tenant is told its erasure date. The
**`cargo xtask check-layers`** check holds the tenancy context to its allowed
edges.

---
status: accepted  # proposed | accepted | locked | superseded
date: 2026-11-04
rests-on: [74, 75, 76, 79]
lessons: [MS-7, DR-2, TM-4]
---

# Multi-tenant Projects keep their Tenants in shared tables, separated by row-level security

## Context

[Record 78](0078-a-multi-tenant-project-keeps-one-tenant-database-per-tenant.md)
gave each multi-tenant Project one database per Tenant, on a Postgres server
recorded with the Tenant, against the advice of the
[research](../research/multi-tenancy.md#1-data-isolation-on-postgres). None of
it is built yet. The research states these facts:

- With a database per Tenant, a connection reaches one database, PgBouncer keeps
  one pool per database and user pair, each `CREATE DATABASE` copies about
  8 MB, and a migration runs once per database and again at each Tenant's
  creation. At 1000 Tenants and five multi-tenant Projects that is up to 5000
  production databases, each migrated, backed up and vacuumed on its own.
  [Record 81](0081-migrations-reach-tenant-databases-in-waves.md) needed
  Migration waves and a Behind state to run one revision across them.
- With shared tables, a migration runs once per table. A table with row-level
  security enabled is default-deny. Superusers and `BYPASSRLS` roles always
  bypass it, and a table's owner bypasses it unless the table has
  `FORCE ROW LEVEL SECURITY`.
- A transaction-local setting (`SET LOCAL`, or `set_config(..., true)`) lasts
  only for its transaction, so it is safe under transaction pooling. A session
  `SET` leaks to the next client of the same server connection.
- A Tenant's backup from shared tables is a copy of its rows, and its Purge a
  delete across every table keyed by the Tenant.

[Record 79](0079-the-tenant-of-a-request-comes-only-from-the-signed-principal.md)
already gives every request and message exactly one Tenant, taken only from the
Gate's signed Principal. The tenancy library
([issue 151](https://github.com/JorisJonkers-dev/estate-kit/issues/151),
workstream W12) carries that Tenant into each Application. The Release Gate
answers from cluster state and fails closed
([record 74](0074-the-release-gate-and-observation-each-have-a-named-write.md)),
and each Environment has its own data
([record 75](0075-three-environments-run-in-the-one-cluster.md)).

## Decision

This supersedes
[record 78](0078-a-multi-tenant-project-keeps-one-tenant-database-per-tenant.md)
and amends
[record 80](0080-a-tenant-is-a-custom-resource-in-a-sixth-bounded-context-tenancy.md),
[record 81](0081-migrations-reach-tenant-databases-in-waves.md) and
[record 82](0082-backups-are-per-tenant-generations-and-mirrors-refresh-staging-and-development.md),
which now say how a Tenant is reconciled, migrated and backed up on shared tables.

**Shared tables.** A multi-tenant Project keeps every Tenant's data in shared
tables. Each tenant-scoped table has a `tenant_id` column holding the Tenant
key, a row-level security policy on that column, and
`FORCE ROW LEVEL SECURITY`. Only a table the Project declares shared reference
data has none of the three. There is no database-per-Tenant tier.

**One database per Project per Environment.** A multi-tenant Project has one
database in each Environment, on that Environment's Postgres server, as a
single-tenant Project does. No Tenant moves between servers, and the Tenant
resource records no server. Sharding by `tenant_id` is a later record, written
only if one database cannot carry the load.

**The library sets the Tenant in every transaction.** The tenancy library runs
`SET LOCAL app.tenant_id = '<tenant key>'` in every transaction, from the
verified signed Principal of
[record 79](0079-the-tenant-of-a-request-comes-only-from-the-signed-principal.md),
and never sets it for a session. Each policy compares `tenant_id` with
`current_setting('app.tenant_id', true)`, so a transaction in which it is unset
matches no rows.

**Two kinds of role.** A per-Project owner role with `BYPASSRLS` owns the
tables. Only `migration-run` Jobs and the backup component use it: for DDL,
for backfills, and for per-Tenant exports and the restores and deletes built on
them. The Application roles have no `BYPASSRLS` and own no table. The role audit
allows exactly those two users of the owner role.

**Migrations run once per Project database.** A revision is expand/contract and
runs once per Project database per Environment. Migration waves and the Behind
state are dropped. Each revision runs in one transaction wherever Postgres
allows it, so a failure leaves the old schema. `migration-run`'s record marks
that Project database failed, and the Release Gate refuses further releases of
the Project in that Environment until an Operator retries the migration or rolls
forward. [Record 81](0081-migrations-reach-tenant-databases-in-waves.md) holds
the detail. Canary Tenants stay only as a targeting group for feature flags
inside Applications. Deploy canaries stay weight-based through Flagger.

**The other stores are unchanged from record 78:**

| Store | One per | The Tenant is kept apart by |
| --- | --- | --- |
| Postgres server | Environment | One database per Project, shared tables with `tenant_id` and row-level security |
| Valkey | Environment | Keys prefixed `<app>:<tenant key>:`, and one ACL user per Application limited to `<app>:*` |
| RabbitMQ | Environment, one vhost | Shared queues, with the Tenant key on each message |
| Garage | Project and Environment, one bucket | Each Tenant's objects under its key |

**Three leak checks hold the isolation.** A schema lint, a two-Tenant test per
Project, and a role audit, named below.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| A database per Tenant ([record 78](0078-a-multi-tenant-project-keeps-one-tenant-database-per-tenant.md)) | Up to 5000 production databases at 1000 Tenants, each about 8 MB empty, each with its own pool, migration, backup and vacuum; a recorded server and a move per Tenant | Reversed on 2026-11-04. Shared tables give one model to build, the same database shape as a single-tenant Project; a migration runs once per Project database, with no waves and no Behind state; and the cost no longer grows with the Tenant count |
| Shared tables for most Tenants and a database for a few | Two implementations, a pool and a silo, in every library, migration path and backup | One model; a silo tier waits for a later record |
| A schema per Tenant | Weak isolation, catalogs and lock tables that grow with the Tenant count, and a `search_path` that leaks under transaction pooling | The database enforces nothing, and the research counts the scaling costs |
| Isolation in application code only, with no row-level security | One missing `WHERE` leaks another Tenant's rows | The database enforces the policy, and the library cannot forget it |
| The Tenant set once per session or connection | Under transaction pooling the setting leaks to the next client | `SET LOCAL` lasts only for its transaction |
| Application roles that own the tables | An owner bypasses row-level security unless the table forces it | A separate owner role, used only by `migration-run` and backup, and `FORCE` on every table |
| Shard by `tenant_id` now | Routing, rebalancing and cross-shard migrations before any load needs them | A later record, only if one database cannot carry the load |

## Consequences

- Easier: a multi-tenant Project has one database per Environment, like any
  other; a revision runs once, and a Tenant's creation needs no database or
  migration; the number of databases, pools and backups does not grow with
  the Tenant count; a request with no Tenant set reads nothing.
- Harder: isolation rests on a policy and `FORCE` on every tenant-scoped table,
  so a missing one is a leak, and the three leak checks must run for every
  Project; a Tenant's backup, restore and Purge become row exports, copies and
  deletes; Tenants share one database's resources, which
  [the scale test](0109-a-row-level-security-scale-test-at-1000-tenants-runs-before-the-tenancy-machinery.md)
  measures.
- [Record 78](0078-a-multi-tenant-project-keeps-one-tenant-database-per-tenant.md)
  is superseded; [records 80](0080-a-tenant-is-a-custom-resource-in-a-sixth-bounded-context-tenancy.md),
  [81](0081-migrations-reach-tenant-databases-in-waves.md) and
  [82](0082-backups-are-per-tenant-generations-and-mirrors-refresh-staging-and-development.md)
  are amended.
- Forbidden: a database or schema per Tenant; a Tenant move between servers; a
  tenant-scoped table without `tenant_id`, its policy or `FORCE`; an
  Application role with `BYPASSRLS` or that owns a table; any user of the owner
  role but `migration-run` and backup; `app.tenant_id` set for a session, or
  from anything but the signed Principal; a release while a Project database is
  marked failed; a Valkey key without its prefix; a Tenant's object outside its
  key's prefix.

## Confirmation

The **Tenant table lint** fails when a table in a multi-tenant Project's
database lacks `tenant_id`, a policy on it or `FORCE ROW LEVEL SECURITY`, and
the Project has not declared it shared reference data. The **Two-Tenant leak
test** writes as one Tenant and reads as another in each Project, and fails when
the second sees anything, or when a transaction with `app.tenant_id` unset sees
any row. The **Tenant role audit** fails when an Application role has
`BYPASSRLS` or owns a table, or anyone but `migration-run` and backup uses the
owner role. The **Tenant transaction setting test** fails when the library
opens a transaction without `SET LOCAL app.tenant_id` from the signed
Principal, or sets it for a session. The **Failed migration release refusal**
fails when the Release Gate allows a release while the Project database is
marked failed. The **Valkey scope test**, the **Object prefix test** and the
**Environment store fixtures** hold the other stores.

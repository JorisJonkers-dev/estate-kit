---
status: proposed  # proposed | accepted | locked
date: 2026-11-01
rests-on: [74, 75, 78, 80]
lessons: [MS-3, TM-4]
---

# Migrations reach Tenant databases in waves that continue past failure, and a Behind database blocks the next release

## Context

[Record 78](0078-a-multi-tenant-project-keeps-one-tenant-database-per-tenant.md)
gives a multi-tenant Project one Tenant database per Tenant, so a migration
revision runs once per database, and once more when a Tenant is created. At more
than 1000 Tenants no one can watch each run, and one bad revision must not halt
every other Tenant's migration.

The expand/contract rule keeps a schema compatible with two adjacent versions of
a Project, no more. A Tenant database that missed a revision and then meets the
version after next has no such guarantee. So a database that failed must be
repaired before the Project moves on.

The `migration-run` component already runs a Project's managed migrations, `up`
and `down` per revision ([Mail and components](../design/mail-and-components.md#components)).
The Release Gate already holds named writes and a fail-closed answer
([record 74](0074-the-release-gate-and-observation-each-have-a-named-write.md)).
The Tenant resource and its operation log come from
[record 80](0080-a-tenant-is-a-custom-resource-in-a-sixth-bounded-context-tenancy.md),
and [record 75](0075-three-environments-run-in-the-one-cluster.md) gives each
Environment its own databases to migrate.

## Decision

A multi-tenant Project must declare a Liquibase changelog. The compiler refuses
`migration: self` and `migration: none` on a multi-tenant Project, because only a
managed migration can reach every Tenant database in turn.

The `migration-run` component runs each revision on every Tenant database of the
Project in an Environment, in Migration waves:

- In production, the first wave is the Project's Canary Tenants. The component
  starts the other waves only when that wave has run. The other waves run in
  parallel, up to a set width.
- In development and staging every Tenant database is in one wave.
- A failure does not stop the wave. The component marks that database Behind at
  its last good revision and writes the full output to the operation log
  ([record 80](0080-a-tenant-is-a-custom-resource-in-a-sixth-bounded-context-tenancy.md)).
  The Project's current version keeps serving a Behind database.
- A Tenant's Tenant resource marks whether it is a Canary Tenant. A Tenant
  created while a revision is pending receives every pending revision before it
  runs after-create.

The Release Gate refuses to start a new version of the Project in an Environment
while any of that Project's Tenant databases there is Behind. It answers from
cluster state and fails closed, as [record 74](0074-the-release-gate-and-observation-each-have-a-named-write.md)
requires, so the refusal is a read and adds no write to that record's table. A
database stops being Behind when a revision runs on it successfully: the
maintainer retries after the repair, and the component marks it current.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Stop the wave at the first failure | One Tenant's bad data holds back every other Tenant's migration | Failures are per database, and the rest should be migrated |
| Migrate every Tenant at once, with no Canary Tenants | A bad revision reaches every production Tenant before any failure shows | Canary Tenants show the failure on a few first |
| Migrate a Tenant database when its first request arrives | A request pays for a migration, and Tenants sit on different versions for long | The platform must know each database's revision and finish the work |
| Let a Project release while databases are Behind | A Tenant can fall two versions behind, past what expand/contract guarantees | The rule covers two adjacent versions only |
| Let a Project run `migration: self` and own its Tenant migrations | Each Project invents its own fan-out, with no Behind state and no shared log | One managed path gives one log and one Behind rule |
| Roll back every database when one fails | A rollback runs on databases that were fine, and may itself fail | A failure is kept as Behind and repaired on its own |

## Consequences

- Easier: one failing Tenant does not stop the others; a bad revision first shows
  on the Canary Tenants; the operation log holds each failure's full output; no
  Tenant database falls two versions behind its Project.
- Harder: one Behind database blocks a Project's releases in that Environment
  until it is repaired, so the maintainer must act on a Tenant's failure; the
  component must record each database's last good revision.
- Forbidden: `migration: self` or `migration: none` on a multi-tenant Project; a
  wave that stops at a failure; a release while a Tenant database in that
  Environment is Behind; a database marked Behind without its output in the
  operation log.

## Confirmation

The **Migration declaration refusal** fails when the compiler accepts
`migration: self` or `migration: none` on a multi-tenant Project. The **Migration
wave continuation test** fails when a failing database stops its wave or is not
marked Behind at its last good revision with its output in the operation log. The
**Canary wave order test** fails when a production revision reaches a Tenant
that is not a Canary Tenant before the Canary Tenants have run. The **Behind
release refusal** fails when the Release Gate allows a new version while a Tenant
database in that Environment is Behind, and it fails closed when the state
cannot be read. The expand/contract rule itself is a review rule, and no check
holds it.

---
status: accepted  # proposed | accepted | locked
date: 2026-11-01
rests-on: [74, 75, 80, 114]
lessons: [MS-3, TM-4]
---

# Migrations run once per Project database by expand and contract, a failed migration blocks the next release, and multi-tenant Projects use managed Liquibase migrations

Amended by [record 114](0114-multi-tenant-projects-keep-their-tenants-in-shared-tables-separated-by-row-level-security.md):
a multi-tenant Project keeps one database per Environment, so a revision runs
once per Project database by expand and contract. Migration waves and the Behind
state are dropped, a failed migration marks the Project database failed, and
Canary Tenants only target feature flags. The text below says so.

## Context

[Record 114](0114-multi-tenant-projects-keep-their-tenants-in-shared-tables-separated-by-row-level-security.md)
keeps every Tenant of a multi-tenant Project in shared tables, in one database
per Environment. A migration revision therefore runs once per Project database,
as it does for a single-tenant Project, whatever the number of Tenants.

The expand/contract rule keeps a schema compatible with two adjacent versions of
a Project, no more. A database that missed a revision and then meets the version
after next has no such guarantee, so a database whose migration failed must be
repaired before the Project moves on. Postgres runs most DDL inside a
transaction, so a revision that runs in one transaction and fails leaves the old
schema; a few statements, such as `CREATE INDEX CONCURRENTLY`, cannot run in one.

The `migration-run` component already runs a Project's managed migrations, `up`
and `down` per revision ([Mail and components](../design/mail-and-components.md#components)).
The Release Gate already holds named writes and a fail-closed answer
([record 74](0074-the-release-gate-and-observation-each-have-a-named-write.md)).
The Tenant resource comes from
[record 80](0080-a-tenant-is-a-custom-resource-in-a-sixth-bounded-context-tenancy.md),
and [record 75](0075-three-environments-run-in-the-one-cluster.md) gives each
Environment its own databases to migrate. Deploy canaries are weight-based,
through Flagger.

## Decision

A multi-tenant Project must declare a Liquibase changelog. The compiler refuses
`migration: self` and `migration: none` on a multi-tenant Project, because only
a managed migration is run, recorded and gated by `migration-run`.

Every revision is expand/contract: the Project's current version and the
version before it both work with the schema it leaves. The `migration-run`
component runs each revision once per Project database per Environment. It runs
a revision in one transaction wherever Postgres allows it, so a failure leaves
the old schema.

`migration-run` keeps its migration record in a custom resource it owns, one per
Project database per Environment. When a revision fails, the record marks that
Project database failed at that revision, with the error. The Project's current
version keeps serving. The Release Gate refuses further releases of that Project
in that Environment while its database is marked failed. It answers from cluster
state and fails closed, as [record 74](0074-the-release-gate-and-observation-each-have-a-named-write.md)
requires, so the refusal is a read and adds no write to that record's table. The
mark clears only when an Operator retries the migration and it succeeds, or
explicitly requests a Roll-forward
([record 101](0101-a-rollout-rolls-forward-when-rolling-back-would-run-a-migration-backwards.md));
nothing automatic may do either.

A Tenant's Tenant resource marks whether it is a Canary Tenant. Canary Tenants
are only a targeting group for feature flags inside Applications: a flag is on
for the Canary Tenants first, then for everyone. A migration reaches every
Tenant at once, and deploy canaries stay weight-based through Flagger.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Migration waves across a database per Tenant, Canary Tenants first, and a Behind state (this record before [record 114](0114-multi-tenant-projects-keep-their-tenants-in-shared-tables-separated-by-row-level-security.md)) | A fan-out, a wave width and a Behind state per Tenant database | One database per Project needs one run |
| Let a Project release while its database is marked failed | The next version can meet a schema two versions behind, past what expand/contract guarantees | The rule covers two adjacent versions only |
| Retry a failed migration automatically, or roll forward automatically | A fault repeats, or a release starts on a database nobody has looked at | An Operator retries or requests the Roll-forward |
| Roll the database back when a revision fails | A down migration runs on production data and may itself fail | A transactional revision already leaves the old schema; the rest are reconciled first ([record 101](0101-a-rollout-rolls-forward-when-rolling-back-would-run-a-migration-backwards.md)) |
| Let a Project run `migration: self` and own its migrations | No record, no failed mark and no refusal for that Project | One managed path gives one record and one gate |
| Canary Tenants receive each migration first | Shared tables give every Tenant the same schema, so there is nothing to stage per Tenant | Canary Tenants target feature flags |

## Consequences

- Easier: a revision runs once, whatever the number of Tenants; a failed
  transactional revision leaves the schema it found; a new feature reaches the
  Canary Tenants before everyone; no database falls two versions behind its
  Project.
- Harder: a failed migration blocks the Project's releases in that Environment
  until an Operator acts; every revision must be expand/contract, and one that
  cannot run in a transaction says so.
- Forbidden: `migration: self` or `migration: none` on a multi-tenant Project; a
  release while the Project database in that Environment is marked failed; a
  failure that leaves no failed mark; an automatic retry or Roll-forward of a
  failed migration.

## Confirmation

The **Migration declaration refusal** fails when the compiler accepts
`migration: self` or `migration: none` on a multi-tenant Project. The **Failed
migration state test** fails when a failing transactional revision leaves a
schema other than the one it found, or the Project database is not marked failed
at that revision in `migration-run`'s record. The **Failed migration release
refusal** fails when the Release Gate allows a release while the Project
database in that Environment is marked failed, allows a Roll-forward that no
Operator requested, or fails open when the record cannot be read. The **Canary
Tenant group test** fails when the tenancy library's Canary group differs from
the Tenants whose Tenant resource marks them Canary Tenants. The expand/contract
rule, and turning a flag on for Canary Tenants first, are review rules, and no
check holds them.

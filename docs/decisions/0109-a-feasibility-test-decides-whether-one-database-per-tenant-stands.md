---
status: proposed  # proposed | accepted | locked
date: 2026-11-04
rests-on: [76, 78, 81, 82]
lessons: [DR-1, DR-2, MS-7]
---

# A feasibility test decides whether one database per Tenant stands, and rendered objects do not grow with the Tenant count

## Context

[Record 78](0078-a-multi-tenant-project-keeps-one-tenant-database-per-tenant.md)
gives each multi-tenant Project one Tenant database per Tenant, against the
[research](../research/multi-tenancy.md#1-data-isolation-on-postgres)'s advice of
shared tables with row-level security. It names the costs (about 8 MB per empty
database, a pool and a migration per database, no query across Tenants) and
counts at most 5000 production databases at 1000 Tenants and five such
Projects. It is read again "if the research's counts of databases and pools
prove wrong", but nothing measures them, so that clause cannot fire.

The architecture evaluation of 2026-11-04 (sections 3.15, 11.3 and 13, item 29)
keeps that record and finds three gaps. The costs are unmeasured. Lazy pools
that expire when idle do not bound how many pools are open at once. Rejecting
shared tables for most Tenants and a database for a few does not reject one
shared-table design with row-level security, which a fair test should run. The
evaluation's critics name what to measure: migration-wave time, backup and
restore per database, catalog size, autovacuum, connections under concurrent
pools and Tenant creation time. The maintainer kept the record on 2026-11-04,
behind such a test, before the tenancy machinery is built (milestone M9).

The evaluation's section 2.3 also finds that the number of rendered objects
depends on Projects and Environments, never on Tenants. A host finds its Tenant
through a lookup
([record 77](0077-product-domains-are-admitted-by-platform-intent.md)), the
stores are one per Environment, and a Tenant is a custom resource that Delivery
writes
([record 80](0080-a-tenant-is-a-custom-resource-in-a-sixth-bounded-context-tenancy.md)),
not an object the compiler renders. Nothing checks it. Work on the Tenant side
(databases, [migration waves](0081-migrations-reach-tenant-databases-in-waves.md),
[Backup generations](0082-backups-are-per-tenant-generations-and-mirrors-refresh-staging-and-development.md))
does grow with Tenants, and that is what the test measures.

## Decision

A feasibility test runs on a throwaway cluster before any crate of the tenancy
context beyond its domain crate, `tenant`, is built. It loads one Database
server of the production size with 1000 Tenants in five multi-tenant Projects,
5000 Tenant databases of a stated synthetic schema, and runs the measures
below against the design of
[record 78](0078-a-multi-tenant-project-keeps-one-tenant-database-per-tenant.md).
It then runs the same measures on one
shared-table design with row-level security (`FORCE`, under a role that does
not own the tables) holding the same data, as a comparison that has no
threshold to meet.

| Measure | What is run | Starting threshold |
| --- | --- | --- |
| Tenant creation | Create one Tenant with its databases in the five Projects, migrated to the current revision | Under 60 seconds |
| Migration-wave time | One revision across one Project's 1000 Tenant databases, at the set wave width | Under 30 minutes |
| Connections | 200 Tenants active at once across the five Projects, with lazy, idle-expiring pools | Peak server connections under 80% of `max_connections`; 95th percentile wait for a connection under 50 ms |
| Catalog and disk | 5000 empty Tenant databases | Under 10 MB of disk per empty database; server start under 2 minutes |
| Autovacuum | Seven days of synthetic load | Every database vacuumed at least once a day; no database's transaction ID age above half of `autovacuum_freeze_max_age` |
| Backup time and cost | A Backup generation for every Tenant, encrypted and copied off the cluster | All 1000 within a 4-hour window; retained generations under 500 GB off the cluster |
| Restore | One Tenant of 1 GB, through the restore steps | Under 15 minutes |
| Server recovery | A WAL recovery of the whole server on a throwaway cluster | Under 2 hours |

The thresholds are starting proposals; the maintainer confirms or changes each
before the test first runs, and that question stays open. If the design of
[record 78](0078-a-multi-tenant-project-keeps-one-tenant-database-per-tenant.md)
meets every threshold, that record stands. If it misses one, that record's
review fires: the maintainer reads it again with both runs' results, and the
outcome is a new record. The result, with both runs, is committed beside the test.

The number of rendered objects does not depend on the number of Tenants. A
Tenant is never an input that adds, removes or names a rendered object.

When this record is accepted, the **Tenancy feasibility test** and the
**Tenancy feasibility gate** join the Confirmation of
[record 78](0078-a-multi-tenant-project-keeps-one-tenant-database-per-tenant.md),
and the **Render Tenant-count test** joins that of
[record 76](0076-tenants-are-the-organisations-the-estate-serves.md).

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Reverse [record 78](0078-a-multi-tenant-project-keeps-one-tenant-database-per-tenant.md) now and pool every Tenant in shared tables | Isolation rests on a policy per table; backup, restore and Purge of one Tenant become row copies and deletes | Nothing measured has fired its review; the maintainer kept it |
| Keep database per Tenant with no test | Its review clause can never fire; a limit is found in production at hundreds of Tenants | The costs are named but unmeasured |
| A test of database per Tenant alone | A miss gives no comparison to choose by | A fair test runs the shared-table design too |
| Run the test after the tenancy machinery is built | The evaluation's 150 to 250 hours for M9 spent before the data placement is known | Running it first costs a synthetic load only |
| A namespace per Tenant in the count | Counts objects the design never creates | A Project has one namespace per Environment, which its Tenants share ([record 75](0075-three-environments-run-in-the-one-cluster.md)) |
| Fixed thresholds chosen here | The maintainer's budget for hours, disk and recovery time set by this record | The thresholds are the maintainer's to confirm |

## Consequences

- Easier: the review clause of database per Tenant has numbers that can fire
  it; the tenancy build starts on a measured footing; a change that renders per-Tenant objects
  fails in CI.
- Harder: a synthetic load and a production-sized server must be built and run
  before M9; the thresholds need the maintainer's confirmation first.
- Forbidden: building a tenancy application or adapter crate before a committed
  result; a rendered object added, removed or named by a Tenant.

## Confirmation

The **Tenancy feasibility test** fails when the design of
[record 78](0078-a-multi-tenant-project-keeps-one-tenant-database-per-tenant.md)
misses any threshold at the stated Tenant count, or when either run omits a measure. The
**Tenancy feasibility gate** fails when the workspace holds a tenancy crate
other than `tenant` and no committed result either shows every threshold met
or links the record the maintainer wrote after a miss. The
**Render Tenant-count test** fails when an estate fixture with 1000 Tenants
renders objects that differ in number or name from the same fixture with one
Tenant.

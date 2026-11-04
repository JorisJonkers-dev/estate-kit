---
status: accepted  # proposed | accepted | locked | superseded
date: 2026-11-04
rests-on: [76, 81, 82, 114]
lessons: [DR-1, DR-2, MS-7]
---

# A row-level security scale test at 1000 Tenants runs before the tenancy machinery, and rendered objects do not grow with the Tenant count

## Context

[Record 114](0114-multi-tenant-projects-keep-their-tenants-in-shared-tables-separated-by-row-level-security.md)
keeps every Tenant of a multi-tenant Project in shared tables, separated by
row-level security, in one database per Project per Environment. It reverses
the database per Tenant of
[record 78](0078-a-multi-tenant-project-keeps-one-tenant-database-per-tenant.md).
The [research](../research/multi-tenancy.md#1-data-isolation-on-postgres) finds
that policies that compare only the current row are the simplest and fastest
case, that Azure advises extra indexes and performance tests, and that shared
tables share one database's resources, so one busy Tenant can slow the rest. A
Tenant's backup, restore and Purge become row exports, copies and deletes
([record 82](0082-backups-are-per-tenant-generations-and-mirrors-refresh-staging-and-development.md)).
Nothing has measured any of this at the horizon of more than 1000 Tenants.

The architecture evaluation of 2026-11-04 (sections 3.15, 11.3 and 13, item 29)
asked for a feasibility test of the data placement before the tenancy machinery
is built (milestone M9). It was first written as a test of a database per
Tenant. When the maintainer reversed that choice on 2026-11-04, the test became
a scale test of the shared-table design, with thresholds the maintainer set.

The evaluation's section 2.3 also finds that the number of rendered objects
depends on Projects and Environments, never on Tenants. A host finds its Tenant
through a lookup
([record 77](0077-product-domains-are-admitted-by-platform-intent.md)), the
stores are one per Environment, and a Tenant is a custom resource that Delivery
writes
([record 80](0080-a-tenant-is-a-custom-resource-in-a-sixth-bounded-context-tenancy.md)),
not an object the compiler renders. Nothing checks it. Work on the Tenant side
(rows, [Tenant exports](0082-backups-are-per-tenant-generations-and-mirrors-refresh-staging-and-development.md),
restores and Purges) does grow with Tenants, and that is what the test measures.

## Decision

A scale test runs on a throwaway cluster before any crate of the tenancy context
beyond its domain crate, `tenant`, is built. It loads one Postgres server of the
production size with 1000 Tenants in the shared tables of five multi-tenant
Project databases, of a stated synthetic schema, with the policies, `FORCE` and
roles of
[record 114](0114-multi-tenant-projects-keep-their-tenants-in-shared-tables-separated-by-row-level-security.md).
It runs these measures:

| Measure | What is run | Threshold |
| --- | --- | --- |
| Policy cost | The synthetic query mix with the policies on, then off | Query p95 with policies on within 10% of policies off |
| Index use | The plan of every tenant-scoped query in the mix | Every one uses a `tenant_id` index |
| Noisy neighbour | One heavy Tenant, with a load the test states, beside the others | The other Tenants' p95 rises by under 20% |
| Export | A Tenant export of a Tenant holding 1 GB | Under 5 minutes |
| Restore | That Tenant, through the restore steps of [record 82](0082-backups-are-per-tenant-generations-and-mirrors-refresh-staging-and-development.md) | Under 15 minutes |
| Purge | That Tenant's Purge | Under 10 minutes |

The result of each run is committed beside the test. A miss does not stop the
build. It becomes an issue, it is fixed (an index, pooling, per-Tenant limits)
and the test runs again. If it still misses, a new record decides whether to
raise the threshold or add a mitigation such as sharding by `tenant_id`.

The number of rendered objects does not depend on the number of Tenants. A
Tenant is never an input that adds, removes or names a rendered object.

When this record is accepted, the **Tenancy scale test** and the **Tenancy scale
gate** join the Confirmation of
[record 114](0114-multi-tenant-projects-keep-their-tenants-in-shared-tables-separated-by-row-level-security.md),
and the **Render Tenant-count test** joins that of
[record 76](0076-tenants-are-the-organisations-the-estate-serves.md).

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| A feasibility test of a database per Tenant, with shared tables as the comparison | Measures a design that is no longer chosen | [Record 114](0114-multi-tenant-projects-keep-their-tenants-in-shared-tables-separated-by-row-level-security.md) reversed the database per Tenant |
| Build the tenancy machinery with no test | A slow policy, a missing index or a noisy Tenant is found in production at hundreds of Tenants | The costs of shared tables are named but unmeasured |
| Run the test after the tenancy machinery is built | The evaluation's 150 to 250 hours for M9 spent before the design is measured | Running it first costs a synthetic load only |
| A miss stops the build | One slow measure halts all tenancy work, though most misses have a known fix | A miss is an issue to fix, and a second miss a record |
| A namespace per Tenant in the count | Counts objects the design never creates | A Project has one namespace per Environment, which its Tenants share ([record 75](0075-three-environments-run-in-the-one-cluster.md)) |
| Thresholds left for later | The test can neither pass nor fail | The maintainer set them on 2026-11-04 |

## Consequences

- Easier: the shared-table design is measured before the tenancy build; a slow
  policy, a missing index or a noisy Tenant shows on a synthetic load; a change
  that renders per-Tenant objects fails in CI.
- Harder: a synthetic load and a production-sized server must be built and run
  before M9; a miss must be fixed and run again, and a second miss needs a record.
- Forbidden: building a tenancy application or adapter crate before a committed
  result; a rendered object added, removed or named by a Tenant.

## Confirmation

The **Tenancy scale test** fails when a measure misses its threshold at 1000
Tenants, or a run omits a measure. The **Tenancy scale gate** fails when the
workspace holds a tenancy crate other than `tenant` and no result is committed,
or the committed result shows a miss that links neither an open issue nor the
record written after a second miss. The **Render Tenant-count test** fails when
an estate fixture with 1000 Tenants renders objects that differ in number or
name from the same fixture with one Tenant.

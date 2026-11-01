---
status: proposed  # proposed | accepted | locked
date: 2026-11-01
rests-on: [75, 76, 78, 80, 81]
lessons: [DR-1]
---

# Each Tenant is backed up as a Backup generation on its own schedule, and Mirrors refresh staging and development Tenants

## Context

[Record 78](0078-a-multi-tenant-project-keeps-one-tenant-database-per-tenant.md)
gives a Tenant one database per multi-tenant Project, and it chose that shape so
that one Tenant's data is backed up and restored on its own.
[Record 80](0080-a-tenant-is-a-custom-resource-in-a-sixth-bounded-context-tenancy.md)
gives the backup component a finalizer on the Tenant and defines the Tenant hooks.
[Record 81](0081-migrations-reach-tenant-databases-in-waves.md) gives each Tenant
database a migration revision. [Record 75](0075-three-environments-run-in-the-one-cluster.md)
makes staging and production exist as separate Environments with separate Tenants.

The backup component today works per Project: it takes a Project's Backup
generations and copies them off the cluster encrypted
([Mail and components](../design/mail-and-components.md#components)). That scope
does not fit a Tenant that owns up to one database in each of several Projects.
It does not change how the API server's datastore is backed up, which
[record 59](0059-vault-unseal-and-datastore-backup-are-assumed-from-fleet-infra.md)
leaves to fleet-infra.

The [research](../research/multi-tenancy.md#6-backups-and-production-into-staging)
finds that CloudNativePG takes physical backups of a whole cluster and recovers
only into a new cluster. Logical dumps are "not suitable for business
continuity", but they are the only route to one Tenant's databases. Copying
production into staging copies personal data, and pseudonymised data is still
personal data under Recital 26 of the GDPR.

## Decision

This record replaces the per-Project scope of the backup component for a
multi-tenant Project. A single-tenant Project keeps its generation as it is.

**A Backup generation is per Tenant.** It is a logical dump of every Tenant
database of one Tenant, taken together, on that Tenant's own schedule. It records
the migration revision of each database. It is encrypted, copied off the cluster,
and listed in one central catalogue with its Tenant, its Environment, its time and
those revisions. Retention is set per Environment. A Purge does not delete the
Tenant's generations; they expire under that retention.

**Each Postgres server also archives WAL** for point-in-time recovery. This is for
disaster only: the loss of a whole server. It restores a whole server into a new
cluster and is never used to restore one Tenant.

**A restore is a Tenant operation.** It takes these steps in order:

1. Lock the Tenant, with a Tenant lock.
2. Call the prepare-restore Tenant hook of each Application.
3. Replace each Tenant database from the generation.
4. Migrate each database up to the revision the target Environment is at.
5. Call the after-restore hook of each Application.
6. Unlock the Tenant.

A generation whose revision is newer than the target Environment's is refused,
and the refusal names both revisions. A failed lock or prepare-restore hook
aborts before any data changes, as
[record 80](0080-a-tenant-is-a-custom-resource-in-a-sixth-bounded-context-tenancy.md)
sets out.

**A Mirror refreshes a staging or development Tenant from one production Tenant.**
The Tenant resource names the production Tenant and a schedule. The Mirror
restores that Tenant's latest generation into the target Tenant, by the steps
above, but it loads into databases no person can read, masks them there, and only
then replaces the target's databases. A staging Tenant and its production Tenant
exist independently: a Mirror copies data, and creates no link in the other
direction.

- A development Mirror is always masked.
- A staging Mirror is masked only when it says so.
- Each Project declares masking rules for its own tables. A Project that declares
  none is not loaded into a development Mirror.

**An unmasked staging Mirror makes staging hold production personal data.**
Staging then needs the access of production for that Tenant's data: only the
people who may read that Tenant's production data may reach its staging Tenant.
Pseudonymising does not change the law, so masking reduces the exposure and does
not remove the duty. The choice to leave a staging Mirror unmasked belongs to the
maintainer and to nobody who only has staging access.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Whole-cluster physical backups only, restoring one Tenant by recovering to a scratch cluster and copying rows | A restore needs a scratch cluster, a copy per Tenant and tooling for each Project's schema | A dump of one Tenant's databases is one restore step each, which is why [record 78](0078-a-multi-tenant-project-keeps-one-tenant-database-per-tenant.md) chose a database per Tenant |
| Per-Tenant dumps without WAL archiving | The loss of a server loses every change since each Tenant's last generation | WAL archiving gives point-in-time recovery for disaster at little cost |
| One estate-wide schedule | A Tenant that pays for a tighter recovery point cannot have one, and one slow dump delays all | The schedule is a property of the Tenant |
| Backup per Project, as today | A Tenant's databases are restored one Project at a time and can land at different moments | A generation takes a Tenant's databases together, so a restore is consistent across Projects |
| Mirror always masked | Staging never tests against production-shaped data | The maintainer may choose it per staging Tenant, at the cost stated above |
| Mirror straight into the target, then mask | The target holds unmasked data while people can read it | The load goes to databases no person can read, and masking comes before exposure |
| Restore a newer generation and migrate down | Down migrations run on production-shaped data and may lose it | A generation newer than the target is refused |

## Consequences

- Easier: one Tenant is restored alone and consistently across its Projects;
  development always has production-shaped data without personal data; each
  generation says which revision it holds.
- Harder: the catalogue, the schedules and the encrypted copies grow with the
  Tenant count; every Project with personal columns keeps masking rules in step
  with its migrations; a restore into an older Environment can be refused.
- Forbidden: a generation that omits a Tenant database of its Tenant or its
  revisions; a restore that changes data before its lock and prepare-restore
  hooks succeed; a restore of a generation newer than the target; a development
  Mirror that is not masked; an exposed Mirror target before its masking ends;
  an unencrypted copy off the cluster.

## Confirmation

The **Backup generation completeness test** fails when a generation omits a
Tenant database of its Tenant, omits a database's revision, or is catalogued
before its encrypted copy is off the cluster. The **Restore order test** fails
when a restore changes data before its lock and prepare-restore hooks succeed,
skips a step, or leaves the Tenant locked after a failure. The **Restore revision
refusal** fails when a generation newer than the target is restored, or the
refusal omits either revision. The **Mirror masking test** fails when a
development Mirror is not masked, a staging Mirror that says it is masked is
not, a target is readable before its masking ends, or a Project with no masking
rules is loaded into a development Mirror. The **WAL recovery drill** fails when
a production Postgres server archives no WAL, or a recovery to a chosen time does
not reach it on a throwaway cluster. Who may reach a staging Tenant with an
unmasked Mirror is a maintainer's decision that no check holds; the record is
read again if staging access widens.

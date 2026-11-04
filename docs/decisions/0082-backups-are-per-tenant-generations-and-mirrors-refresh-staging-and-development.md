---
status: accepted  # proposed | accepted | locked
date: 2026-11-01
rests-on: [75, 76, 80, 81, 114]
lessons: [DR-1]
---

# Each Tenant is backed up as a Backup generation on its own schedule, and Mirrors refresh staging and development Tenants

Amended by [record 114](0114-multi-tenant-projects-keep-their-tenants-in-shared-tables-separated-by-row-level-security.md):
a Backup generation is now the set of a Tenant's Tenant exports, one per Project
database, with no shared point in time; a restore deletes and re-inserts the
Tenant's rows; production pushes each Mirror's export, masked where the Mirror
requires, to the target Environment; and a Purge deletes the exports and states
its erasure date. The text below says so.

Amended by [record 115](0115-backups-are-kopia-snapshots-in-one-locked-repository-per-environment-on-an-eu-object-store-with-wal-archived-beside-them.md):
each Tenant export is a source in its Environment's Kopia repository, on an EU
object store under a 30-day COMPLIANCE object lock, which is the off-cluster
copy; whole-database backups keep 7 daily, 4 weekly and 6 monthly snapshots;
and WAL is archived continuously to the same provider. The text below says so.

Amended by [record 110](0110-a-purge-erases-backup-generations-and-mirrors-from-an-inventory-of-every-copy.md):
a Purge deletes the Tenant's exports at once and states its erasure date from
the copy inventory. The text below says so.

## Context

[Record 114](0114-multi-tenant-projects-keep-their-tenants-in-shared-tables-separated-by-row-level-security.md)
keeps every Tenant of a multi-tenant Project in shared tables, keyed by
`tenant_id`, in one database per Project per Environment. One Tenant's data is
therefore a set of rows in each Project database it uses, and only the
Project's owner role, which the backup component may use, reads them all.
Projects own their data and talk to one another through APIs.
[Record 80](0080-a-tenant-is-a-custom-resource-in-a-sixth-bounded-context-tenancy.md)
gives the backup component a finalizer on the Tenant and defines the Tenant hooks.
[Record 81](0081-migrations-reach-tenant-databases-in-waves.md) gives each
Project database a migration revision. [Record 75](0075-three-environments-run-in-the-one-cluster.md)
makes staging and production exist as separate Environments with separate Tenants.

The backup component today works per Project: it takes a Project's Backup
generations and copies them off the cluster encrypted
([Mail and components](../design/mail-and-components.md#components)). That scope
does not fit a Tenant whose rows sit in several Projects' databases.
It does not change how the API server's datastore is backed up, which
[record 59](0059-vault-unseal-and-datastore-backup-are-assumed-from-fleet-infra.md)
leaves to fleet-infra.

The [research](../research/multi-tenancy.md#6-backups-and-production-into-staging)
finds that CloudNativePG takes physical backups of a whole cluster and recovers
only into a new cluster. Logical exports are "not suitable for business
continuity", but they are the only route to one Tenant's rows. Copying
production into staging copies personal data, and pseudonymised data is still
personal data under Recital 26 of the GDPR.

## Decision

This record replaces the per-Project scope of the backup component for a
multi-tenant Project. A single-tenant Project keeps its generation as it is.

**A Backup generation is the set of a Tenant's Tenant exports.** A Tenant export
is one Tenant's rows exported from one Project database
(`COPY ... WHERE tenant_id = ...`, table by table) in one snapshot transaction,
so it is consistent within its own database. It carries that database's
migration revision. There is no shared point in time across Projects. The backup
component takes a generation on the Tenant's own schedule and writes each
export as a snapshot of its own Kopia source into its Environment's Kopia
repository, which encrypts it and keeps it off the cluster in a locked bucket
([record 115](0115-backups-are-kopia-snapshots-in-one-locked-repository-per-environment-on-an-eu-object-store-with-wal-archived-beside-them.md)). It lists the generation in one central catalogue with its Tenant,
its Environment, its time and each export's revision.

**A Backup generation may be restored into its own Tenant or into another Tenant
of an equal or lower Environment,** under the target's `tenant_id`.

**Each Postgres server also keeps whole-database backups and archives WAL** for
point-in-time recovery. The whole-database backups are snapshots in the same
repository, kept 7 daily, 4 weekly and 6 monthly; WAL is archived continuously
to the same provider. This is for disaster only: the loss of a whole server. It
restores a whole server into a new cluster and is never used to restore one
Tenant.

**A restore is a Tenant operation, and it names the Projects it restores.** It
takes these steps in order:

1. Compare each export's revision with its Project database's. An export newer
   than the database is refused, and the refusal names both revisions.
2. Lock the Tenant, with a Tenant lock.
3. Call the prepare-restore Tenant hook of each Application.
4. In each Project named, delete the Tenant's rows and re-insert them from the
   export. An export at the database's revision is inserted directly. An older
   one is first loaded into a scratch database at its own revision, migrated
   forward there to the database's revision, and copied in from there.
5. Call the after-restore hook of each Application.
6. Unlock the Tenant.

A failed lock or prepare-restore hook aborts before any data changes, as
[record 80](0080-a-tenant-is-a-custom-resource-in-a-sixth-bounded-context-tenancy.md)
sets out, and the Tenant is unlocked. A failure after the first delete leaves
the Tenant locked, with the output in the operation log, until an Operator
retries the restore.

**A Mirror refreshes a staging or development Tenant from one production Tenant.**
The Tenant resource names the production Tenant and a schedule. Production's
backup component reads that Tenant's latest exports, masks them when the Mirror
requires it, and writes them into the target Environment's Kopia repository,
whose password production holds. A lower Environment never holds production's
credentials. The target Environment then loads the exports into its shared
database under a Tenant lock: it locks the target Tenant, deletes its rows,
imports the exports under its `tenant_id` by the revision rules of a restore,
runs the after-restore hooks and unlocks. A failure leaves the target Tenant
locked. A staging Tenant and its production Tenant exist independently: a
Mirror copies data, and creates no link in the other direction.

- A development Mirror is always masked.
- A staging Mirror is masked only when it says so.
- Each Project declares masking rules for its own tables. A Project that declares
  none is not loaded into a development Mirror.

**A Purge deletes the Tenant's exports and empties its Mirrors at once.** It
deletes the Tenant's rows, deletes its export snapshots from the backup
repository and runs full maintenance on it, and empties every Mirror target of
the Tenant. The Purge's entry in the operation log states the erasure date: the
expiry of the last copy in the copy inventory of
[record 110](0110-a-purge-erases-backup-generations-and-mirrors-from-an-inventory-of-every-copy.md).
Whole-database backups are kept up to 6 months, WAL no longer than the oldest
base backup kept, and the 30-day object lock bounds only the Tenant exports.

**An unmasked staging Mirror makes staging hold production personal data.**
Staging access must then be treated like production access: who may sign in,
where logs go, and how long data is kept.
Pseudonymising does not change the law, so masking reduces the exposure and does
not remove the duty. The choice to leave a staging Mirror unmasked belongs to the
maintainer and to nobody who only has staging access.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Whole-cluster physical backups only, restoring one Tenant by recovering to a scratch cluster and copying rows | A restore needs a scratch cluster and a copy of every Project database the Tenant uses | A Tenant export is one `COPY` per table, because every tenant-scoped table is keyed by `tenant_id` ([record 114](0114-multi-tenant-projects-keep-their-tenants-in-shared-tables-separated-by-row-level-security.md)) |
| Per-Tenant exports without WAL archiving | The loss of a server loses every change since each Tenant's last generation | WAL archiving gives point-in-time recovery for disaster at little cost |
| One estate-wide schedule | A Tenant that pays for a tighter recovery point cannot have one, and one slow export delays all | The schedule is a property of the Tenant |
| One point in time across every Project of a Tenant | A snapshot across databases needs a coordination the Projects otherwise do not have | Projects own their data and talk through APIs; a restore names the Projects it restores |
| Backup per Project, as before | A Tenant's exports are spread over Project schedules and catalogues | The generation is a property of the Tenant |
| Mirror always masked | Staging never tests against production-shaped data | The maintainer may choose it per staging Tenant, at the cost stated above |
| Mask in the target Environment | The target holds unmasked production data, and its backup component needs production's credentials | Production masks before the export leaves it, and pushes it down |
| Restore a newer export and migrate down | Down migrations run on production-shaped data and may lose it | An export newer than the database is refused |
| Insert an older export straight into the current schema | The rows do not fit the schema they meet | It is migrated forward in a scratch database first |
| Unlock a Tenant after a failed load | Its people see a Tenant whose rows are half deleted | The Tenant stays locked until an Operator acts |

## Consequences

- Easier: one Tenant is restored alone, Project by Project; development always
  has production-shaped data without personal data; each export says which
  revision it holds; no lower Environment holds a production credential; a Purge
  says when the Tenant's data is gone.
- Harder: the catalogue, the schedules and the encrypted copies grow with the
  Tenant count; every Project with personal columns keeps masking rules in step
  with its migrations; a restore of an older export needs a scratch database; a
  failed load leaves a Tenant locked until an Operator acts.
- The backup component's entry in [Mail and components](../design/mail-and-components.md#components) is amended: its scope is per Tenant for a multi-tenant Project.
- Forbidden: a generation that omits an export of a Project database holding the
  Tenant's rows, or an export without its revision; a restore that changes data
  before its lock and prepare-restore hooks succeed; a restore of an export newer
  than its database; a development Mirror that is not masked; an unmasked export
  of a masked Mirror outside production; production's credentials in a lower
  Environment; an unencrypted copy off the cluster.

## Confirmation

The **Backup generation completeness test** fails when a generation omits an
export of a Project database that holds the Tenant's rows, an export omits its
revision or is not taken in one snapshot transaction, or the generation is
catalogued before its encrypted copy is off the cluster. The **Restore order
test** fails when a restore changes data before its lock and prepare-restore
hooks succeed, skips a step, touches a Project it does not name, or unlocks the
Tenant after a failure that changed data. The **Restore revision refusal** fails
when an export newer than its database is restored, the refusal omits either
revision, or an older export is copied in without being migrated forward in a
scratch database. The **Mirror masking test** fails when a development Mirror is
not masked, a staging Mirror that says it is masked is not, an unmasked export
of a masked Mirror leaves production, a lower Environment holds production's
backup credentials, or a Project with no masking rules is loaded into a
development Mirror. The **Mirror load order test** fails when a Mirror load
changes the target's rows before its Tenant lock, imports under any `tenant_id`
but the target's, or unlocks the target after a failure. The **WAL recovery
drill** fails when a production Postgres server archives no WAL, or a recovery
to a chosen time does not reach it on a throwaway cluster. The **Erasure date
test** fails when a Purge's entry states no erasure date, or one earlier than
the expiry of the last copy in the inventory. Who may reach a staging Tenant
with an unmasked Mirror is a maintainer's decision that no check holds; the
record is read again if staging access widens.

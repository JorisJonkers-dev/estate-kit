---
status: accepted  # proposed | accepted | locked
date: 2026-11-05
rests-on: [82, 115]
amends: [82]
lessons: [DR-1]
---

# A restore names the Projects it restores, takes a verified safety copy first, and never crosses into a lower Environment unmasked

## Context

The restore of
[record 82](0082-backups-are-per-tenant-generations-and-mirrors-refresh-staging-and-development.md)
is a Tenant operation that names the Projects it restores, locks the Tenant,
calls the prepare-restore hooks and then deletes the Tenant's rows in each
Project named and re-inserts them from the export. As written the delete comes
with no recovery copy: an export that turns out unusable — a failed re-insert,
a corrupt or mis-revisioned export — has already destroyed the Tenant's rows
in every Project the restore names. The same record allows a Backup generation
to be restored "into another Tenant of an equal or lower Environment", which
is an unmasked route for production personal data into staging or development,
beside the masked route its own Mirror rules define. And the scratch database
that migrates an older export forward was left to be built however the
implementation pleased.

The architecture evaluation of 2026-11-04 (finding `A5-01`, promoted P0 in the
adjudication: "The single-Tenant restore cannot be executed as written and can
destroy rows with no recovery copy; a restore into a lower Environment is an
unmasked route for personal data") recommends one ordered restore with a safety
generation and masking by default. The maintainer settled it on 2026-11-04: a
restore names the Projects it restores, takes a safety copy first, refuses an
unmasked route into a lower Environment, and the scratch database is built
from a schema dump.

## Decision

This amends
[record 82](0082-backups-are-per-tenant-generations-and-mirrors-refresh-staging-and-development.md);
its Mirror rules are unchanged.

**A restore takes a verified safety copy first.** A restore's first step,
before it locks anything or calls any hook, writes a safety copy of the
Tenant's current rows: one export per Project the restore names, taken in one
snapshot transaction, written to the Environment's backup repository and read
back verified
([record 115](0115-backups-are-kopia-snapshots-in-one-locked-repository-per-environment-on-an-eu-object-store-with-wal-archived-beside-them.md)).
The safety copy is a Backup generation, catalogued like any other, so the
inventory, the object lock and the Purge rules hold it too. A restore whose
safety copy fails — a Project it names cannot be exported, the write fails, or
the read-back differs — aborts before any data changes and leaves the Tenant
unlocked.

**A restore names the Projects it restores, and touches no other.** A restore
that names no Project is refused, and no step of it reaches a Project it does
not name
([record 82](0082-backups-are-per-tenant-generations-and-mirrors-refresh-staging-and-development.md)).
What a restore is not asked to restore — a Project the Tenant uses but the
restore does not name — keeps its current rows, and the Tenant's remaining
Projects are restored in a second restore that names them.

**An unmasked restore never crosses into a lower Environment.** Within one
Environment a restore is unchanged: a generation may be restored into its own
Tenant or another Tenant of the same Environment, under the target's
`tenant_id`. A restore whose target Environment is lower than its export's
masks before the export leaves its Environment, by the masking rules a Mirror
load uses; the masking is the default and not the caller's choice. A restore
that would land unmasked in a lower Environment is refused, and the refusal
names the target and the masking rule.

**The scratch database is built from a schema dump.** When an export older
than its database is migrated forward, the scratch database is created from a
schema dump of the Project database at the export's own revision — a dump of
the schema and nothing else — so a scratch database holds no Tenant's rows at
any point in its life.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Delete first and re-insert from the export, as written | An unusable export has already destroyed the Tenant's rows, with no copy to retry from | The safety generation is written and verified first |
| A safety copy inside the cluster alone | A disaster that takes the database takes the copy with it | It is written to the Environment's backup repository, off the cluster under object lock ([record 115](0115-backups-are-kopia-snapshots-in-one-locked-repository-per-environment-on-an-eu-object-store-with-wal-archived-beside-them.md)) |
| Restore every Project the Tenant uses, named or not | A restore the caller believed partial rewrites Projects it never named | The restore names the Projects it touches, and only them |
| Keep any-Environment restores allowed under the target's `tenant_id` | Production personal data lands unmasked in staging or development | The Mirror rules already define the masked route down, so the unmasked route is refused |
| Mask in the target Environment | The lower Environment holds unmasked production data on the way in | Production masks before the export leaves it, as it does for a Mirror |
| Build the scratch database from a data-bearing copy | The scratch databases multiply Tenant data and its retention | A schema dump carries no rows |

## Consequences

- Easier: a failed restore is retried from the safety copy with nothing lost;
  every restore is executable step by step; a Project the restore does not name
  keeps its rows, on purpose and on record.
- Harder: every restore writes and verifies one more generation before it
  starts; a restore into a lower Environment waits for masking; a scratch
  database needs a schema dump at its export's revision.
- Forbidden: a restore that deletes or re-inserts a Tenant's rows before its
  safety copy is written and verified; a restore that touches a Project it
  does not name; an unmasked restore into a lower Environment; a scratch
  database that holds rows.

## Confirmation

The **Restore safety copy test** fails when a restore deletes or re-inserts
a Tenant's rows before the safety copy of every Project it names is written and
verified, or when a restore whose safety copy failed still changes data: it
runs in the `backup` component tests, every run ([the table of
checks](../design/code-shape-and-speed.md#the-checks)). The **Restore masking
refusal** fails when an unmasked restore is accepted into a lower Environment,
or a restore into a lower Environment masks by any rules but the Mirror's:
it runs in the `backup` component tests, every run. The **Restore order test**
and the **Restore revision refusal** of
[record 82](0082-backups-are-per-tenant-generations-and-mirrors-refresh-staging-and-development.md)
still hold their steps; the revision refusal now also fails when the scratch
database is built from anything but a schema dump.

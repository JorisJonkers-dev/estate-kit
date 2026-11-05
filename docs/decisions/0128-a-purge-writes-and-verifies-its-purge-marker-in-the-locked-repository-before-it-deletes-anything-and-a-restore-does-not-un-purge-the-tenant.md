---
status: accepted  # proposed | accepted | locked
date: 2026-11-05
rests-on: [76, 82, 110, 115]
amends: [82, 110]
lessons: [DR-1, DO-2]
---

# A Purge writes and verifies its Purge marker in the locked repository before it deletes anything, and a restore does not un-purge the Tenant

## Context

[Record 110](0110-a-purge-erases-backup-generations-and-mirrors-from-an-inventory-of-every-copy.md)
keeps a Purged Tenant un-restorable with sentences about what participants do:
"the catalogue marks the Purged Tenant", "Delivery keeps the key of every
Purged Tenant", and when a store is restored to a time before a Purge "the
rows, the key prefix and the secret path of each Purged key are removed again
before the store serves". But the catalogue
[record 82](0082-backups-are-per-tenant-generations-and-mirrors-refresh-staging-and-development.md)
names is one central catalogue on the shared platform-postgres — the same
store a whole-database restore brings back, and the same store whose
whole-database backup of [record 110](0110-a-purge-erases-backup-generations-and-mirrors-from-an-inventory-of-every-copy.md) keeps up to 6 months of history. A Purge
whose durable record of itself lives inside the stores a restore reaches can
be undone by that restore: the restored platform-postgres serves a catalogue
that no longer marks the Tenant, and the estate that told a Tenant it was
erased loads its rows again.

The architecture evaluation of 2026-11-04 (finding `A5-05`, answered by
recommendation `NR-7`) asks that the Purged keys and the Tenant catalogue be rebuildable from
markers in the Kopia repository, and the maintainer settled it on 2026-11-04:
each Purge writes a small locked marker into the repository before it deletes
anything and aborts if the marker write fails; after a store restore the
markers are re-read and the Purged Tenants removed again. Tombstones and the
Purge inventory carry opaque UUIDs.

## Decision

This amends
[record 110](0110-a-purge-erases-backup-generations-and-mirrors-from-an-inventory-of-every-copy.md)
and the Purge paragraph of
[record 82](0082-backups-are-per-tenant-generations-and-mirrors-refresh-staging-and-development.md).

**A Purge writes and verifies its Purge marker in the locked repository
before it deletes anything.** The marker is one small object in the
Environment's backup repository
([record 115](0115-backups-are-kopia-snapshots-in-one-locked-repository-per-environment-on-an-eu-object-store-with-wal-archived-beside-them.md)),
under the repository's object lock, and it is kept as long as its Tenant key
is never reused
([record 76](0076-tenants-are-the-organisations-the-estate-serves.md)). The
Purge writes it, reads it back verified, and only then deletes its first row.
A Purge whose marker write or read-back fails aborts with a failure and
deletes nothing, and the failure enters the operation log.

**The markers are the record; platform-postgres only caches them.** The
Tenant catalogue's entry for a Purged Tenant, and the key of every Purged
Tenant, live as Purge markers in the locked repository. platform-postgres
holds only a cache of them, rebuilt from the markers whenever the two
disagree. A restore does not un-purge the Tenant: when any store is restored
to a time before a Purge — a Postgres server, a bucket or Vault — the
Purged-key list is rebuilt from the markers, and each Purged Tenant is removed
again before the store serves, as
[record 110](0110-a-purge-erases-backup-generations-and-mirrors-from-an-inventory-of-every-copy.md)
already demands of a whole-store recovery.

**Tombstones and the Purge inventory carry opaque UUIDs.** Each Purge marker,
and each entry the copy inventory of
[record 110](0110-a-purge-erases-backup-generations-and-mirrors-from-an-inventory-of-every-copy.md)
keeps that names a Tenant, is named by an opaque UUID and never by a readable
Tenant key or Tenant handle, so nothing readable survives the Purge where a
listing can reach it. Each marker's own contents keep what [record 110](0110-a-purge-erases-backup-generations-and-mirrors-from-an-inventory-of-every-copy.md)'s rules
need, beneath its UUID name.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| The central catalogue in platform-postgres as the record of a Purge | platform-postgres is the store a whole-database restore brings back, so the marker dies with what it marks | The marker lives in the locked repository, outside every store a restore reaches |
| The operation log as the record of a Purge | The log is on platform-postgres too, and is kept 400 days, not forever | Records 82 and 110 need the Purged keys kept as long as keys are never reused |
| Write the marker first, without reading it back | A write that silently failed leaves the Purge unmarked over deleted rows | The marker is verified before the first delete, and the Purge aborts |
| Rebuild the Purged-key list on demand, after a restore | A restored store serves while the list is rebuilt | The markers are re-read before the store serves |
| Name the markers by their Tenant keys | A readable key survives the Purge in repository listings | Tombstones and the Purge inventory carry opaque UUIDs |
| A signed marker file in each Project database the Tenant used | One more writer per database, and a Project database is exactly what a restore brings back | Nothing inside a restored store can hold the record |

## Consequences

- Easier: a Purge cannot touch anything until its durable marker exists; a
  database restore cannot resurrect a Purged Tenant; repository listings show
  no readable names; the cache is rebuilt from one place.
- Harder: every Purge writes and verifies one repository object first, and
  the object is kept forever; the caches need a rebuild path after every store
  restore; a store restored does not serve until its markers are re-read.
- Forbidden: a Purge that deletes anything before its Purge marker is written
  and verified, or that continues after the marker write failed; Purged keys or
  the Tenant catalogue held only in platform-postgres; a store restored that
  serves before its Purged-key list is rebuilt from the markers; a marker or
  inventory entry named by a readable Tenant key or handle.

## Confirmation

The **Purge rules** check fails when the record text of
[record 82](0082-backups-are-per-tenant-generations-and-mirrors-refresh-staging-and-development.md)
or
[record 110](0110-a-purge-erases-backup-generations-and-mirrors-from-an-inventory-of-every-copy.md)
omits the marker-first or the restore-does-not-un-purge rule: it runs in the
Records job of `Pipeline Complete` ([the table of
checks](../design/code-shape-and-speed.md#the-checks)). The **Tenant finalizer
Purge** check fails when a Purge deletes anything before its Purge marker is
written and verified, or a Purge whose marker write failed continues. The
**Purged restore refusal** fails when a restored store serves before its
Purged-key list is rebuilt from the markers. The **Purge reapplication drill**
fails when a WAL recovery to a time before a Purge lets the Purged Tenant's
rows serve, or leaves them once the server is back.

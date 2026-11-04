---
status: accepted  # proposed | accepted | locked
date: 2026-11-04
rests-on: [76, 80, 82, 114]
amends: [80, 82]
lessons: [DO-2, DR-1]
---

# A Purge deletes a Tenant's exports and empties its Mirrors at once, and states its erasure date from an inventory of every copy

## Context

A Purge removes a Tenant's rows, cache keys, stored objects, Tenant secrets,
mail domain and Memberships, and completes only when every participant has
released its finalizer
([record 80](0080-a-tenant-is-a-custom-resource-in-a-sixth-bounded-context-tenancy.md)).
[Record 114](0114-multi-tenant-projects-keep-their-tenants-in-shared-tables-separated-by-row-level-security.md)
keeps a Tenant's rows in shared tables, so a Purge deletes rows rather than
dropping databases. A Backup generation is the set of a Tenant's Tenant exports,
and each Postgres server also keeps whole-database backups and archives WAL
([record 82](0082-backups-are-per-tenant-generations-and-mirrors-refresh-staging-and-development.md)).
A Tenant export holds one Tenant only; a whole-database backup and its WAL hold
every Tenant of the database together. Production pushes each Mirror's exports
into the target Environment's backup repository. A Tenant key is never reused,
even after a Purge
([record 76](0076-tenants-are-the-organisations-the-estate-serves.md)).

The architecture evaluation of 2026-11-04 (section 9.11, and section 13, item
30) asks that the design list every copy that holds Tenant data, among them WAL
archives, object versions, Mirrors and off-site copies, and how each expires,
before it claims erasure, and that tombstones keep a restore from bringing a
Purged Tenant back. The [research](../research/multi-tenancy.md#5-tenant-lifecycle)
cites the UK regulator's guidance that erasure reaches backups, and that a
backup copy may wait until it is overwritten if it is put beyond use.

## Decision

This amends
[record 80](0080-a-tenant-is-a-custom-resource-in-a-sixth-bounded-context-tenancy.md)
and
[record 82](0082-backups-are-per-tenant-generations-and-mirrors-refresh-staging-and-development.md).

**An inventory names every copy.** A committed inventory, kept with the backup
component, lists each kind of copy that can hold a Tenant's data: its rows in
each Project database, its Tenant exports in each Environment's backup
repository and their off-cluster copies, each Postgres server's whole-database
backups and WAL archive, Mirror targets' rows and the exports pushed for them,
objects and any kept object versions, Valkey keys, messages that carry its
Tenant header, Tenant secrets and Vault's snapshots, its mail domain and mail,
and telemetry that carries its Tenant key. Each entry states where the copy
lives, how long it is kept, and whether a Purge removes it at once or it
expires. Whole-database backups are kept up to 6 months, WAL no longer than the
oldest base backup kept, and the 30-day object lock bounds only the Tenant
exports. The other lengths are the maintainer's to set in the inventory.

**A Purge deletes the Tenant's exports at once.** The backup component deletes
the Tenant's rows from each Project database, deletes the Tenant's export
snapshots, and runs full maintenance on the repository, so no snapshot still
refers to the data. The object lock then holds the deleted objects for at most
30 days.

**A Mirror's copy lives only as long as its source.** A Purge ends every Mirror
whose source is the Purged Tenant. It deletes each target Tenant's rows at once,
and the exports production pushed for it into the target Environment's
repository. The backup component releases its finalizer only after that.

**A whole-database backup is beyond use for a Purged Tenant.** The catalogue
marks the Purged Tenant, and no restore or Mirror loads an export of it, into
any Tenant. Delivery keeps the key of every Purged Tenant, which the key reuse
rule of [record 76](0076-tenants-are-the-organisations-the-estate-serves.md)
already needs. When a Postgres server, a bucket or Vault is restored to a time
before a Purge, the rows, the key prefix and the secret path of each Purged key
are removed again before the store serves.

**The Purge states its erasure date.** The operation log marks a Purge complete
when the finalizers are released, as before. Its entry states the erasure date:
the expiry of the last copy in the inventory. The Tenant is marked erased only
on that date, once that copy has expired.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Keep the Tenant exports until their retention ends, beyond use | A Purged Tenant's rows stay in the backup repository for months | An export holds one Tenant, so it can be deleted at once |
| Delete whole-database backups and WAL at a Purge | Every other Tenant of the database loses its recovery point | They cannot be cut per Tenant, so they expire under their retention and are put beyond use |
| Keep exports restorable after a Purge | A restore brings back a Purged Tenant's data under a key that is never used again | They are deleted, and the catalogue marks the Tenant |
| Leave a Mirror's copy until its next refresh | Production data of a Purged Tenant stays readable in staging or development | A Mirror's copy lives only as long as its source |
| Encrypt each Tenant's data under its own key and destroy the key at Purge | A key per Tenant to manage in every store; no ruling says key destruction alone is erasure | A later option if the inventory shows a copy that cannot otherwise expire |
| Claim erasure when the Purge completes | Copies still exist within their retention | The Purge states the date the last copy expires |
| Trust a whole-server recovery to omit Purged Tenants | A disaster recovery brings back rows that were Purged | The recovery removes them again before the store serves |

## Consequences

- Easier: the estate can say when each Purged Tenant's data is gone, and where
  it still is until then; a Purged Tenant's exports and Mirrors go at once; a
  restore or a disaster recovery cannot bring a Purged Tenant back.
- Harder: a new store, component kind or retention change needs an inventory
  entry; a Purge runs full maintenance on a backup repository; every
  whole-store restore runs the Purged keys before it serves.
- Forbidden: a store that holds Tenant data without an inventory entry; a
  restore or Mirror of a Purged Tenant's export; a Mirror's copy, or an export,
  that outlives the Purge of its Tenant; a copy kept past its retention; a Purge
  with no erasure date; a Tenant marked erased while a copy remains.

## Confirmation

The **Copy inventory check** fails when a store a multi-tenant Project can use,
or a copy [record 82](0082-backups-are-per-tenant-generations-and-mirrors-refresh-staging-and-development.md)
makes, has no inventory entry, or an entry lacks its retention or how it
expires. The **Purged restore refusal** fails when a restore or a Mirror loads
an export of a Purged Tenant. The **Purge expiry test** fails when a Purged
Tenant's rows, export snapshots or Mirror targets' rows and exports remain once
the Purge completes, or a copy of it remains after its retention ends. The
**Erasure date test** fails when a Purge's entry states no erasure date, or one
earlier than the expiry of the last copy in the inventory. The **Purge
reapplication drill** fails when a WAL recovery to a time before a Purge lets
the Purged Tenant's rows serve, or leaves them once the server is back. The
**Tenant finalizer Purge** check still holds the Purge itself.

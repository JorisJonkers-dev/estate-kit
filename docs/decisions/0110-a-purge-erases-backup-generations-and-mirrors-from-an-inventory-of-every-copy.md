---
status: proposed  # proposed | accepted | locked
date: 2026-11-04
rests-on: [76, 78, 80, 82]
lessons: [DO-2, DR-1]
---

# A Purge erases Backup generations and Mirrors at the end of their retention, from an inventory of every copy

## Context

A Purge removes a Tenant's databases, cache keys, stored objects, Tenant
secrets, mail domain and Memberships, and completes only when every
participant has released its finalizer
([record 80](0080-a-tenant-is-a-custom-resource-in-a-sixth-bounded-context-tenancy.md)).
A Purge does not remove the Tenant's Backup generations; they expire under
their normal retention
([record 82](0082-backups-are-per-tenant-generations-and-mirrors-refresh-staging-and-development.md)).
That record also archives WAL on each Postgres server, and its Mirrors load a
production Tenant's data into staging and development Tenants. Neither record
says what happens to a Mirror's copy when its source is Purged, what stops a
kept generation from being restored, or what a whole-server recovery to a time
before the Purge brings back. A Tenant key is never reused, even after a Purge
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
component, lists each kind of copy that can hold a Tenant's data: its Tenant
databases, its Backup generations and their off-cluster copies, each Postgres
server's WAL archive and base backups, Mirror targets and the generations taken
of them, objects and any kept object versions, Valkey keys, messages that carry
its Tenant header, Tenant secrets and Vault's snapshots, its mail domain and
mail, and telemetry that carries its Tenant key. Each entry states where the
copy lives, how long it is kept, and whether a Purge removes it at once or it
expires. The lengths of retention are the maintainer's to set in the
inventory; this record sets none.

**A Mirror's copy lives only as long as its source.** A Purge ends every Mirror
whose source is the Purged Tenant, and replaces each target's databases loaded
from it with empty ones at the current revision. The backup component releases
its finalizer only after that.

**A kept generation is beyond use.** The catalogue marks each generation of a
Purged Tenant, and no restore or Mirror loads one, into any Tenant. When its
retention ends, the backup component deletes the generation and every copy of
it off the cluster, object versions included, and logs each deletion in the
operation log.

**A whole-store restore applies the Purges again.** Delivery keeps the key of
every Purged Tenant, which the key reuse rule of
[record 76](0076-tenants-are-the-organisations-the-estate-serves.md) already
needs. When a Postgres server, a bucket or Vault is restored to a time before a Purge, the database, the key
prefix and the secret path of each Purged key are removed again before the
store serves.

**Erasure is claimed only when the inventory says so.** The operation log marks
a Purge complete when the finalizers are released, as before, and marks the
Tenant erased only when the last copy in the inventory has expired.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Delete every generation and copy at Purge | Every off-cluster copy and object version must be found and deleted at once, and WAL archives and base backups cannot be cut per Tenant | The guidance lets a copy put beyond use wait for its retention, and one rule then covers every kind of copy |
| Keep generations restorable after a Purge | A restore brings back a Purged Tenant's data under a key that is never used again | A kept generation is beyond use |
| Leave a Mirror's copy until its retention or next refresh | Production data of a Purged Tenant stays readable in staging or development | A Mirror's copy lives only as long as its source |
| Encrypt each Tenant's data under its own key and destroy the key at Purge | A key per Tenant to manage in every store; no ruling says key destruction alone is erasure | A later option if the inventory shows a copy that cannot otherwise expire |
| Claim erasure when the Purge completes | Copies still exist within their retention | Erasure is claimed only when the inventory says every copy has gone |
| Trust a whole-server recovery to omit Purged Tenants | A disaster recovery brings back databases that were Purged | The recovery removes them again before the store serves |

## Consequences

- Easier: the estate can say when each Purged Tenant's data is gone, and where
  it still is until then; a restore or a disaster recovery cannot bring a
  Purged Tenant back.
- Harder: a new store, component kind or retention change needs an inventory
  entry; every whole-store restore runs the Purged keys before it serves.
- Forbidden: a store that holds Tenant data without an inventory entry; a
  restore or Mirror of a Purged Tenant's generation; a Mirror's copy that
  outlives the Purge of its source; a generation or copy kept past its
  retention; a Tenant marked erased while a copy remains.

## Confirmation

The **Copy inventory check** fails when a store a multi-tenant Project can use,
or a copy [record 82](0082-backups-are-per-tenant-generations-and-mirrors-refresh-staging-and-development.md) makes, has no inventory entry, or an entry lacks its
retention or how it expires. The **Purged restore refusal** fails when a
restore or a Mirror loads a generation of a Purged Tenant. The **Purge expiry
test** fails when a generation of a Purged Tenant, or a copy or object version
of it, remains after its retention ends, or a Mirror target still holds data
loaded from a Purged Tenant after the Purge completes. The **Purge reapplication
drill** fails when a WAL recovery to a time before a Purge lets the Purged
Tenant's databases serve, or leaves them once the server is back. The
**Tenant finalizer Purge** check still holds the Purge itself.

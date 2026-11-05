---
status: accepted  # proposed | accepted | locked
date: 2026-11-05
rests-on: [80, 82, 110]
amends: [80]
lessons: [DR-1, DO-2]
---

# The estate is a processor, the tenancy record gains a Tenant export hook, and the erasure date is stated to the Tenant

## Context

[Record 80](0080-a-tenant-is-a-custom-resource-in-a-sixth-bounded-context-tenancy.md)
settles the Tenant resource, the Tenant operations and the Tenant hooks, and
ends a Tenant by Purge with an erasure date in the operation log. It never
says what the estate owes the organisations whose people's data it holds. The
[research](../research/multi-tenancy.md) holds its sources, and the GDPR gives
data subjects a right to take their data with them: the estate runs each
Tenant's Applications for the Tenant, so portability and erasure are duties
the estate carries out, on the Tenant's behalf.

The design review of 2026-11-04 (section 13, item 26) asks whether the estate
is a processor owing portability, whether six months of whole-database
retention is the erasure date, and when the Tenant is told. The maintainer
settled it on 2026-11-04: the estate is a processor, so
[record 80](0080-a-tenant-is-a-custom-resource-in-a-sixth-bounded-context-tenancy.md)
gains a Tenant export hook; Tenant exports are signed after the first Mirror;
and the erasure date is the end of six months of whole-database retention,
stated to the Tenant.

## Decision

This amends
[record 80](0080-a-tenant-is-a-custom-resource-in-a-sixth-bounded-context-tenancy.md).

**The estate is a processor.** The estate holds a Tenant's people's data to
serve that Tenant, and its Applications act on the estate's machinery, so
portability and erasure are due to it, carried out as Tenant operations and
recorded in the operation log.

**A Tenant export hook joins the Tenant hooks.** The list grows to
after-create, lock, unlock, prepare-restore, after-restore and export. An
export that a Tenant takes away stands on its Backup generations of
[record 82](0082-backups-are-per-tenant-generations-and-mirrors-refresh-staging-and-development.md):
the tenancy context makes one export per Project database that holds the
Tenant's rows, as the operation `export`, and calls each multi-tenant
Application's export hook, so the Application hands over the data it keeps
where the platform cannot see it. The hook is called as every hook is: over
HTTP with a signed machine token, the Tenant key and an operation id; an
undeclared hook counts as a no-op success, and a failed export hook flags the
Tenant and enters the operation log. Tenant exports are signed after the
first Mirror has run, so the Tenant can verify that what it takes away came
from the estate unmodified.

**The erasure date is stated to the Tenant.** The Purge already states its
erasure date in the operation log; the Tenant is told it too, by the same
answer the log keeps: the end of the six months of whole-database retention of
[record 82](0082-backups-are-per-tenant-generations-and-mirrors-refresh-staging-and-development.md),
[record 110](0110-a-purge-erases-backup-generations-and-mirrors-from-an-inventory-of-every-copy.md)
and [record 115](0115-backups-are-kopia-snapshots-in-one-locked-repository-per-environment-on-an-eu-object-store-with-wal-archived-beside-them.md),
the expiry of the last copy in the copy inventory.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| The estate as controller of every Tenant's data | Portability and erasure become the estate's to decide per Tenant, and the estate answers for its Tenants' purposes | The estate serves each Tenant's Applications for the Tenant; processor is the honest role |
| No export hook, the platform `COPY`s all there is | What an Application keeps outside the estate's databases never reaches the Tenant | The hook lets the Application add what the platform cannot see |
| A bespoke export path per Project | Each Project invents its own export and its own credentials | The hook rides the Tenant hook contract that Applications already implement |
| The erasure date as an internal operation-log field | The Tenant never learns when its data is gone from backups | The Tenant is told the date, as its processor owes |
| Let each Tenant's erasure date differ from the inventory | A stated date can be wrong twice | One date: the expiry of the last copy in the copy inventory |

## Consequences

- Easier: the Tenants the estate serves are owed their data by one path, and
  each Purge's answer to a Tenant is one sentence, from the copy inventory.
- Harder: the tenancy context gains an operation, one more hook, and a Tenant
  contact to tell the erasure date; exports handed to a Tenant are signed once
  the first Mirror has run.
- Forbidden: an export that omits a Project database holding the Tenant's
  rows; an export handed over unsigned once the first Mirror has run; a Purge
  that tells the Tenant no erasure date, or one that is not the expiry of the
  last copy in the inventory.

## Confirmation

The **Tenant export hook check** fails when an export handed to a Tenant omits a
Project database that holds its rows, a failed export hook neither flags the
Tenant nor enters the operation log, or an export handed over is unsigned once
the first Mirror has run ([the table of
checks](../design/code-shape-and-speed.md#the-checks)). The **Erasure date
test** fails when a Purge's entry states no erasure date, or one earlier than
the expiry of the last copy in the copy inventory, or the Tenant is not told
the date.

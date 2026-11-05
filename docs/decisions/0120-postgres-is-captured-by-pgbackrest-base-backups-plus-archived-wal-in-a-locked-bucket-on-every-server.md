---
status: accepted  # proposed | accepted | locked | superseded
date: 2026-11-05
rests-on: [87, 115]
amends: [115]
lessons: [DR-1, DR-2]
---

# Postgres is captured by pgBackRest base backups plus archived WAL, in a locked bucket, on every server

## Context

[Record 87](0087-recovery-time-and-recovery-point-are-stated-per-recovery-class.md)
gives Tenant and Project databases a recovery point of 15 minutes.
[Record 115](0115-backups-are-kopia-snapshots-in-one-locked-repository-per-environment-on-an-eu-object-store-with-wal-archived-beside-them.md)
claims to meet it with whole-database backups taken as Kopia sources and each
server's WAL "archived beside them". A dump cannot be replayed with WAL: it is
a base for a restore, not for a point-in-time recovery, so the 15-minute
recovery point has no mechanism behind it.

The WAL archive the record names has no lock and no writer rule. The COMPLIANCE
lock and the writer key's rule bind what Kopia writes; nothing stops the WAL
writer, or a credential stolen from it, from deleting the WAL objects, and no
check reads how much lock the objects have left. platform-postgres, which holds
every Tenant resource and the Rollout event log, was captured by a daily
snapshot alone.

The 2026-11-04 design review (A3-01, adjudicated P0) found both, and the
maintainer settled the capture on the same day: pgBackRest physical base
backups plus a WAL archive for every Postgres server, platform-postgres
included, with the WAL bucket locked like the Kopia repository.

## Decision

This amends
[record 115](0115-backups-are-kopia-snapshots-in-one-locked-repository-per-environment-on-an-eu-object-store-with-wal-archived-beside-them.md),
whose text now says so: Postgres capture moves out of the Kopia sources, and
Kopia keeps what it already held well, the Tenant exports and the contents of
local-path volumes.

**Capture is physical.** Every Postgres server, platform-postgres included, is
captured by pgBackRest: scheduled physical base backups plus its WAL, archived
continuously to a repository in a bucket of its own Environment on the same
EU-controlled provider as the Kopia repository, where
[record 116](0116-every-store-of-estate-data-runs-on-an-eu-controlled-provider-or-on-owned-hardware.md)'s
rule binds where they go. The 15-minute recovery point of
[record 87](0087-recovery-time-and-recovery-point-are-stated-per-recovery-class.md)
is met by replaying archived WAL over a base backup; a dump is never a server's
capture. Base backups keep 7 daily, 4 weekly and 6 monthly, and WAL is kept no
longer than the oldest base backup kept. Each server switches segment at least
every 5 minutes, so the point holds on a quiet database.

**The WAL bucket is locked, and the lock is watched.** Every object in the WAL
archive carries an object lock in COMPLIANCE mode for 30 days, like the Kopia
repository's objects. The Environment's WAL writer key writes and cannot
delete an object version or shorten a lock; a maintenance job extends the locks
of the WAL objects still kept, and a lifecycle rule removes a WAL object once
its lock has ended and it precedes the oldest base backup kept. So a bug, a
stolen credential or a stopped maintenance run cannot silently shorten the
recovery window: the
**WAL archive freshness check**
reads the bucket, and fails when the newest WAL object has under 7 days of its
lock left — a week of margin to fix the maintenance before any WAL object can
be deleted — or when no object is under 15 minutes old.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Keep the dump-based capture [record 115](0115-backups-are-kopia-snapshots-in-one-locked-repository-per-environment-on-an-eu-object-store-with-wal-archived-beside-them.md) named | The recovery point of [record 87](0087-recovery-time-and-recovery-point-are-stated-per-recovery-class.md) is a claim the capture cannot deliver | A dump cannot be replayed with WAL; a point-in-time recovery needs a physical base backup |
| barman, or logical decoding into the export pipeline | A second tool and a second replay path to hold and drill for one estate | pgBackRest takes the base backups and archives the WAL with one configuration |
| An unlocked WAL bucket, fresh but deletable | The archive looks healthy while a single credential can delete the recovery point behind it | The COMPLIANCE lock is [record 115](0115-backups-are-kopia-snapshots-in-one-locked-repository-per-environment-on-an-eu-object-store-with-wal-archived-beside-them.md)'s own protection, and the WAL archive deserves the same |
| A freshness alert only, with no lock-time probe | The archive looks healthy while stopped maintenance walks the oldest recoverable hour forward | The lock's remaining time is the window the estate actually has, and a check must read it before the last week |
| Managed EU Postgres with its own point-in-time recovery | The estate's capture moves into a store it cannot rebuild the way it rebuilds its own | A trigger to re-record the store under [record 116](0116-every-store-of-estate-data-runs-on-an-eu-controlled-provider-or-on-owned-hardware.md), not a capture decision |

## Consequences

- Easier: the recovery point has one mechanism on every Postgres server; one
  drill covers them all; the WAL writer key alone can no longer shorten the
  recovery window.
- Harder: pgBackRest is another moving part on every server, and its repository
  is a store [record 87](0087-recovery-time-and-recovery-point-are-stated-per-recovery-class.md)
  must hold in a Recovery class; the maintenance job that extends locks must
  keep running, and the check that watches it must run too.
- Forbidden: a dump standing in for a server's capture; an unlocked WAL
  object; a writer key that can delete an object version or shorten a lock; a
  WAL archive whose remaining lock time no check reads.

## Confirmation

The **WAL archive freshness check** fails when a production Postgres server's
newest archived WAL segment is more than 15 minutes old, or the newest WAL
object has under 7 days of its 30-day COMPLIANCE lock left. The
**WAL recovery drill** fails when a production Postgres server archives no WAL,
or a recovery to a chosen time on a throwaway cluster does not reach it.

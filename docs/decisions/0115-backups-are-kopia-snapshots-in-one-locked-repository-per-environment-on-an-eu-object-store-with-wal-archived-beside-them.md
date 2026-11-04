---
status: accepted  # proposed | accepted | locked | superseded
date: 2026-11-04
rests-on: [59, 75, 82, 87, 106, 108, 110, 114, 116]
lessons: [DR-1, DR-2]
---

# Backups are Kopia snapshots in one locked repository per Environment on an EU object store, with WAL archived beside them

## Context

[Record 82](0082-backups-are-per-tenant-generations-and-mirrors-refresh-staging-and-development.md)
makes a Backup generation the set of a Tenant's Tenant exports, keeps
whole-database backups and a WAL archive per Postgres server, and has
production push each Mirror's exports into the target Environment's backup
repository, whose password production holds. It says the copies are encrypted
and off the cluster, but not where they live, what tool writes them, or what
stops a stolen credential from deleting them.
[Record 87](0087-recovery-time-and-recovery-point-are-stated-per-recovery-class.md)
gives Tenant and Project databases a recovery point of 15 minutes, and the
other classes 6 or 24 hours. [Record 110](0110-a-purge-erases-backup-generations-and-mirrors-from-an-inventory-of-every-copy.md)
bounds a Purged Tenant's exports by a 30-day object lock.
[Record 75](0075-three-environments-run-in-the-one-cluster.md) runs three
Environments, each with its own data.

The backup component today is delivery's Go backup and offcluster jobs: age
encryption and an S3 upload ([Rust workspace](../design/rust-workspace.md)).
The maintainer pointed at the backups of the ESA-Blueshell/website repository
as the model. A read of that repository found:

- One Kubernetes CronJob per store dumps it (MariaDB in one transaction, a
  Vault raft snapshot, a Valkey save, uploads, a mail server scaled to zero
  for its copy, a SQLite backup), at fixed night-time hours, with no two runs
  at once.
- Kopia writes every dump into one repository on Scaleway Object Storage in
  nl-ams. Each object carries an object lock in COMPLIANCE mode for 30 days,
  and Kopia's maintenance extends the locks of the blobs still in use. The
  writer key cannot delete an object version.
- The repository password is random and kept in two places. The writer key
  reaches each namespace through its own Vault role.
- Retention keeps the latest snapshot, 7 daily and 4 weekly. Each store is
  its own Kopia source, and each reports to a heartbeat that alerts after 26
  hours without a run.
- A restore script exists, with a rehearsal mode, but nothing runs it on a
  schedule. Its own decision record describes a weekly verify that was never
  built. There is no second copy.

That repository rejected restic in its own decision record. Scaleway is a
French provider, so it meets the rule of
[record 116](0116-every-store-of-estate-data-runs-on-an-eu-controlled-provider-or-on-owned-hardware.md).

## Decision

This amends
[record 82](0082-backups-are-per-tenant-generations-and-mirrors-refresh-staging-and-development.md),
which now says where its generations live and how, and states the mechanisms
behind the targets of
[record 87](0087-recovery-time-and-recovery-point-are-stated-per-recovery-class.md).

**One Kopia repository per Environment.** Production, staging and development
each have one Kopia repository, in a bucket of its own on Scaleway Object
Storage in nl-ams, with its own random password. The password is kept in Vault
under the Environment's path and in the maintainer's offline store, from which
[record 106](0106-the-control-plane-is-restored-in-a-dependency-order-that-is-tested-drilled-and-timed.md)
restores. Production also holds the lower Environments' passwords, to push
Mirror exports; a lower Environment never holds production's password or
writer key.

**The lock is the off-cluster copy.** Every object Kopia writes carries an
object lock in COMPLIANCE mode for 30 days. Full maintenance runs more often
than the lock period and extends the locks of every blob still in use. Each
Environment's writer key can write objects and cannot delete an object version
or shorten a lock. A noncurrent version is removed once its lock has ended, by
a lifecycle rule on the bucket or by a clean-up job whose key the backup
component does not hold. That one locked bucket per Environment is the
off-cluster copy; there is no second provider and no local copy.

**What goes in.** Each Tenant export is its own Kopia source, kept for the
retention set with its Tenant's schedule and stated in the copy inventory of
[record 110](0110-a-purge-erases-backup-generations-and-mirrors-from-an-inventory-of-every-copy.md).
Whole-database backups, platform-postgres and the contents of local-path
volumes are each a source too, taken by a scheduled job per store, with no two
runs of one source at once. Whole-database backups keep 7 daily, 4 weekly and
6 monthly snapshots. The datastore's backup and Vault's snapshots stay
fleet-infra's, as
[record 59](0059-vault-unseal-and-datastore-backup-are-assumed-from-fleet-infra.md)
says; the rule of
[record 116](0116-every-store-of-estate-data-runs-on-an-eu-controlled-provider-or-on-owned-hardware.md)
binds where they go.

**WAL beside them.** Each Postgres server archives its WAL continuously to a
bucket of its own Environment at the same provider, and switches segment at
least every 5 minutes, so the 15-minute recovery point of
[record 87](0087-recovery-time-and-recovery-point-are-stated-per-recovery-class.md)
holds on a quiet database. WAL is kept no longer than the oldest base backup
kept.

**A restore is rehearsed every week.** The backup component restores the
latest snapshot of each store into throwaway containers once a week and checks
what it reads back. Each result is an active check result of
[record 108](0108-active-checks-run-in-the-owning-components-observation-reads-their-results-and-one-heartbeat-lives-outside-the-cluster.md):
Observation reads it, and a pass also reaches the external heartbeat, so a
rehearsal that stops running raises an alert from outside the cluster. The
restore order is rehearsed in CI on every release, and a timed drill runs on
the real estate once a year, as
[record 106](0106-the-control-plane-is-restored-in-a-dependency-order-that-is-tested-drilled-and-timed.md)
sets out.

The maintainer's personal backups are not an estate-kit concern.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| restic | Its maintenance does not extend object locks, so a locked bucket and pruning work against each other | ESA-Blueshell/website rejected it in its own decision record; Kopia writes the locks and extends them in maintenance |
| A second provider, with `kopia repository sync-to` | A second bill, a second credential set and a sync to watch | The COMPLIANCE lock already protects against a stolen key; one locked bucket per Environment is the off-cluster copy |
| A local copy beside the cluster | A disk to keep, and a copy lost with the site | It adds a copy in the place the backups must outlive |
| Object lock in GOVERNANCE mode | A key with the bypass permission can delete inside the lock | COMPLIANCE cannot be shortened by any key, the estate's own included |
| No object lock | One stolen writer key deletes every backup | The lock is the protection that makes one copy enough |
| One repository for every Environment | One password opens production, staging and development; a lower Environment holds production's password | One repository and one password per Environment |
| Whole-database backups only, with no WAL | The recovery point of a Project database is a day, not 15 minutes | WAL meets [record 87](0087-recovery-time-and-recovery-point-are-stated-per-recovery-class.md) |
| A restore script that runs only when someone runs it | A broken backup is found on the day it is needed | ESA-Blueshell/website's weekly verify was described and never built; here it is a scheduled check |

## Consequences

- Easier: one tool and one bucket per Environment; a stolen writer key cannot
  delete a backup; a broken backup shows up within a week; each Environment's
  restore needs only its own password.
- Harder: a Purged Tenant's exports stay in the bucket for up to the lock
  period after the full maintenance that drops them, and the rest of its data
  until the last copy in the inventory of
  [record 110](0110-a-purge-erases-backup-generations-and-mirrors-from-an-inventory-of-every-copy.md)
  expires; a Scaleway outage blocks every restore until it ends; a lock cannot
  be cut short, even to save money; maintenance must keep running, or locks
  lapse.
- Forbidden: a backup outside its Environment's repository; a repository or
  password shared between Environments; production's password or writer key in
  a lower Environment; a writer key that can delete an object version or
  shorten a lock; an object written without its lock; a store in a Recovery
  class whose restore is not rehearsed.

## Confirmation

The **Weekly restore rehearsal** fails when a store's latest snapshot has not
been restored and checked within a week, when a restored snapshot fails its
check, or when its result does not reach Observation and the external
heartbeat. The **Backup repository credential check** fails when a staging or
development Environment holds production's repository password or writer key,
or two Environments share a repository or password. The **Backup object lock
check** fails when a repository's objects lack a 30-day COMPLIANCE lock,
maintenance does not extend locks, a writer key can delete an object version
or shorten a lock, or nothing removes a noncurrent version once its lock has
ended. The **WAL archive freshness check** fails when a production Postgres
server's newest archived WAL segment is more than 15 minutes old. The **WAL
recovery drill** still proves a recovery to a chosen time.

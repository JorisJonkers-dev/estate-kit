---
status: accepted  # proposed | accepted | locked
date: 2026-11-04
rests-on: [1, 59, 82, 114]
amends: [59]
lessons: [DR-1, DR-2]
---

# Recovery time and recovery point are stated per Recovery class before the drill, and the drill measures them

Amended by [record 140](0140-break-glass-custody-is-written-and-drilled-and-a-named-successor-holds-a-sealed-copy-of-the-recovery-key.md): the drill now verifies that a named recovery-key successor holds a sealed copy of the recovery key, an open item until 2027-04-30, so the keystone a break-glass needs survives the maintainer's absence.

Amended by [record 141](0141-a-second-copy-exists-only-for-the-critical-set-at-a-second-eu-provider.md): the table carries a row for the Critical set's second copy, at a second EU provider, held to the age each item states.

Revised: 2026-11-05: the rehearsal sentence names the stores a drill covers and
excludes the datastore until its backup exists, carrying it as the open item
[datastore backup](https://github.com/JorisJonkers-dev/estate-kit/issues/41)
due 2027-04-30; the Datastore, Delivery's history and Tenant and Project
databases rows name the mechanisms that now meet them, including
[record 120](0120-postgres-is-captured-by-pgbackrest-base-backups-plus-archived-wal-in-a-locked-bucket-on-every-server.md)'s
pgBackRest capture.

## Context

One control-plane node holds the k3s datastore, every local-path volume, Vault
and the volume that holds Vault's snapshots and the Postgres dump. A datastore
backup restores Kubernetes objects, not the contents of local-path volumes.
The estate already takes a Vault raft snapshot every 6 hours and keeps an
off-cluster copy, but no estate-kit page cites or owns it. No record orders a
restore after total loss, and no record states a recovery time or a recovery
point. The architecture evaluation of 2026-11-04 (sections 2.2, 3.18 and 9.13)
marks these facts as strong and rates the recovery of the substrate as poor.

[Record 59](0059-vault-unseal-and-datastore-backup-are-assumed-from-fleet-infra.md)
leaves Vault unseal and the datastore's backup to fleet-infra and says
estate-kit's recovery pages "describe a target, not a fact". It names no target.
[Record 82](0082-backups-are-per-tenant-generations-and-mirrors-refresh-staging-and-development.md)
backs up each Tenant as a Backup generation and archives WAL per Postgres
server, again with no stated recovery point.

A drill run without a target can only report a number; it cannot say whether
the number is good enough. The evaluation's rule is that the targets come
first and the drill measures against them.

## Decision

Each Recovery class has a recovery time objective (how long from loss until
it serves again) and a recovery point objective (how much recent data may be
lost), set by the maintainer before the first drill. The restore proof and the
yearly drill measure each class against its targets and record the result; a
miss is an issue, never a quiet change of the target. A new store is put in a
class before it holds production data.

This amends the assumption of
[record 59](0059-vault-unseal-and-datastore-backup-are-assumed-from-fleet-infra.md).
fleet-infra still decides how the datastore and Vault are backed up, but
estate-kit now states what it needs from them as targets, and the drill shows
whether fleet-infra's mechanism meets them. The sentence in that record about "a target, not a fact" cites this table.

The maintainer set the targets below on 2026-11-04. The column "How it is
met" names the mechanism the drill measures; where it is estate-kit's, it is
[record 115](0115-backups-are-kopia-snapshots-in-one-locked-repository-per-environment-on-an-eu-object-store-with-wal-archived-beside-them.md)'s.

| Recovery class | What it holds | How it is met | RTO | RPO |
| --- | --- | --- | --- | --- |
| Datastore | The k3s datastore: every Kubernetes object, ProjectControl and Tenant resources included | fleet-infra's backup and restore ([record 59](0059-vault-unseal-and-datastore-backup-are-assumed-from-fleet-infra.md)), taken at least every 6 hours; none is written today, carried as the open item [datastore backup](https://github.com/JorisJonkers-dev/estate-kit/issues/41), due 2027-04-30 | 4 h | 6 h |
| Vault | Secrets, Transit keys, policies | A raft snapshot every 6 hours with an off-cluster copy | 4 h | 6 h |
| Delivery's history | The Rollout event log, the job table and the Tenant operation log on the shared platform-postgres | pgBackRest base backups of platform-postgres with its archived WAL ([record 120](0120-postgres-is-captured-by-pgbackrest-base-backups-plus-archived-wal-in-a-locked-bucket-on-every-server.md)) | 24 h | 24 h |
| Tenant and Project databases | Every Project database, a multi-tenant Project's shared database included ([record 114](0114-multi-tenant-projects-keep-their-tenants-in-shared-tables-separated-by-row-level-security.md)) | pgBackRest base backups and the WAL archived continuously, for a server; Tenant exports, for one Tenant ([record 82](0082-backups-are-per-tenant-generations-and-mirrors-refresh-staging-and-development.md), [record 120](0120-postgres-is-captured-by-pgbackrest-base-backups-plus-archived-wal-in-a-locked-bucket-on-every-server.md)) | 4 h | 15 min |
| Volume contents | Local-path volumes other than Postgres | A daily snapshot in the Environment's Kopia repository; a datastore backup does not restore them | 24 h | 24 h |
| Registry | Renders, their signatures and the tags that name them | Held by the registry provider, off the cluster, with a nightly copy; a render can be composed again from its pinned inputs, a tag cannot | 24 h | 24 h |
| Binary cache | Host closures | Off the cluster; rebuilt in CI from the pinned source | 24 h | none: rebuildable |
| Second copy of the Critical set | A copy of each item of the [Critical set](../../CONTEXT.md): the Vault snapshot, the signing and repository credentials, and the datastore snapshot ([record 141](0141-a-second-copy-exists-only-for-the-critical-set-at-a-second-eu-provider.md)) | At a second EU provider, written with each first copy and held to a stated age: within 6 hours for the Vault snapshot and the datastore snapshot, within 24 hours of any change for a credential; its holder is not yet chosen, an open item, due 2027-04-30 ([record 141](0141-a-second-copy-exists-only-for-the-critical-set-at-a-second-eu-provider.md)) | the copied class's | the copied class's |

The k3s datastore stays SQLite, deliberately different from the applications'
Postgres; its restore order is [record 106](0106-the-control-plane-is-restored-in-a-dependency-order-that-is-tested-drilled-and-timed.md)'s.

Mail, buckets and other component stores join a row, or get their own, when
the restore order that orders all of them is written. The offline recovery key
is not a store and has no row: its custody, which a named successor holds a
sealed copy of, is [record 140](0140-break-glass-custody-is-written-and-drilled-and-a-named-successor-holds-a-sealed-copy-of-the-recovery-key.md)'s,
an open item, due 2027-04-30, until the successor is named.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Run the drill first and adopt what it measures as the targets | The targets describe what happened, not what the estate needs | A drill without a target cannot fail |
| One RTO and RPO for the whole estate | The registry and the event log are held to the same bound as Tenant data, or the bound is too loose for Tenants | The classes differ by orders of magnitude in cost and need |
| Leave the targets to fleet-infra, as [record 59](0059-vault-unseal-and-datastore-backup-are-assumed-from-fleet-infra.md) does today | estate-kit relies on numbers no one has written | estate-kit is the consumer and states what it needs; fleet-infra still chooses how |
| Move the datastore to Postgres, like the applications | The datastore's recovery would share the applications' failure modes and tools | It stays SQLite, deliberately different |
| A second k3s server instead of targets | Two voting etcd members tolerate no failure, and control-plane members do not copy local volumes | It moves the risk and states no target |

## Consequences

- Easier: a drill has a pass and a fail; the maintainer can see which store
  is the weakest; fleet-infra knows what it must provide.
- Harder: every store needs a class and a measured restore; a target that the
  current mechanism cannot meet is a visible gap with an owner.
- Forbidden: a row with no target; changing a target because a drill missed it,
  without an issue; a store that holds production data with no class.

## Confirmation

The **Recovery targets lint** fails when a row of the table above has no RTO or
no RPO while this record is Accepted. The **Weekly restore rehearsal** proves
each store a drill covers restores, every week: the Tenant exports,
platform-postgres, every Project database and the volume contents, captured by
[record 115](0115-backups-are-kopia-snapshots-in-one-locked-repository-per-environment-on-an-eu-object-store-with-wal-archived-beside-them.md)'s
Kopia repository and
[record 120](0120-postgres-is-captured-by-pgbackrest-base-backups-plus-archived-wal-in-a-locked-bucket-on-every-server.md)'s
pgBackRest. The datastore is excluded until its backup exists: the open item
[datastore backup](https://github.com/JorisJonkers-dev/estate-kit/issues/41),
due 2027-04-30. The **Restore proof** fails when a backup
of a Recovery class does not restore into the throwaway environment, or takes
longer than its RTO, or loses more than its RPO. The **WAL recovery drill**
already covers the recovery of one Postgres server to a chosen time. The
**Second-copy freshness check** fails when an item of the Critical set has no
second copy at the second EU provider, or its newest copy is older than the age
its row states. The yearly
drill on the real estate is the maintainer's, and its recorded times are
reviewed against this table; no check runs it. It also verifies that the named
recovery-key successor holds a sealed copy
([record 140](0140-break-glass-custody-is-written-and-drilled-and-a-named-successor-holds-a-sealed-copy-of-the-recovery-key.md)),
and that each second copy restores, from
[record 141](0141-a-second-copy-exists-only-for-the-critical-set-at-a-second-eu-provider.md);
each is an open item, due 2027-04-30, until the successor and the second
copy's holder are named.

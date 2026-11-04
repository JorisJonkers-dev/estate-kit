---
status: proposed  # proposed | accepted | locked
date: 2026-11-04
rests-on: [1, 59, 82]
lessons: [DR-1, DR-2]
---

# Recovery time and recovery point are stated per Recovery class before the drill, and the drill measures them

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
whether fleet-infra's mechanism meets them. When this record is accepted, the
sentence in that record about "a target, not a fact" cites this table.

The classes and today's mechanisms are below. The targets are open: no number
here is decided, and this record is not accepted until the maintainer has set
every target. The column "What today gives" is a fact where a source says so,
and a starting point for the maintainer, not a proposal of the target.

| Recovery class | What it holds | What today gives | RTO | RPO |
| --- | --- | --- | --- | --- |
| Datastore | The k3s datastore: every Kubernetes object, ProjectControl and Tenant resources included | No backup and no written restore today ([record 59](0059-vault-unseal-and-datastore-backup-are-assumed-from-fleet-infra.md)); fleet-infra's to provide | open | open |
| Vault | Secrets, Transit keys, policies | A raft snapshot every 6 hours with an off-cluster copy, so no better than 6 hours of loss | open | open |
| Delivery's history | The Rollout event log, the job table and the Tenant operation log on the shared platform-postgres | The platform-postgres dump, on the same node's volume | open | open |
| Tenant and Project databases | Each Tenant database and each single-tenant Project's databases | Backup generations on each Tenant's schedule, and WAL archive per server ([record 82](0082-backups-are-per-tenant-generations-and-mirrors-refresh-staging-and-development.md)) | open | open |
| Volume contents | Local-path volumes other than Postgres | A Project's Backup generation where it declares one; a datastore backup does not restore them | open | open |
| Registry | Renders, their signatures and the tags that name them | Held by the registry provider, off the cluster; a render can be composed again from its pinned inputs, a tag cannot | open | open |
| Binary cache | Host closures | Off the cluster; rebuildable in CI from the pinned source | open | open |

Mail, buckets and other component stores join a row, or get their own, when
the restore order that orders all of them is written. The offline recovery key
is not a store and has no row.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Run the drill first and adopt what it measures as the targets | The targets describe what happened, not what the estate needs | A drill without a target cannot fail |
| One RTO and RPO for the whole estate | The registry and the event log are held to the same bound as Tenant data, or the bound is too loose for Tenants | The classes differ by orders of magnitude in cost and need |
| Leave the targets to fleet-infra, as [record 59](0059-vault-unseal-and-datastore-backup-are-assumed-from-fleet-infra.md) does today | estate-kit relies on numbers no one has written | estate-kit is the consumer and states what it needs; fleet-infra still chooses how |
| Decide starting numbers in this record | Numbers chosen by a writer, not by the person who pays for them | The targets are the maintainer's choice |
| A second k3s server instead of targets | Two voting etcd members tolerate no failure, and control-plane members do not copy local volumes | It moves the risk and states no target |

## Consequences

- Easier: a drill has a pass and a fail; the maintainer can see which store
  is the weakest; fleet-infra knows what it must provide.
- Harder: every store needs a class and a measured restore; a target that the
  current mechanism cannot meet is a visible gap with an owner.
- Forbidden: accepting this record with a target left open; changing a target
  because a drill missed it, without an issue; a store that holds production
  data with no class.

## Confirmation

The **Recovery targets lint** fails when a row of the table above has no RTO or
no RPO while this record is Accepted. The **Restore proof** fails when a backup
of a Recovery class does not restore into the throwaway environment, or takes
longer than its RTO, or loses more than its RPO. The **WAL recovery drill**
already covers the recovery of one Postgres server to a chosen time. The yearly
drill on the real estate is the maintainer's, and its recorded times are
reviewed against this table; no check runs it.

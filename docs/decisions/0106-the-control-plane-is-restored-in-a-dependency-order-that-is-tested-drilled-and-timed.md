---
status: accepted  # proposed | accepted | locked
date: 2026-11-04
rests-on: [9, 31, 59, 63, 87]
lessons: [DR-1, DR-2]
---

# The control plane is restored in a dependency order that is tested, drilled and timed

## Context

The estate has one control-plane node, `frankfurt-contabo-1`. It holds the k3s
datastore as one SQLite file, every local-path volume, Vault, and the volume
that holds Vault's snapshots and the Postgres dump (the architecture evaluation
of 2026-11-04, section 3.18). Vault takes a raft snapshot every six hours, with
an off-cluster copy; the design neither cites nor owns it.

[Record 59](0059-vault-unseal-and-datastore-backup-are-assumed-from-fleet-infra.md)
leaves Vault's unseal and the datastore backup to fleet-infra and calls
estate-kit's recovery pages a target, not a fact. A datastore backup restores
Kubernetes objects, not what local-path volumes hold. The failure table on
[Operating the estate](../design/operating.md#when-something-underneath-fails)
lists the steps for a lost control-plane node, but no record orders them, says
which must wait for which, or states how long a restore may take.

The order matters. If Flux reconciles a data-holding Project before its volumes
are restored, the workloads start on empty stores. If a component reads an
empty store as the truth, it may act as if everything was deleted. Flux finds
each Project's live render in the registry, which lives off the cluster
([record 9](0009-the-live-render-is-a-signed-registry-tag-per-project-and-environment.md)),
and nodes fetch their closures from a cache off the cluster
([record 31](0031-host-closures-are-built-in-ci-and-cached-outside-the-cluster.md)).
Delivery rebuilds its Rollouts from observed state
([record 63](0063-delivery-has-one-writer-and-reconciles-from-observed-state.md)).

A second k3s server is not high availability here: two embedded etcd members
tolerate no failure, and control-plane members do not replicate application
data held on local volumes.

## Decision

After total loss of the control-plane node, the estate is restored in this
order, written as an executable procedure whose steps name what they depend on:

1. A new host from nixos-anywhere, with its first generation from the cache, and
   the offline credentials (Recovery key, admin credential, backup decryption
   keys) from the maintainer's offline store.
2. The k3s datastore from its off-provider copy. Every Flux Kustomization of a
   Project that holds data stays suspended until step 7, when its Project is
   resumed after the components have applied their Retirement tombstones. The
   maintainer corrected this from step 5 on 2026-11-04, since Flux is not
   bootstrapped until step 6.
3. Vault from its raft snapshot, unsealed as fleet-infra provides.
4. The registry and the binary cache, checked reachable; neither depends on the
   cluster, and neither may run on the control-plane node.
5. The contents of local-path volumes and platform-postgres, from their
   off-cluster backups. The backup times are compared and any gap is recorded.
6. Flux, bootstrapped from the bootstrap render with the CLI.
7. Projects resumed in dependency order. Components apply their Retirement
   tombstones first
   ([record 105](0105-removal-is-a-retire-lifecycle-with-durable-retirement-tombstones-and-declared-moves-and-prune-protected-kinds-never-prune.md))
   and hold destructive actions until their stores are confirmed restored.
8. Delivery reconciles its Rollouts from observed state, marking reconstructed
   events.
9. The time taken and the data lost are recorded against the targets.

The maintainer runs the procedure with the offline admin credential; Delivery
writes no Flux object. The restore order is rehearsed in CI on every release,
on a throwaway cluster. Once a year the procedure is drilled on the real estate
and timed against the recovery time and point of each Recovery class
([the planned record on recovery targets](register.md)). It builds on
[record 59](0059-vault-unseal-and-datastore-backup-are-assumed-from-fleet-infra.md),
which still leaves unseal and the datastore backup to fleet-infra. The k3s
datastore stays one SQLite file, deliberately different from the applications'
Postgres.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| The failure table's three steps, unordered (today) | Flux and the components start on empty stores | The order is where the data is lost |
| A second k3s server | A node to run; two etcd members tolerate no failure | No high availability, and no copy of local volumes |
| Test only on a throwaway cluster | A procedure that has never met the real backups | A drill on the real estate finds what a test cluster lacks |
| Drill without targets | Any time measured counts as success | The targets come first, and the drill measures them |
| A single embedded etcd member with snapshots to object storage | A datastore change on the one control-plane node | The datastore stays SQLite |
| Rehearse the order only in the yearly drill | A broken order is found once a year, on the real estate | Rehearsed in CI on every release |
| Drill the real estate more often than yearly | Downtime the maintainer schedules, several times a year | The CI rehearsal on every release covers the order; the yearly drill measures the real backups |

## Consequences

- Easier: a lost control-plane node has a known order, a known time and a known
  data loss; no data-holding Project starts on an empty store.
- Harder: the procedure is code to keep current with every store it restores;
  every release waits for the rehearsal; the yearly drill costs downtime the
  maintainer schedules.
- Forbidden: resuming a data-holding Project before its volumes are restored; a
  component acting destructively before its store is confirmed restored; the
  registry or the binary cache on the control-plane node.

## Confirmation

The **Restore procedure graph check** fails when a step names a dependency that
is no step, the steps form a cycle, or a Recovery class has no restore step.
The **Restore order rehearsal** fails when the procedure, run in CI on every
release on a throwaway cluster from backups alone, does not bring every Project
back to Serving, or unsuspends a data-holding Project before its volumes are
restored. The **Cold-rebuild drill record** fails when the last drill on the
real estate is older than a year, or its recorded time or data loss exceeds the
targets.

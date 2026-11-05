---
status: proposed  # proposed | accepted | locked
date: 2026-11-04
rests-on: [12, 13, 21, 31, 59]
lessons: [DR-1, DR-2]
---

# A host applier on each node pulls its signed host tag, decides a reboot before the Lease, and switches on its own only where its Node class's fallback is rehearsed

## Context

NixOS nodes are switched today by deploy-rs, pushed from the maintainer's
machine. The review recommended deferring a bespoke applier; the maintainer
chose to build it alongside Delivery ([review](../research/review/README.md)
D2), with the switching rules of D11. Only one node runs the control plane.

Three parts cannot be built as first written
([hosts review](../research/review/hosts.md)), and the architecture evaluation
of 2026-11-04, section 3.14, confirms them:

- "Boots its previous generation" has no mechanism on four of six nodes.
  Automatic boot assessment exists in nixpkgs for systemd-boot only; the
  Raspberry Pis boot through U-Boot and extlinux, and the Contabo VPS through
  GRUB in BIOS mode. The fleet is headless.
- RBAC cannot scope `pods/eviction` to one node. A ValidatingAdmissionPolicy on
  `spec.nodeName` can.
- The k3s documentation says a rollback to an earlier minor version needs a
  datastore snapshot taken on that minor. A NixOS rollback swaps the k3s binary
  and leaves the datastore as the newer minor wrote it.

An older generation also recovers software, never mutable data, and a
dependency with one replica is down while its node switches, whatever the
applier does (section 9.9 of the evaluation). The evaluation's section 7.4
names an `adapter-boot` crate, one strategy per bootloader, with a `None`
strategy that disables automatic rollout.

## Decision

- **Pull, not push.** A Rust agent on each node, a systemd service beside k3s,
  polls its node's host tags, a numbered, immutable Sequence tag per
  publication ([record 98](0098-the-live-pointer-is-an-immutable-sequence-tag-that-flux-selects-by-version.md),
  extended to hosts). Delivery publishes the next `host/<node>:<number>`;
  the applier switches only to the highest and refuses a lower or replayed
  one, verifies the chosen tag with the host key or the recovery key, and
  fetches and verifies the closure from the binary cache of
  [record 31](0031-host-closures-are-built-in-ci-and-cached-outside-the-cluster.md).
  A host rollback publishes a higher number at the signed digest of an older
  generation. Fetching disrupts nothing, and neither fetching nor signing
  needs the cluster: the cache lives off it, and its signing key lives on the
  owned builder
  ([record 31](0031-host-closures-are-built-in-ci-and-cached-outside-the-cluster.md)).
- **Decide the reboot before the Lease.** It compares the fetched closure's
  kernel, initrd, modules, kernel parameters and device trees with the booted
  ones. A reboot change is staged with `switch-to-configuration boot`, and the
  Lease and drain happen only once the node's maintenance window opens. A live
  change goes `test`, then a health check, then `boot`.
- **One node at a time, each node only itself.** A cluster-wide Lease
  serialises switches and reboots; pods leave through the Eviction API so
  PodDisruptionBudgets hold. Each node's applier has its own credential,
  static to that node: sops-nix delivers it with the node's host secrets, and
  it is replaced only at re-enrolment. A ValidatingAdmissionPolicy on
  `spec.nodeName` lets it cordon and evict only its own node; if the
  admission-policy spike fails, the same limit is held by a code rule in the
  applier itself, unit-tested against a field selector on `spec.nodeName`,
  that refuses an eviction of any pod on another node. No outside coordinator
  orders the nodes, and Delivery does not
  pace them: order is an applier precondition. Each applier waits until its
  predecessor in the order reports running the new generation, through a Node
  annotation the predecessor's applier writes, or is recorded skipped; two
  adjacent nodes never switch together. A skipped node is recorded and counts
  as satisfied; a node that is down stalls the rollout until the maintainer
  skips it.
- **Node order is derived, then carried in the payload.** It follows from the
  change: a k3s version change goes control plane first, then one canary
  worker, then the rest; an OS-only change goes canary, workers, control
  plane last. A check refuses any target that breaks the Kubernetes version
  skew policy. The compiled order is published with the host tags as the
  rollout payload, and each applier reads its place and its predecessor from
  it. The page gives the rules: [Order of nodes](../design/hosts.md#order-of-nodes).
- **Soak and windows pace the rollout.** After the canary worker runs the new
  generation, the rollout waits 24 hours before the next worker; a change
  that bumps k3s waits for a full maintenance window before its next member.
  A node's window is stated in site-local IANA time
  ([record 123](0123-host-maintenance-windows-are-stated-in-site-local-iana-time-and-the-link-between-sites-is-fleet-infra-s.md)).
- **Snapshot before a k3s minor bump.** Before it switches the control-plane
  node to a new k3s minor, the applier takes a consistent datastore snapshot on
  the old minor, with the server token, copies it off the node beside the
  datastore backups of
  [record 59](0059-vault-unseal-and-datastore-backup-are-assumed-from-fleet-infra.md),
  and records its id in the node's rollout state. A failed snapshot stops the
  switch. Rolling that node back is the old binary plus a restore of that
  snapshot, a written procedure.
- **Automatic rollout per Node class, only after its fallback is rehearsed.**
  Each Node class has a boot strategy in `adapter-boot`: boot counting with
  systemd-boot, `grub-reboot` with `default=saved` for GRUB, Pi firmware
  `tryboot` if spike #15 shows it works with the Pis' boot chain, or `None`.
  A class switches on its own only when its strategy is not `None` and a
  rehearsal on a real node of the class is recorded: a generation that fails
  its health check was booted, and the node returned to its previous
  generation unaided. A class with `None`, or with no recorded rehearsal, gets
  manual activation: the applier fetches and stages, and an Operator starts
  each switch, with a rehearsed recovery procedure for that class. A change to
  a class's bootloader or strategy voids its rehearsal.
- **No zero-downtime promise.** A Process with one replica on a switching node
  is down for that switch, and the plan says so.
- **Break-glass is deploy-rs under the maintainer's SSH credential**, with
  targets generated from host data. It is the one documented path outside the
  cache signature of
  [record 31](0031-host-closures-are-built-in-ci-and-cached-outside-the-cluster.md):
  the only way a node runs a generation no applier verified against the
  binary cache. T6, the applier reduced to a stager that fetches and stages
  while a human applies, is a review trigger, not a designed fallback.

The page is [Hosts](../design/hosts.md).

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Defer, keep deploy-rs (review's recommendation) | Hosts need the maintainer's machine to change | The maintainer chose to build it now |
| kured plus a small stager | kured's cluster-wide grant; per-site locks | Weaker isolation of eviction |
| Lease, drain, switch, then wait for the window | A node sits drained for hours | D11 |
| Node-to-node push of closures | A node holds credentials to other nodes | Each node pulls its own signed tag |
| A fixed node order, or declared waves | The order goes stale when the change differs, and ignores the version skew rule | The order is derived from the change; k3s bumps go control plane first |
| CI moves the host tag, or nodes follow main | A deploy credential in CI, or nodes that apply what nobody signed | Delivery publishes the signed host tag, as it does for Projects; the key stays in Vault |
| A serverless host coordinator outside the cluster, a scale-to-zero container at a provider that orders nodes and moves host tags ([decomposition research](../research/decomposition.md#host-updates-outside-the-cluster)) | The host signing key leaves Vault or needs a route to it, reopening [record 21](0021-renders-and-host-tags-are-signed-by-separate-keys-with-an-offline-recovery-key.md); durable rollout state and a provider account outside the estate; one more deployable | Dropped by the maintainer on 2026-11-04. Each node's own applier, held to its own node by the admission policy, and the cluster Lease already order the nodes, so a coordinator would add durable state and a second home for a signing key and catch no failure the Lease misses |
| Automatic rollout on every class at once, trusting the bootloader | A class whose fallback does not work leaves a headless node unbootable | Four of six nodes have no proved boot assessment |
| Rely on the NixOS generation to undo a k3s minor bump | The datastore stays at the newer minor; k3s cannot start the old binary on it | The k3s rollback documentation requires a snapshot from the old minor |
| Proceed after a stated wait past a down node | The rollout continues on the clock while a node nobody examined is down | A down node stalls the rollout until the maintainer records the skip (2026-11-04 review, question 22) |
| RBAC to limit evictions to the node's own pods | Cannot be expressed: RBAC grants `pods/eviction` by namespace, not by node | The admission policy can, with a field-selector code rule behind it if the spike fails |
| A short-lived applier credential, renewed on a schedule | Renewal machinery on the node, or a reachability the cluster's loss must not take from it | A static per-node credential, replaced only at re-enrolment |
| agenix for the host secrets, or the node fetching them from Vault | A second tool to keep, or the cluster on the activation path | One tool: sops-nix decrypts the node's secrets on the node |
| A designed T6 fallback, the applier reduced to a stager a human applies | A second mode to build, test and keep, and a fallback that quietly loses the admission-policy isolation | A review trigger; deploy-rs under the maintainer's SSH credential is the one path outside the cache signature |

## Consequences

- Easier: no push credential and no coordinator to run; nodes update without
  the maintainer's machine; a class with a proved fallback updates in its
  window unattended.
- Harder: the largest bespoke component in the plan; each Node class needs a
  rehearsal on real hardware before it rolls out on its own, and again after a
  bootloader change; a k3s minor bump waits for its snapshot.
- Forbidden: a reboot outside the node's window; two nodes switching at once;
  an applier that cordons or evicts on another node; any path outside the
  cache signature but deploy-rs under the maintainer's SSH credential; a
  designed fallback that reduces the applier to a stager; automatic rollout on a
  class with strategy `None` or no recorded rehearsal; a k3s minor switch of
  the control plane without a snapshot from the old minor; a host rollback
  that rewrites a tag instead of publishing a higher number; an applier that
  proceeds past a down node by itself, before the maintainer records a skip.

## Confirmation

The **Host VM tests**, one NixOS VM test per node class, run the applier
through a live change and a reboot change; the **Node-order check** refuses a
target that breaks the version skew policy; the **Eviction fixture** asserts
the admission policy refuses a cordon or eviction on another node, and the
**Eviction code rule fixture** holds the same limit in the applier's code when
the admission-policy spike fails: it fails when the field-selector code rule
accepts an eviction of a pod on another node. The **Closure signature test**
fails when the applier switches to a closure whose signature does not verify
against the cache key: the deploy-rs break-glass under the maintainer's SSH
credential is the one exception, named above. The **Automatic rollout gate
test** fails when the applier switches a node on its
own whose class has strategy `None` or no recorded rehearsal. The **Boot
fallback rehearsal** fails when a node of a class does not return to its
previous generation unaided after booting one that fails its health check. The
**k3s minor snapshot test** fails when the control-plane node switches to a new
k3s minor without a recorded snapshot from the old minor, or after the snapshot
failed. The **Host rollout failure scenarios** fail when a blocked drain, a
volume pinned to the node, too little spare capacity, loss of the control
plane mid-rollout, or a Lease that expires while an earlier node is still down
leaves a node drained, a second node switching, or the rollout continuing. The
**Host sequence tag test** fails when a host applier switches to any tag
but the highest number of its node, or accepts a lower, replayed or unsigned
one. The **Host rollout order check** fails when two adjacent nodes switch
together, or a node proceeds before its predecessor reports running the new
generation or a skip is recorded, or a recorded skip does not satisfy the
next node. The **Host soak check** fails when a rollout proceeds before the
24-hour soak after the canary worker ends, or a k3s change proceeds without
a full maintenance window.

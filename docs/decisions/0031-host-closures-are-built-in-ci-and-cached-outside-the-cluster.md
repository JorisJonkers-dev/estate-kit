---
status: proposed  # proposed | accepted | locked
date: 2026-11-04
rests-on: [12, 13, 21]
lessons: [DR-1]
---

# Host data is rendered by the compiler for hand-written modules, and host closures are built on owned hardware into a signed static cache outside the cluster

## Context

A node must be able to fetch its generation when the cluster is down, and must
not build it itself. Host configuration is partly generated from Infrastructure
Intent and partly written by hand in Nix, and the two must not mix. Whoever holds
the binary cache's signing key can sign root code for every node
([review](../research/review/README.md) D10); that key is decided in
[record 21](0021-renders-and-host-tags-are-signed-by-separate-keys-with-an-offline-recovery-key.md).

A NixOS closure with its build inputs is larger than the 10 GB of disk a
provider's serverless job gets, such a job keeps no Nix store between runs, and
NixOS VM tests need KVM
([decomposition research](../research/decomposition.md#where-the-builds-run)).
Nix reads and writes a signed binary cache on any S3-compatible bucket as
static narinfo and NAR files, with no server process. Attic, the first cache
named, needs a server and a database. The architecture evaluation of
2026-11-04 (sections 5 and 8) therefore puts the closure builder on owned
hardware with KVM and the cache on object storage, off the cluster and off the
control-plane node, and says neither may share a machine with anything the
control plane needs to recover.

## Decision

- The compiler renders host data from Infrastructure Intent; hand-written Nix
  modules consume it. Generated host data and hand-written modules are
  separate files, and a generated file is never hand-edited.
- **The closure builder runs on owned hardware with KVM**, as the estate-kit
  CI job beside nix-config. It builds every node's closure on a change to
  Infrastructure Intent or the hand-written modules, and on a schedule for
  nixpkgs updates, from a warm Nix store, and runs one NixOS VM test per Node
  class.
- **The binary cache is a signed, static Nix cache on object storage**:
  narinfo and NAR files, with no process to run. It lives off the cluster, on
  no machine the control plane needs to recover, so a node fetches and
  verifies its generation while the cluster is down. Nodes only read it and
  trust it through `trusted-public-keys`; only the closure builder writes it.
  Its location is named in Platform Intent.
- **The cache's signing key is environment-scoped and held by the builder.**
  Only the builder's signing job, in its environment, can use it, as
  [record 21](0021-renders-and-host-tags-are-signed-by-separate-keys-with-an-offline-recovery-key.md)
  sets out. It never reaches a node or the cluster.
- Delivery moves the host tags only after the build and the VM tests pass.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| A cache inside the cluster | Nodes cannot fetch while the cluster is down | Hosts must recover the cluster |
| Nodes build their own closures | CPU and memory on small nodes; no gate before a switch | The VM test is the gate, and per-node builds defeat the cache |
| Hand-write the host data too | Intent and host configuration drift apart | The compiler already owns Intent |
| Server-side signing (niks3) with OIDC push | A signing service to run | A later upgrade |
| Attic | A server and a database to run, back up and keep up while the cluster is down | A static cache needs neither; Attic only if garbage collection or deduplication becomes a measured need |
| Cachix | A hosted service and its account on the recovery path | Object storage does the same with nothing to run |
| Builds in a provider's serverless jobs | Too little disk for a closure, a cold store on every run, and no KVM for the VM tests | Owned hardware is already paid for and builds incrementally |
| Full `.nix` files from string templates | Generated Nix would hold logic that nothing checks | Generated Nix holds data; hand-written modules hold logic |
| Build only, or a VM test per node | Boot and service failures reach a node, or every node needs its own test | A VM test per Node class catches boot and service failures without emulating GPUs |

## Consequences

- Easier: a node switches to something the builder built and tested, and
  fetches it with the cluster down; the cache has no process to patch.
- Harder: each host change waits for a reviewer's approval of the signing run;
  the builder machine must be kept up; a static cache has no garbage
  collection, so old NARs leave by a lifecycle rule on the bucket.
- Forbidden: hand-editing generated host data; a closure signed outside the
  environment-scoped job; a cache served from the cluster or from the
  control-plane node; a node with write access to the cache.

## Confirmation

The **Host-data regeneration check** regenerates the host data and fails when
a committed file differs from the compiler's output. The **Cluster-down fetch
test** fails when a node cannot fetch and verify its generation from the cache
with the API server stopped, or when a node's credential can write to the
cache. The cache key's checks, among them the **Closure signature test**, are
in [record 21](0021-renders-and-host-tags-are-signed-by-separate-keys-with-an-offline-recovery-key.md).

---
status: proposed  # proposed | accepted | locked
date: 2026-10-30
rests-on: [12, 13, 21]
lessons: [DR-1]
---

# Host data is rendered by the compiler for hand-written modules, and host closures are built in CI and cached outside the cluster

## Context

A node must be able to fetch its generation when the cluster is down, and must
not build it itself. Host configuration is partly generated from Infrastructure
Intent and partly written by hand in Nix, and the two must not mix. Whoever holds
the binary cache's signing key can sign root code for every node
([review](../research/review/README.md) D10); that key is decided in
[record 21](0021-renders-and-host-tags-are-signed-by-separate-keys-with-an-offline-recovery-key.md).

## Decision

- The compiler renders host data from Infrastructure Intent; hand-written Nix
  modules consume it. Generated host data and hand-written modules are
  separate files, and a generated file is never hand-edited.
- CI builds every node's closure on a change to Infrastructure Intent or the
  hand-written modules, and runs one NixOS VM test per node class.
- The closures go to a binary cache outside the cluster, named in Platform
  Intent, and nodes trust it through `trusted-public-keys`.
- The cache's signing key is the environment-scoped key of
  [record 21](0021-renders-and-host-tags-are-signed-by-separate-keys-with-an-offline-recovery-key.md).
- The service moves the host tags only after the build and the VM tests pass.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| A cache inside the cluster | Nodes cannot fetch while the cluster is down | Hosts must recover the cluster |
| Nodes build their own closures | CPU and memory on small nodes; no gate before a switch | The VM test is the gate |
| Hand-write the host data too | Intent and host configuration drift apart | The compiler already owns Intent |
| Server-side signing (niks3) with OIDC push | A signing service to run | A later upgrade |
| Full `.nix` files from string templates | Generated Nix would hold logic that nothing checks | Generated Nix holds data; hand-written modules hold logic |
| Build only, or a VM test per node | Boot and service failures reach a node, or every node needs its own test | A VM test per Node class catches boot and service failures without emulating GPUs |

## Consequences

- Easier: a node switches to something CI built and tested.
- Harder: each host change waits for a reviewer's approval of the signing run.
- Forbidden: hand-editing generated host data; a closure signed outside the environment-scoped job.

## Confirmation

The **Host-data regeneration check** regenerates the host data and fails when a committed file differs from
the compiler's output. The cache key's checks are in
[record 21](0021-renders-and-host-tags-are-signed-by-separate-keys-with-an-offline-recovery-key.md).

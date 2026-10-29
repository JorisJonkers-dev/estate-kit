---
status: proposed  # proposed | accepted | locked
date: 2026-10-29
rests-on: [12, 13, 21, 29, 32]
lessons: [DR-1, DR-2, DO-7]
---

# A host applier on each node pulls its signed host tag, and decides a reboot before the Lease

## Context

NixOS nodes are switched today by deploy-rs, pushed from the maintainer's
machine. The review recommended deferring a bespoke applier; the maintainer
chose to build it alongside the service ([review](../research/review/README.md)
D2), with the switching rules of D11. Four of the six active nodes have no
boot assessment, and only one node runs the control plane.

## Decision

- **Pull, not push.** A Rust agent on each node, a systemd service beside k3s,
  polls its signed `host/<node>:prod` tag, verifies it with the host key or the
  recovery key, and fetches and verifies the closure from the binary cache.
  Fetching disrupts nothing.
- **Decide the reboot before the Lease.** It compares the fetched closure's
  kernel, initrd, modules, kernel parameters and device trees with the booted
  ones. A reboot change is staged with `switch-to-configuration boot`, and the
  Lease and drain happen only once the node's maintenance window opens. A live
  change goes `test`, then a health check, then `boot`.
- **One node at a time.** A cluster-wide Lease serialises switches and
  reboots; pods leave through the Eviction API so PodDisruptionBudgets hold.
  Each node has its own credential, and a ValidatingAdmissionPolicy limits its
  evictions to its own node.
- **Fall back by bootloader**: GRUB's saved default on the VPS, boot counting
  with systemd-boot, a documented reflash on the Raspberry Pis. Spike #15
  settles each.
- **Break-glass stays on deploy-rs**, with targets generated from host data.

The page is [Hosts](../design/hosts.md).

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Defer, keep deploy-rs (review's recommendation) | Hosts need the maintainer's machine to change | The maintainer chose to build it now |
| kured plus a small stager | kured's cluster-wide grant; per-site locks | Weaker isolation of eviction |
| Lease, drain, switch, then wait for the window | A node sits drained for hours | D11 |

## Consequences

- Easier: no push credential; nodes update without the maintainer's machine.
- Harder: the largest bespoke component in the plan.
- Forbidden: a reboot outside the node's window; two nodes switching at once.

## Confirmation

A NixOS VM test per node class runs the applier through a live change and a
reboot change; a fixture asserts the eviction policy refuses another node's
pods.

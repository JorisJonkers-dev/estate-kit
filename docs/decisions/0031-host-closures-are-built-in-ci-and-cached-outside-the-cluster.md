---
status: proposed  # proposed | accepted | locked
date: 2026-10-29
rests-on: [21, 29, 30]
lessons: [DR-1]
---

# Host closures are built in CI and cached outside the cluster, signed by an environment-scoped key

## Context

A node must be able to fetch its generation when the cluster is down, and must
not build it itself. Whoever holds the binary cache's signing key can sign root
code for every node; as a plain CI secret it was readable by any workflow
([review](../research/review/README.md) D10).

## Decision

- CI builds every node's closure on a change to Infrastructure Intent or the
  hand-written modules, and runs one NixOS VM test per node class.
- The closures go to a binary cache outside the cluster, named in Platform
  Intent, and nodes trust it through `trusted-public-keys`.
- The cache's signing key is a GitHub environment secret, usable only on
  `main` and only after a reviewer approves the run.
- The service moves the host tags only after the build and the VM tests pass.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| A cache inside the cluster | Nodes cannot fetch while the cluster is down | Hosts must recover the cluster |
| Nodes build their own closures | CPU and memory on small nodes; no gate before a switch | The VM test is the gate |
| The key as a plain CI secret | Any workflow can sign for root | D10 |
| Server-side signing (niks3) with OIDC push | A signing service to run | A later upgrade |

## Consequences

- Easier: a node switches to something CI built and tested.
- Harder: each host change waits for a reviewer's approval of the signing run.
- Forbidden: a closure signed outside the environment-scoped job.

## Confirmation

The signing workflow fails without its environment; a test asserts nodes
reject a closure signed by any other key.

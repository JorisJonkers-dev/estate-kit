# Hosts

The same model and compiler that render Projects also render each NixOS node's
configuration. A separate host applier on every node switches it, one node at a
time, and reboots only inside its maintenance window. It is built alongside the
service, by the maintainer's choice against the [review](../research/review/README.md)'s advice to defer it (D2);
break-glass and enrolment stay on deploy-rs and nixos-anywhere, generated from
the same host data.

## One model, two appliers

The split follows the failure domain, not the model. Flux applies Projects
inside the cluster. The host applier runs on the node itself, outside
Kubernetes, because it must update the nodes the cluster runs on, and must
still work when the cluster is down.

| | Projects | Hosts |
| --- | --- | --- |
| Authored in | Project Intent | Infrastructure Intent (sites, nodes, maintenance windows) |
| Compiler output | Kubernetes objects | Typed host data, consumed by hand-written NixOS modules |
| Gate before applying | Server-side dry-run | Build every closure, plus a NixOS VM test per Node class |
| Signed pointer | `render/<p>:prod` | `host/<node>:prod`, moved by the service |
| Applier | Flux | Host applier on each node |

## Where each host input comes from

![Inputs to a host rollout](../diagrams/png/inputs-host.png)

## A host rollout

CI builds and signs every node's closure into an off-cluster binary cache and
runs the VM tests. The cache's signing key is an environment-scoped secret,
limited to main with a reviewer
([record 21](../decisions/0021-renders-and-host-tags-are-signed-by-separate-keys-with-an-offline-recovery-key.md)). Then the service moves the host tags,
signed with the host key; each tag binds its closure's store path. Each applier
fetches and verifies its closure first, which disrupts nothing. Only the switch
and the reboot are serialised, under a cluster-wide Lease, with pods leaving
through the Eviction API so PodDisruptionBudgets hold. Each applier has its own
credential, and a ValidatingAdmissionPolicy limits its evictions to its own
node.

![Sequence: a host rollout](../diagrams/png/seq-host-rollout.png)

## States of the host applier

The applier decides whether a change needs a reboot before it takes the Lease,
by comparing the fetched closure's kernel, initrd, kernel modules, kernel
parameters and device trees with the booted ones (D11).

- **A reboot change** is staged with `switch-to-configuration boot`. The Lease
  and the drain happen only once the window opens, so no node sits drained
  waiting for it.
- **A live change** goes `test`, then a health check, then `boot`, so a failed
  health check leaves the previous generation as the boot default.
- **Falling back** depends on the bootloader: the saved default and
  `grub-reboot` with GRUB on the Contabo VPS, boot counting with systemd-boot,
  and a documented reflash on the Raspberry Pis, which have no boot assessment.

An unhealthy node returns to its previous generation and halts the rollout.

![States of the host applier](../diagrams/png/state-host-applier.png)

## Order of nodes

The order is derived from what the rollout changes
([record 30](../decisions/0030-a-host-applier-on-each-node-pulls-its-signed-host-tag.md)):

- **The k3s version changes:** the control plane first, inside its window, then
  one canary worker, then the remaining workers. A minor bump on the control
  plane needs a fresh datastore snapshot and an Operator's approval first,
  because rolling back the generation does not roll back the datastore.
- **Only the OS or host services change:** one canary worker, then the
  remaining workers, then the control plane last.

A check refuses any target that breaks the
[Kubernetes version skew policy](https://kubernetes.io/releases/version-skew-policy/):
a kubelet newer than the API server, or a minor version that jumps more than
one step. The [k3s upgrade guide](https://docs.k3s.io/upgrades/automated)
likewise upgrades servers before agents.

![How the node order is derived](../diagrams/png/flow-host-order.png)

## Known limit: one control plane

`frankfurt-contabo-1` is the only control-plane node. While it switches or
reboots, inside its window, the API pauses: workloads keep serving, but Flux,
Flagger and the service wait. Its k3s datastore is one SQLite file; a timer
copies a backup of it, with the server token, off the provider, and a restore
runbook rebuilt on nixos-anywhere has been drilled in a VM (D5). Vault on the
same node unseals itself through a cloud KMS (D6). Both are decided in
[fleet-infra](https://github.com/JorisJonkers-dev/fleet-infra) and assumed here
([record 59](../decisions/0059-vault-unseal-and-datastore-backup-are-assumed-from-fleet-infra.md)). Moving to three servers is a
separate decision.

## When the cluster is down

The host tags cannot move, and the Lease cannot be taken. Break-glass uses
deploy-rs, with targets generated from host data, to switch one node to a
signed generation; nixos-anywhere enrols or rebuilds a node from the same
targets.

## Where the host parts run

Each node runs its own applier as a systemd service, beside k3s. The appliers
share nothing but the Lease in the API server; closures come from the cache,
pointers from ghcr.

![Deployment: the host appliers](../diagrams/png/deploy-hosts.png)

## Inside the host applier

The agent is one reconcile step at a time over six ports, each with one
hand-written fake. A crash at any step resumes from the node's observed state.

![Class diagram: the host applier](../diagrams/png/host-applier.png)

## UC-10 Declare a node

An Admin adds or changes a node in Infrastructure Intent. Outcome: the node's
host data is rendered, and its class is built and VM-tested.

![UC-10 Declare a node](../diagrams/png/uc10-declare-node.png)

## UC-11 Roll out a host change

CI passes the host gate, and the service moves the host tags. Outcome: every
node runs the new generation, one at a time, rebooting only in its window.

![UC-11 Roll out a host change](../diagrams/png/uc11-roll-out-hosts.png)

## UC-12 Switch a node by hand

The cluster is down, so no tag can move and no Lease can be taken. An Operator
switches one node to a signed generation by hand. Outcome: the node runs that
generation; the Operator owns draining it.

![UC-12 Switch a node by hand](../diagrams/png/uc12-break-glass.png)

## When an applier crashes mid-rollout

Every step is idempotent. A restarted applier reads the node's observed state
(is the Lease still mine, is the node cordoned) and resumes from there; a Lease
that expires frees the next node.

![Failure: the applier crashes after draining](../diagrams/png/seq-fail-host-crash.png)

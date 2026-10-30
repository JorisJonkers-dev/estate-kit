---
status: proposed  # proposed | accepted | locked
date: 2026-10-30
rests-on: [1, 12, 21]
lessons: [DR-1, DR-2]
---

# Vault unseal and the API server's datastore backup are decided in fleet-infra; estate-kit assumes them

## Context

Two production risks sit under the design but are operations on today's estate,
not estate-kit's model. Vault is unsealed by hand, so a reboot of
`frankfurt-contabo-1`, an out-of-memory kill or a crash stops signing, secrets,
migrations and mail provisioning until the maintainer types the keys in
([review](../research/review/README.md) D6). And that node is the only
control-plane node: its k3s datastore is one SQLite file with no backup and no
written restore ([review](../research/review/README.md) D5). The decisions on
both live in [fleet-infra](https://github.com/JorisJonkers-dev/fleet-infra),
which owns the cluster's operations.

## Decision

estate-kit does not decide how Vault unseals or how the datastore is backed up.
It records that it assumes both, and what it relies on:

- **Vault unseals without a person** after a restart, and a `VaultSealed` alert
  fires while it is sealed. The deploy path signs through Vault, so every
  signing record rests on this ([record 21](0021-renders-and-host-tags-are-signed-by-separate-keys-with-an-offline-recovery-key.md)).
- **The datastore has an off-provider backup and a drilled restore.** A restore
  rebuilds the control plane from the binary cache, the datastore copy and the
  Vault snapshot. A k3s minor bump on the control plane takes a fresh snapshot
  first, which the host applier's node order requires.

Spikes #12 and #14 prove the unseal path and the restore. Until fleet-infra
carries both, estate-kit's host and recovery pages describe a target, not a fact.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Decide both here, as two records | estate-kit owns operations it does not run, beside fleet-infra's | The estate's operations are fleet-infra's |
| Assume them without a record | The reliance is invisible until a restore is needed | A design that rests on an operation should say so |

## Consequences

- Easier: one place for what estate-kit takes from the cluster's operations.
- Harder: a change in fleet-infra to either operation can break an estate-kit
  assumption without a pull request here.
- Forbidden: a design page that treats either as estate-kit's decision.

## Confirmation

The Links job resolves the fleet-infra link. The control-plane node's reboot
and restore drills belong to fleet-infra; spikes #12 and #14 report their
result back to this record.

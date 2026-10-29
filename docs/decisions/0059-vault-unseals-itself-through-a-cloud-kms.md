---
status: proposed  # proposed | accepted | locked
date: 2026-10-29
rests-on: [21]
lessons: [DR-1]
---

# Vault unseals itself through a cloud KMS

## Context

Vault is unsealed by hand. Every reboot of `frankfurt-contabo-1` in its window,
every out-of-memory kill and every crash stops signing, secrets, migrations and
mail provisioning until the maintainer types the keys in, which can take days.
Vault is pinned to that node ([review](../research/review/README.md) D6).

## Decision

Vault Community uses a cloud KMS seal. The credential that reaches the KMS is
scoped to one key, revocable, and kept as a NixOS host secret on the
control-plane node. A `VaultSealed` alert fires when Vault reports sealed, and
the failure is drawn as its own sequence on
[Releasing a Project](../design/releasing.md). Spike #12 settles the provider
and the startup path.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| OpenBao with a static seal | The unseal key sits on the node | No separation between the node and the key |
| Keep manual unseal | Signing stops until the maintainer is back | The maintainer has a few hours a week |

## Consequences

- Easier: a reboot no longer stops the deploy path.
- Harder: Vault depends on a cloud KMS being reachable at startup; a static
  cloud credential exists on the node.
- Forbidden: the KMS credential anywhere but the host secret.

## Confirmation

A drill reboots the control-plane node and asserts Vault is unsealed without a
person; the alert has a test that fires on a sealed status.

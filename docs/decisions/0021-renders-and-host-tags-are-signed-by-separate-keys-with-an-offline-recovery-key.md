---
status: accepted  # proposed | accepted | locked
date: 2026-10-30
rests-on: [9, 17]
lessons: [DR-1, DR-2]
---

# Signing keys: renders and host tags by separate Transit keys, closures by an environment-scoped key, and an offline recovery key

Amended by [record 140](0140-break-glass-custody-is-written-and-drilled-and-a-named-successor-holds-a-sealed-copy-of-the-recovery-key.md): the recovery key's custody is written down and drilled, and a named recovery-key successor holds a sealed copy of it, so a break-glass survives the maintainer's absence; the successor is not yet named, an open item, due 2027-04-30.

Revised: 2026-11-05: a host tag is now a numbered, immutable `host/<node>:<number>` tag, so the host signing key signs each publication, not a moving `:prod` tag.

## Context

The first design signed renders and host tags with one Vault Transit key. A
misuse of that key could change every Project and run as root on every node,
and losing Vault meant break-glass on every node
([review](../research/review/README.md) D10). Flux and the host verifier each
accept several public keys. The binary cache's signing key had the same reach:
whoever held it could sign root code for every node, and as a plain CI secret
any workflow could read it. How the closures are built and cached is
[record 31](0031-host-closures-are-built-in-ci-and-cached-outside-the-cluster.md).

## Decision

- **Two Transit keys.** The render signing key signs `render/<project>:prod`
  artifacts; the host signing key signs each node's numbered
  `host/<node>:<number>` tag. Delivery's Vault policy can use
  each only for its own signing path.
- **An environment-scoped cache signing key.** The key that signs the binary
  cache's closures is a GitHub environment secret, usable only on `main` and
  only after a reviewer approves the run. Nodes trust its public half through
  `trusted-public-keys`.
- **An offline recovery key.** A hardware-held key, kept offline, is trusted by
  Flux and by every host applier beside the online key. It signs only in a
  break-glass, when Vault is gone. A named recovery-key successor holds a
  sealed copy of it, so the break-glass survives the maintainer's absence; the
  custody — where the key lives, who opens it if the maintainer cannot, what
  the offline store holds, and the loss case — is written down and drilled. The
  signing and repository credentials this key keeps company with have a second
  copy at a second EU provider, whose holder is not yet chosen either, both
  open items due 2027-04-30
  ([record 140](0140-break-glass-custody-is-written-and-drilled-and-a-named-successor-holds-a-sealed-copy-of-the-recovery-key.md),
  [record 141](0141-a-second-copy-exists-only-for-the-critical-set-at-a-second-eu-provider.md)).
- **One signature format, fixed by a contract test.** The format (a cosign
  signature with transparency-log upload off, so repository names stay out of
  public Rekor) is signed by Delivery's signer and verified by the pinned
  Flux and the host verifier in one test. Spike #17 settles signature replay
  and rollback behaviour in Flux.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| One Transit key | Misuse reaches every Project and every node | D10 |
| The cache key as a plain CI secret | Any workflow can sign for root | D10 |
| A key per Project | One Transit key and one Flux secret per Project to rotate | More keys than the threat needs at this scale |
| Keyless signing from the cluster | A public transparency log and an OIDC issuer the cluster must reach | Repository names in public logs |

## Consequences

- Easier: a leaked render signing key cannot touch hosts; losing Vault is survivable.
- Harder: the recovery key needs a custody procedure and a yearly drill.
- Forbidden: signing a host tag with the render signing key, or the reverse; a closure signed outside the environment-scoped job.

## Confirmation

The **Signature contract test** signs with each key and verifies with the pinned
Flux and the host verifier, and asserts each verifier rejects the other
key's signatures. The **Signing environment check** fails the signing workflow
without its environment, and the **Closure signature test** asserts nodes
reject a closure signed by any other key.

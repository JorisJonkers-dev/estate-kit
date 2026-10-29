---
status: proposed  # proposed | accepted | locked
date: 2026-10-29
rests-on: [9, 17, 30, 31]
lessons: [DR-1, DR-2]
---

# Renders and host tags are signed by separate Transit keys, with an offline recovery key

## Context

The first design signed renders and host tags with one Vault Transit key. A
misuse of that key could change every Project and run as root on every node,
and losing Vault meant break-glass on every node
([review](../research/review/README.md) D10). Flux and the host verifier each
accept several public keys.

## Decision

- **Two Transit keys.** The render signing key signs `render/<project>:prod`
  artifacts; the host signing key signs `host/<node>:prod` tags. The service's Vault policy can use
  each only for its own signing path.
- **An offline recovery key.** A hardware-held key, kept offline, is trusted by
  Flux and by every host applier beside the online key. It signs only in a
  break-glass, when Vault is gone.
- **One signature format, fixed by a contract test.** The format (a cosign
  signature with transparency-log upload off, so repository names stay out of
  public Rekor) is signed by the service's signer and verified by the pinned
  Flux and the host verifier in one test. Spike #17 settles signature replay
  and rollback behaviour in Flux.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| One Transit key | Misuse reaches every Project and every node | D10 |
| A key per Project | One Transit key and one Flux secret per Project to rotate | More keys than the threat needs at this scale |
| Keyless signing from the cluster | A public transparency log and an OIDC issuer the cluster must reach | Repository names in public logs |

## Consequences

- Easier: a leaked render signing key cannot touch hosts; losing Vault is survivable.
- Harder: the recovery key needs a custody procedure and a yearly drill.
- Forbidden: signing a host tag with the render signing key, or the reverse.

## Confirmation

The signature contract test signs with each key and verifies with the pinned
Flux and the host verifier; a test asserts each verifier rejects the other
key's signatures.

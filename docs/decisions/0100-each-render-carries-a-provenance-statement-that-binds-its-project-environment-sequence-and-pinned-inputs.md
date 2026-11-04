---
status: proposed  # proposed | accepted | locked
date: 2026-11-04
rests-on: [6, 21, 28, 63, 98]
lessons: [DR-1, CS-5]
---

# Each render carries a provenance statement that binds its Project, Environment, sequence and pinned inputs

## Context

[Record 21](0021-renders-and-host-tags-are-signed-by-separate-keys-with-an-offline-recovery-key.md)
signs each render with the render signing key, as a cosign signature with the
transparency log off, and Flux verifies it. The signature covers the render's
digest and nothing else. Any render the key ever signed verifies for any
Project and any Environment, at any place in the order. "Survivable key
compromise in software update systems" (2010) names the rollback, freeze and
mix-and-match attacks this leaves open; the architecture evaluation of
2026-11-04 marks the gap Strong (sections 3.7 and 3.13).
[Record 98](0098-the-live-pointer-is-an-immutable-sequence-tag-that-flux-selects-by-version.md)
puts the order into the registry, but a Sequence tag can still name a render
composed for another Project or Environment.

A render is a function of pinned inputs
([record 6](0006-every-render-is-a-function-of-pinned-inputs.md)), and its
Render key, the digest of those inputs, is already meant to be kept with each
published render. "in-toto: Providing farm-to-table guarantees for bits and
bytes" (2019) binds an artifact to the inputs and steps that made it, in a
signed statement. Flux checks the signature only; it does not read a
statement's contents (evaluation section 5). The evaluation also warns that a
statement written by the process that signs is not independent evidence that
a step happened: it records what that process claims (section 3.13). For one
maintainer, build-track provenance is the honest target ("Analyzing
challenges in deployment of the SLSA framework for software supply chain
security", 2024).

## Decision

Delivery attaches to every render it signs an in-toto statement whose subject
is the render's digest. Its predicate names the Project, the Environment, the
sequence number of the Sequence tag the render is first published under, the
Operation id, the Render key, and the digests of the render's pinned inputs:
the fragment, Platform Intent, the ClusterState snapshot and the compiler
version. The render signing key signs it, in the one signature format of
[record 21](0021-renders-and-host-tags-are-signed-by-separate-keys-with-an-offline-recovery-key.md).
The predicate's schema is a committed contract with its own major. This is
not the per-field Provenance that
[record 72](0072-per-field-provenance-and-explain-are-deferred.md) defers.

Flux verifies the signature, as today. Delivery checks the binding when it
observes the revision Flux applied. The statement must name the Project and
Environment whose repository holds the tag, and a sequence no higher than the
tag's. A lower sequence is allowed only for a Rollback that Delivery
recorded. On a mismatch, Delivery does two things: it alerts, and it sets
the Project's ProjectControl to Paused
([record 28](0028-pause-and-rollback-are-a-cluster-object-per-project.md)).
It does not roll back by itself. A Rollback refuses a target whose statement
names another Project or Environment; the check needs the public key only, so
a Rollback still works with Vault sealed. This extends
[record 21](0021-renders-and-host-tags-are-signed-by-separate-keys-with-an-offline-recovery-key.md),
which is left unchanged.

The statement records Delivery's claim about its inputs. It detects a
substituted or replayed render after Flux applies it; it does not prevent the
apply, and it does not protect against a compromised Delivery, which stays
out of scope beyond what
[record 21](0021-renders-and-host-tags-are-signed-by-separate-keys-with-an-offline-recovery-key.md)
covers. Image build provenance stays with
[record 8](0008-an-image-digest-is-sealed-into-the-fragment-and-registered-by-its-build.md).

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| The signature alone (today) | A render for one Project or Environment verifies in another; a replay goes unseen by the reader | The gap section 3.7 names |
| Have Flux check the statement's fields | Flux verifies signatures, not a statement's contents | Not something the pinned applier does |
| A key per Project and Environment, so Flux refuses a foreign render at the reader | One key and one Flux secret per Project and Environment to rotate | [Record 21](0021-renders-and-host-tags-are-signed-by-separate-keys-with-an-offline-recovery-key.md) rejected a key per Project; revisit if review trigger T5 fires |
| Keyless Sigstore for renders | A public transparency log and an issuer the cluster must reach | Repository names in public logs ([record 21](0021-renders-and-host-tags-are-signed-by-separate-keys-with-an-offline-recovery-key.md)) |
| A separate signer process now | A second process and credential, for a compromise no threat table names | Added only when a threat table names the compromise it stops |
| A Vault policy that signs only with a dry-run receipt | A receipt written by the same process | Not independent evidence (in-toto, 2019) |
| Keep the Render key only in Delivery's event log | Lost with Postgres; not beside the render | The binding must live with the render |

## Consequences

- Easier: every applied render traces to its Project, Environment, sequence,
  Operation and inputs; a substituted render is found when it is applied; a
  Rollback cannot pick another Project's render.
- Harder: one more artifact per render, retained as long as the render; a
  predicate schema to version; detection comes after the apply, not before.
- Forbidden: publishing a render without its statement; a statement signed
  by any key but the render signing key; a Rollback to a render whose
  statement names another Project or Environment; treating the statement as
  independent evidence that a step happened.

## Confirmation

The **Render statement binding test** fails if a render is published without
its statement, if a statement's subject is not the render's digest or it
verifies with another key, or if Delivery observes an applied render whose
statement names another Project, another Environment or a higher sequence and
fails either to alert or to pause the Project; and if a Rollback to such a
render is not refused. The **Schema evolution check** holds the predicate's
schema. A scenario of the **E2E scenarios** places another Environment's signed
render under a Project's next Sequence tag and asserts the alert and the Pause
([record 69](0069-the-deploy-path-is-tested-end-to-end.md)).

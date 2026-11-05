---
status: proposed  # proposed | accepted | locked
date: 2026-11-04
rests-on: [9, 21, 28, 63, 75, 99]
amends: [9, 63]
lessons: [DR-1, DR-2]
---

# The live pointer is an immutable Sequence tag that Flux selects by version

## Context

[Record 9](0009-the-live-render-is-a-signed-registry-tag-per-project-and-environment.md)
names a Project's live render in an Environment by one signed tag,
`render/<project>:<env>` ([record 75](0075-three-environments-run-in-the-one-cluster.md)),
which Delivery moves. ghcr has no compare-and-swap, so
[record 63](0063-delivery-has-one-writer-and-reconciles-from-observed-state.md)
moves the tag by read, verify, write, read again under the Writer Lease, and
states the window it leaves: a holder that has just lost the Lease can still
write, and a writer that holds the token but not the Lease "is not fenced at
all".

The signature binds a digest, not a Project, an Environment or an order. Any
render the render signing key ever signed verifies on any tag, so a moved tag
can name an old render, keep a stale one in place, or name another Project's.
"Survivable key compromise in software update systems" (2010) names these
rollback, freeze and mix-and-match attacks and says the reader should enforce
the order. Today only the nightly drift check would notice (the architecture
evaluation of 2026-11-04, sections 1.1 and 3.7).

Flux's OCIRepository can select the highest tag that matches a semver range,
and can verify a cosign signature on the digest it selects. Some registries
refuse to update a tag once it exists; ghcr does not. Neither behaviour has
been tried with the pinned Flux, the estate's signature format
([record 21](0021-renders-and-host-tags-are-signed-by-separate-keys-with-an-offline-recovery-key.md))
or a candidate registry. The evaluation marks the mechanism Moderate, lists
the trial as an M0 spike, and keeps the Lease and read, verify, write until it
passes (sections 11.3 and 11.4). Where the renders move is
[record 99](0099-renders-and-host-tags-live-in-an-off-cluster-registry-chosen-by-its-features.md).

[Record 28](0028-pause-and-rollback-are-a-cluster-object-per-project.md)
rolls back by moving the tag to the last Serving render, signing nothing.
cosign signatures attach to the digest, so an old render still verifies under
a new tag (section 9.6).

## Decision

Once the spike below passes and the registry of
[record 99](0099-renders-and-host-tags-live-in-an-off-cluster-registry-chosen-by-its-features.md)
is running, the live pointer is a Sequence tag. Each Project has one render repository per
Environment. Delivery publishes a render by creating the next Sequence tag in
it, one higher than the highest, at the render's digest. That creation is the
Publication point. The registry refuses to create a tag that already exists,
so of two writers racing for the same number, one is refused. A refused
writer observes and decides again; it never retries on its old decision. The
Project's OCIRepository selects the highest tag by a semver range and verifies
its signature. No Sequence tag is ever updated, and Delivery's push credential
cannot delete one. Retention removes only tags below the highest that the
retention rule no longer keeps, with its own credential.

A Rollback creates the next Sequence tag at the last Serving render's digest,
which is already signed. It signs nothing and composes nothing, so it still
needs only the API server and the registry, as
[record 28](0028-pause-and-rollback-are-a-cluster-object-per-project.md) promises.
Delivery alerts on a tag it did not create, and when the applied revision
trails the highest published tag for 1 hour. Flux ignores a lower or
replayed tag.

This amends [record 9](0009-the-live-render-is-a-signed-registry-tag-per-project-and-environment.md)
(a tag per Project and Environment becomes a repository of Sequence tags per
Project and Environment) and point 4 of
[record 63](0063-delivery-has-one-writer-and-reconciles-from-observed-state.md):
the move becomes read the highest tag, verify it names the digest the decision
was made from, check the Lease, create the next tag. The Writer Lease stays.
It still orders signing and the choice of the next number, and one
composition still runs at a time. It is no longer the only fence: a stale
holder or a writer without the Lease can create the next tag only if no one
has, and can never replace one. Point 5's race window shrinks to that.

The spike must pass first: OCIRepository semver selection together with cosign
verification and the tag format, on the pinned Flux; and create-only tags on
each candidate registry. Owner: the maintainer; due before the registry move
of [record 99](0099-renders-and-host-tags-live-in-an-off-cluster-registry-chosen-by-its-features.md)
starts, completing by 2027-05-31. Until
then the tag-move rule of
[record 63](0063-delivery-has-one-writer-and-reconciles-from-observed-state.md)
stands unchanged. If the spike fails, this record is rewritten. Host tags
follow the same rule, resolved by the host applier rather than Flux: a host
tag is a numbered, immutable Sequence tag `host/<node>:<number>`, one
repository per node; the applier switches only to the highest and refuses a
lower or replayed one, and a host rollback publishes a higher number at the
signed digest of an older generation
([record 30](0030-a-host-applier-on-each-node-pulls-its-signed-host-tag.md)).

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Keep the mutable tag under the Lease, by read, verify, write, read again | A writer with the token but not the Lease is not fenced; the reader checks no order | The registry move makes a fence possible; [record 63](0063-delivery-has-one-writer-and-reconciles-from-observed-state.md) names the gap |
| A compare-and-swap on the tag | No OCI standard; ghcr has none; the reader still checks no order | Create-only gives the fence and the order together |
| A signed, sequenced pin resource in the cluster, enforced by an estate-kit Applier | An Applier to build; the pin is lost with the datastore | Flux stays the one applier; the order must survive the cluster |
| A promotion controller through Flux's ExternalArtifact | A second writer of Flux objects and a controller to own | [Record 28](0028-pause-and-rollback-are-a-cluster-object-per-project.md) forbids a second writer of Flux objects |
| Delivery sets the OCIRepository's tag | A second writer of Flux objects | As above |
| The nightly drift check alone | A wrong or stale render is found a day late | The reader should refuse, not a report |
| A key per Project and Environment, so Flux refuses a foreign render | One key and one Flux secret per Project and Environment to rotate | [Record 21](0021-renders-and-host-tags-are-signed-by-separate-keys-with-an-offline-recovery-key.md) rejected a key per Project |

## Consequences

- Easier: the reader enforces the order; a racing write is refused by the
  registry, not caught after; a Rollback creates a tag and needs no signer;
  a rebuilt cluster finds every live render from the registry alone.
- Harder: a repository per Project and Environment, and a tag list that
  grows until retention trims it; the retention rule and the vocabulary's
  Environment tag, Prod tag and Writer Lease must be rewritten when this is
  accepted; two pointer rules exist until every Project has moved.
- Forbidden: updating a Sequence tag; deleting the highest one or the last
  Serving render's; creating a tag that is not one above the highest; a
  Rollback that signs or composes while its dry-run passes; publishing by
  Sequence tags before the spike passes.

## Confirmation

The **Sequence tag race test** runs two writers against the registry and fails
if both create the same tag, if the registry accepts an update of an existing
tag, or if the refused writer retries on its old decision. The **Sequence
selection test** fails if the pinned Flux applies anything but the highest
signed Sequence tag, or applies a lower, replayed or unsigned one. The
**Sequence tag alert test** fails if a tag Delivery did not create, or an
applied revision that trails the highest tag for 1 hour, raises no alert.
The **Host sequence tag test** fails when a host applier switches to any tag
but the highest number of its node, or accepts a lower, replayed or unsigned
one ([record 30](0030-a-host-applier-on-each-node-pulls-its-signed-host-tag.md)).
The **Single-writer tests** keep holding the Lease. The **E2E scenarios** roll
a Project back with Vault sealed and assert a new tag at the old digest, and
rebuild the test cluster and assert it finds every live render from the
registry ([record 69](0069-the-deploy-path-is-tested-end-to-end.md)).

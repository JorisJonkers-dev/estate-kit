---
status: proposed  # proposed | accepted | locked
date: 2026-11-04
rests-on: [9, 28, 30, 31, 59, 116]
amends: [9]
lessons: [DR-1, DR-2]
---

# Renders and host tags live in an off-cluster registry chosen by its features

## Context

[Record 9](0009-the-live-render-is-a-signed-registry-tag-per-project-and-environment.md)
keeps renders and host tags on ghcr. ghcr accepts only a classic personal
access token for this, so a machine account's long-lived token, granted per
package, moves every tag; spike #10 is to confirm that App tokens are refused.
ghcr has no compare-and-swap and cannot refuse an update to an existing tag
([record 63](0063-delivery-has-one-writer-and-reconciles-from-observed-state.md)).
The architecture evaluation of 2026-11-04 marks both defects Strong
(sections 3.7 and 1.3). [Record 98](0098-the-live-pointer-is-an-immutable-sequence-tag-that-flux-selects-by-version.md)
needs a registry that refuses to update a tag.

[Record 9](0009-the-live-render-is-a-signed-registry-tag-per-project-and-environment.md)
already rejects an in-cluster registry: a rebuilt cluster must pull its
renders. A node must fetch its generation while the cluster is down
([record 30](0030-a-host-applier-on-each-node-pulls-its-signed-host-tag.md),
[record 31](0031-host-closures-are-built-in-ci-and-cached-outside-the-cluster.md)).
A Rollback needs only the API server and the registry
([record 28](0028-pause-and-rollback-are-a-cluster-object-per-project.md)),
so the registry is on the recovery path. The evaluation therefore keeps it
off the control-plane node, out of the cluster, and off any machine the
control plane needs to recover (section 8, "Where things should not run").
Running pods do not depend on it; Rollback and fresh pulls do.

GitHub is load-bearing in five places and ghcr in one, none behind a port
(section 3.21). The maintainer intends to depend less on GitHub: likely a
move to Tangled once it has private repositories, or a self-hosted Forgejo
behind a VPN with sign-in at Traefik. "Introducing Tangled" (2025) describes
Git hosting on knots; it names no package registry. The maintainer counts
cost; the evaluation prices the registry as object storage and perhaps one
small VPS, and the move at about 40 to 80 hours, which the maintainer
settled before the cutover on 2026-11-04 (sections 8 and 11.4).

Project images and fragments are pushed by each Project's own CI, not by
Delivery. The evaluation keeps Project images on ghcr for now (section 5).

[record 116](0116-every-store-of-estate-data-runs-on-an-eu-controlled-provider-or-on-owned-hardware.md) puts every store of estate data on an EU-controlled provider or
on owned hardware, for protection against US sanctions, and lists ghcr as an
exception for renders and host tags until the registry move, dated
2027-05-31 in its provider-and-exit table.

## Decision

Before the cutover, Delivery publishes renders and host tags to one OCI
registry outside the cluster, each a numbered, immutable Sequence tag
([record 98](0098-the-live-pointer-is-an-immutable-sequence-tag-that-flux-selects-by-version.md)),
chosen by five features, each shown in the registry spike before a product is
chosen:

1. **Create-only tags.** Delivery's push credential can create a tag and can
   neither update nor delete one.
2. **Scoped credentials.** Delivery's push credential reaches only the render
   and host repositories. Flux and the host appliers hold read-only
   credentials. No credential is a person's or a forge account's token.
3. **An object-storage back end**, so the data outlives the registry's
   machine and is backed up and restored with the datastore
   ([record 59](0059-vault-unseal-and-datastore-backup-are-assumed-from-fleet-infra.md)).
4. **Not on the control-plane node and not in the cluster**, and not on a
   machine that anything the control plane needs to recover runs on.
5. **EU-controlled or owned.** The registry, its machine and its object
   storage run on an EU-controlled provider or on owned hardware
   ([record 116](0116-every-store-of-estate-data-runs-on-an-eu-controlled-provider-or-on-owned-hardware.md)).

This supersedes the registry half of
[record 9](0009-the-live-render-is-a-signed-registry-tag-per-project-and-environment.md):
the ghcr machine account, its classic token and the checks on it hold only
until every Project has moved, and are then retired. The move completes
before the cutover, on 2027-05-31, when the ghcr exception of
[record 116](0116-every-store-of-estate-data-runs-on-an-eu-controlled-provider-or-on-owned-hardware.md) ends. Its other rules stand: the push credential reaches Delivery as a Kubernetes Secret that the
Vault Secrets Operator syncs, so no tag creation reads Vault. The move goes
one Project at a time, with renders and host tags mirrored first. The port is
`Registry`, and its adapter becomes `adapter-registry` (renamed from
`adapter-ghcr`), with create-if-absent; the design pages are renamed when this
record is accepted.

Which product is open: the maintainer chooses after the spike, weighing
authentication, restore, retention, egress, cost and maintainer hours. The
candidates are in Alternatives; each must be EU-controlled or owned, and a
candidate that is not is rejected there. Project images and fragments stay where each
Project's CI pushes them, on ghcr today. This record does not move them; a
forge move decides where they go.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Stay on ghcr, with the Lease and read, verify, write | A classic token in the delivery path; no create-only tags, so no [record 98](0098-the-live-pointer-is-an-immutable-sequence-tag-that-flux-selects-by-version.md); a US-controlled provider | Both defects remain, and ghcr's exception under [record 116](0116-every-store-of-estate-data-runs-on-an-eu-controlled-provider-or-on-owned-hardware.md) ends with the registry move, by 2027-05-31 |
| zot on a small VPS at an EU-controlled provider or on owned hardware, object-storage back end at an EU-controlled provider, with a create-only access policy | One small process and VPS to run, patch and back up | Open: a candidate for the spike |
| Distribution (the CNCF registry), placed as zot is, with a create-only policy in front | The policy is an extra layer to own | Open: a candidate for the spike |
| Harbor, placed as zot is, with tag immutability rules | A database, a cache and several services to run for two kinds of artifact | Open: a candidate for the spike, heavier than the need |
| A managed OCI registry at an EU-controlled provider, with scoped keys and immutable tags | Storage and egress charges; one more provider account | Open: a candidate for the spike, if its provider offers both features |
| A managed registry at a provider controlled from outside the EU, in any region | Such a provider follows US or other foreign sanctions wherever the data lies | Rejected by [record 116](0116-every-store-of-estate-data-runs-on-an-eu-controlled-provider-or-on-owned-hardware.md) |
| Forgejo's package registry, if the forge moves to a self-hosted Forgejo on owned hardware or at an EU-controlled provider | The registry moves with the forge; tag immutability unknown | Open: a candidate only once a move is planned |
| An in-cluster registry | A rebuilt cluster cannot pull its renders | [Record 9](0009-the-live-render-is-a-signed-registry-tag-per-project-and-environment.md) rejects it |
| The registry on the control-plane node, or beside Vault | One machine loss takes the cluster and its recovery path | Evaluation section 8 |
| Move images and fragments too, now | Every Project's CI changes before a forge move is planned | The classic token and the tag defects are Delivery's; images are not |

## Consequences

- Easier: no classic token and no GitHub account in the delivery path;
  create-only tags make [record 98](0098-the-live-pointer-is-an-immutable-sequence-tag-that-flux-selects-by-version.md)
  possible; the render store survives the cluster and a forge move.
- Harder: one more thing to run or pay for, back up, restore in the drill and
  watch; a new credential to rotate; a mirror while Projects move; a registry
  outage stops Rollbacks and new deploys.
- Forbidden: renders or host tags in the cluster or on the control-plane
  node; a push credential that can update or delete a tag, or reach beyond
  the render and host repositories; a tag creation that reads Vault; a
  product chosen before it passes the spike; a registry or its storage at a
  provider that is neither EU-controlled nor owned.

## Confirmation

The **Registry feature test** runs Delivery's push credential against a canary
repository on the chosen registry and fails if it can update or delete a tag,
or push outside the render and host repositories, or if a read-only
credential can push. The **Registry placement check** fails when the
registry's address resolves to a cluster node. A scenario of the **E2E
scenarios** rebuilds the test cluster and asserts it pulls every live render
from the registry alone ([record 69](0069-the-deploy-path-is-tested-end-to-end.md)).
The **Provider register lint** fails when the registry or its storage is at a
provider that is neither EU-controlled nor owned, or when ghcr still holds
renders and host tags once the registry move's exit date, 2027-05-31, has
passed. The **Token grant check** and
**Token rotation alert** hold until the classic token is retired.

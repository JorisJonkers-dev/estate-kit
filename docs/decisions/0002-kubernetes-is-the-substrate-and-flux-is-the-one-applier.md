---
status: accepted  # proposed | accepted | locked
date: 2026-10-30
rests-on: [1]
lessons: [DO-5]
---

# Kubernetes is the substrate, and Flux is the one applier

Amended by [record 94](0094-flux-stays-the-one-applier-observed-closely-and-an-estate-kit-applier-waits-for-a-review-trigger.md): Flux stays the one applier, observed closely object by object, and an estate-kit Applier is built only when one of its review triggers T1 to T5 fires.

Amended by [record 95](0095-a-project-renders-as-a-chain-of-flux-kustomizations-one-per-apply-group.md): Flux applies a Project's render as a chain of Kustomizations, one per Apply group.

Amended by [record 144](0144-delivery-holds-no-actions-write-and-dispatches-no-workflow-and-its-own-deployment-is-applied-by-a-bootstrap-step-that-verifies-the-render-signature.md): beside the host applier's, one further named exception applies inside the cluster — the bootstrap step that applies Delivery's own Deployment, from a render whose signature it verified.

## Context

Kubernetes earns its place here for two properties, not for scheduling. The API
server bounds what each in-cluster writer may change, and no deploy credential
exists outside the cluster. Server-side-apply field ownership names which
controller owns each field of an object, so a field two writers fight over is
visible rather than silent. Rescheduling, control-plane HA and horizontal scale
do not apply: storage is node-local and the control plane is one host
([record 1](0001-one-maintainer-one-cluster-one-estate.md)).

Delivery already runs on Flux pulling a signed render. The question is whether
estate-kit keeps that, or replaces it with its own applier.

## Decision

Kubernetes is the substrate for everything the estate runs as a workload, and
Flux is the one applier of objects into the cluster. Delivery composes,
dry-runs, signs and moves a tag; Flux pulls the tag and applies, as a chain of
Kustomizations, one per Apply group
([record 95](0095-a-project-renders-as-a-chain-of-flux-kustomizations-one-per-apply-group.md)).
Nothing else creates or changes an object in the cluster: not Delivery, not a
Project's CI, not a person with `kubectl` outside a break-glass. The one named
exception inside the cluster is the bootstrap step that applies Delivery's own
Deployment, from a render whose signature it verified first
([record 144](0144-delivery-holds-no-actions-write-and-dispatches-no-workflow-and-its-own-deployment-is-applied-by-a-bootstrap-step-that-verifies-the-render-signature.md)).

The signed artifact is the seam, so a later record could replace Flux without
touching the compiler; an estate-kit Applier is built only when one of the
review triggers of
[record 94](0094-flux-stays-the-one-applier-observed-closely-and-an-estate-kit-applier-waits-for-a-review-trigger.md)
fires. Hosts beneath the cluster are not in this record's
scope: a node's configuration is applied by the host applier, which pulls its own
signed tag.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Delivery applies, replacing Flux | A second applier with its own drift, pruning and credentials | Keeps one proven applier |
| CI pushes and Delivery applies | A deploy credential outside the cluster | The boundary is that none exists |
| Several appliers, each bounded by its own namespace | A credential, namespace and lease per applier | A second applier is what the design refuses |
| Plain NixOS and systemd per node | Every adapter rewritten as a module generator | Loses the authorisation boundary and field ownership |
| Nomad | A second orchestrator to operate | Buys scheduling the estate does not use, and has no field ownership |

## Consequences

- Easier: one applier, now observed object by object, means one place where
  drift, pruning and ordering are decided, and one identity to narrow.
- Harder: the estate keeps paying Kubernetes' overhead and upgrades for two
  properties; Flux's reach must be narrowed to what a render carries.
- Forbidden: a deploy credential outside the cluster; a second applier; a write
  into the cluster by Delivery other than the exceptions its own record names;
  citing rescheduling, HA or horizontal scale as a reason in a later record.

## Confirmation

The lockdown record's per-Project Flux identities and its refusing admission
policy ([record 58](0058-flux-is-locked-down-per-project-and-delivery-dry-runs-as-an-identity-that-cannot-write.md))
carry the check (**Dry-run admission fixtures**), and the **E2E scenarios**
assert that an object reaches the cluster only through Flux ([record 17](0017-delivery-runs-in-the-cluster-in-rust.md)).

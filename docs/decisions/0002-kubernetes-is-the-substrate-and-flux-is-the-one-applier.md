---
status: accepted  # proposed | accepted | locked
date: 2026-10-30
rests-on: [1]
lessons: [DO-5]
---

# Kubernetes is the substrate, and Flux is the one applier

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
Flux is the one applier of objects into the cluster. The service composes,
dry-runs, signs and moves a tag; Flux pulls the tag and applies. Nothing else
creates or changes an object in the cluster: not the service, not a Project's
CI, not a person with `kubectl` outside a break-glass.

The signed artifact is the seam, so a later record could replace Flux without
touching the compiler. Hosts beneath the cluster are not in this record's
scope: a node's configuration is applied by the host applier, which pulls its own
signed tag.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| The service applies, replacing Flux | A second applier with its own drift, pruning and credentials | Keeps one proven applier |
| CI pushes and the service applies | A deploy credential outside the cluster | The boundary is that none exists |
| Several appliers, each bounded by its own namespace | A credential, namespace and lease per applier | A second applier is what the design refuses |
| Plain NixOS and systemd per node | Every adapter rewritten as a module generator | Loses the authorisation boundary and field ownership |
| Nomad | A second orchestrator to operate | Buys scheduling the estate does not use, and has no field ownership |

## Consequences

- Easier: one applier means one place where drift, pruning and ordering are
  decided, and one identity to narrow.
- Harder: the estate keeps paying Kubernetes' overhead and upgrades for two
  properties; Flux's reach must be narrowed to what a render carries.
- Forbidden: a deploy credential outside the cluster; a second applier; a write
  into the cluster by the service other than the exceptions its own record names;
  citing rescheduling, HA or horizontal scale as a reason in a later record.

## Confirmation

The lockdown record's per-Project Flux identities and its refusing admission
policy ([record 58](0058-flux-is-locked-down-per-project-and-the-service-dry-runs-as-an-identity-that-cannot-write.md))
carry the check, and the end-to-end suite asserts that an object reaches the
cluster only through Flux ([record 17](0017-the-service-runs-in-the-cluster-in-rust.md)).

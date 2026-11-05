---
status: accepted  # proposed | accepted | locked
date: 2026-11-05
rests-on: [2, 6, 58, 95]
amends: [95]
lessons: [DO-1, TM-4]
---

# The platform render creates every Project namespace, and a Project render holds namespaced kinds only

## Context

A Project's render reaches the cluster as a chain of Kustomizations, each
naming the Project's one service account and target namespace
([record 95](0095-a-project-renders-as-a-chain-of-flux-kustomizations-one-per-apply-group.md)),
and the lockdown derives those accounts and namespaces into the platform
render ([record 58](0058-flux-is-locked-down-per-project-and-delivery-dry-runs-as-an-identity-that-cannot-write.md)).
The same records let a Project's own render hold cluster-scoped kinds and
namespaces — the first Apply group of
[the vocabulary's example](../../CONTEXT.md) is "cluster-scoped kinds and
namespaces" — so a Project's first Kustomization needs an identity with
cluster-scoped rights to apply its own objects, and nothing says who creates
the namespace the rest of the render lives in. The design review of 2026-11-04
(the final report's section 15, question 7, and its recommendation `A1-11`)
named the gap; the maintainer settled the answer the same day: the platform
render creates every Project namespace, and a Project's render holds
namespaced kinds only.

DO-1 keeps each Project's unit self-contained, but a namespace is an estate
fact, not a Project's own object: admitting a Project is a
[Platform Intent](../../CONTEXT.md) change, and with it the platform render
gains the Project's namespace
([record 75](0075-three-environments-run-in-the-one-cluster.md)
gives the estate one namespace per Project per Environment). The offline
dry-run's live-fact input stays the closed list the vocabulary states: the
kinds the cluster serves, the installed CRDs with their versions, the
namespace names and the Kubernetes version — no other fact of the cluster
enters a render, and the namespace names now name what the platform render
creates.

## Decision

The platform render, and only it, creates each admitted Project's namespaces,
one per Environment ([record 75](0075-three-environments-run-in-the-one-cluster.md)),
beside the per-Project service accounts and Flux sources it already derives
([record 58](0058-flux-is-locked-down-per-project-and-delivery-dry-runs-as-an-identity-that-cannot-write.md)).
A Project's render holds namespaced kinds only: the compiler refuses a Project
whose fragment needs a cluster-scoped object — naming the element that needs
it — and no Apply group of its chain is cluster-scoped. A Project's first
Apply group therefore needs no cluster-scoped identity: it applies into a
namespace the platform render already created, under the Project's own service
account, with the rights of [record 58](0058-flux-is-locked-down-per-project-and-delivery-dry-runs-as-an-identity-that-cannot-write.md)'s
lockdown alone. This amends [record 95](0095-a-project-renders-as-a-chain-of-flux-kustomizations-one-per-apply-group.md):
its chain stands, with no group of a Project's chain carrying a cluster-scoped
kind or a Namespace.

Every cluster-scoped kind a Project needs — a rendered CRD, an admission
policy, a ClusterRole — is an object of the platform render, published and
applied under its own Kustomization and service account, and a render that
introduces a kind is published in the two stages of
[record 97](0097-the-publication-point-is-named-and-tested-and-a-render-that-introduces-a-kind-is-published-in-two-stages.md)
there. An object [Unverifiable by construction](../../CONTEXT.md) because its
kind or its namespace does not exist reaches the cluster through the platform
render first; the objects of a Project's render are verifiable as soon as its
namespace does. The [ClusterState snapshot](../../CONTEXT.md) still holds its
closed list, and a Project's dry-run still checks every object its render
holds, against the namespace names the platform render's last apply gave the
snapshot.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| A Project's render creates its own namespace, as today's example group allows | Its first Kustomization needs cluster-scoped rights, and a compromised render races the platform for the namespace | The admitting authority (Platform Intent) and the object (the namespace) belong together |
| A Project may hold cluster-scoped kinds in a platform-owned group of its own render | Two owners for one render; a Project's refusal reasons about another render's objects | One Project, one render, one identity ([record 58](0058-flux-is-locked-down-per-project-and-delivery-dry-runs-as-an-identity-that-cannot-write.md)) |
| The compiler moves a Project's cluster-scoped objects into the platform render on its own | A stage that decides ownership the authored input never stated | The platform render is authored by Platform Intent, not derived from any Project's fragment |
| Namespaces created by Delivery as a write | A third writer of namespaces beside Flux and the bootstrap step, against the one-applier rule ([record 2](0002-kubernetes-is-the-substrate-and-flux-is-the-one-applier.md)) | Creation is a render change like any other |
| Keep the group example's cluster-scoped head as unused | The example reads as a rule, and the next record cites it as one | The derivation is the decision; the example follows it |

## Consequences

- Easier: a Project's first Apply group is namespaced and low-privilege; the
  dry-run's closed list answers for the platform render; admitting a Project
  changes one render.
- Harder: a Project that needs a cluster-scoped kind waits for a Platform
  Intent change, and the platform render's own list of kinds must be reviewed
  as its own boundary of change.
- Forbidden: a cluster-scoped object in a Project's render; a namespace
  created by a Project's render or by Delivery; a Project's Kustomization
  with rights outside its own namespace.

## Confirmation

The **Render scope fixtures** fail when the compiler accepts a Project whose
fragment needs a cluster-scoped object or a Namespace, or the platform render
omits the namespace of a Project Platform Intent admits in an Environment;
one failing fixture per refusal. The **Apply group chain fixtures** hold the
amended derivation: a group of a Project's chain that names a cluster-scoped
kind fails them.

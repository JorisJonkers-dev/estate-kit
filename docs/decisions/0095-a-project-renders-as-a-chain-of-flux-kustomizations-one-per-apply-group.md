---
status: proposed  # proposed | accepted | locked
date: 2026-11-04
rests-on: [2, 58, 67, 74, 94]
lessons: [DO-2, DO-3]
---

# A Project renders as a chain of Flux Kustomizations, one per Apply group

## Context

A render must reach the cluster in order: cluster-scoped kinds and namespaces,
then grants and secrets, then the migration Job, then workloads, then routes.
Today a Project's render is one Kustomization, so Flux applies it in its own
order and reports one condition for the whole of it, and the Release Gate and a
suspended migration Job work around what that cannot express
([Splitting estate-kit](../research/decomposition.md#what-the-design-does-today)).

Flux already orders Kustomizations by `dependsOn` and waits for each one's
health checks, and each Kustomization has its own conditions, inventory and
events. deploy-kit renders one Kustomization per Reconcile Unit in production,
joined by `dependsOn` along the dependency graph
([deploy-kit ADR 0033](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/model/0033-reconcile-unit-derived.md)).
That chain orders Projects; this one orders the steps inside a Project. Each
Project's Kustomization names its own service account and namespace
([record 58](0058-flux-is-locked-down-per-project-and-delivery-dry-runs-as-an-identity-that-cannot-write.md)).

The Release Gate starts a release's migration Job by unsuspending it
([record 74](0074-the-release-gate-and-observation-each-have-a-named-write.md)).
delivery's gate (`internal/gate/tend.go`) starts the up Job only when the
release is still proven (the primaries run the revision it was proven
against), and starts a down Job only when the release is held, every new copy
is at zero, the primaries have not moved and every changeset ran in a
transaction. The architecture evaluation of 2026-11-04 (sections 1.1, 3.7 and
the risk table of 11.3) recommends the chain and names its cost: more Flux
objects per Project, and slower reconciles if groups are made where no order is
needed.

## Decision

The compiler derives a Project's Apply groups and their order, and renders each
group as its own Flux Kustomization. Group *n* depends on the groups it needs
by `dependsOn`, and its health checks cover the objects of that group, so Flux
applies a group only once the groups before it are healthy. Every Kustomization
of the chain names the Project's one service account and target namespace, as
[record 58](0058-flux-is-locked-down-per-project-and-delivery-dry-runs-as-an-identity-that-cannot-write.md)
requires; the chain adds no identity. A group exists only where an order is
required: an empty group is not rendered, and an optional edge never creates an
order (DO-3). This extends [record 2](0002-kubernetes-is-the-substrate-and-flux-is-the-one-applier.md):
Flux still applies everything, now in steps that Delivery observes one by one
([record 94](0094-flux-stays-the-one-applier-observed-closely-and-an-estate-kit-applier-waits-for-a-review-trigger.md)).

The chain enters by the route [record 67](0067-the-compiler-is-written-to-the-1-0-contract.md)
gives every new behaviour before parity: it lands in the specification first,
with its oracles, so the shadow compares like with like. Until it lands, a
Project is one group, and the observation of
[record 94](0094-flux-stays-the-one-applier-observed-closely-and-an-estate-kit-applier-waits-for-a-review-trigger.md)
works on that one Kustomization.

The Release Gate keeps starting the migration Job by unsuspending it, the
write [record 74](0074-the-release-gate-and-observation-each-have-a-named-write.md)
names; the unsuspend is not a step of the chain. The migration Job has its own
group, rendered suspended. Flux applies the group, and the group turns healthy
only once the gate has unsuspended the Job and the Job has completed, so the
workloads wait for both. The migration group's health timeout covers the time
the gate waits before it starts the Job. The gate's check that the release is
still proven therefore keeps its place, and the down Job, which runs only
after a release is held, stays the gate's as well.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| One Kustomization per Project, as today | One condition for the whole render; order only by Flux's own stages | No step to observe, and no order for the migration Job |
| A Kustomization per object kind | Many more Flux objects, with order where none is needed | Groups only where order is required |
| A separate service account per group | More identities to narrow and fixture | The Project is the isolation unit of [record 58](0058-flux-is-locked-down-per-project-and-delivery-dry-runs-as-an-identity-that-cannot-write.md) |
| A ledger cause for the chain in the shadow | Changes the Locked expected-differences ledger | Specification first keeps the closed set of causes |
| Make the up Job an ordinary step, rendered unsuspended | The gate's check that the release is still proven has no place to run, and the down Job still needs the gate | The gate keeps the unsuspend |

## Consequences

- Easier: Flux enforces the order between steps; each step has its own
  condition, inventory and events for the stream; a failing migration group
  stops the workloads from applying.
- Harder: more Flux objects per Project, whose reconcile time counts toward
  trigger T2 of
  [record 94](0094-flux-stays-the-one-applier-observed-closely-and-an-estate-kit-applier-waits-for-a-review-trigger.md);
  a change to the group derivation reorders every
  Project at once.
- Forbidden: a Kustomization of the chain that names another identity or
  namespace than its Project's; a `dependsOn` edge that is not a required edge;
  a group without health checks on its objects; a migration Job rendered
  unsuspended; a migration group whose health timeout is shorter than the
  gate's wait.

## Confirmation

The **Apply group chain fixtures** fail on a render whose Kustomizations differ
from the derived groups and order, name another service account or namespace,
carry an edge that is not required, form a cycle or lack health checks, render
the migration Job unsuspended, or give the migration group a health timeout
shorter than the gate's wait, with one failing fixture per rule. A scenario of
the **E2E scenarios** fails the migration group and asserts that no workload of
the new render is applied.

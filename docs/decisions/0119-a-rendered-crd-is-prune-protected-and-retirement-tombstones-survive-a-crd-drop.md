---
status: accepted  # proposed | accepted | locked | superseded
date: 2026-11-05
rests-on: [2, 97, 105]
amends: [105]
lessons: [DO-2, DO-5]
---

# A rendered CRD is prune-protected, and Retirement tombstones survive a CRD drop

## Context

A CustomResourceDefinition is itself a rendered object: Flux prunes what a
render no longer names
([record 2](0002-kubernetes-is-the-substrate-and-flux-is-the-one-applier.md)),
and a render that stops naming a CRD removes it, which deletes every custom
resource of its kind at once. Among those kinds are the estate's own: Tenant,
ProjectControl, and every component kind — the Retirement tombstones of
[record 105](0105-removal-is-a-retire-lifecycle-with-durable-retirement-tombstones-and-declared-moves-and-prune-protected-kinds-never-prune.md)
among them, which that record makes custom resources so they are restored with
the datastore.

That record's protection stops one step short: it protects namespaces, claims
whose volume is declared `recoverable` or `irreplaceable`, Mailboxes, buckets
and databases, but names no CRD. A rendered namespace is protected because
deleting it deletes every claim in it
([deploy-kit ADR 0142](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/model/0142-a-rendered-namespace-is-never-pruned.md));
a CRD is the same case with more behind it (the architecture evaluation of
2026-11-04, finding A2-02). A CRD a render introduces is published in
[record 97](0097-the-publication-point-is-named-and-tested-and-a-render-that-introduces-a-kind-is-published-in-two-stages.md)'s
first stage, so CRDs are published and would be pruned like any other rendered
kind.

## Decision

A rendered CRD is a prune-protected kind, extended from
[record 105](0105-removal-is-a-retire-lifecycle-with-durable-retirement-tombstones-and-declared-moves-and-prune-protected-kinds-never-prune.md)
like a rendered namespace or a claim: every rendered CRD carries the
prune-disabled mark, and a render that stops naming one changes nothing — not
the CRD, not one custom resource of its kind, and no Retirement tombstone. A
CRD is never removed by a render change alone; it leaves the cluster by the
Retire lifecycle, on the policy
[record 105](0105-removal-is-a-retire-lifecycle-with-durable-retirement-tombstones-and-declared-moves-and-prune-protected-kinds-never-prune.md)
states for a prune-protected kind: the owning context records its Retirement
tombstone first, and the deletion is a step of that policy.

A Retirement tombstone therefore survives a CRD drop as it survives a render
change, a lost render and a restore: the tombstones of a component are custom
resources of the component's CRD, and the CRD of the kind the tombstone
retires is a rendered CRD too, so both carry the prune-disabled mark and no
render change removes them. Dropping a kind from what a Project declares can
retire its objects; it can never delete their custom resources, their data or
the tombstones that record what is being retired.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Leave CRDs prunable, as today | One dropped kind deletes Tenant, ProjectControl and the components' tombstones at once | [Record 105](0105-removal-is-a-retire-lifecycle-with-durable-retirement-tombstones-and-declared-moves-and-prune-protected-kinds-never-prune.md)'s guarantee must reach the kinds that hold it |
| Protect only the CRDs that carry tombstones or Tenants | The mark depends on live state the render cannot see, so no render test holds it | Protection is a property of the rendered kind, not of the cluster's contents |
| Remove a CRD by an operator's one-off action | An unrecorded second path into the cluster | The Retire lifecycle states removal; Flux is the one applier |
| Keep the CRDs out of the render, installed by hand | A kind stops matching the model that declares it and drifts silently | [Record 105](0105-removal-is-a-retire-lifecycle-with-durable-retirement-tombstones-and-declared-moves-and-prune-protected-kinds-never-prune.md) protects what a render holds; a second path was rejected there too |

## Consequences

- Easier: dropping a kind from a render can no longer delete Tenant,
  ProjectControl or a component's tombstones; a rebuild from the datastore
  keeps its Retirement tombstones.
- Harder: a CRD that must go waits the Retire lifecycle's grace period, so
  abandoned kinds linger as claims and namespaces do; the render test gains a
  case for CRDs.
- Forbidden: pruning a rendered CRD by a render change; deleting a CRD while
  custom resources of its kind live or below live Retirement tombstones; a
  tombstone lost to a dropped kind.

## Confirmation

The **Prune protection test** fails when a rendered CRD lacks the
prune-disabled mark, or when a render in which a rendered CRD disappeared
leaves its custom resources removable: one fixture drops a rendered CRD and
the check fails unless the CRD is protected. The **Retirement tombstone
tests** fail when a Retirement tombstone is removed with a dropped CRD, or
when the CRD of a tombstone's kind is pruned while tombstones live.

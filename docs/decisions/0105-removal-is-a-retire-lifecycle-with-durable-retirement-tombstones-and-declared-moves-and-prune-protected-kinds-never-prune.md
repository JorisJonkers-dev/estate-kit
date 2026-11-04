---
status: proposed  # proposed | accepted | locked
date: 2026-11-04
rests-on: [2, 33, 80, 82]
lessons: [DO-2, DO-5]
---

# Removal is a Retire lifecycle with durable Retirement tombstones and declared moves, and prune-protected kinds never prune

## Context

Flux prunes what a render no longer names
([record 2](0002-kubernetes-is-the-substrate-and-flux-is-the-one-applier.md)).
For an object without durable state that is right. For one that holds data it is
a loss: a Rollback to a render from before a Project, or a render that stops
naming one, would delete whatever the pruned object held.

deploy-kit already protects some kinds. A claim whose volume derives a backup
carries the prune-disabled mark, and "stays bound until deleted by hand"
([deploy-kit ADR 0018](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/model/0018-durability-class-derives-a-backup.md)).
Every rendered namespace carries the same mark, because deleting a namespace
deletes every claim in it
([deploy-kit ADR 0142](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/model/0142-a-rendered-namespace-is-never-pruned.md)).
Neither says what happens next: the claim and the namespace stay forever, and
external-dns never deletes a record.

The Mailbox lifecycle goes the other way. Its "dropped from intent" edge deletes
the account ([Mail and components](../design/mail-and-components.md#states-of-a-mailbox)),
and [record 33](0033-a-mailbox-is-declared-by-its-local-part-and-owned-by-one-project.md)
says removing a Project removes its Mailboxes. A renamed local part is a removal
and an addition, so a rename deletes the old account and its mail. Tenant
removal is designed, as Suspend, a grace period and a Purge that waits for every
finalizer ([record 80](0080-a-tenant-is-a-custom-resource-in-a-sixth-bounded-context-tenancy.md)).
Projects and their durable resources have no such design (the architecture
evaluation of 2026-11-04, sections 2.2 and 9.8).

## Decision

This record adopts
[deploy-kit ADR 0142](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/model/0142-a-rendered-namespace-is-never-pruned.md):
prune-protected kinds never prune. They are namespaces, claims whose volume is
declared `recoverable` or `irreplaceable`, Mailboxes, buckets and databases.
Every rendered object of those kinds carries the prune-disabled mark.

When an Application, Process, volume, bucket, database or Mailbox leaves Intent,
`estate-kit plan` lists it as retiring, not deleted. Objects without durable
state are pruned by Flux as before. For a prune-protected object, its owning
component first records a Retirement tombstone: what is retiring, since when,
and under which policy. The tombstone is a custom resource of the owning
component, so it is restored with the datastore, before the components resume.
The policy is set per kind and per class of data: suspend the object, wait a
grace period, verify a recovery copy, then let the owning component delete it
and record the deletion. The grace period is 30 days unless the policy states
another. Declaring the object again
within the grace period cancels the retirement. A tombstone survives a render
change, a lost render and a restore, and a component applies its tombstones
before restored data serves, so a restore never brings back what was retired.

Moves are declared, never inferred. A renamed Mailbox local part, or a volume
moving to another Application, is a `moved_from` in Intent. A removal and an
addition of the same kind under the same owner, with no declared move, is
refused by the plan until the author declares the move or confirms the
retirement. This amends
[record 33](0033-a-mailbox-is-declared-by-its-local-part-and-owned-by-one-project.md):
a Mailbox that leaves Intent, or whose Project leaves, is retired, never removed
by a render change, and a rename moves the account. Tenant removal keeps
[record 80](0080-a-tenant-is-a-custom-resource-in-a-sixth-bounded-context-tenancy.md)'s
lifecycle.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Let Flux prune everything a render omits | A rename or a lost render deletes data | Durable state must not depend on one render |
| Protect, and leave retired objects for the maintainer by hand (today) | Claims, namespaces, records and accounts pile up, and nobody knows which are retired | Removal must actually remove, on a stated policy |
| Infer a move from a removal plus an addition | A wrong guess moves or deletes data silently | The heuristic only refuses; the author declares |
| A tombstone as a row on platform-postgres, or a mark in the outside system | No new kind; restored with its own store, which may be later or lost with the object | A custom resource is restored with the datastore, before the components resume |
| No default grace period; each policy sets its own | A policy that forgets its grace period deletes at once | 30 days unless a policy says otherwise |
| Re-design Tenant removal here | Two lifecycles for one Tenant | [Record 80](0080-a-tenant-is-a-custom-resource-in-a-sixth-bounded-context-tenancy.md) already holds it |

## Consequences

- Easier: a rename never deletes a Mailbox; a lost or old render never deletes
  durable data; a retired object is removed on a stated policy, with a recovery
  copy, instead of lingering.
- Harder: every component that owns a durable kind defines a tombstone kind,
  versioned as a persisted format, and keeps its policies; an author declares
  each move; retirement takes a grace period, 30 days by default.
- Forbidden: pruning a prune-protected kind; deleting a durable object without a
  tombstone, before its grace period ends, or without a verified recovery copy;
  inferring a move.

## Confirmation

The **Prune protection test** fails when a rendered object of a prune-protected
kind lacks the prune-disabled mark. The **Retire refusal fixtures** fail when
the plan accepts a removal and an addition of the same kind under the same
owner with no declared move or confirmed retirement, or treats a declared move
as a retirement. The **Retirement tombstone tests** fail when a component
deletes a durable object without a tombstone, before its grace period (30 days
unless its policy says otherwise), or without a verified recovery copy; when a
cancelled retirement still deletes; or when restored data serves before the
tombstones are applied. The **Mailbox fixtures** keep their contention cases.

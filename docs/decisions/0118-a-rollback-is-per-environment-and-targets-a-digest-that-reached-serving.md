---
status: accepted  # proposed | accepted | locked
date: 2026-11-05
rests-on: [28, 74, 97, 101]
amends: [28]
lessons: [CS-6, TM-4, DR-1]
---

# A Rollback is per Environment and targets a digest that reached Serving

## Context

[Record 28](0028-pause-and-rollback-are-a-cluster-object-per-project.md)'s Rollback has
no defined target: it rolls a Project back to "the Project's last Serving
render", found in the registry. The registry holds every render that was
published, and says nothing about which of them served: a
[Held](../../CONTEXT.md) render is published and never took traffic, so nothing
below the Environment tag's current digest can be trusted to have run. If
signatures are retained exactly as long as their renders but "what served"
lives nowhere, an emergency Rollback can move production onto a render that
never served anyone.

The same record gives the Project one `ProjectControl` for all three
Environments, and its commands name no Environment. Pausing production then
reads and writes a state staging shares, and a command with the Environment
left out acts on whatever its default names.

## Decision

Each admitted Project has one
[ProjectControl](../../CONTEXT.md) per [Environment](../../CONTEXT.md), in the
Project's namespace and named by the Environment, written only by Delivery:
whether the Project is [Paused](../../CONTEXT.md) there, the digest
`rollbackTo` names while a Rollback is running, and a monotone `lastServing`,
the digest of the last render whose Rollout ended
[Serving](../../CONTEXT.md) in that Environment. Every read and write names
the Environment, so pausing or rolling a Project back in one Environment
changes nothing in any other. A missing or unreadable object still reads as
Paused, per Environment
([record 28](0028-pause-and-rollback-are-a-cluster-object-per-project.md)).

The CLI and the OpenAPI document take `--env` as a required parameter on every
Pause, Resume and Rollback command, in every Environment; the CLI and the API
refuse a call that omits it. Both documents are
[Locked contract paths](../../CONTEXT.md#locked-contract-path): the change that
makes them needs the maintainer's `contract-change` label on its pull request
([record 117](0117-a-wording-fix-is-a-dated-revised-line-a-change-of-rule-is-an-amending-record-and-a-locked-change-needs-the-contract-change-label.md)).

A Rollback targets the digest `rollbackTo` names, and that digest must have
reached Serving in the Environment rolled back. The CLI and the API refuse any
other: a render that was published and never served — a Held one — and a digest
that served only in another Environment. `lastServing` is the target a Rollback
is offered; an Operator may name an earlier digest that reached Serving in that
Environment, and Delivery checks the name against what it recorded as Serving,
refusing it when the record cannot be read. The refusal names its target and
its reason; it never moves to a substitute.

Delivery writes Paused and the target to `rollbackTo` in one update of that
Environment's ProjectControl, before it moves anything; the target is durable
from then on. It then takes the writer Lease, dry-runs the target, moves that
Environment's [Environment tag](../../CONTEXT.md) to it by read, verify, write
— the Rollback's Publication point
([record 97](0097-the-publication-point-is-named-and-tested-and-a-render-that-introduces-a-kind-is-published-in-two-stages.md)) — clears
`rollbackTo` when the move is done, and leaves the ProjectControl
[Paused](../../CONTEXT.md). A restarted Delivery finishes any ProjectControl
still carrying `rollbackTo`, from the object and the registry, never from the
event log
([record 104](0104-every-reconciler-estate-kit-owns-passes-crash-point-stale-read-and-safety-tests-before-it-takes-production-responsibility.md)).
Because the target already reached Serving, the Release Gate answers pass for
the digest `rollbackTo` names, without waiting for an
[Analysis verdict](../../CONTEXT.md): no verdict holds an emergency Rollback,
and [record 102](0102-analysis-is-a-pure-verdict-function-and-an-inconclusive-verdict-holds.md)'s
verdicts keep holding releases. If the target render's migration preconditions
do not hold, the Rollback is still refused and the Operator rolls forward
([record 101](0101-a-rollout-rolls-forward-when-rolling-back-would-run-a-migration-backwards.md)).

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| One `ProjectControl` per Project, its fields keyed by Environment | A pause of one Environment writes the object every other Environment reads, and a partial write reaches them all | One object per Project and Environment was settled after the 2026-11-04 review |
| The registry as the source of the target: its highest tag below the current one | A Held render was published and never served, so the highest is not the last that served | The defect this record closes |
| `--env` optional, defaulting to production | An omitted `--env` acts on the wrong Environment by omission | A command validates every input it carries (CS-6) |
| Full analysis before a Rollback's answer | An inconclusive verdict holds an emergency rollback | The target already served; verdicts hold releases |
| The event log as the source of the target | A rollback then needs the database up and intact | A Rollback works with Postgres down ([record 28](0028-pause-and-rollback-are-a-cluster-object-per-project.md)) |

## Consequences

- Easier: an Operator acts on exactly one Environment; a Rollback's target is
  durable before the tag moves, and reconciliation finishes an interrupted one;
  analysis never holds an emergency Rollback.
- Harder: one ProjectControl per Project per Environment rather than one, and a
  change to two Locked contract paths — the CLI and the OpenAPI document —
  which needs the maintainer's `contract-change` label on its pull request.
- Forbidden: a Rollback to a digest that never reached Serving in its
  Environment, or that reached it in another; a Pause, Resume or Rollback call
  without its Environment; one Environment's Pause or Rollback reading or
  writing another Environment's state; retention that prunes the digest
  `lastServing` names.

## Confirmation
The **Rollback target test** fails when a Pause, Resume or Rollback call
without `--env` is accepted, when a Rollback whose target never reached
Serving in its Environment — a Held, never-served digest, or one another
Environment served — is not refused, and when the Release Gate does not answer
pass for the digest `rollbackTo` names; one failing fixture per refusal. The
**Pause refusal test** fails when deleting one Environment's ProjectControl
leaves the next deploy to that Environment accepted instead of refused as
Paused, and when a Paused ProjectControl in one Environment stops a release in
another. Both are Delivery tests, every run ([the table of
checks](../design/code-shape-and-speed.md#the-checks)).

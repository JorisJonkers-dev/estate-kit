---
status: accepted  # proposed | accepted | locked
date: 2026-11-04
rests-on: [28, 81, 96, 97]
lessons: [MS-3]
---

# A Rollout rolls forward when rolling back would run a migration backwards

## Context

A Rollback publishes the last Serving render again, after a dry-run against
today's cluster
([record 28](0028-pause-and-rollback-are-a-cluster-object-per-project.md)).
That restores what runs, not data. A valid old signature proves the render is
authentic, not that the old version can read today's schema. "Atomic Upgrading
of Distributed Systems" (2008) separates preparing an upgrade from activating
it, but does not make database effects reversible. The expand/contract rule
keeps a schema compatible with two adjacent versions of a Project and no more
([record 81](0081-migrations-reach-tenant-databases-in-waves.md)), so rolling
back across a contract migration, a half-applied migration, or a data shape
the previous binary cannot read breaks the old version instead of saving it.
The design has no step for this case (the architecture evaluation of
2026-11-04, sections 3.9, 9.6 and 9.7).

The `migration-run` component runs a Project's managed migrations, `up` and
`down` per revision ([Mail and components](../design/mail-and-components.md#components)).
delivery's Release Gate already holds a down migration to conditions before it
starts one inside a release that has not promoted: the release is held, every
new copy is at zero, the primaries have not moved and every changeset ran in a
transaction (`internal/gate/tend.go`). That undo happens before a promotion and
is not a Rollback; this record does not change it.

## Decision

Every managed migration revision declares its precondition (the schema state
it needs) and its postcondition (the state it leaves), and whether it is
idempotent and whether it runs in one transaction. `migration-run` checks both
around each run and records which hold, so the current state of every
migration is known.

A Rollback reads that record before it dry-runs. If the current state does not
meet the target render's migration preconditions, the Rollback is refused with
a code that names the migration that blocks it, and nothing is published. An
unreadable record refuses the Rollback the same way. A Rollback never runs a
down migration: reversing a migration is its own operation, offered only where
the migration declares a down path. This amends
[record 28](0028-pause-and-rollback-are-a-cluster-object-per-project.md).
`migration-run` keeps the record, with the failed mark of
[record 81](0081-migrations-reach-tenant-databases-in-waves.md), in a custom
resource it owns, one per Project database per Environment. A Rollback reads it
from the API server alone, so it still needs only the API server and the
registry.

A Roll-forward is then the way out. `estate-kit roll-forward <project> --env
<env>` deploys a fixed fragment the Project has released, as a new Operation
([record 96](0096-a-deploy-is-an-operation-that-ends-serving-held-refused-superseded-or-observation-lost.md))
on the full deploy path, with both dry-runs and the Publication point
([record 97](0097-the-publication-point-is-named-and-tested-and-a-render-that-introduces-a-kind-is-published-in-two-stages.md)).
Its failsafe is to hold at the current version, never to revert. A migration
that is neither idempotent nor transactional and stopped part way is never
just run again: `migration-run` refuses it until its partial effects are
reconciled, by a fix migration or by hand, and an Operator records that.
While a Project database is marked failed
([record 81](0081-migrations-reach-tenant-databases-in-waves.md)), the Release
Gate refuses every release of that Project in that Environment, a Roll-forward
included, unless an Operator explicitly requests the Roll-forward. Nothing
automatic may request one.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Roll back regardless of migrations | The old version meets a schema it cannot read | Rollback must not break what serves |
| Run the down migration as part of a Rollback | A Rollback depends on the database and may fail half way | Data reversal is its own operation |
| Restore the database from backup on Rollback | Loses every write since the backup | Data restoration is a separate, deliberate operation |
| Keep the record in the migration's own database table only | A Rollback would read the database, which may be down | Rollback needs only the API server and the registry |
| Carry the requirement in the render, and the state on the Job's status | The render must know its migration's preconditions at composition, and the state goes when the Job is deleted | A custom resource that `migration-run` owns outlives its Jobs |
| Roll forward automatically from a failed migration | A release starts on a database nobody has looked at | Only an Operator may request it |
| Retry a failed non-transactional migration | Its partial effects are applied twice | Reconcile first, then run |

## Consequences

- Easier: a Rollback that would break the old version stops with a reason; the
  maintainer knows when the only safe move is forward.
- Harder: every migration declares its conditions; `migration-run` records them
  per run in a custom resource kind of its own, a write it must be granted; a
  fix fragment must be released before a roll-forward can start.
- Forbidden: a Rollback past a migration whose preconditions do not hold; a
  Rollback that runs a down migration; re-running a partly applied
  non-transactional migration before its effects are reconciled; a
  Roll-forward from a failed migration that no Operator requested.

## Confirmation

The **Rollback migration refusal** fails when a Rollback to a render whose
migration preconditions do not hold, or whose record cannot be read, is not
refused, when the refusal does not name the migration, or when a Rollback runs
a down migration. The **Migration condition record test** fails when
`migration-run` records a run without its pre- and postconditions, keeps its
record anywhere but its custom resource, or starts a partly applied
non-transactional migration again. The **Failed migration release refusal**
fails when a Roll-forward from a Project database marked failed starts without
an Operator's request. A scenario of the **E2E
scenarios** half-applies a contract migration, sees the Rollback refused, and
rolls forward to Serving.

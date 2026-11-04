---
status: proposed  # proposed | accepted | locked
date: 2026-11-04
rests-on: [1, 25, 28, 63, 80, 81]
lessons: [CS-3]
---

# The estate states its defaults for a low-attention week, and every default fails safe

## Context

The estate has one maintainer ([record 1](0001-one-maintainer-one-cluster-one-estate.md)),
whose attention varies: a holiday, an illness or a busy week elsewhere. During
such a week Projects still release, nightly jobs still run, and Flux, Flagger
and the components keep acting. What happens then is decided by defaults, not
by anyone watching.

"Continuous Deployment at Facebook and OANDA" (2016) reports a major failure at
OANDA whose cause was the output of failing unit tests, which had found the
bug, being disregarded among too many false positives. The remedy was to make
the test output part of the deployment decision, not to add approvals. The
architecture evaluation of 2026-11-04 (sections 2.2 and 10.3) reads this as:
safety must come from defaults when the owner's attention varies, and lists
the defaults the design should state in one place. It marks the evidence as
moderate.

Some defaults are already decided, one record at a time: a dry-run must pass
before anything moves
([record 25](0025-a-dry-run-must-pass-before-anything-is-applied-and-what-dry-ran-is-what-deploys.md));
a missing or unreadable ProjectControl reads as Paused
([record 28](0028-pause-and-rollback-are-a-cluster-object-per-project.md));
an unknown outcome is rebuilt from observed state and never replayed
([record 63](0063-delivery-has-one-writer-and-reconciles-from-observed-state.md));
a failed lock or prepare-restore hook aborts a Tenant operation
([record 80](0080-a-tenant-is-a-custom-resource-in-a-sixth-bounded-context-tenancy.md));
a Behind database blocks the next release
([record 81](0081-migrations-reach-tenant-databases-in-waves.md)). Nothing
gathers them, and nothing says what the rule for a new one is.

## Decision

Every situation the estate can reach without the maintainer has a stated
default, and every default fails safe: it blocks, holds or keeps the last good
state, and it alerts. A default never widens what changes, never retries a
move of traffic or a destructive step on its own, and never warns and carries
on. An unattended step that destroys data proceeds only where a recovery copy
outlives it. A low-attention week costs throughput, not correctness.

The defaults are this table. A new situation gets its row, and its default,
in the record that creates it.

| Situation | Default |
| --- | --- |
| A dry-run fails, or an object is unverifiable for a reason other than construction | Block the move; never warn and continue |
| Objects are Unverifiable by construction | Publish the objects they depend on first; dry-run the rest after |
| An Analysis verdict is inconclusive | Hold; never promote; alert when the Held deadline passes |
| A Rollout ends Held | The old version keeps serving; nothing retries on its own |
| ProjectControl is missing or unreadable | Read as Paused |
| A step's outcome is unknown after a crash | Rebuild from observed state; never replay a write on the log's word |
| A composition input moved during the run | Publish nothing; compose again |
| A Sequence tag already exists | The registry refuses; Delivery observes and decides again |
| A lower or replayed Sequence tag appears | Flux ignores it; Delivery alerts on the unknown tag |
| The applied revision differs from the latest published one for longer than a bound | Alert; running workloads keep serving |
| A credential is expired or cannot be verified | Fail closed |
| Vault is sealed | Nothing is signed; a Rollback still works |
| Delivery is down | Nothing new deploys; Flux keeps serving the last renders |
| A Tenant database is Behind | No new version of that Project in that Environment |
| A lock or prepare-restore Tenant hook fails | The Tenant operation stops before any data changes |
| A Suspended Tenant reaches the end of its grace period | The Purge proceeds; its Backup generations remain until their retention ends |
| A Retire grace period ends | Delete only after a verified recovery copy exists |
| A backup reconciler is down | Alert; nothing else changes |
| A node class has no rehearsed fallback | No automatic host rollout for that class |
| Observation of an Operation is lost | The CI job exits with its own code; the Operation continues |

The rows for Unverifiable by construction, the Analysis verdict and its Held
deadline, Sequence tags, Retire, node-class fallbacks and Observation lost
name mechanisms that other Proposed records
decide. Each such row binds when its mechanism's record is accepted, and that
record cites this table rather than restating the default. The length of the
bound on applied-revision drift stays open for the maintainer; the current
drift objective is 24 hours ([conventions](../design/conventions.md#service-levels)).

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Leave each default in its own record | No one place answers "what happens while I am away", and a new record can pick a default that fails open | The rule and the list belong together |
| Warn and continue on a failed check | The maintainer learns of the failure from its effect | The OANDA failure was ignored output; a default must act, not inform |
| Retry a held or failed step automatically | A retry repeats a bad change while no one watches | Holding keeps the old version serving at no cost |
| Pause every deploy while the maintainer is away | No fixes ship during the week, and the switch is one more thing to forget | Fail-safe defaults make a pause unnecessary |
| Ask the maintainer to approve each destructive step | Steps queue for days, and approvals become habit | A recovery copy that outlives the step gives the same safety |

## Consequences

- Easier: a week away needs no preparation; a reviewer can hold a new record
  to one rule; each default is something a test can check.
- Harder: every new mechanism must name its default and the alert that goes
  with it; held work piles up and waits for the maintainer.
- Forbidden: a default that fails open, warns and continues, or retries a
  traffic move or a destructive step on its own; a destructive unattended step
  without a recovery copy that outlives it.

## Confirmation

The **Default scenarios** check fails when a row of the table has no scenario
in the end-to-end suite or no Delivery or component test, or when its scenario
ends other than the row says. The rows already held by a check keep it: the
**Pause refusal test**, the **Sign-precondition test**, the **Single-writer
tests**, the **Behind release refusal**, the **Tenant hook abort** and the
**Purge grace test**. Whether a new record's default fails safe is a review
rule.

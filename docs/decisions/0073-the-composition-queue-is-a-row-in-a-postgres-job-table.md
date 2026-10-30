---
status: proposed  # proposed | accepted | locked
date: 2026-10-29
rests-on: [17, 23, 63]
lessons: [DO-6]
---

# The composition queue is a row in a Postgres job table on the shared platform-postgres

## Context

The service runs one composition at a time, and triggers that arrive meanwhile
merge into the next one ([record 63](0063-the-service-has-one-writer-and-reconciles-from-observed-state.md)).
Something must hold the waiting triggers and say which composition carries
which deploy job's fragment. The
[Rust workspace page](../design/rust-workspace.md) left open whether that
queue lives in memory with the single writer or as rows in Postgres.

The service already keeps its rollout event log in a database on the shared
platform-postgres ([record 23](0023-a-rollout-is-an-append-only-event-log-on-the-shared-postgres.md)).
A queue held in memory is lost on a restart, and the restart is the case the
Lease and observation design exist for.

## Decision

The composition queue is a row in a job table in a database on the shared
platform-postgres, next to the event log. A trigger inserts a row, or merges
into the queued row for the same target. The one writer, holding the Lease,
claims the queued row, composes, and marks it done. A row that was claimed and
never finished is found by a sweeper and queued again. The row is a work
request, not a record of what happened: after a restart the writer observes the
cluster and the registry and decides again, as [record 63](0063-the-service-has-one-writer-and-reconciles-from-observed-state.md)
requires. No new datastore and no message broker is added.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| In memory with the single writer | A restart loses the waiting triggers and the deploy jobs' mapping to a composition | The queue is exactly what a restart must not lose |
| A Kubernetes object per trigger | Another API-server write path and another thing to back up | The event log already needs Postgres |
| A message broker | A new component to run for one queue | Nothing else needs one |

## Consequences

- Easier: a restart keeps the queue; the same database is backed up once.
- Harder: the queue's availability is the database's, so a database outage
  stops new compositions while Flux keeps applying the last tags.
- Forbidden: a second place that decides what is queued; trusting a claimed
  row as proof that a composition ran.

## Confirmation

- The **Job queue tests**: a service test against the `JobStore` fake and, in the adapter's contract
  suite, against a real Postgres, asserts that two triggers during one
  composition produce one queued row.
- A scenario of the **E2E scenarios** kills the service mid-composition and asserts that the
  restarted service finds the claimed row, observes, and either finishes or
  queues it again ([record 69](0069-the-deploy-path-is-tested-end-to-end.md)).

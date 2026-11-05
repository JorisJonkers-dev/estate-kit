---
status: accepted  # proposed | accepted | locked
date: 2026-10-29
rests-on: [17]
lessons: [DR-4]
---

# A rollout is an append-only event log on the shared Postgres

Amended by [record 96](0096-a-deploy-is-an-operation-that-ends-serving-held-refused-superseded-or-observation-lost.md): a deploy call is idempotent on the caller's Operation id, and an Operation ends Serving, Held, Refused, Superseded or Observation lost.

Amended by [record 145](0145-every-rollout-event-row-carries-a-predecessor-digest.md): each row carries the digest of the row before it in the same Rollout, and an append whose predecessor digest does not name the last row the writer read is refused.

## Context

A rollout is a deploy run that streams Delivery's work to the deploy job.
The deploy job may retry a call or lose its connection, and the UI shows the
rollout's history. Delivery needs a store it can append to and replay from.
The estate runs one platform-postgres whose dump and restore are already
checked.

Rollout events outlive the code that wrote them, so a reader must know which
version of an event it holds. There is so far one version of each event: an
upcaster built today would be code with nothing to lift. After a crash Delivery reconciles from what it observes
([record 63](0063-delivery-has-one-writer-and-reconciles-from-observed-state.md)),
and that can append events Delivery did not see happen. Those events differ
in kind from the ones written as the work was done.

## Decision

A rollout is a deploy run, and its events live in one table in a database of
their own on the shared platform-postgres. A rollout's state is the fold of its
events. Events are only appended: never updated, never rewritten, and never
deleted except by the retention job after 400 days
([record 51](register.md)). The columns are on the
[event log section of Delivery page](../design/inside-delivery.md#the-event-log),
plus the [predecessor digest](../../CONTEXT.md) each row carries of the row
before it in the same Rollout, added before the schema is committed
([record 145](0145-every-rollout-event-row-carries-a-predecessor-digest.md)).

A deploy call is idempotent on the caller's Operation id, not the Project and
the fragment digest: a retry with the same id and the same fragment digest
returns the same Operation, the same id with another digest is refused, and
identical content under a new id is a new Operation
([record 96](0096-a-deploy-is-an-operation-that-ends-serving-held-refused-superseded-or-observation-lost.md)).
An Operation ends Serving, Held, Refused, Superseded or Observation lost. A
stream resumes by sequence, at least once, and the
client drops duplicates.

Every event carries a version, and an event holds no personal data: actors are
ids, resolved at read time. Upcasting is deferred. No upcaster is built until a
second version of some event exists; the change that adds that version brings
the upcaster and the test that proves old events still read.

An event that reconciliation appends after a crash is marked as reconstructed
and names the observation it came from. A reader can tell what Delivery saw
happen from what it inferred.

Two database roles touch the table. Delivery's role may insert and select,
and cannot update or delete. The retention job's role may delete and is held by
the job alone; Delivery never holds it. The schema ships as a changelog in a
migration image that alone holds the owner role, as every estate service's does
([workspace ADR-0021](https://github.com/JorisJonkers-dev/workspace/blob/main/docs/decisions/ADR-0021-liquibase-runner-is-the-one-migration-path.md)).

The log is Delivery's history, not the authority on what runs: that is the
cluster and the registry.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| A Postgres of its own | A second database to back up and restore | The shared one is already drilled |
| A Rollout custom resource | History in etcd/SQLite with the cluster's retention | 400 days of history does not belong in the API server |
| In memory | No history; a restart loses every stream | The deploy job resumes by sequence |
| Build the upcaster now | Code and tests for a lift nothing needs | There is one version; build it with the second |
| One role for append and retention | Delivery could delete events | The append-only rule would rest on discipline, not a grant |
| Reconstructed events look like any other | A reader cannot tell a seen event from an inferred one | The log's honesty after a crash is lost |
| An `Idempotency-Key` header on deploy calls | A header standard whose draft expired, beside a key that already exists | The natural key, project and fragment digest, is already there |
| Rewrite events in place when their shape changes | History stops being immutable | Events are upcast on read and hold no personal data, so nothing needs erasing |

## Consequences

- Easier: one backup covers it; the UI and the stream read one table; a retry
  is safe; a reader knows which events were inferred.
- Harder: Delivery depends on platform-postgres; while it is down, new
  rollouts wait, and Flux keeps serving. A second event version brings the
  upcaster and its tests with it.
- Forbidden: updating or deleting an event from Delivery's role; rewriting
  an event to a new version; personal data in an event; a retention role held
  by Delivery.

## Confirmation

Each is one of the **Event-log tests**, run against a real Postgres, except
the lint.

- The unique (rollout id, sequence) key refuses a duplicate append.
- Delivery's database role cannot `UPDATE` or `DELETE` the events table.
- The retention job's role can `DELETE` an event older than 400 days and holds
  no other grant on the table; the two roles are distinct.
- A repeated deploy call with the same Operation id and fragment digest returns
  the same Operation, and a stream resumed from a sequence yields only later
  events.
- Every stored event has a version, and the **Event payload lint** refuses a payload field that
  names a person.
- An event appended by reconciliation is stored marked reconstructed with its
  source observation; one appended by a live step is not.

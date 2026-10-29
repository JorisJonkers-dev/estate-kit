---
status: accepted  # proposed | accepted | locked
date: 2026-10-29
rests-on: [17]
lessons: [DR-4]
---

# A rollout is an append-only event log on the shared Postgres

## Context

A rollout is a deploy run that streams the service's work to the deploy job.
The deploy job may retry a call or lose its connection, and the UI shows the
rollout's history. The service needs a store it can append to and replay from.
The estate runs one platform-postgres whose dump and restore are already
checked.

Rollout events outlive the code that wrote them, so a reader must know which
version of an event it holds. There is so far one version of each event: an
upcaster built today would be code with nothing to lift. After a crash the
service reconciles from what it observes
([record 63](0063-the-service-has-one-writer-and-reconciles-from-observed-state.md)),
and that can append events the service did not see happen. Those events differ
in kind from the ones written as the work was done.

## Decision

A rollout is a deploy run, and its events live in one table in a database of
their own on the shared platform-postgres. A rollout's state is the fold of its
events. Events are only appended: never updated, never rewritten, and never
deleted except by the retention job after 400 days
([record 51](register.md)). The columns are on the
[event log section of the service page](../design/inside-the-service.md#the-event-log).

A deploy call is idempotent on the Project and the fragment digest: a retry
returns the same rollout. A stream resumes by sequence, at least once, and the
client drops duplicates.

Every event carries a version, and an event holds no personal data: actors are
ids, resolved at read time. Upcasting is deferred. No upcaster is built until a
second version of some event exists; the change that adds that version brings
the upcaster and the test that proves old events still read.

An event that reconciliation appends after a crash is marked as reconstructed
and names the observation it came from. A reader can tell what the service saw
happen from what it inferred.

Two database roles touch the table. The service's role may insert and select,
and cannot update or delete. The retention job's role may delete and is held by
the job alone; the service never holds it. The schema ships as a changelog in a
migration image that alone holds the owner role, as every estate service's does
([workspace ADR-0021](https://github.com/JorisJonkers-dev/workspace/blob/main/docs/decisions/ADR-0021-liquibase-runner-is-the-one-migration-path.md)).

The log is the service's history, not the authority on what runs: that is the
cluster and the registry.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| A Postgres of its own | A second database to back up and restore | The shared one is already drilled |
| A Rollout custom resource | History in etcd/SQLite with the cluster's retention | 400 days of history does not belong in the API server |
| In memory | No history; a restart loses every stream | The deploy job resumes by sequence |
| Build the upcaster now | Code and tests for a lift nothing needs | There is one version; build it with the second |
| One role for append and retention | The service could delete events | The append-only rule would rest on discipline, not a grant |
| Reconstructed events look like any other | A reader cannot tell a seen event from an inferred one | The log's honesty after a crash is lost |

## Consequences

- Easier: one backup covers it; the UI and the stream read one table; a retry
  is safe; a reader knows which events were inferred.
- Harder: the service depends on platform-postgres; while it is down, new
  rollouts wait, and Flux keeps serving. A second event version brings the
  upcaster and its tests with it.
- Forbidden: updating or deleting an event from the service's role; rewriting
  an event to a new version; personal data in an event; a retention role held
  by the service.

## Confirmation

Each is a test against a real Postgres.

- The unique (rollout id, sequence) key refuses a duplicate append.
- The service's database role cannot `UPDATE` or `DELETE` the events table.
- The retention job's role can `DELETE` an event older than 400 days and holds
  no other grant on the table; the two roles are distinct.
- A repeated deploy call with the same Project and fragment digest returns the
  same rollout, and a stream resumed from a sequence yields only later events.
- Every stored event has a version, and a lint refuses a payload field that
  names a person.
- An event appended by reconciliation is stored marked reconstructed with its
  source observation; one appended by a live step is not.

---
status: proposed  # proposed | accepted | locked
date: 2026-10-29
rests-on: [17, 23, 45, 49]
lessons: [DO-7]
---

# A rollout is an append-only event log on the shared Postgres

## Context

A rollout streams the service's work to the deploy job
([record 23](register.md)), resumes by sequence
([record 45](register.md)), and the UI shows its history. The service needs a
store it can append to and replay from. The estate runs one platform-postgres
whose dump and restore are already checked.

## Decision

Rollout events live in one table in a database of their own on the shared
platform-postgres: rollout id, sequence, type, version, time, payload, with a
unique (rollout id, sequence) key. A rollout's state is the fold of its events.
Events are versioned and upcast on read, never rewritten, and hold no personal
data ([record 49](register.md)). The schema ships as a changelog in a migration
image that alone holds the owner role, as every estate service's does
([workspace ADR-0021](https://github.com/JorisJonkers-dev/workspace/blob/main/docs/decisions/ADR-0021-liquibase-runner-is-the-one-migration-path.md)).
The log is the service's history, not the authority on what runs: that is the
cluster and the registry ([record 63](0063-the-service-has-one-writer-and-reconciles-from-observed-state.md)).

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| A Postgres of its own | A second database to back up and restore | The shared one is already drilled |
| A Rollout custom resource | History in etcd/SQLite with the cluster's retention | 400 days of history does not belong in the API server |
| In memory | No history; a restart loses every stream | The deploy job resumes by sequence |

## Consequences

- Easier: one backup covers it; the UI and the stream read one table.
- Harder: the service depends on platform-postgres; while it is down, new
  rollouts wait, and Flux keeps serving.
- Forbidden: updating or deleting an event, except the retention job after 400
  days ([record 51](register.md)).

## Confirmation

The (rollout id, sequence) unique key refuses a duplicate; a test asserts the
service's database role cannot `UPDATE` or `DELETE` the events table.

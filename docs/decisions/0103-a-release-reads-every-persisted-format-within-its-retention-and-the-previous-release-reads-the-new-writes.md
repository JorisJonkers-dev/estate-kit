---
status: proposed  # proposed | accepted | locked
date: 2026-11-04
rests-on: [23, 48, 73, 80, 89]
lessons: []
---

# A release reads every persisted format within its retention, and the previous release reads the new writes

## Context

estate-kit writes data that outlives the release that wrote it. Rollout events
and the Tenant operation log are kept 400 days
([record 23](0023-a-rollout-is-an-append-only-event-log-on-the-shared-postgres.md),
[record 80](0080-a-tenant-is-a-custom-resource-in-a-sixth-bounded-context-tenancy.md)).
The job table holds unfinished compositions across a restart
([record 73](0073-the-composition-queue-is-a-row-in-a-postgres-job-table.md)).
ProjectControl and the Tenant resource are custom resources stored in the API
server ([record 28](0028-pause-and-rollback-are-a-cluster-object-per-project.md),
[record 80](0080-a-tenant-is-a-custom-resource-in-a-sixth-bounded-context-tenancy.md)).
A render is kept while it is among its Project's last 20, younger than 90 days,
or named by a tag ([conventions](../design/conventions.md#retention)), and a
Rollback applies an old one, so today's components read the custom resources an
old render carries. Host data and host tags are written by Delivery and read by
host appliers that are updated one node at a time
([record 31](0031-host-closures-are-built-in-ci-and-cached-outside-the-cluster.md)).

[Record 23](0023-a-rollout-is-an-append-only-event-log-on-the-shared-postgres.md)
gives events a version and defers the upcaster to the change that adds a second
version. It states no window and no test that runs the previous release against
new writes, and nothing covers the other formats (the architecture evaluation of
2026-11-04, section 3.10).

"Understanding and Detecting Software Upgrade Failures in Distributed Systems"
(2021) studied 123 real upgrade failures. Incompatible cross-version interaction
caused 63% of them, 60% of those through persistent data. More than 80% were
exposed by running two consecutive major or minor versions, and another 9% by a
two-version gap. Every failure needed three nodes or fewer to trigger.

## Decision

This record extends
[record 23](0023-a-rollout-is-an-append-only-event-log-on-the-shared-postgres.md)
from rollout events to every format estate-kit persists: the event log, the
operation log, the job table, every custom resource estate-kit defines or
renders, host data and the host tag's payload, and the Retirement tombstones of
[record 105](0105-removal-is-a-retire-lifecycle-with-durable-retirement-tombstones-and-declared-moves-and-prune-protected-kinds-never-prune.md).
Each carries its Contract major and a version
([the planned record on Contract majors](register.md)). Two rules hold for each:

- **Forward.** A release reads every version of a format that may still exist:
  any event or operation-log row younger than 400 days, any unfinished job row,
  any stored version of a custom resource, any custom resource in a retained
  render, and the host data of any generation a node can still switch back to.
  A custom resource's served version is removed only when no stored object and
  no retained render uses it.
- **Back, by one release.** The previous release reads what the new release
  writes. So a new version of a format is written in two steps: one release
  learns to read it, and only a later release starts to write it. Upgrading
  estate-kit and then rolling estate-kit back one release never meets data that
  release cannot read.

The upcaster that
[record 23](0023-a-rollout-is-an-append-only-event-log-on-the-shared-postgres.md)
defers still comes with the second version of an event, and it now comes with
the samples and tests below. Wider downgrades (two
releases or more) are not promised.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Upcast on read, with no window and no test (today) | A release that drops an old reader, or writes what the last one cannot read, fails on rollback or on old data | 60% of cross-version failures in the 2021 study went through persistent data |
| Rewrite stored data to the newest version on upgrade | A migration of 400 days of history; the append-only rule breaks | [Record 23](0023-a-rollout-is-an-append-only-event-log-on-the-shared-postgres.md) forbids rewriting events |
| No downgrade: roll forward only | A bad estate-kit release can only be fixed by another release, under pressure | The previous release is the cheapest recovery there is |
| A downgrade window of two releases | Every format change waits two releases before it is written | Two consecutive versions expose more than 80%; the gap adds 9% at double the wait |
| Test every pair of versions within retention | A matrix that grows with every release | Consecutive versions find most failures; samples cover the old versions |

## Consequences

- Easier: rolling estate-kit back one release is always safe for its data; a
  Rollback to a 90-day-old render meets components that can read it; a reader
  knows which version it holds.
- Harder: a format change takes two releases; each format keeps samples of every
  version in retention; a custom resource version lingers until no stored object
  or retained render uses it.
- Forbidden: writing a format version that the previous release cannot read;
  dropping a reader while data of that version is within retention; removing a
  served custom resource version still in use.

## Confirmation

The **Retention-wide read test** fails when the release candidate cannot read a
committed sample of any version of a persisted format still within its
retention, or when a custom resource version still used by a stored sample or a
retained render is no longer served. The **Format write-version check** fails
when a release candidate writes a version of a format that the last release's
supported range does not include. The **Downgrade read test** runs the previous
release against stores the release candidate wrote, and fails when it cannot
read a write, misreads one, or rewrites one in an older version. The **Schema
evolution check** still classifies each change to a committed schema
([record 48](0048-the-cli-s-json-output-has-a-committed-schema.md)).

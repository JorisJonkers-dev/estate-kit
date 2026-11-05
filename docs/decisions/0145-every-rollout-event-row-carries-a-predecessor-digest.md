---
status: accepted  # proposed | accepted | locked
date: 2026-11-05
rests-on: [23, 48, 89]
amends: [23]
lessons: [DO-4]
---

# Every Rollout event row carries a predecessor digest

## Context

The event log is a table of Rollout events, appended and never rewritten
([record 23](0023-a-rollout-is-an-append-only-event-log-on-the-shared-postgres.md)).
Its uniqueness today is a (rollout id, sequence) key: a duplicate append is
refused, and a stream resumes by sequence. A sequence number orders what
Delivery sees, but nothing on a row says which row it follows: a gap left by a
lost write, or a reorder after a crash, reads as an intact log whose count is
simply short. The design review of 2026-11-04 (the final report's section 15,
question 20) recommended adding a predecessor digest to each row now, and the
maintainer settled it the same day — before the log's schema is committed.

The event log is a persisted, externally read contract: once
`contracts/` holds its schema, every change to it is classified against every
reader by Contract major and supported range
([record 89](0089-every-persisted-or-externally-read-contract-has-its-own-identifier-contract-major-and-supported-range.md)),
and evolves additively within its major version
([record 48](0048-the-cli-s-json-output-has-a-committed-schema.md)). Adding a
column before the schema is committed buys the chain for nothing; adding it
after makes every reader's first major a reluctant one.

DO-4 makes the chain worth its cost: the log is the record a deploy job
streams, the UI reads and a rebuild reconciles from, so its integrity is a
value a consumer reads, not an argument.

## Decision

Every Rollout event row carries, beside its (rollout id, sequence) key, the
[predecessor digest](../../CONTEXT.md): the digest of the stored content of
the row before it in the same Rollout — its rollout id, sequence, type,
version, time and payload. The first event of a Rollout carries the empty
digest. An append is refused when the predecessor digest it carries does not
name the last row the writer read, so a gap, a reorder and an overwrite are
detected at the log itself: the next writer cannot append onto a past it did
not see. An event reconciliation appends after a crash
([record 23](0023-a-rollout-is-an-append-only-event-log-on-the-shared-postgres.md))
carries the digest of the row it read, marked reconstructed as before, so the
chain holds across the gap it names. The digest covers the stored content,
never the digest column of its predecessor, so the chain cannot loop.

This amends [record 23](0023-a-rollout-is-an-append-only-event-log-on-the-shared-postgres.md):
its columns gain the predecessor digest now, before the event payload schema
is committed to `contracts/`, and every later version of an event carries one.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Sequence numbers alone | A lost append leaves an intact-looking log missing a row; the count of a reorder is a silent lie | The unique key refuses duplicates but names no predecessor |
| A digest chain added with the first schema change | Every reader's first major is spent on an integrity column | The column is cheap now, expensive later |
| A digest of the predecessor's entire row, digest column included | A hash loop the writer cannot order; the chain must grow one way | The digest covers stored content only |
| A periodic Merkle root over the log | A tree to keep and verify for a table one process appends and one job prunes | One link per row already detects the gap and the reorder |
| Verify the chain at read time only | A corrupted or reordered log is found after it streamed | The append itself refuses what the chain does not name |

## Consequences

- Easier: a gap or a reorder is detected at the log itself, and by the writer
  that would extend it; the schema carries the column from its first version.
- Harder: every append reads the last row's digest; a crash mid-append leaves
  a retry to re-read it, and the fixture set gains one more refusal.
- Forbidden: an event row with no predecessor digest; an append whose
  predecessor digest does not name the last row the writer read; a digest
  that covers its predecessor's digest column.

## Confirmation

One of the **Event-log tests**, against a real Postgres: an appended row
whose predecessor digest does not name its Rollout's last stored row is
refused, and a row stored with no predecessor digest fails its read. The
**Event payload lint** refuses a payload field that names a person, as before;
the columns of the table stay as [record 23](0023-a-rollout-is-an-append-only-event-log-on-the-shared-postgres.md)
names them, plus its predecessor digest.

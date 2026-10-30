---
status: accepted  # proposed | accepted | locked
date: 2026-10-29
rests-on: [9, 17, 23]
lessons: [DO-6, TM-4]
---

# The service has one writer and reconciles from observed state

## Context

The service signs renders and moves tags ([record 17](0017-the-service-runs-in-the-cluster-in-rust.md)).
Two writers at once could sign and move the same Project's tag from two
compositions, and two compositions at once could each publish a render built
from inputs the other moved. The design ran one replica with no leader election, but a
one-replica Deployment with the default rolling update surges to two pods
during every update, so for a while two writers run
([review](../research/review/README.md) D9, finding ops-3).

The service's own record of a rollout, the event log ([record 23](0023-a-rollout-is-an-append-only-event-log-on-the-shared-postgres.md)),
can also be wrong after a crash: an event may be written for a tag move that
never happened, or a tag may have moved without its event. Flux keeps applying
the last tags throughout, so the cluster, not the log, is what runs.

ghcr has no compare-and-swap: a tag is moved by pushing a manifest to it, and
the push carries no condition on the tag's current value. Nothing at the
registry can refuse a move because the tag changed since it was read.

## Decision

1. **One pod, never two, and one composition at a time.** The service's Deployment uses strategy `Recreate`,
   so an update stops the old pod before it starts the new one. The pod runs one
composition at a time; triggers that arrive meanwhile merge into the next
composition. A composition covers all its inputs and publishes nothing if an
input moved during the run. Where the queue is kept is
[record 73](0073-the-composition-queue-is-a-row-in-a-postgres-job-table.md).
2. **A Lease before every write.** The service takes a coordination Lease in
   the API server immediately before it signs a render or moves a tag, and
   checks it is still the holder before the write. A pod that is not the
   holder signs and moves nothing.
3. **Observed state over the log.** On startup, and whenever a step's outcome
   is unknown, the service rebuilds each unfinished rollout from what it can
   observe: the Project's tag in ghcr, and Flux's Kustomization and
   OCIRepository status and Flagger's Canary status. It appends the events the
   observation implies, or ends the rollout with an Abandoned event. It never
   replays a write because the log says it is due.
4. **A tag move is read, verify, write, read again.** The service reads the
   tag, verifies that it still names the digest the decision was made from,
   checks the Lease, writes, and reads the tag again. If the second read shows
   any value other than the one written, the move lost a race: the service
   stops, observes, and decides again. It never retries a write on the old
   decision ([record 23](0023-a-rollout-is-an-append-only-event-log-on-the-shared-postgres.md)). Signing a digest twice yields a valid
   signature, so signing needs no such check.
5. **The race window is stated, not hidden.** Between the Lease check and the
   registry accepting the write, a holder that has just lost its Lease (a
   paused process, a clock jump) can still write. The re-read after the write
   catches it only while the other writer's value is still there, and a write
   by something that holds the machine token but not the Lease is not fenced
   at all. The window is as long as one registry call plus any stall of the
   process between the check and the call.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| One replica, no leader election (the first design) | Two writers during every rolling update | Review D9 |
| Several replicas with leader election | Standby pods for a service with one composition at a time | Nothing to scale; the Lease alone suffices |
| A level-triggered composer with Postgres as a disposable cache (review D9, option B) | Rollout visibility and stream semantics redesigned | The rollout stream is the deploy job's view; the log stays, but observation wins |
| Say the tag move is a compare-and-swap | A claim ghcr cannot honour; a lost race goes unnoticed | The registry has no conditional write |
| Trust the event log on startup | A crash between a write and its event leaves the log wrong | The cluster and the registry are what runs |
| Compose in parallel per Project | Estate-wide checks race between Projects | One composition runs at a time, and triggers coalesce |

## Consequences

- Easier: a crash or an update at any step is recovered without a human;
  the deploy job's stream resumes with the observed outcome.
- Harder: every step needs an observation that says whether it happened.
- Forbidden: a second writer; a sign or a tag move without holding the Lease;
  a write repeated on the log's word alone; a tag move that is not read again
  afterwards.

## Confirmation

- A deployment test fails if the service's Deployment strategy is not `Recreate`.
- A service test runs two instances against fakes and asserts that only the
  Lease holder signs or moves a tag.
- A service test makes the fake registry change the tag between the write and
  the re-read, and asserts that the move is reported as a lost race and not
  retried on the old decision.
- A service test queues two triggers during one composition and asserts that
  one composition follows, covering both.
- An e2e scenario kills the service after each write step and asserts that the
  restarted service ends the rollout with the outcome the cluster shows
  ([record 69](0069-the-deploy-path-is-tested-end-to-end.md)).

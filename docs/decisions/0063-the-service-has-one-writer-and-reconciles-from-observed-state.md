---
status: accepted  # proposed | accepted | locked
date: 2026-10-29
rests-on: [9, 17, 19, 24, 45]
lessons: [DO-6, DO-7, TM-4]
---

# The service has one writer and reconciles from observed state

## Context

The service signs renders and moves tags ([record 17](0017-the-service-runs-in-the-cluster-in-rust.md)).
Two writers at once could sign and move the same Project's tag from two
compositions. The design ran one replica with no leader election, but a
one-replica Deployment with the default rolling update surges to two pods
during every update, so for a while two writers run
([review](../research/review/README.md) D9, finding ops-3).

The service's own record of a rollout, the event log ([record 24](register.md)),
can also be wrong after a crash: an event may be written for a tag move that
never happened, or a tag may have moved without its event. Flux keeps applying
the last tags throughout, so the cluster, not the log, is what runs.

## Decision

1. **One pod, never two.** The service's Deployment uses strategy `Recreate`,
   so an update stops the old pod before it starts the new one.
2. **A Lease before every write.** The service takes a coordination Lease in
   the API server immediately before it signs a render or moves a tag, and
   checks it is still the holder before the compare-and-swap. A pod that is
   not the holder signs and moves nothing.
3. **Observed state over the log.** On startup, and whenever a step's outcome
   is unknown, the service rebuilds each unfinished rollout from what it can
   observe: the Project's tag in ghcr, and Flux's Kustomization and
   OCIRepository status and Flagger's Canary status. It appends the events the
   observation implies, or ends the rollout with an Abandoned event. It never
   replays a write because the log says it is due.
4. **Every write is idempotent.** Signing a digest twice yields a valid
   signature; a tag move is a compare-and-swap from the observed digest, so a
   repeated move is refused, read again and decided again
   ([record 45](register.md)).

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| One replica, no leader election (the first design) | Two writers during every rolling update | Review D9 |
| Several replicas with leader election | Standby pods for a service with one composition at a time ([record 19](register.md)) | Nothing to scale; the Lease alone suffices |
| A level-triggered composer with Postgres as a disposable cache (review D9, option B) | Rollout visibility and stream semantics redesigned | The rollout stream is the deploy job's view; the log stays, but observation wins |
| Trust the event log on startup | A crash between a write and its event leaves the log wrong | The cluster and the registry are what runs |

## Consequences

- Easier: a crash or an update at any step is recovered without a human;
  the deploy job's stream resumes with the observed outcome.
- Harder: every step needs an observation that says whether it happened.
- Forbidden: a second writer; a sign or a tag move without holding the Lease;
  a write repeated on the log's word alone.

## Confirmation

- A deployment test fails if the service's Deployment strategy is not `Recreate`.
- A service test runs two instances against fakes and asserts that only the
  Lease holder signs or moves a tag.
- An e2e scenario kills the service after each write step and asserts that the
  restarted service ends the rollout with the outcome the cluster shows
  ([record 69](0069-the-deploy-path-is-tested-end-to-end.md)).

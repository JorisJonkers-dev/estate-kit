---
status: proposed  # proposed | accepted | locked
date: 2026-11-04
rests-on: [23, 54, 63, 94, 95]
lessons: [DO-4, DO-6]
---

# A deploy is an Operation that ends Serving, Held, Refused, Superseded or Observation lost

## Context

A deploy run holds an SSE stream until the last promotion
([Releasing](../design/releasing.md)), and a Rollout ends in Serving, Held or
Refused. Three things are missing for a live view the maintainer can trust
(the architecture evaluation of 2026-11-04, sections 1.1, 9.3 and 9.4). A
deploy has no identity of its own: [record 23](0023-a-rollout-is-an-append-only-event-log-on-the-shared-postgres.md)
makes a deploy call idempotent on the Project and the fragment digest, so a
deliberate redeploy of the same content cannot be told from a retry. "Serving"
is not defined against the steps and objects Flux applies. And a run that was
replaced by a newer deploy, or that lost sight of the cluster, has no honest
end: it either waits or reports something it does not know.

A later run superseding an earlier one is how delivery already works (DO-6). A
`Ready` condition or an exit code has never been the evidence a deploy worked
(DO-4). The stream feeds `estate-kit watch` in a CI log, where it prints one
line per event grouped per step, in a terminal, and in the UI
([Splitting estate-kit](../research/decomposition.md#watching-a-switchover-live)).

## Decision

A deploy is one Operation of one Project to one Environment. The caller mints
its Operation id (the reusable deploy workflow mints one per run attempt), and
Delivery returns it with the URL of its stream. Every Rollout event carries
it, and the source revision and render digest are bound to it. A retry with
the same id and the same fragment digest returns the same Operation; the same
id with another digest is refused; identical content under a new id is a new
Operation. This replaces the idempotency key of
[record 23](0023-a-rollout-is-an-append-only-event-log-on-the-shared-postgres.md)
and extends that record with the outcomes below. Losing the caller never
cancels an Operation; `estate-kit watch <operation>` reattaches.

An Operation ends in exactly one of five outcomes, and `estate-kit watch` exits
with that outcome's code:

| Outcome | When | Exit |
| --- | --- | --- |
| Serving | The intended digest is the applied revision of every Apply group's Kustomization ([record 95](0095-a-project-renders-as-a-chain-of-flux-kustomizations-one-per-apply-group.md)), every inventoried object is healthy by the kstatus rules, that digest's migration has completed, and every Canary has promoted that digest | 0 |
| Held | The render was published, and a step, object, migration or analysis failed, so the old version keeps serving; with a reason and a deadline | 10 |
| Refused | Delivery stopped it before the Publication point: admission, digest registration, Pause, composition or dry-run; nothing changed | 11 |
| Superseded | A newer Operation for the same Project and Environment was composed in its place or published over it before it ended | 12 |
| Observation lost | Delivery has had no observation of Flux or Flagger for 10 minutes, so it cannot say how the Rollout ended; the Rollout goes on and may still reach Serving | 13 |

Exit 1 means the watch itself failed (it could not authenticate or reach
Delivery) and says nothing of the Operation; exit 2 is a usage error. An
observation for another digest never advances an Operation, and a Canary
result for an older revision never completes a newer one. A Rollout that
reconciliation ends as Abandoned ([record 63](0063-delivery-has-one-writer-and-reconciles-from-observed-state.md))
ends its Operation as Observation lost. A new Operation whose render is
unchanged publishes nothing and ends Serving once the fold sees that digest
serving. Two bounds apply. When Flux has not picked a published render up
after 30 seconds, the stream says so, and the Operation goes on. When Delivery
has had no observation at all for 10 minutes, the Operation ends Observation
lost. Separately, Delivery alerts when the applied revision trails the latest
published one for 1 hour, as the low-attention defaults of
[record 86](0086-the-estate-states-its-defaults-for-a-low-attention-week.md)
state. The maintainer has approved the exit codes in the table, with 1 and 2
as above, and they enter the CLI's committed contract
([record 48](0048-the-cli-s-json-output-has-a-committed-schema.md)).

The stream is SSE. A client resumes with `Last-Event-ID`; if the cursor has
expired it gets a snapshot and continues; authorisation is checked again on
every reconnect; a slow reader is dropped, never allowed to stall the fold.
Pause, Resume and Rollback are POSTs, each with its own row in the
authorisation matrix ([record 54](0054-every-trust-boundary-has-a-threat-table-and-every-route-an-authorization-row.md)),
and idempotent on a command id the caller mints: a repeat gives one effect.
They act only through ProjectControl, publication and the Release Gate's
answers, never on a Flux object
([record 94](0094-flux-stays-the-one-applier-observed-closely-and-an-estate-kit-applier-waits-for-a-review-trigger.md)).

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Keep idempotency on Project and fragment digest | A deliberate redeploy is a retry; a lost response and a second deploy look alike | The caller's id tells them apart |
| Delivery mints the id and the caller keeps none | A retried call after a lost response starts a second Operation | The id must exist before the first call |
| One non-zero exit for every outcome but Serving | CI cannot tell Held from Superseded without parsing output | One code per outcome |
| Outcome codes 1 to 4 | They collide with the usual meaning of 1 and 2 | 10 to 13 leave 1 and 2 to the command itself |
| Superseded exits 0 | A run whose content never served looks like a success | Only Serving exits 0 |
| End on a timeout with a failure | A slow Flux is reported as a failed deploy | Observation lost says what is known |
| Cancel the Operation when the CI job ends | A cancelled job leaves a half-made decision | The Operation continues; watch reattaches |

## Consequences

- Easier: CI branches on the outcome; a run reattaches after a lost job; the
  same stream drives the CI log, the terminal and the UI.
- Harder: every outcome needs an end-to-end scenario; the exit codes are a
  committed contract, so changing one needs the maintainer's approval; a Flux
  that regularly takes longer than 30 seconds to pick a render up fills the stream
  with notices.
- Forbidden: exit 0 for anything but Serving; an Operation advanced by another
  digest's observation; a command that writes a Flux object; cancelling an
  Operation because its caller went away.

## Confirmation

The **Operation outcome tests** fail when a recorded sequence of observations
ends other than its fixture says, another digest advances an Operation, a newer
Operation does not end the older Superseded, the stream does not say a render
has not been picked up after 30 seconds, an Operation with no observation for
10 minutes does not end Observation lost, or `estate-kit watch` exits with
another code than the table, 1 or 2 gives. The **Operation idempotency tests**
and the **Operation stream tests** hold the id and stream rules, and the
**Authorization matrix test** the commands' rows. The **E2E scenarios** end one
Operation in each outcome.

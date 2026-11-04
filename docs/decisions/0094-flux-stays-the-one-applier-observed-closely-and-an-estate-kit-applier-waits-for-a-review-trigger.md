---
status: accepted  # proposed | accepted | locked
date: 2026-11-04
rests-on: [2, 23, 58, 63, 74]
amends: [2, 63]
lessons: [DO-4, DO-5]
---

# Flux stays the one applier, observed closely, and an estate-kit Applier waits for a review trigger

## Context

The maintainer wants to watch every deploy live, from CI, the terminal and the
UI, until it has fully completed, while Flux pulls. Pull decides who applies
and where the apply credential lives
([record 2](0002-kubernetes-is-the-substrate-and-flux-is-the-one-applier.md),
[record 58](0058-flux-is-locked-down-per-project-and-delivery-dry-runs-as-an-identity-that-cannot-write.md)).
A live view needs a complete, ordered and timely record of what the applier
did. Flux already writes one to the API server: conditions with typed reasons,
an inventory of every object it applied, a Kubernetes Event per change, and
the status of each applied object. Today Delivery reads only Kustomization and
OCIRepository status ([Inside Delivery](../design/inside-delivery.md#what-it-reads-from-the-cluster)),
so it learns late and by inference ([Splitting estate-kit](../research/decomposition.md#the-deploy-path-without-flux)).
That research note leaned to option B, an estate-kit Applier that replaces Flux.

The architecture evaluation of 2026-11-04, section 1.1, found the two
compatible: the gap is in the observer, not in pull. "Performance Evaluation of
Intent-Based Networking Scenarios: A GitOps and Nephio Approach" (2025)
measured Flux syncing in 1 to 10 seconds with a webhook, and as the least
resource-intensive of three GitOps operators. "Mutiny! How does Kubernetes
fail, and what can we do about it?" (2024) saw no error reported to the user in
more than 85% of its experiments, so an observer must compare desired and
observed state itself. Owned controllers are where measured bugs sit: "Anvil:
Verifying Liveness of Cluster Management Controllers" (2024) reports that 69%
of the bugs earlier tools found were failures to converge. deploy-kit has a
Proposed record that drives a Rollout from the cluster's own Flux events
([deploy-kit ADR 0099](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/model/0099-a-rollout-is-a-github-deployment-driven-by-the-clusters-events.md)).
The maintainer chose this direction on 2026-11-04.

## Decision

Flux stays the one applier, with no end date, and Delivery observes it closely.
This amends [record 2](0002-kubernetes-is-the-substrate-and-flux-is-the-one-applier.md)'s
consequences (one applier, now watched object by object, and a review clause),
the observation list of [record 63](0063-delivery-has-one-writer-and-reconciles-from-observed-state.md),
point 3, and the section of [Inside Delivery](../design/inside-delivery.md#what-it-reads-from-the-cluster)
on what Delivery reads. All three are rewritten to say so.
"Flux, observed closely" has eight parts:

1. **One identity.** A deploy is one Operation, bound to its Project,
   Environment, source revision and render digest. CI receives its Operation
   id and the URL of its stream.
2. **Trigger.** After the Publication point, Delivery calls the Project's Flux
   Receiver, so Flux fetches at once; the reconcile interval stays as the
   fallback if the call is lost. How the call authenticates (`generic-hmac`,
   or OIDC with the cluster's issuer) is a spike.
3. **Ordered steps.** Each Apply group is its own Flux Kustomization, joined by
   `dependsOn` and health checks, under the Project's one service account.
4. **Per-object truth.** Delivery watches, read-only, the Project's
   Kustomizations, OCIRepository and Canary objects, Events in `flux-system`
   and the Project's namespaces, and every object in each step's inventory. It
   computes each object's health itself by the kstatus rules and never takes
   Flux's summary as the truth. It correlates by the render digest Flux reports
   as applied, and writes no Flux object. It watches rather than taking Flux's
   or Flagger's webhooks, since it takes no unauthenticated push.
5. **One fold.** Each observation becomes a versioned Rollout event with a
   sequence number ([record 23](0023-a-rollout-is-an-append-only-event-log-on-the-shared-postgres.md));
   events rebuilt after a gap are marked reconstructed. The sequence orders
   Delivery's observations; it claims no physical order across controllers.
6. **The stream and the commands.** One SSE stream feeds `estate-kit watch` in
   CI, the terminal and the UI, until the Operation ends. Pause, Resume and
   Rollback are separately authorised POSTs.
7. **Serving is defined**: the intended digest is applied in every step, and
   that digest's migration, health and promotion conditions hold.
8. **The forge is a projection.** A GitHub Deployment status mirrors the fold;
   the event log is the authority.

What stays opaque is said, not hidden: Flux's own queue (the stream can say
"not picked up for 20 seconds", not why); order inside one step; errors, which
are shown as Flux's strings verbatim and not parsed; prune decisions, which
show as events, while prune protection stays declared in the render; the
health clock, which Flux's timeout sets and Delivery mirrors; Events, which are
rate-limited and expire, so Delivery also watches the objects, resynchronises
periodically and marks gaps; two foreign state machines, of which the Rollout
is a fold and not the authority; and ordering at the reader, which Flux checks
by signature over a digest, not by sequence.

Two crates hold it: `observe`, a domain crate with the pure fold of Flux,
Flagger and object observations into Rollout events (step state from
Kustomization conditions, object health by kstatus rules, correlation by
digest, gap marking); and `adapter-flux-watch`, the read-only watches and the
Receiver call. Parts 1, 6 and 7 are detailed in
[the Operation record](0096-a-deploy-is-an-operation-that-ends-serving-held-refused-superseded-or-observation-lost.md),
and part 3 in [the Kustomization chain record](0095-a-project-renders-as-a-chain-of-flux-kustomizations-one-per-apply-group.md).

An estate-kit Applier is built only when one of these review triggers fires:

| Trigger | Fires when |
| --- | --- |
| T1 Order | A Release Unit or migration scenario of the end-to-end suite fails under the best chain of Kustomizations plus the Release Gate |
| T2 Latency | Over 20 consecutive production deploys with Receivers in place, the p95 from publication to the first observed apply exceeds 30 seconds |
| T3 Upstream | A Flux release breaks [record 58](0058-flux-is-locked-down-per-project-and-delivery-dry-runs-as-an-identity-that-cannot-write.md)'s lockdown flags, OCI signature verification or server-side apply and no fixed release follows within one minor; or Flux ships no security release for six months |
| T4 Explanation | Three stalls in one quarter whose cause the stream could not name and that needed Flux's logs to diagnose |
| T5 Reader refusal | Refusing an out-of-order or cross-Project render at the reader becomes a requirement that sequence tags cannot meet |

If one fires, Argo CD is benchmarked first. An Applier replaces Flux only after
a behavioural comparison on a canary Project: it runs in shadow, planning and
computing inventories without writing; it passes crash-in-the-middle,
stale-read, prune and field-ownership scenarios; ownership moves explicitly,
one Project at a time, never two appliers on one Project; and the Rollback of
[record 28](0028-pause-and-rollback-are-a-cluster-object-per-project.md) is
proved again.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Watch from afar, as today (Kustomization and OCIRepository status) | A deploy looks like an inference; a stall cannot be explained | The data a live view needs is already in the API server |
| An estate-kit Applier now (research option B) | 120 to 200 hours plus convergence tests; pruning, drift and field ownership become our bugs | It catches no mistake Flux observed closely misses; kept dormant behind T1 to T5 |
| Delivery applies, or CI pushes (options C and D) | A write credential beside the signer, or outside the cluster | Already refused by [record 2](0002-kubernetes-is-the-substrate-and-flux-is-the-one-applier.md) |
| Take Flux's and Flagger's webhooks | An unauthenticated push into Delivery | Watches give the same data with no push |
| A promotion controller feeding Flux through ExternalArtifact | A second writer of Flux objects and a controller to own | [Record 9](0009-the-live-render-is-a-signed-registry-tag-per-project-and-environment.md) and [record 28](0028-pause-and-rollback-are-a-cluster-object-per-project.md) refuse a second writer; sequence tags give the order |
| Replace Flux on an inventory match alone | Says little about pruning, stale reads, field ownership or interrupted migrations | The behavioural gate above |

## Consequences

- Easier: a deploy is seen live per step and per object from one stream; Flux
  keeps absorbing the convergence bugs an owned applier would bring; the
  question "when do we replace Flux" has measured answers.
- Harder: the fold must stay correct against two foreign state machines; Flux
  upgrades must be watched for T3; a stall inside Flux's queue stays
  unexplained.
- Forbidden: a write to a Flux object by Delivery; an applier beside Flux; an
  Applier built without a fired trigger, or put into production without the
  behavioural gate; reporting Serving from Flux's summary alone.

## Confirmation

The **Flux observation fold tests** fail when `observe` advances an Operation
on another digest's observation, derives a step or object state other than its
fixture says, or appends after a gap without the reconstructed mark. The
**Dry-run admission fixtures** keep Delivery's identity from writing any Flux
object. The **E2E scenarios** gain a deploy watched per group and per object,
ending in each outcome. The **Applier review triggers** job reports T2 and T4
from the event log; T1 is an end-to-end scenario, T3 is the lockdown fixtures
run on every Flux upgrade, and T5 is a review rule with no check.

---
status: proposed  # proposed | accepted | locked
date: 2026-11-04
rests-on: [9, 25, 28, 58, 63, 69]
lessons: [TM-6]
---

# The Publication point is named and tested, and a render that introduces a kind is published in two stages

## Context

A deploy composes, dry-runs, takes the writer Lease, signs, pushes the render
and then moves its Environment tag
([record 9](0009-the-live-render-is-a-signed-registry-tag-per-project-and-environment.md),
[record 63](0063-delivery-has-one-writer-and-reconciles-from-observed-state.md)).
Only the tag move makes the render visible to Flux. Before it, a crash has
changed nothing the cluster reads; after it, Flux may apply the render at any
time, and over time, not atomically. The design has no name for that step, and
no test that interrupts on each side of it (the architecture evaluation of
2026-11-04, section 3.9). The E2E scenario of
[record 63](0063-delivery-has-one-writer-and-reconciles-from-observed-state.md)
already kills Delivery after each write, which is the harness such a test
needs.

[Record 25](0025-a-dry-run-must-pass-before-anything-is-applied-and-what-dry-ran-is-what-deploys.md)
sends every changed object to the API server with `dryRun=All` and moves no tag
unless it passed. An object whose CustomResourceDefinition or namespace arrives
in the same render cannot be dry-run: the API server does not know its kind or
its namespace yet. Read literally, the first install of a Project, or the first
render with a new kind, can never be published (the evaluation, sections 1.4
and 3.9).
[Record 58](0058-flux-is-locked-down-per-project-and-delivery-dry-runs-as-an-identity-that-cannot-write.md)
also concedes that Delivery's dry-run identity does not
exercise each Project's RBAC; only Flux's apply does.

## Decision

The Publication point is one named step of a deploy and of a Rollback: today
the move of the Environment tag by read, verify, write and read again; once
the live pointer becomes a sequence tag, the creation of the next tag. No other
step makes a render visible to Flux. Code tests an interruption on each side
of it. Interrupted before it, a render may be pushed and signed but no tag
names it; the restarted Delivery finds no change Flux can read and decides
again from the inputs. Interrupted after it, the restarted
Delivery observes the tag, follows the Rollout by observation, and never
publishes again on the log's word.

A render that introduces a kind or a namespace is published in two stages.
The plan names each object that is Unverifiable by construction: one whose
kind or namespace the API server does not yet serve because this render brings
it. The first stage is the full render without those objects, dry-run and
published as usual. Once Flux has applied it and the API server serves the new
kinds and namespaces, the full render is dry-run again and published as the
second stage, in the same Operation. The first stage prunes nothing the second
adds back, because no earlier render can have held an object of a kind or
namespace that did not exist. An object that cannot be dry-run for any other
reason blocks the move. Each stage is a function of the same pinned inputs,
since which kinds the cluster serves is in the ClusterState snapshot.

This amends the wording of [record 25](0025-a-dry-run-must-pass-before-anything-is-applied-and-what-dry-ran-is-what-deploys.md):
"every changed object" becomes every changed object that is not Unverifiable
by construction, which is dry-run in the second stage before it is published,
and "before any tag moves" becomes before each Publication point. It amends
the wording of [record 28](0028-pause-and-rollback-are-a-cluster-object-per-project.md):
a Rollback's tag move is a Publication point, and it moves the Environment tag
of the Environment rolled back, not only the Prod tag; once the pointer is a
sequence tag, a Rollback creates the next tag naming the older, already-signed
digest. Both records are corrected
when this one is accepted.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Call the tag move "the commit" | Suggests an atomic rollout that Flux does not give | Publication says what happens: the render becomes visible |
| Block every object that cannot be dry-run | The first install and every new kind deadlock | Two stages keep the gate and make bootstrap possible |
| Skip the dry-run for objects of new kinds | What deploys was never dry-run | The second stage dry-runs them first |
| Validate new kinds offline from their schemas | No admission webhook, quota or field-conflict check | Offline is the fallback only when the dry-run cannot run |
| Install CRDs and namespaces outside the render | A second path into the cluster | Flux is the one applier |
| Test interruption only end to end | Each side of the step is hit by chance | A test per side, with fakes and end to end |

## Consequences

- Easier: a first install and a new kind deploy without a hand step; a reader
  of the code knows the one place where a render crosses into the cluster.
- Harder: an Operation may publish twice, and its stream shows both stages;
  the plan must name what is Unverifiable by construction.
- Forbidden: making a render visible to Flux anywhere but the Publication
  point; publishing an object Unverifiable by construction before its own
  dry-run passed; publishing an object that is unverifiable for any other
  reason.

## Confirmation

The **Publication point interruption tests** fail when a run interrupted
before the Publication point leaves a change Flux can read, or one interrupted
after it publishes again or ends its Operation other than the cluster shows.
The **Staged publication test** fails when a render that introduces a kind is
refused instead of staged, or an object is published before its dry-run
passed. The **Sign-precondition test** still holds for each stage. The **E2E
scenarios** gain a first install of a fixture Project, and a render that the
dry-run accepts but the Project's Flux identity may not apply, which must end
Held with Flux's message.

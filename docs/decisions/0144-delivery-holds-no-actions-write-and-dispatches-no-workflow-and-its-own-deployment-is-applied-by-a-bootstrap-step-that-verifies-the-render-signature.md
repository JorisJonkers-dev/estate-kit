---
status: accepted  # proposed | accepted | locked
date: 2026-11-05
rests-on: [2, 8, 21, 63]
amends: [2, 8]
lessons: [DR-1, TM-4]
---

# Delivery holds no `actions:write` and dispatches no workflow, and its own
Deployment is applied by a bootstrap step that verifies the render signature

## Context

The design has Delivery start a deploy nobody called for by dispatching the
Project's `deploy` workflow
([Operating the estate](../design/operating.md), "Rollouts no Project run
started"), and names GitHub as load-bearing in five places: OIDC identity,
Deployments, check runs, workflow dispatch and release-please
([record 8](0008-an-image-digest-is-sealed-into-the-fragment-and-registered-by-its-build.md)).
A dispatch is a write into the forge: it needs `actions:write` on every
Project's repository, and a token with it reaches every workflow there. The
design review of 2026-11-04 (the final report's section 15, question 11, and
chunk 07-03) found the dispatch row missing from
[record 112](0112-the-write-boundary-is-stated-once.md)'s table while
operating.md still names one; the maintainer settled the answer the same day
by shrinking the boundary instead of widening it: Delivery drops
`actions:write`.

Not chained to that answer but settled with it (section 15, question 30):
Delivery's own Deployment. Flux applies every render, but a render Delivery
publishes must never carry the Delivery that publishes it, and an apply path
for Delivery itself needs its own rollback — the alternative, a Flux-applied
Deployment under its own account, leaves a broken Delivery image to be undone
by the break-glass alone. The maintainer chose the bootstrap step with an
Environment-tag rollback.

The events the forge port shows are Delivery's projection, never its trigger:
Rollout projection writes a GitHub Deployment and the event log stays the
authority ([record 8](0008-an-image-digest-is-sealed-into-the-fragment-and-registered-by-its-build.md)),
so losing the dispatch loses no record, only a write nobody needs.

## Decision

**Delivery holds no `actions:write` on any repository and dispatches no
workflow.** The workflow-dispatch use of GitHub leaves the five the previous
record counted; Release source, the forge port that reads a merged revision
and used to dispatch a run, reads only: a Project's release deploys from its
own release-published workflow run
([Releasing a Project](../design/releasing.md)), and a rollout no Project run
started — a Platform Intent change, the nightly recompose, a Rollback whose
target dry-run fails — is composed because Delivery triggers itself: the
composition queue gains the trigger directly
([record 73](0073-the-composition-queue-is-a-row-in-a-postgres-job-table.md)),
and the fragment scan that healed missed triggers on a timer becomes the
short-interval poll that finds a fragment newer than the last composition.
Delivery writes nothing into any forge to start, resume or trigger a deploy.
After the Publication point, the Project's Flux Receiver call triggers the
fetch at once, and Flux's reconcile interval stays the fallback
([record 94](0094-flux-stays-the-one-applier-observed-closely-and-an-estate-kit-applier-waits-for-a-review-trigger.md)).
This amends [record 8](0008-an-image-digest-is-sealed-into-the-fragment-and-registered-by-its-build.md):
GitHub is load-bearing in four places, and the Release source port never
writes.

**Delivery's own Deployment is applied by a bootstrap step, not by Flux and
not by Delivery.** The bootstrap step reads the Environment tag that names
Delivery's current render, verifies the signature on every manifest it would
apply — the [render signing key](../../CONTEXT.md) signs every render
([record 21](0021-renders-and-host-tags-are-signed-by-separate-keys-with-an-offline-recovery-key.md))
— and refuses the whole render when one manifest does not verify. It applies
only Delivery's own Deployment, with the maintainer's offline admin credential,
the credential the restore order already names
([record 106](0106-the-control-plane-is-restored-in-a-dependency-order-that-is-tested-drilled-and-timed.md));
nothing automated holds it. This amends
[record 2](0002-kubernetes-is-the-substrate-and-flux-is-the-one-applier.md):
Flux stays the one applier, with one further named exception beside the host
applier's — the bootstrap step that applies Delivery's own Deployment — and
every object of a Project's or the platform's render is still applied by Flux
alone.

A bootstrap step's rollback is by Environment tag, and only the maintainer's
CLI moves it: the tag names an older, already-signed digest of Delivery's
render, the move is read, verify, write with the machine account's token —
the [Machine account](../../CONTEXT.md) credential — and only the pod or the
CLI that holds the [Writer Lease](../../CONTEXT.md) may write, so the
maintainer's CLI cannot race Delivery. Delivery never moves its own
Environment tag: a process that updates itself by its own write has no
independent rollback. The bootstrap step re-applies from the tag, so a
rollback is the same verified path as an upgrade.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Add the dispatch row to the write table with `actions:write` | A token on every Project repository that reaches every workflow there | The projection shows the deployment; the fragment poll triggers the composition |
| Keep the dispatch as a fallback behind the poll | The permission stays granted on every repository for a path with no other use | A credential no one uses is a credential no one watches |
| Flux applies Delivery's Deployment under its own account | A broken Delivery image is restored by the break-glass alone, with no rollback of its own | The bootstrap step verifies a signature and rolls back by Environment tag |
| Delivery applies its own Deployment | The applier of everything would update itself, and its own bad render would disable the rollback | The writer of a render never applies it ([record 2](0002-kubernetes-is-the-substrate-and-flux-is-the-one-applier.md)) |
| The bootstrap step trusts the render's provenance statement instead of verifying every manifest | A provenance statement is data beside the artifact, not a signature over it | Verification is the step's one job; an unverified manifest is refused |
| The bootstrap step's rollback is a git revert | [Record 9](0009-the-live-render-is-a-signed-registry-tag-per-project-and-environment.md) forbids estate pin commits, and the registry, not git, names renders | The Environment tag's older digest is already signed and kept |

## Consequences

- Easier: the write boundary's forge side shrinks by one entry; the GitHub
  App holds no permission that starts a run; Delivery's own Deployment has a
  verified apply path and a rollback its bad render cannot disable.
- Harder: the bootstrap step is a deploy step the maintainer runs and its
  fixtures belong in the end-to-end suite; a fragment that misses its Project
  event composes at poll latency, not dispatch latency.
- Forbidden: `actions:write` on Delivery's GitHub App or any token it holds;
  a workflow dispatch or repository dispatch by Delivery; an unverified
  manifest applied by the bootstrap step; any mover of Delivery's own
  Environment tag but the maintainer's CLI; a Delivery that moves its own
  Environment tag.

## Confirmation

The **Bootstrap signature fixtures** fail when the bootstrap step applies
Delivery's own Deployment from a render whose signature does not verify —
one fixture with an unsigned render, one with a manifest whose signature
fails — and each is refused. The **Rollback tag fixtures** fail when a mover
other than the maintainer's CLI moves the Environment tag of Delivery's own
render, or the CLI moves it without holding the [Writer Lease](../../CONTEXT.md)
or re-reading the tag after the move. The **Token grant check** fails when
the GitHub App's installation token holds `actions:write`, or the
machine-account token grants a package beyond the ones its record lists. The
**Write table check** holds the new writers: the bootstrap step's apply and
the maintainer's CLI's tag move outside their rows fail it.

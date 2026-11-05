---
status: accepted  # proposed | accepted | locked
date: 2026-11-05
rests-on: [75, 96, 102, 131]
amends: [75]
lessons: [TM-4]
---

# A staging Rollout that ended Refused, Held on a failed verdict or Observation lost blocks its release's production approval, and a quiet Held does not

## Context

[Record 75](0075-three-environments-run-in-the-one-cluster.md) deploys a
published release to staging, then to production after the `production`
approval, with the same digests in both. Staging rehearses the release, but
nothing gates the approval on what the rehearsal showed: a release whose
staging Rollout ended [Refused](../../CONTEXT.md), Held on a failed
[Analysis verdict](../../CONTEXT.md), or
[Observation lost](../../CONTEXT.md) could be approved into production hours
later, and the review of 2026-11-04 (the final report's section 15, question
26) asked whether a Held staging Rollout should block it. The maintainer
settled the same day: blocking depends on the end, and the quiet Project is
the exception — staging with no traffic proves nothing either way, and the
gate would stall a traffic-less staging Application for ever
([record 131](0131-a-held-rollout-on-a-quiet-project-ends-at-its-deadline-with-the-tag-unchanged.md)).

## Decision

The staging Rollout of a release gates that release's `production` approval.
A staging Rollout that ended Refused, Held on a failed
[Analysis verdict](../../CONTEXT.md), or
[Observation lost](../../CONTEXT.md) blocks the same release's `production`
approval until the maintainer confirms that the staging Application served
the release; the confirmation is recorded against the Project and the
release, and it is what lifts the block. Delivery refuses a production deploy
of a release whose staging Rollout so ended while no confirmation is recorded.

A staging Rollout that ended Held on an inconclusive verdict — its Project
too quiet to gather the plan's minimum sample
([record 131](0131-a-held-rollout-on-a-quiet-project-ends-at-its-deadline-with-the-tag-unchanged.md))
— blocks nothing, and one that ended
[Serving](../../CONTEXT.md) never blocked anything. Staging with no traffic
says nothing about the release either way, and demanding a quiet staging
Application promote before every production deploy would stall the Project,
not prove the release: the maintainer's confirmation is the gate's evidence
instead.

This amends [record 75](0075-three-environments-run-in-the-one-cluster.md),
whose promotion path stands: staging still runs the same digests first. The
gate reads the staging Rollout's end and its Held reason as recorded in its
append-only log of [Rollout events](../../CONTEXT.md), so no new state is
added.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| No gate on the staging end | A staging refusal, a failed verdict or a lost observation reaches production through the approval | Staging is the rehearsal ([record 75](0075-three-environments-run-in-the-one-cluster.md)); its verdict must gate |
| Block on every Held staging Rollout | A staging Application with no traffic never un-stalls: its verdicts are always inconclusive | A quiet staging Rollout proves nothing ([record 131](0131-a-held-rollout-on-a-quiet-project-ends-at-its-deadline-with-the-tag-unchanged.md)); the maintainer confirms instead |
| Block until a fresh staging Rollout ends Serving | A clear needs a redeploy of an unchanged release | The confirmation names what is actually known, the staging Application served |
| Gate the deploy call rather than the approval | The approval could be given and then wasted | The approval is the decision production waits on ([record 75](0075-three-environments-run-in-the-one-cluster.md)) |

## Consequences

- Easier: production approvals read what staging showed; a failed verdict or
  a lost observation cannot slide through hours later; a quiet staging
  Project releases without a human.
- Harder: the confirmation must be recorded against the Project and the
  release and shown to the approver; the staging Rollout's Hold reason must
  travel with its end.
- Forbidden: a production deploy that proceeds while its release's staging
  Rollout blocks its approval; lifting the block without the maintainer's
  recorded confirmation; blocking on a quiet Project's Held end.

## Confirmation

The **Staging gate test** fails when a production deploy of a release
proceeds while the staging Rollout of the same release ended
[Refused](../../CONTEXT.md), Held on a failed
[Analysis verdict](../../CONTEXT.md), or
[Observation lost](../../CONTEXT.md) and the maintainer's confirmation is not
recorded, when a staging Rollout Held on an inconclusive verdict blocks a
release, or when a recorded confirmation does not lift the block. The gate
fails closed, and its negative fixture fires when a blocked release is
approved.

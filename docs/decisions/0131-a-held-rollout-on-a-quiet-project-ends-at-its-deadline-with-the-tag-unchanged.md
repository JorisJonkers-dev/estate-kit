---
status: accepted  # proposed | accepted | locked
date: 2026-11-05
rests-on: [93, 96, 102]
amends: [93]
lessons: [CS-3]
---

# A Held Rollout on a quiet Project ends at its deadline, with the tag unchanged

## Context

[Record 93](0093-the-rollout-plan-is-compiled-with-checks-bound-to-cohorts-a-failsafe-and-a-held-deadline.md)
compiles a Held deadline into every rollout plan, and says a Held Rollout
stays Held after its deadline, with the alert the only thing the deadline
does. The Release Gate holds on an [Analysis verdict](../../CONTEXT.md), and
[record 102](0102-analysis-is-a-pure-verdict-function-and-an-inconclusive-verdict-holds.md)
holds the Rollout on an inconclusive one. On a Project too quiet to gather
the plan's minimum sample the verdict stays inconclusive for ever, so the
Rollout would wait for a sample nothing will produce. The design review of
2026-11-04 asked what ends such a Rollout (the final report's section 15,
question 13), and the maintainer settled the same day: the deadline does.
[Record 96](0096-a-deploy-is-an-operation-that-ends-serving-held-refused-superseded-or-observation-lost.md)
ends the Operation Held, with a reason and a deadline; nothing says when the
Rollout closes.

Every wait needs a deadline, and the estate states what happens rather than
defaulting to waiting for ever: CS-3. [Held](../../CONTEXT.md) in the
vocabulary already carries the settled mechanics.

## Decision

A Held Rollout records why it is Held: a failed [Analysis verdict](../../CONTEXT.md),
or an inconclusive one on a Project too quiet to gather the plan's minimum
sample. On a failed verdict the plan's failsafe has run, and the Rollout ends
Held at once. On an inconclusive one it stays Held and waits, through its
deadline: 24 hours unless the Project states another, as
[record 93](0093-the-rollout-plan-is-compiled-with-checks-bound-to-cohorts-a-failsafe-and-a-held-deadline.md)'s
compiled plan states.

At the deadline the Rollout ends Held, its inconclusive verdict recorded, and
the [Environment tag](../../CONTEXT.md) keeps naming the held render: nothing
is promoted or rolled back by itself, the maintainer is alerted, and an
[Operator](../../CONTEXT.md) promotes or rolls back explicitly. A later
render starts a new Rollout and cancels the deadline. Time still never
promotes: the deadline ends the Rollout, and the Operator's promote is the
only one.

This amends [record 93](0093-the-rollout-plan-is-compiled-with-checks-bound-to-cohorts-a-failsafe-and-a-held-deadline.md):
the Held deadline ends the Rollout instead of only alerting. The alert
stands, the plan's other rules stand, and
[record 96](0096-a-deploy-is-an-operation-that-ends-serving-held-refused-superseded-or-observation-lost.md)'s
exit 10 covers the end: `estate-kit watch` on a quiet Project ends there.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| [Record 93](0093-the-rollout-plan-is-compiled-with-checks-bound-to-cohorts-a-failsafe-and-a-held-deadline.md) as written: the deadline only alerts | A quiet Project's Rollout sits Held for ever; its watch streams never end | The maintainer settled that the deadline ends it |
| Promote at the deadline | An unverified version takes traffic because nobody answered | Time never promotes |
| Roll back at the deadline | A version that may be healthy is withdrawn by a timer | The old version already serves; an [Operator](../../CONTEXT.md) decides |
| End it Observation lost | Delivery did observe the Rollout; it just had no sample | [Observation lost](../../CONTEXT.md) names what is not known; Held names what happened |
| Cancel the Held Rollout when a later render starts composing | The held render stays published and named by the tag, with nothing recording what it held for | The deadline is what ends the Rollout; the later render starts a new one |

## Consequences

- Easier: every Rollout ends exactly once
  ([record 130](0130-a-rollout-ends-serving-held-refused-replaced-or-observation-lost-and-superseded-is-an-operation-end-only.md));
  a quiet Project's deploy job ends with exit 10 at its 24-hour deadline; the
  staging gate
  ([record 132](0132-a-staging-rollout-that-ended-refused-held-on-a-failed-verdict-or-observation-lost-blocks-its-release-s-production-approval-and-a-quiet-held-does-not.md))
  can tell a failed verdict's Hold from a quiet Project's.
- Harder: the Release Gate and Delivery need a timer that ends Held Rollouts
  and cancels with the next render; the reason a Rollout was Held must be
  recorded with its end.
- Forbidden: promoting or rolling back by the timer; ending a quiet Held
  Rollout in any other way; reading a Held Rollout's reason from anything but
  its record.

## Confirmation

The **Held deadline test** fails when a Rollout Held past its deadline raises
no alert, is promoted or rolled back by the timer, does not end Held at its
deadline with the [Environment tag](../../CONTEXT.md) still naming the held
render, or when a later render does not start a new Rollout and cancel the
pending deadline.

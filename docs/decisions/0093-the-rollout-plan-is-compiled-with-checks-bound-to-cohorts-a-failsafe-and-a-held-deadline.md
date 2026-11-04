---
status: accepted  # proposed | accepted | locked
date: 2026-11-04
rests-on: [3, 5, 14, 74]
amends: [3, 14, 74]
lessons: [CS-1, TM-4]
---

# The rollout plan is compiled, with checks bound to cohorts, a failsafe and a Held deadline

## Context

Flagger runs each switchover and asks the Release Gate before every traffic
step; the gate holds every member of a Release Unit behind one barrier and
fails closed ([record 74](0074-the-release-gate-and-observation-each-have-a-named-write.md)).
The compiler derives the rollout strategy from what the author states, such as
whether an upgrade may interrupt service
([record 5](0005-derivation-is-total.md)), and every decision lives in the
Resolved Deployment so renderers only serialise
([record 3](0003-three-models-intent-resolved-deployment-deliverable-set.md); CS-1).

The architecture evaluation of 2026-11-04 (section 3.8) rated progressive
delivery adequate and named three gaps: analysis has one window and no
inconclusive outcome; the strategy is not a compiled artifact with a declared
failsafe; and checks are not bound to cohorts. The sources behind it:

- "Canary Analysis Service" (2018) keeps analysis apart from action and
  returns PASS, FAIL or NONE when it cannot reach a verdict.
- "Gandalf" (2020) analyses on a fast path and a slower one.
- "Flagger: Webhooks" (2026): a timeout or a non-2xx answer halts the advance.
- "Bifrost" (2016) writes a release strategy as a formal model that can be
  checked before it runs; "ActivFORMS" (2023) declares a failsafe mode
  before adaptation.
- "Making Deployments Safe at Meta" (2026) binds each check's query to the
  cohort under test and a control cohort at evaluation time; a programme that
  measured each check's false-positive rate and flagged checks with no control
  cohort cut the fleet's false positives from 12.1% to 2.7% in a year.

None of them prescribes a number of windows for an Application with little
traffic. A gate with no negative fixture cannot be shown to fire (TM-4).

## Decision

The compiler compiles a rollout plan for each Application into the Resolved
Deployment, in a new step crate, `step-plan`, which extends the chain of
[record 14](0014-the-compiler-is-a-chain-of-typed-models-one-crate-per-step.md).
The plan names:

- the strategy, derived from the Application's cutover and its Release Unit;
- each check, bound to cohorts from the model (the new version's slice, a
  control slice and the Rollout's Operation id), with its own sampling and
  horizon;
- the failsafe, declared before the rollout starts: on a fail verdict or an
  exception check such as a crash loop, traffic goes back, the old version keeps
  serving and the reason is recorded;
- the Held deadline: how long the Rollout may stay Held before the maintainer
  is alerted. A Held Rollout stays Held after its deadline; time never promotes,
  and the alert is the only thing the deadline does.

Checks come from templates in the Profiles, the Component kinds and Platform
Intent's defaults, so an Application that declares nothing is still gated.
The default plan binds two checks: the HTTP success rate and the p95 latency
of the new version's slice, each against a control cohort, each needing at
least 100 requests per check and evaluated over a 10-minute horizon. Its Held
deadline is 24 hours. Project Intent may add checks of its own; it may not
remove a default one.
`step-plan` refuses a plan with no failsafe or no Held deadline, a check with
no cohort, sampling or horizon, or a hook timeout that ends before a check's
horizon. Flagger's Canary is rendered from the plan, and the Release Gate
answers from the plan, the Analysis verdicts and cluster state. Too little
traffic or missing telemetry gives an inconclusive Analysis verdict, which
holds. Each verdict is kept with the Rollout's outcome, so a check's precision
can be measured later. This extends records
[3](0003-three-models-intent-resolved-deployment-deliverable-set.md) and
[74](0074-the-release-gate-and-observation-each-have-a-named-write.md).

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Flagger's analysis as written today: one window, pass or fail | Low traffic passes as healthy; no failsafe is declared | The three gaps the evaluation found stay |
| Two fixed windows, fast and slow, for every check | A horizon chosen for no check in particular | No source prescribes two windows for low traffic; each check declares its own |
| Checks without a control cohort | A fleet-wide change looks like a regression, or hides one | Meta's flagged checks without a control cohort as low quality |
| The failsafe chosen at failure time | The action is decided under pressure, by whoever is there | ActivFORMS and Bifrost declare it before the run |
| Promote a Held Rollout when its deadline passes | An unverified version takes traffic because nobody answered | Time is not evidence |
| Roll back a Held Rollout when its deadline passes | A version that may be healthy is withdrawn on a timer | The old version already serves; the deadline only alerts |
| Let a Project remove a default check | A Project can turn its own gate off | Projects add checks; the defaults stay |
| A strategy authored per Application | Every Application restates the platform's rollout knowledge | [Record 5](0005-derivation-is-total.md): the compiler derives mechanism |

## Consequences

- Easier: a reviewer reads the plan in the Resolved Deployment's diff before
  anything runs; an Application with no checks of its own is still gated; a
  noisy check can be found from its kept verdicts.
- Harder: a new step crate and a larger Resolved Deployment; every check
  template needs a cohort, sampling and horizon; an Application with fewer
  than 100 requests in 10 minutes will often sit Held and alert after 24
  hours.
- Forbidden: a plan without a failsafe or a Held deadline; a check without a
  cohort, sampling or horizon; promotion on an inconclusive verdict or by time;
  a Project that removes a default check.

## Confirmation

The **Rollout plan refusal fixtures** fail when `step-plan` accepts a plan
without a failsafe or a Held deadline, a check without a cohort, sampling or
horizon, or a hook timeout shorter than a check's horizon, with one negative
fixture per refusal. The **Default check binding test** fails when an
Application that declares no check gets a plan without the two default checks,
their control cohort, their 100-request minimum, their 10-minute horizon or the
24-hour Held deadline, or when a Project Intent that removes a default check is
accepted. The **Held deadline test** fails when a Rollout Held past its
deadline raises no alert, or is promoted or rolled back. A scenario of the
**E2E scenarios** fails a check and asserts that the declared failsafe ran and
the old version kept serving
([record 69](0069-the-deploy-path-is-tested-end-to-end.md)).

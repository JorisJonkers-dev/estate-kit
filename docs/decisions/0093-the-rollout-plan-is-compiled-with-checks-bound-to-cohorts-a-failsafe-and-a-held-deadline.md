---
status: proposed  # proposed | accepted | locked
date: 2026-11-04
rests-on: [3, 5, 14, 74]
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
  is paged. A Held Rollout stays Held after its deadline; time never promotes.

Checks come from templates in the Profiles, the Component kinds and Platform
Intent's defaults, so an Application that declares nothing is still gated.
`step-plan` refuses a plan with no failsafe or no Held deadline, a check with
no cohort, sampling or horizon, or a hook timeout that ends before a check's
horizon. Flagger's Canary is rendered from the plan, and the Release Gate
answers from the plan, the Analysis verdicts and cluster state. Too little
traffic or missing telemetry gives an inconclusive Analysis verdict, which
holds. Each verdict is kept with the Rollout's outcome, so a check's precision
can be measured later. This extends records
[3](0003-three-models-intent-resolved-deployment-deliverable-set.md) and
[74](0074-the-release-gate-and-observation-each-have-a-named-write.md).
The default checks, their sampling and horizons, the default Held deadline, and
whether Project Intent may add a check of its own stay open for the maintainer.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Flagger's analysis as written today: one window, pass or fail | Low traffic passes as healthy; no failsafe is declared | The three gaps the evaluation found stay |
| Two fixed windows, fast and slow, for every check | A horizon chosen for no check in particular | No source prescribes two windows for low traffic; each check declares its own |
| Checks without a control cohort | A fleet-wide change looks like a regression, or hides one | Meta's flagged checks without a control cohort as low quality |
| The failsafe chosen at failure time | The action is decided under pressure, by whoever is there | ActivFORMS and Bifrost declare it before the run |
| Promote a Held Rollout when its deadline passes | An unverified version takes traffic because nobody answered | Time is not evidence |
| A strategy authored per Application | Every Application restates the platform's rollout knowledge | [Record 5](0005-derivation-is-total.md): the compiler derives mechanism |

## Consequences

- Easier: a reviewer reads the plan in the Resolved Deployment's diff before
  anything runs; an Application with no checks of its own is still gated; a
  noisy check can be found from its kept verdicts.
- Harder: a new step crate and a larger Resolved Deployment; every check
  template needs a cohort, sampling and horizon; an Application with little
  traffic will often sit Held and page.
- Forbidden: a plan without a failsafe or a Held deadline; a check without a
  cohort, sampling or horizon; promotion on an inconclusive verdict or by time.

## Confirmation

The **Rollout plan refusal fixtures** fail when `step-plan` accepts a plan
without a failsafe or a Held deadline, a check without a cohort, sampling or
horizon, or a hook timeout shorter than a check's horizon, with one negative
fixture per refusal. The **Default check binding test** fails when an
Application that declares no check gets a plan with none bound. The **Held
deadline test** fails when a Rollout Held past its deadline does not page, or
is promoted. A scenario of the **E2E scenarios** fails a
check and asserts that the declared failsafe ran and the old version kept
serving ([record 69](0069-the-deploy-path-is-tested-end-to-end.md)).

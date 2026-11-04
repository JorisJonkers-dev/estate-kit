---
status: accepted  # proposed | accepted | locked
date: 2026-11-04
rests-on: [74, 93, 96]
lessons: [TM-4]
---

# Analysis is a pure verdict function, and an inconclusive verdict holds

## Context

Flagger runs each canary and asks the Release Gate at its hooks; the gate
answers from cluster state and fails closed
([record 74](0074-the-release-gate-and-observation-each-have-a-named-write.md)).
The design has one analysis window and two outcomes, so a check with too little
traffic or no telemetry must still say pass or fail (the architecture
evaluation of 2026-11-04, sections 3.8 and 9.5). An Application with little
traffic meets that case on most releases.

Practice is ahead in three ways. "Canary Analysis Service" (2018) keeps
analysis apart from action, never changes production itself, and returns PASS,
FAIL or NONE, the last when it could not reach a verdict. "Gandalf" (2020)
analyses on a fast horizon for prompt decisions and a slower one for latent
faults. "Making Deployments Safe at Meta" (2026) cut its fleet-wide false
positive rate from 12.1% to 2.7% in a year by measuring and improving each
check, which needs every verdict and its outcome kept. Flagger's hooks differ
in what an error means ("Flagger: Webhooks", 2026): a confirm hook pauses until
it gets a success; a failed rollout or pre-rollout hook counts toward rolling
the canary back; a rollback hook that answers success fails the canary at once.

## Decision

Analysis is a pure function in its own domain crate, `analysis`: from one
check's declaration and the samples for its window, it returns an Analysis
verdict, pass, fail or inconclusive, with a reason. It reads no clock and does
no I/O; `adapter-metrics` fetches the samples read-only from Prometheus, and
the window is an input. Each check declares its own sampling, cohort, horizons
and minimum sample in the compiled rollout plan; a check may have a fast and a
slow horizon. Too little traffic and missing telemetry are inconclusive, never
pass and never fail.

The Release Gate turns verdicts into Flagger's answers. Every check passing
lets it answer yes. A fail sets off the plan's declared failsafe; by default
the gate answers yes on the rollback hook, so Flagger reverts traffic, the old
version keeps serving, and the Operation ends Held with the check's reason
([record 96](0096-a-deploy-is-an-operation-that-ends-serving-held-refused-superseded-or-observation-lost.md)).
An inconclusive verdict holds: the gate answers no on the confirm hooks, which
pause the canary, and never gives it as an error on a hook that counts toward a
rollback. Inconclusive never promotes, and a Rollout held past the plan's
deadline pages the maintainer and stays held; time never promotes it. Each
verdict is a Rollout event with its check, horizon, sample size and reason, so
each check's precision can be computed later. This extends
[record 74](0074-the-release-gate-and-observation-each-have-a-named-write.md):
the gate's answer stays a read, and adds no write. The minimum sample and the
horizons of each check are set per check in the plan; no estate-wide value is
decided here.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Flagger's own metric thresholds decide alone | No inconclusive outcome; a quiet Application passes or fails by chance | Analysis must say when it cannot decide |
| Inconclusive counts as fail | Healthy releases of quiet Applications roll back | A missing signal is not a bad one |
| Inconclusive promotes after a timeout | A release no check has judged takes the traffic | Promotion by time is what the failsafe forbids |
| A score or confidence instead of a verdict | The gate needs its own rule to turn it into an action | One clear verdict per check |
| Analysis in Observation | A promotion decision across a process boundary, from the read side | The gate's answer is Delivery's |
| One window for every check | Fast faults are caught late, or latent ones never | Each check declares its horizons |
| Analysis code that fetches its own metrics | A verdict that cannot be replayed or tested without Prometheus | Pure function, samples as input |

## Consequences

- Easier: a verdict is replayed from its inputs in a test; a quiet release
  waits instead of guessing; each check's precision can be measured.
- Harder: every check declares its sampling, cohort, horizons and minimum
  sample; a Held Rollout waits for the maintainer.
- Forbidden: promotion on an inconclusive verdict or by time alone; analysis
  that reads a clock or fetches its own data; an inconclusive verdict given to
  Flagger as a failure that counts toward a rollback.

## Confirmation

The **Analysis verdict tests** fail when the function returns pass or fail on
too little traffic or missing telemetry, or any verdict other than its
fixture's. The **Inconclusive hold test** fails when the gate answers yes on an
inconclusive verdict, answers it on a hook that counts toward a rollback, or a
Held Rollout is promoted by time. **`cargo xtask check-layers`** refuses an
edge from `analysis` to an adapter crate.

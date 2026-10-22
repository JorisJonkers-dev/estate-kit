# Operating the estate

Operators act through the UI. Every rollout they start still shows up as a
deploy run and a Deployment in the Project's own repository.

## Rollouts no Project run started

A Platform Intent change, the nightly recompose or a Rollback from the UI: the
service dispatches the Project's `deploy` workflow in watch mode, with a run
name that says why (for example "Deploy notes: Platform Intent changed").
Missed triggers heal on a timer that scans the registry for fragments newer
than the last composition.

## UC-5 Pause or resume a Project

An Operator pauses a Project in the UI. The service records it in the Project's
cluster object and stops moving its tag until the Operator resumes. Outcome:
Flux keeps serving the current render.

![UC-5 Pause or resume a Project](../diagrams/png/uc5-pause.png)

## UC-6 Roll back a Project

An Operator rolls a Project back to an earlier release. The service re-composes
at that fragment and dispatches the deploy run in watch mode. Outcome: a deploy
run and a Deployment, like any release.

![UC-6 Roll back a Project](../diagrams/png/uc6-rollback.png)

![Sequence: roll back a Project](../diagrams/png/seq-rollback.png)

## UC-7 Admit a Project

An Admin merges a Platform Intent change that admits a Project's
`repository_id`. The service derives the Project's Flux source into the
platform render. Outcome: the Project's CI may deploy from then on.

![UC-7 Admit a Project](../diagrams/png/uc7-admit.png)

## UC-8 Pull and apply a render

Flux sees `render/<p>:prod` point at a new digest, verifies the signature, then
applies and prunes. Outcome: the cluster holds the new render; the traffic
switch is UC-9.

![UC-8 Pull and apply a render](../diagrams/png/uc8-apply.png)

## UC-9 Gate a traffic switch

Flagger asks the Release Gate whether to promote. The service answers yes only
when every member of the Release Unit is healthy. Outcome: traffic switches
together, or the release is Held.

![UC-9 Gate a traffic switch](../diagrams/png/uc9-gate.png)

## States of a Project

A Project's state decides whether the service may move its tag.

![States of a Project](../diagrams/png/state-project.png)

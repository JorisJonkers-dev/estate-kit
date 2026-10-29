---
status: accepted  # proposed | accepted | locked
date: 2026-10-29
rests-on: [25, 68]
lessons: [DO-4, TM-6, MD-5]
---

# The deploy path is tested end to end on a throwaway k3s cluster, nightly and before every release

## Context

Unit, property and fixture tests prove each crate, and every adapter passes its
port's contract suite against the real system in a container
([record 68](0068-every-fake-passes-its-port-s-contract-suite.md)). None of
them proves that the parts work together: that Flux pulls the tag the service
moved, that Flagger asks the Release Gate, that a rollback works with Vault
down (it reads no secret from Vault: the token is a Kubernetes Secret), or that a restarted service resumes from observed state, and that a waiting deploy job keeps authenticating across an upgrade. Those are the
behaviours the design review's scenarios rank highest, and a Ready condition
alone has proved nothing before (DO-4).

## Decision

A suite in `e2e/` runs the deploy path the way production does, with nothing
faked except GitHub:

- a k3s cluster in CI with Flux, Flagger and the ValidatingAdmissionPolicies;
- zot standing in for ghcr, requiring the machine account's token as ghcr
  does (no unauthenticated registry), so a Rollback that secretly needs Vault
  for it fails here; Vault in dev mode with the render and host Transit
  keys, Postgres, and the service image built from the change;
- a fixture Project whose `deploy` job the test runner replays with a minted
  OIDC token.

Its scenarios are the use cases: validate and plan; dry-run; deploy to
Serving; a refused deploy; Pause and Resume; Rollback with Vault sealed or scaled to
zero ([record 28](0028-pause-and-rollback-are-a-cluster-object-per-project.md)); a service restart mid-rollout; a service upgraded mid-rollout (the deploy job re-requests a GitHub OIDC token and resumes its stream by sequence); an unchanged render that publishes
nothing. Each asserts a value a consumer reads (the tag, the object in the
cluster, the Deployment status), never only a condition. The suite runs
nightly and is required before a release, within 15 minutes. The scenarios are
listed on [Testing and speed](../design/code-shape-and-speed.md#end-to-end).

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Fakes and contract suites only | Integration across Flux, Flagger and Vault is never exercised | The failures the review feared live between the parts |
| Run on every pull request | 15 minutes on every change | Over the 2-minute and 5-minute pull-request budgets |
| Test against the production cluster | Tests can change what runs | The shadow is the only production-adjacent test, and it is inert ([record 67](0067-the-compiler-is-written-to-the-1-0-contract.md)) |

## Consequences

- Easier: a release ships only after its deploy, rollback and restart paths
  have run against real Flux, Flagger and Vault.
- Harder: the suite's cluster setup is code to keep current with the
  production versions of k3s, Flux and Flagger.
- Forbidden: a release whose e2e run failed or did not run.

## Confirmation

The release workflow requires the e2e job's success on the release commit, and
the suite's own test fails if a use case in the scenario list has no scenario.

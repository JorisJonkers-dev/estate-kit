---
status: accepted  # proposed | accepted | locked
date: 2026-10-30
rests-on: [1, 2]
lessons: [DO-1]
---

# A Project's state lives with the Project

## Context

Estate held a central list of what is deployed: pin commits per Project, an
images lock, a participants file and a cluster-state file, all written by
workflows. One shared unit that every Project depended on stalled all of them
when it failed, and a consumer adding an edge once moved its provider's pin.

## Decision

Code is central; state is per Project. estate-kit holds the compiler, the
service and the toolchain configuration once. What a Project has released lives
with that Project: its repository, its signed render tag, its own namespace and
its own Deployments. What runs is recorded by the cluster itself, read live.

No repository holds a list of what is deployed, and no lock or pin sits outside
a Project. Projects refer to each other by name only, and a change to one Project
re-renders and redeploys only that Project. Estate-wide policy is the exception
that proves the rule: Platform Intent lives in the thin estate repo, which is
itself a Project. Where each fact lives is on
[Where state lives](../design/where-state-lives.md).

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Code and state both central | A central deploy list and a lock outside any Project | One failure stalls every Project |
| Code split per Project as well | The toolchain is copied and drifts | Code is the same for every Project |
| Estate pin commits | A central list written by a workflow | A second writer of what Flux applies ([record 2](0002-kubernetes-is-the-substrate-and-flux-is-the-one-applier.md)) |

## Consequences

- Easier: a Project deploys, pauses and rolls back alone; no shared unit to stall.
- Harder: there is no single file to read for the estate's state, so the service
  and the dashboard read it from the cluster and the registry.
- Forbidden: a committed list of deployed versions or digests; a lock file
  outside a Project; a Project's render depending on another Project's pin.

## Confirmation

The Hygiene job fails on a file in this repository or the estate repo that
names a deployed digest or pin. A two-Project end-to-end test changes one
Project and asserts that nothing the other owns is re-rendered or applied
([record 17](0017-the-service-runs-in-the-cluster-in-rust.md)).

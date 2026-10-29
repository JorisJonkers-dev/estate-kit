---
status: accepted  # proposed | accepted | locked
date: 2026-10-29
rests-on: [13, 17, 18, 65]
lessons: [DO-1, CS-2]
---

# Five bounded contexts, each boundary its own record: compiler, service, observation, hosts, components

## Context

The design named four contexts: compiler, service, host applier and
components. The inventory of 2026-10-29 found the dashboard's read views
(units, pods, containers, alerts and silences, logs, health, checks) with no
context; the earlier plan would have put them in the service, beside the
rollout core. estate-dashboard today holds no credential that can deploy,
pause or roll back, and its value is that it stays read-only.

## Decision

Five bounded contexts, each a set of crates in the layers of
[record 65](0065-the-workspace-is-layered-and-the-crate-graph-is-checked.md):

| Context | Owns | Talks to others through |
| --- | --- | --- |
| Compiler | The model | Its application crate's use cases |
| Service | Rollouts, compositions, admission, Pause and Rollback, the Release Gate | The compiler's use cases, in-process |
| Observation | What runs and how it is doing, read only | Rollout events, read through a query port |
| Hosts | Generations and their rollout across nodes | Signed host tags only |
| Components | Migrations, secret grants, catalogs, backups, Mailboxes | Rendered objects only |

A Project is the aggregate root in the compiler and a Rollout in the service;
other aggregates refer to them by id. Each boundary is a crate boundary, and
the context map on [The Rust workspace](../design/rust-workspace.md#bounded-contexts)
is the normative list of edges.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Four contexts, the read views inside the service | Prometheus, Loki and Alertmanager clients beside the rollout core; read code near credentials that write | The read side holds no write credential |
| One context | Nothing stops the host applier importing model types | The applier must work when the cluster and the compiler are not there |

## Consequences

- Easier: the read views can fail or change without touching a rollout.
- Harder: Observation reads rollout history through a port rather than the
  event store directly.
- Forbidden: a crate in one context depending on another context's crates
  except along the context map.

## Confirmation

`cargo xtask check-layers` reads each crate's context from its manifest and
fails on an edge the context map does not list, with a failing fixture.

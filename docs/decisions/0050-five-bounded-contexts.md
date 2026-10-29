---
status: accepted  # proposed | accepted | locked
date: 2026-10-29
rests-on: [13, 17, 18]
lessons: [DO-1, CS-2, MS-1, TM-4, PR-4]
---

# The workspace is five bounded contexts in five layers, and a check holds the crate graph to both

## Context

The design named four contexts: compiler, service, host applier and
components. The inventory of 2026-10-29 found the dashboard's read views
(units, pods, containers, alerts and silences, logs, health, checks) with no
context; the earlier plan would have put them in the service, beside the
rollout core. estate-dashboard today holds no credential that can deploy,
pause or roll back, and its value is that it stays read-only apart from one
named write, Alertmanager silences ([record 74](0074-the-release-gate-and-observation-each-have-a-named-write.md)).
A boundary that is only a crate boundary does not keep that value: if
Observation shared a process with the service, the service's Vault, ghcr and
signing credentials would sit in the same address space as the read code.

deploy-kit held its layers with dependency-cruiser, and estate services in
Kotlin hold theirs with ArchUnit. Two lessons came with them. A rule that
matches nothing passes silently: blueshell's "controllers do not call
services" matched package names, not class names, and never fired. And an
architecture document drifts from the code unless a check reads both (CS-2).

In Rust a crate is the unit of compilation, of visibility and of a mutant's
rebuild. A dependency that is not in a crate's manifest cannot be used, and a
cycle between crates cannot compile. Cargo's graph is therefore the cheapest
architecture test there is, provided the rules about which edges are allowed
are written down in one place and checked.

## Decision

The workspace is split into five bounded contexts, a shared foundation, and
five layers. Every crate belongs to one context (or the foundation) and one
layer.

| Context | Owns | Talks to others through |
| --- | --- | --- |
| Compiler | The model | Its application crate's use cases |
| Service | Rollouts, compositions, admission, Pause and Rollback, the Release Gate | The compiler's use cases, in-process |
| Observation | What runs and how it is doing; read only except Alertmanager silences ([record 74](0074-the-release-gate-and-observation-each-have-a-named-write.md)) | Rollout events, read from the Service's API |
| Hosts | Generations and their rollout across nodes | Signed host tags only |
| Components | Migrations, secret grants, catalogs, backups, Mailboxes | Rendered objects only |

| Layer | May depend on | Holds |
| --- | --- | --- |
| foundation | other foundation crates | Diagnostics, model paths, digests, canonical output, the transformation kit, the test kit. No domain words |
| domain | foundation; its own context's domain crates | Types, invariants, pure transformations, deciders. No I/O, no async runtime, no clock |
| application | domain; foundation | Use cases and the port traits they drive. No concrete adapter |
| adapter | application (for the ports); foundation; external crates | One outside system each, behind one port |
| binary | anything | The composition root: configuration, wiring, `main` |

A Project is the aggregate root in the compiler and a Rollout in the service;
other aggregates refer to them by id. A context may use another context's
crates only through its application crate's public API, and only along the
edges listed in `crates/layers.toml`, which is written with the workspace.
That file holds the layer table and the allowed context edges; it is the one
normative source, and no design page repeats the edges as a rule. Each crate's
manifest names its context and layer in `[package.metadata.estate-kit]`.

Observation ships as its own binary and its own Deployment, with its own
read-only adapters: its own kube adapter, and adapters for Prometheus, Loki,
Alertmanager and Gatus. It does not link the service's adapters. It holds no
Vault, ghcr or signing credential and none that can deploy, pause or roll
back. Its one write, creating and expiring Silences, uses the narrow
credential that [record 74](0074-the-release-gate-and-observation-each-have-a-named-write.md)
names. The boundary therefore holds at the process level as well as the crate
level.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Four contexts, the read views inside the service | Prometheus, Loki and Alertmanager clients beside the rollout core; read code near credentials that write | The read side holds no credential that can deploy; its one write is silences, under its own narrow credential |
| Observation a context but in the service's binary | The service's Vault, ghcr and signing credentials share a process with the read adapters; one Deployment, one set of mounted secrets | A crate boundary does not stop a credential being read in the same process |
| One context | Nothing stops the host applier importing model types | The applier must work when the cluster and the compiler are not there |
| One crate per binary, modules for layers | Visibility only by `pub(crate)`; every change rebuilds the binary's whole crate; mutants rebuild everything | The compile and mutation cost the maintainer named |
| One crate per context | Layers inside a context unchecked; a change to an adapter rebuilds the domain's tests | Domain tests must not compile kube or sqlx |
| cargo-deny bans alone | Bans whole crates, not edges between our own crates | Cannot express the layer table or the context edges |

## Consequences

- Easier: the read views can fail, change or be redeployed without touching a
  rollout. A domain crate compiles and tests in seconds because it has no
  heavy dependencies; parallel work splits along crates with one owner each.
- Harder: Observation reads rollout history from the Service's API rather than
  the event store, so it needs a client for that API and the service must be
  up for those panels. A second binary and image. More manifests; workspace
  inheritance (`[workspace.dependencies]`, `[workspace.lints]`,
  `version.workspace = true`) keeps each one short.
- Forbidden: a crate in one context depending on another context's crates
  except along `crates/layers.toml`; a crate without a context and layer; a
  domain crate depending on `tokio`, `kube`, `sqlx`, `reqwest` or `axum`;
  Observation's binary depending on a Vault, ghcr or signing adapter.

## Confirmation

`cargo xtask check-layers` reads `cargo metadata` and `crates/layers.toml` and
fails on any edge the file does not allow, including an edge between contexts
and any dependency of Observation's binary on a Vault, ghcr or signing adapter.
It runs in the Lint job. Its test suite holds one failing fixture workspace per
rule, so a rule that can no longer fire fails its own test.

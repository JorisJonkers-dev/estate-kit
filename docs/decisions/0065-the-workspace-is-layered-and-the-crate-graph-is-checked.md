---
status: accepted  # proposed | accepted | locked
date: 2026-10-29
rests-on: [13, 50]
lessons: [CS-2, MS-1, TM-4, PR-4]
---

# The workspace is layered by crate, and a check holds the crate graph to the layer table

## Context

deploy-kit held its layers with dependency-cruiser, and estate services in
Kotlin hold theirs with ArchUnit. Two lessons came with them. A rule that
matches nothing passes silently: blueshell's "controllers do not call
services" matched package names, not class names, and never fired. And an
architecture document drifts from the code unless a check reads both (CS-2).

In Rust a crate is the unit of compilation, of visibility and of a mutant's
rebuild. A dependency that is not in a crate's manifest cannot be used, and a
cycle between crates cannot compile. Cargo's graph is therefore the cheapest
architecture test there is, provided the rules about which edges are allowed
are written down and checked.

## Decision

Every crate belongs to one bounded context (compiler, service, hosts,
components, or the shared foundation) and one layer:

| Layer | May depend on | Holds |
| --- | --- | --- |
| foundation | other foundation crates | Diagnostics, model paths, digests, canonical output, the transformation kit, the test kit. No domain words |
| domain | foundation; its own context's domain crates | Types, invariants, pure transformations, deciders. No I/O, no async runtime, no clock |
| application | domain; foundation | Use cases and the port traits they drive. No concrete adapter |
| adapter | application (for the ports); foundation; external crates | One outside system each, behind one port |
| binary | anything | The composition root: configuration, wiring, `main` |

A context may use another context's crates only through its application
crate's public API, and only along the context map (compiler to service).
The table lives in `crates/layers.toml`. Each crate's manifest names its
context and layer in `[package.metadata.estate-kit]`.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| One crate per binary, modules for layers | Visibility only by `pub(crate)`; every change rebuilds the binary's whole crate; mutants rebuild everything | The compile and mutation cost the maintainer named |
| One crate per context | Layers inside a context unchecked; a change to an adapter rebuilds the domain's tests | Domain tests must not compile kube or sqlx |
| cargo-deny bans alone | Bans whole crates, not edges between our own crates | Cannot express the layer table |

## Consequences

- Easier: a domain crate compiles and tests in seconds because it has no
  heavy dependencies; parallel work splits along crates with one owner each.
- Harder: more manifests. Workspace inheritance (`[workspace.dependencies]`,
  `[workspace.lints]`, `version.workspace = true`) keeps each one short.
- Forbidden: an edge the table does not allow; a crate without a context and
  layer; a domain crate depending on `tokio`, `kube`, `sqlx`, `reqwest` or
  `axum`.

## Confirmation

`cargo xtask check-layers` reads `cargo metadata` and `crates/layers.toml` and
fails on any edge the table does not allow. It runs in the Lint job. Its test
suite holds one failing fixture workspace per rule, so a rule that can no
longer fire fails its own test.

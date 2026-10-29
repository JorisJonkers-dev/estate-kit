---
status: accepted  # proposed | accepted | locked
date: 2026-10-29
rests-on: [1, 3, 5, 6]
lessons: [MD-4, CS-2, CS-3, TM-5, PR-2]
---

# Every program in estate-kit is Rust, in one Cargo workspace; only the UI is Vue

## Context

The design of 2026-10-22 kept three backend languages: the TypeScript compiler
until model 1.0, a Go service, Go components and host applier, and a Rust port
only if a later record justified it ([review](../research/review/README.md) D1).
The review's case against Rust was about order and cost, not fit: a parity port
chased a compiler that changed daily, much of what it ported is deleted by
deploy-kit#373, and byte parity needed a bespoke YAML 1.1 emitter
([model-compiler-1, -2, -5](../research/review/model-and-compiler.md)). It also
counted four toolchains for one part-time maintainer
([process-8](../research/review/process-and-plan.md)).

Three facts have changed since. The maintainer has decided not to carry the
TypeScript compiler into estate-kit at all, so there is no parity target to
chase; the Rust compiler is written to the 1.0 contract
([record 67](0067-the-compiler-is-written-to-the-1-0-contract.md)). With the
compiler in Rust, a Go service and Go components would make two backend
toolchains where one suffices. And the estate already has a Rust library,
[rust-commons](https://github.com/JorisJonkers-dev/rust-commons), that reads
identity's Principal contract as tower layers for axum.

What still holds from the review: serde stops at the first error and accepts
`null` as `None`, so serde is not the validating boundary
([model-compiler-3](../research/review/model-and-compiler.md)); the YAML crate
must be chosen by a spike; and `cargo-mutants` rebuilds per mutant, so mutation
cost is set by crate size ([process-5](../research/review/process-and-plan.md)).
Go's mutation tooling is immature (gremlins 0.x, no estate Go repository wires
one), which weakened the Go service's change safety.

## Decision

Every program in estate-kit is Rust: the compiler and its CLI, the service, the
host applier, and the three components (migration runner, secret job, mail
provisioner). They live in one Cargo workspace, at one version, laid out in the
layers of [record 65](0065-the-workspace-is-layered-and-the-crate-graph-is-checked.md).
The UI stays Vue; npm is confined to building its static assets, which the
service embeds. No TypeScript, Go or Python runs in production or in a
Project's CI. Python stays only for this repository's documentation checks.

How the code is shaped is on the design pages
[The Rust workspace](../design/rust-workspace.md),
[Transformations without a DSL](../design/transformations.md) and
[Testing and speed](../design/code-shape-and-speed.md).

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| TypeScript compiler to 1.0, Go service, Rust later (review D1) | Three backend toolchains during the cutover; the compiler is ported later anyway | The maintainer is not keeping the TypeScript tool; the port happens once, to 1.0 |
| Rust compiler, Go service and components | Two backend toolchains; a wire contract between two halves of one product; weak Go mutation tooling | One language gives one set of gates, one dependency audit, and lets the service link the compiler |
| Go for everything | No sum types for a model of about 100 refusal codes; gremlins 0.x for mutation | Change safety is the scenario the review ranks highest after upkeep |
| Leptos or another Rust UI | The dashboard's Vue code is rewritten; WebAssembly tooling joins | The UI is not backend; Vue stays by the maintainer's choice |

## Consequences

- Easier: one toolchain on the backend (rustup, cargo, clippy, cargo-deny,
  cargo-mutants, cargo-llvm-cov); the service links the compiler crates
  ([record 18](0018-the-service-links-the-compiler.md)); Cargo enforces layering.
- Harder: everything in delivery, estate-dashboard's API, liquibase-runner and
  stalwart-provisioner is rewritten, so their behaviour is characterized first
  ([record 55](register.md)). YAML input and canonical output are bespoke code
  in a foundation crate.
- Forbidden: a Go module, a Node runtime or a Python program in estate-kit's
  shipped images or in the reusable workflows a Project runs.

## Confirmation

`cargo xtask check-layers` fails on a workspace member that is not Rust, and
the Hygiene job fails on a `go.mod`, a `package.json` outside `ui/`, or a
`*.py` outside `scripts/` and `docs/`. Both are written with the workspace
skeleton, each with a failing fixture.

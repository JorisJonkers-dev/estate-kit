# Inside the compiler

The compiler stays TypeScript until model 1.0 ([review](../research/review/README.md)
D1). Its design is deploy-kit's: a chain of typed models, one pure step per
arrow, ports for everything that touches the world, layers enforced by
dependency-cruiser. It ships as one executable behind a fixed CLI and
`result.json` contract ([#23](https://github.com/JorisJonkers-dev/estate-kit/issues/23)),
so neither CI nor the service installs npm packages at runtime.

## A Rust port of the 1.0 model

The sections below describe the Rust design kept for a possible port of the
frozen 1.0 model. The port happens only if a record written after 1.0 justifies
it ([#56](https://github.com/JorisJonkers-dev/estate-kit/issues/56)), and then
at byte parity against the TypeScript 1.0 oracles, in the canonical render
format. Rust would add two things: Cargo enforces the layers, and the types
hold more of the model. The review measured what it would cost: serde stops at
the first error and accepts `null` as `None`, so it cannot be the validating
boundary, and no YAML crate is settled.

### Crates

One crate per step and one per adapter. A crate may depend only on `model`
(and adapters and `serialize` on `objects`), so no step can import another.
Cargo's dependency graph replaces dependency-cruiser, and a mutant rebuilds
only its own small crate.

![Rust crates and their dependencies](../diagrams/png/rust-crates.png)

### The pipeline

Each step turns one typed model into the next. Every step can add to the
diagnostic list; none stops at the first error.

![The compile pipeline](../diagrams/png/rust-pipeline.png)

### The authored model

The types carry the vocabulary of `CONTEXT.md` unchanged. Names are newtypes
(`ApplicationId`, `ProcessName`, `SurfaceName`), and every finite set is a
closed enum (`Lifecycle`, `Audience`, `AccessTier`).

![Class diagram: the authored model](../diagrams/png/rust-authored-model.png)

### Pipeline types and ports

The pinned input set is one type, so the closed set of inputs is visible in one
place. Hashing is a trait, so no step reaches for ambient crypto.

![Class diagram: pipeline types and ports](../diagrams/png/rust-pipeline-types.png)

### Data structures

- **Determinism.** Maps are `BTreeMap`, never `HashMap`, so iteration order and
  output bytes are stable. Two renders of the same inputs must compare equal
  byte for byte.
- **References by id.** The dependency graph holds `ApplicationId`s and
  indices, not pointers, so it can be checked for cycles and sorted without
  lifetimes.
- **Spanned parse.** YAML is parsed into a tree that keeps source positions,
  then into the typed model; the model path of every element is recoverable.
  Which crate does the spanned parse is open, to be settled by a spike.
- **Errors.** Authored-input problems are `Diagnostic`s collected in a list.
  Internal bugs are panics, covered by tests.

## Alignment with YAML and Go

The committed JSON Schemas are the contract. The compiler's types (zod today)
are held to them by a drift test. Go types are generated from the schemas. One
shared corpus of valid and invalid YAML runs through both languages.

![How YAML, the schemas, the compiler and Go stay aligned](../diagrams/png/alignment.png)

## The wire to the service

The binary reads fragments from a directory and writes renders, diagnostics and
the lock to an output directory, plus `result.json`. `result.json` is validated
against a committed `compose-result` schema, and the Go service's types are
generated from it. Progress goes out as JSON lines on stderr. Renders are
written in a canonical YAML style specified on one page (review D12), so any
later implementation can match them.

## No render cache

There is no render cache (review D9). A cache keyed by the input digest missed
on every lockstep release, because the compiler version is part of the key. The
render key stays as provenance: the hash of the fragment digest, the Platform
Intent digest, the ClusterState digest and the compiler version. When a
render's digest equals the one already behind the Project's tag, the service
publishes nothing and moves nothing. Inside one run, the binary parses each
fragment once.

![Sequence: skip publishing an unchanged render](../diagrams/png/seq-cache.png)

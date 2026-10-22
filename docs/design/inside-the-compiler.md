# Inside the compiler (Rust)

The compiler keeps the TypeScript design: a chain of typed models, one pure
step per arrow, ports for everything that touches the world. Rust adds two
things: Cargo enforces the layers, and the types hold more of the model.

## Crates

One crate per step and one per adapter. A crate may depend only on `model`
(and adapters and `serialize` on `objects`), so no step can import another.
Cargo's dependency graph replaces dependency-cruiser, and a mutant rebuilds
only its own small crate.

![Rust crates and their dependencies](../diagrams/png/rust-crates.png)

## The pipeline

Each step turns one typed model into the next. Every step can add to the
diagnostic list; none stops at the first error.

![The compile pipeline](../diagrams/png/rust-pipeline.png)

## The authored model

The types carry the vocabulary of `CONTEXT.md` unchanged. Names are newtypes
(`ApplicationId`, `ProcessName`, `SurfaceName`), and every finite set is a
closed enum (`Lifecycle`, `Audience`, `AccessTier`).

![Class diagram: the authored model](../diagrams/png/rust-authored-model.png)

## Pipeline types and ports

The pinned input set is one type, so the closed set of inputs is visible in one
place. Hashing is a trait, so no step reaches for ambient crypto.

![Class diagram: pipeline types and ports](../diagrams/png/rust-pipeline-types.png)

## Data structures

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

The committed JSON Schemas are the contract. Rust types are written by hand,
and a test generates a schema from them and requires it to equal the committed
one. Go types are generated from the schemas. One shared corpus of valid and
invalid YAML runs through both languages.

![How YAML, schemas, Rust and Go stay aligned](../diagrams/png/alignment.png)

## The wire to the service

The binary reads fragments from a directory and writes renders, diagnostics and
the lock to an output directory, plus `result.json`. `result.json` is validated
against a committed `compose-result` schema, and the Go service's types are
generated from it. Progress goes out as JSON lines on stderr.

## Caching

The registry is the cache. A render's key is the hash of its fragment digest,
the Platform Intent digest, the ClusterState digest and the compiler version.
Before rendering a Project, the service asks ghcr for a render with that key and
reuses it if found. Inside one run, the binary parses each fragment once.

![Sequence: looking up a cached render](../diagrams/png/seq-cache.png)

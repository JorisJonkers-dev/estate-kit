---
status: accepted  # proposed | accepted | locked
date: 2026-10-30
rests-on: [1, 3, 5]
lessons: [CS-5]
---

# Every render is a function of pinned inputs

## Context

An earlier specification called purity its load-bearing property, and its own
text broke it: one assignment read a persistent-volume binding from the live
cluster, another read live capacity. A re-render after a volume rebound then
differed from the deploy with every digest identical, and the report blamed the
lock. Reproducibility failed when it was most needed.

## Decision

A render reads a closed set of pinned inputs and nothing else: the Project's
fragment, Platform Intent, the ClusterState snapshot and the compiler version,
each carried by digest. It never reads the live cluster, a secret value, the
clock, a counter or state remembered from an earlier render. Live facts reach a
render by one route only: the service captures them as a ClusterState snapshot,
which is digested and becomes an input.

The same inputs give byte-identical output. Anything a new derivation needs is
first added to a pinned input. The digest of the inputs is the render key, kept
as provenance with each published render ([Where state lives](../design/where-state-lives.md)).

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Absolute purity: no observed state at all | Placement against a bound volume becomes inexpressible | The pressure to read live state returns unchanged |
| No determinism claim | A differing render cannot be told from drift | Gives up the one property the pipeline is for |
| An allocation registry remembered between renders | A render is no longer a function of its inputs | Reintroduces the mutable state the layer excludes |

## Consequences

- Easier: a differing render with identical digests is a defect, never weather;
  any render can be reproduced from its inputs.
- Harder: capturing and digesting the ClusterState snapshot is code to write and
  keep, and every new input is a decision.
- Forbidden: a read of the live cluster, a secret or the clock inside the
  compiler; a render that depends on a previous render.

## Confirmation

A double-render test renders twice from identical pinned inputs, at different
times, and compares the output trees byte for byte; any difference fails. The
compiler crates have no dependency on a cluster client or a clock, which
`cargo xtask check-layers` holds ([record 14](0014-the-compiler-is-a-chain-of-typed-models-one-crate-per-step.md)).

---
status: accepted  # proposed | accepted | locked
date: 2026-10-29
rests-on: [3, 5, 6, 13, 65]
lessons: [CS-1, CS-2, CS-4, MS-1]
---

# The compiler is a chain of typed models, one crate per step

## Context

deploy-kit's compiler is a chain of typed models: read, check, lower, compose,
resolve, render through adapters, serialize. Each step is a pure function in
its own module and imports only the model; the use case sequences them, and no
step imports another
([deploy-kit ADR 0056](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/architecture/0056-the-compiler-is-a-chain-of-typed-models.md)).
dependency-cruiser held that rule. Its rejected alternative is a warning: seven
hexagonal rings, of which three rings and three of four declared ports stayed
empty while ledger rows enforced rules over nothing.

In Rust a crate is the unit of compilation, of visibility and of a mutant's
rebuild ([record 65](0065-the-workspace-is-layered-and-the-crate-graph-is-checked.md)).

## Decision

The compiler is a chain of typed models, and each arrow is one crate:
`step-read` (read and link), `step-check`, `step-lower`, `step-compose`,
`step-resolve`, `step-outputs`, one `render-*` crate per adapter of the
1.0 registry, and `serialize`. Each step crate depends only on the model
crates (`model-intent`, `model-effective`, `model-resolved`,
`deliverable`) and the foundation; none depends on another step. The
`compiler` application crate sequences them and is what the CLI and the
service call. Each step's input is one typed value, and phase types with
private constructors make a skipped step a type error
([Transformations without a DSL](../design/transformations.md)).

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| One compiler crate, modules per step | Layering held by `pub(crate)` only; any change rebuilds the whole compiler, and every mutant rebuilds it | Compile and mutation cost |
| Three crates by stage (intent, resolved, deliverable) | Steps inside a stage can import each other | The rule that no step imports another needs the crate boundary |
| A generic step trait and a pipeline engine | Indirection with one implementation per step | [deploy-kit ADR 0056](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/architecture/0056-the-compiler-is-a-chain-of-typed-models.md): a generic waits for two uses |

## Consequences

- Easier: a change to one rule rebuilds one step crate and its dependents;
  steps can be written in parallel by different hands.
- Harder: a concept that spans steps changes several crates in one pull
  request.
- Forbidden: a dependency from one step crate on another; a step that reads
  anything but its typed input.

## Confirmation

`cargo xtask check-layers` fails on a dependency between two step crates, with
a failing fixture.

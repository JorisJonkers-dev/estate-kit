# Code shape and speed

Each file has one responsibility and changes rarely. A change to one concept
touches one module, and a change to a port touches one fake.

## Rules for files

- **One concept, one module.** Each model concept gets one compiler module, and
  one Go package where the service needs it. One public type per file.
- **Fakes, not mocks.** The pure core needs no test doubles. Each port
  (registry, cluster, Vault, GitHub, event store) has exactly one hand-written
  in-memory fake, in its own file beside the port, shared by every test. No
  mockall, no gomock.
- **Oracles only at the seams.** Hand-reviewed oracle files exist only at the
  four seams: use-cases, adapter port, rendered tree, CLI. No test ever
  rewrites them. Unit tests assert properties and specific fields, never whole
  snapshots.
- **Generated code stays apart.** Types generated from the schemas live in
  their own directories. Nobody edits them by hand, and churn metrics skip
  them.
- **Enforcement.** A module per concept, a file-length cap and one public type
  per file are gated, each with a ledger row and a failing fixture. A
  churn-times-size hotspot report runs in CI as report-only, and flags files
  that change in most PRs.

## Speed budgets

| Gate | Budget | How |
| --- | --- | --- |
| Lint, tests, contracts on a PR | Under 2 minutes | Small modules and packages; npm and Go build caches |
| Mutation on a PR | Under 5 minutes | Only the changed lines, sharded across runners |
| Full mutation | Nightly | 8 to 32 shards |

## Mutation testing

| | TypeScript compiler | Go service |
| --- | --- | --- |
| Tool | Stryker, incremental and diff-scoped | gremlins, diff-scoped ([workspace ADR-0022](https://github.com/JorisJonkers-dev/workspace/blob/main/docs/decisions/ADR-0022-tests-specify-behaviour.md)) |
| Gate | 100% break score, as today | Report-only first, then a ratchet |
| Cost model | Compiled once; mutants switched at runtime | One package rebuild per mutant |
| What keeps it fast | Incremental reports; coverage-routed tests | Small packages; coverage-routed tests |

Stryker is fast because it compiles once and switches between mutants at
runtime. Should the 1.0 model ever be ported to Rust, cargo-mutants rebuilds
for each mutant, and one small crate per step would keep it fast. Go's mutation tools are immature, and no estate Go repository wires
one today.

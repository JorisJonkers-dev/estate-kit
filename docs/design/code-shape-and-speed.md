# Testing and speed

How the Rust workspace is tested, what each kind of test is for, which gates
hold it, and how they stay inside their time budgets. It applies the estate's
testing standard
([workspace ADR-0022, "Tests specify behaviour"](https://github.com/JorisJonkers-dev/workspace/blob/main/docs/decisions/ADR-0022-tests-specify-behaviour.md))
to the layers of [The Rust workspace](rust-workspace.md), with deploy-kit's
lessons on oracles and mutation.

## Rules for code

- **One concept, one module.** Each model concept has one module in the step
  that handles it; each port has one trait, one fake and one adapter crate.
- **One public type per file**, and a file-length cap, gated with a failing
  fixture each.
- **Fakes, not mocks.** Each port has exactly one hand-written fake beside it,
  and the fake passes the port's contract suite
  ([record 68](../decisions/0068-every-fake-passes-its-port-s-contract-suite.md)).
  No `mockall`.
- **Duplication before the wrong abstraction.** Code is shared within the
  workspace when a second caller needs the same behaviour, and moves to
  rust-commons on its third Rust consumer ([workspace ADR-0017](https://github.com/JorisJonkers-dev/workspace/blob/main/docs/decisions/ADR-0017-go-commons-extracts-on-third-use.md)). A helper used
  once stays where it is used.
- **Readable over clever.** No macro where a function will do; no generic
  parameter that only ever takes one type; no trait with one implementation
  unless it is a port.
- **Generated code stays apart**, in its own module, never edited by hand, and
  outside coverage and churn metrics.

## The kinds of test

| Kind | What it proves | Lives in | Runs |
| --- | --- | --- | --- |
| Unit | One behaviour of one function, named as a sentence in `CONTEXT.md` words | `#[cfg(test)]` in each crate | Every `cargo test`, no Docker, no network |
| Property | Totality, determinism, locality, round trips (the canonical emitter, upcasters) | The crate that owns the property | Every run, with a fixed case count; a nightly run with more |
| Fixture and oracle | The compiler's four seams: use cases, the adapter port, the rendered tree, the CLI. Refusal fixtures assert a code and a path | `oracles/`, read-only to tests | Every run |
| Contract | The JSON Schema corpus; the OpenAPI document against the routes; the error catalogue against the fixtures; identity's Principal vectors | `contracts/` and the crate that implements each | Every run |
| Port contract | A fake and its adapter behave alike | Application crate (fake), adapter crate (real) | Fake: every run. Adapter: the integration job |
| Integration | Real HTTP in process; real Postgres, Vault, an OCI registry and k3s in containers | `tests/` behind the `integration` feature | The integration job, on every pull request |
| Characterization | A Go or Python service's recorded answers, before it is replaced ([record 55](../decisions/register.md)) | `oracles/characterization/` | Every run, until the old service is archived |
| End to end | A whole deploy, on a throwaway cluster | `e2e/` | Nightly, and required before a release |
| Host VM | A node class boots its generation; the applier switches, holds the Lease, rolls back | `hosts/vm-tests/`, NixOS tests | On a host change, and nightly |
| UI | Vue components and stores; Playwright journeys against a stubbed API, each stub validated against the OpenAPI document | `ui/` | When `ui/` changes |
| Fuzz | The YAML reader and the schema validator against hostile input | `fuzz/` (cargo-fuzz) | Nightly, time-boxed |

A test that only exercises excluded code is deleted. Retries stay at zero; a
flaky test is quarantined with
`#[ignore = "quarantine: <issue url> until YYYY-MM-DD"]`, at most 14 days out,
which the estate's quarantine check must learn to read (a follow-up in
github-workflows).

## End to end

The e2e suite runs the deploy path the way production does, with nothing
faked except GitHub:

- a k3s cluster in CI with Flux, Flagger and the ValidatingAdmissionPolicies;
- an OCI registry (zot) standing in for ghcr, Vault in dev mode with the two
  Transit keys, Postgres, and the service image built from the pull request;
- a fixture Project repository whose `deploy` job is replayed by the test
  runner with a minted OIDC token.

Its scenarios are the use cases: validate and plan; dry-run; deploy to
Serving; a refused deploy; Pause and Resume; Rollback with Vault scaled to
zero; a service restart mid-rollout that resumes from observed state; a service
upgraded mid-rollout, after which the waiting deploy job re-requests a GitHub
OIDC token and resumes by sequence; an
unchanged render that publishes nothing. Each scenario asserts what a
consumer sees (the tag, the object in the cluster, the Deployment status),
never only a Ready condition (DO-4).

## Gates

| Gate | Threshold | Scope |
| --- | --- | --- |
| Unit coverage | 100% of lines, functions and regions | Domain, application and step crates. Branch coverage needs nightly `cargo llvm-cov --branch`, and is added when it is stable |
| Integration coverage | 100% of functions | Adapter and binary crates |
| Mutation | 100% break score | Domain, application and step crates; adapters report-only, then a ratchet |
| Coverage and mutation ratchet | The measured value, only rising | Every crate ([record 37](../decisions/0037-every-gate-has-a-speed-budget-coverage-and-mutation-are-ratchets.md)) |
| Lints | `clippy::pedantic`, `-D warnings`; `unsafe_code = "forbid"`; `unreachable_pub`; `missing_docs` on public items | Every crate |
| Layers | `cargo xtask check-layers` | The crate graph ([record 50](../decisions/0050-five-bounded-contexts.md)) |
| Ports | A grep-level script: each port trait has a `Fake<Port>` and a `<port>_contract` suite, found by name | The application crates ([record 68](../decisions/0068-every-fake-passes-its-port-s-contract-suite.md)) |
| Supply chain | `cargo-deny` (advisories, licences, banned crates, one version of each), `cargo-machete`, gitleaks | The lockfile and the manifests |

Unit and integration coverage are separate gates, so a unit suite that starts
needing Docker cannot pass on the integration run ([identity ADR 0011](https://github.com/JorisJonkers-dev/identity/blob/main/docs/adr/0011-unit-tests-reach-every-statement-branch-condition-and-function.md)).

## Mutation testing

cargo-mutants changes one expression at a time, rebuilds, and runs the tests.
A mutant rebuilds its own crate and every crate and test binary that depends
on it, so the crate graph decides the cost:

- **Small domain and step crates** keep each rebuild short, and their unit
  tests live in the same crate, so `cargo mutants --package <crate>` runs only
  that crate's tests.
- **No heavy dependency in a mutated crate.** Domain crates do not compile
  `kube` or `sqlx`.
- **On main, never on a pull request.** deploy-kit moved its mutation run to
  every push to main on 2026-10-29: per pull request it took 80% of CI minutes,
  and its spurious failures sat in files the pull request had not changed
  ([deploy-kit ADR 0063](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/architecture/0063-coverage-and-mutation-are-ratchets.md)). estate-kit starts there: each push to main mutates
  the lines changed since the last green report (`--in-diff`), sharded; a
  weekly full run, sharded across 8 to 32 runners, opens an issue per
  survivor.
- **Turned on per crate.** A crate joins the 100% gate when its tests are in;
  until then it reports ([process-5](../research/review/process-and-plan.md)).
- **An equivalent mutant is a design smell.** It is rewritten, not excluded.
  An exclusion in `.cargo/mutants.toml` needs a reason and an issue, and the
  number of exclusions is held at zero by the ratchet.

## Speed budgets

| Gate | Budget | How |
| --- | --- | --- |
| Lint, unit, property, fixture and contract tests on a pull request | Under 2 minutes | Only crates the diff reaches and their dependents; `cargo nextest`; `rust-cache` |
| Integration on a pull request | Under 5 minutes | Containers started once per test binary; a template database per test ([workspace ADR-0021](https://github.com/JorisJonkers-dev/workspace/blob/main/docs/decisions/ADR-0021-liquibase-runner-is-the-one-migration-path.md)) |
| Mutation on main | Under 10 minutes | `--in-diff`, sharded, crates in the graph's leaves |
| Full mutation | Weekly | 8 to 32 shards |
| End to end | Under 15 minutes | Nightly and before a release |

The path-to-crate mapping follows the estate's path buckets: a changed path
runs the crates that own it and their dependents, and a path no crate claims
runs everything.

## Compile time

A change should rebuild only what depends on it. The rules that make that
true are in [Keeping builds fast](rust-workspace.md#keeping-builds-fast): heavy
dependencies only at the edge, no `k8s-openapi`, few proc macros, one feature
set, per-crate test runs.

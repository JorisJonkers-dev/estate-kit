---
status: accepted  # proposed | accepted | locked
date: 2026-10-29
rests-on: [13, 50]
lessons: [CS-2]
---

# Shared Rust code moves to rust-commons on its third consumer; the sign-in kit is the first

## Context

[rust-commons](https://github.com/JorisJonkers-dev/rust-commons) is one crate,
`jorisjonkers-commons`, holding identity's Principal adapter as tower layers.
The estate's rule for shared code is that a package moves into a commons
repository only on its third use, in the same pull request that switches the
third consumer
([workspace ADR-0017](https://github.com/JorisJonkers-dev/workspace/blob/main/docs/decisions/ADR-0017-go-commons-extracts-on-third-use.md)).
estate-kit needs browser sign-in for its UI, which identity#113 already plans
as a Rust sign-in kit that must pass identity's flow-conformance suite. It also
needs typed configuration, telemetry setup, health endpoints and a
testcontainers harness, which no other Rust service needs yet.

## Decision

- **The sign-in kit goes into rust-commons now** (identity#113), because
  every Rust application with a browser UI needs it and identity's conformance
  suite is its contract. Its CI runs the flow-conformance suite explicitly.
- **Everything else stays in estate-kit's foundation crates** until a third
  Rust consumer needs it, and then moves in the pull request that switches
  that consumer.
- **rust-commons becomes a workspace of small crates** (`identity`, `signin`,
  and later others) when it gains the sign-in kit, so a consumer that only
  reads Principals does not compile an OIDC client.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| A commons crate for configuration, telemetry and test harnesses now | An interface designed for one consumer | The estate's third-use rule |
| The sign-in kit inside estate-kit | Every later Rust UI copies or depends on estate-kit | The kit has a contract outside estate-kit: identity's suite |
| Keep rust-commons one crate with features | Features unify across a workspace, so consumers compile more than they use | The compile-time reason for small crates ([record 50](0050-five-bounded-contexts.md)) |

## Consequences

- Easier: estate-kit's shared code changes in one repository until it is truly
  shared.
- Harder: a second Rust consumer copies code before the third extracts it.
- Forbidden: a rust-commons module with fewer than three consumers, apart from
  the identity contract adapters.

## Confirmation

No automated check: an extraction is reviewed in the pull request that switches
its third consumer. The sign-in kit's CI fails if identity's flow-conformance
suite does not run.

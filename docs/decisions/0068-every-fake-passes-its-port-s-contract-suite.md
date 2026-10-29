---
status: proposed  # proposed | accepted | locked
date: 2026-10-29
rests-on: [36, 65]
lessons: [TM-3, TM-4]
---

# Every port has one fake, and the fake passes the same contract suite as its adapter

## Context

[Record 36](register.md) gives each port exactly one hand-written fake, so
use cases are tested without mocks. A fake is only as good as its likeness to
the real system. The workspace's own records name the failure: auth-api's
WebSocket and CORS failure was hidden by fakes ([workspace ADR-0022](https://github.com/JorisJonkers-dev/workspace/blob/main/docs/decisions/ADR-0022-tests-specify-behaviour.md)).
deploy-kit's adapter seam already runs one table-driven contract suite over
every adapter (deploy-kit `docs/architecture.md`, "Testing").

## Decision

Each port trait in an application crate comes with a **contract suite**: a
public generic function in the same crate, behind the `fakes` feature, that
takes a constructor for an implementation and asserts the port's behaviour
(what `Conflict` means, what a second identical call returns, what an absent
item reads as). The suite runs:

- against the fake, in the application crate's unit tests, on every run;
- against the real adapter, in the adapter crate's integration tests, with
  the outside system in a container (Postgres, Vault in dev mode, an OCI
  registry, k3s) where one exists, and against a recorded exchange where it
  does not (GitHub).

A behaviour the fake has and the adapter lacks, or the reverse, fails one of
the two runs.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Fakes without a contract suite | Fakes drift from the systems they stand for | The failure [workspace ADR-0022](https://github.com/JorisJonkers-dev/workspace/blob/main/docs/decisions/ADR-0022-tests-specify-behaviour.md) records |
| Mocks per test (`mockall`) | Every test restates the port's behaviour | Rejected in [record 36](register.md) |
| Integration tests only | Use-case tests need Docker and minutes | The unit gate must run without Docker |

## Consequences

- Easier: use cases are tested in milliseconds against fakes that are held to
  the real systems.
- Harder: a port change touches the trait, the fake, the suite and the
  adapter in one pull request.
- Forbidden: a port without a contract suite; a fake that is not run through
  it.

## Confirmation

`cargo xtask check-ports` fails when a public trait in an application crate
has no contract suite function, or when the suite is not called from both the
fake's tests and an adapter crate's integration tests.

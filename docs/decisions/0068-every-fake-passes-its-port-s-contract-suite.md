---
status: accepted  # proposed | accepted | locked
date: 2026-10-29
rests-on: [50]
lessons: [TM-3, TM-4]
---

# One concept per module, one fake per port that passes its contract suite, oracles only at the seams

## Context

A fake is only as good as its likeness to the real system. The workspace's
own records name the failure: auth-api's WebSocket and CORS failure was hidden
by fakes ([workspace ADR-0022](https://github.com/JorisJonkers-dev/workspace/blob/main/docs/decisions/ADR-0022-tests-specify-behaviour.md)).
deploy-kit's adapter seam already runs one table-driven contract suite over
every adapter (deploy-kit `docs/architecture.md`, "Testing").

Two earlier rules sit beside it and are kept here: a module holds one
concept, and tests compare against oracles only at the system's seams. The
rule that every port has a suite also needs a check. A bespoke rustdoc
analysis of every public trait costs more than the handful of ports in the
first workstream justify, and a name-based convention is enough to check.

## Decision

**One concept per module.** A module holds one concept, so a reader and a
mutant's rebuild both find it in one place.

**Oracles only at the seams.** Tests compare against oracles only at the
four seams of [Testing and speed](../design/code-shape-and-speed.md): the
use cases, the adapter port, the rendered tree and the CLI. No test reaches
into the internals of a transformation.

**One fake per port.** A *port* ([CONTEXT.md](../../CONTEXT.md)) is a trait in
an application crate that names one thing the core needs from one outside
system. The `Ports` bundle that wires use cases to ports is not a port: its
associated types are ports, and it has no adapter, fake or suite of its own.
Every port has exactly one hand-written fake, no mocks, and a **contract
suite**: a public generic function in the same crate, behind the `fakes`
feature, that takes a constructor for an implementation and asserts the
port's behaviour (what `Conflict` means, what a second identical call returns,
what an absent item reads as). The suite runs:

- against the fake, in the application crate's unit tests, on every run;
- against the real adapter, in the adapter crate's integration tests, with
  the outside system in a container (Postgres, Vault in dev mode, an OCI
  registry, k3s) where one exists, and against a recorded exchange where it
  does not (GitHub).

A behaviour the fake has and the adapter lacks, or the reverse, fails one of
the two runs.

**A naming convention finds all three.** For a port trait `Foo`, its fake is
`FakeFoo` and its suite is `foo_contract`. The check is grep-level: a script
reads the source for these names, not rustdoc output. It is written with the
workspace in W0 ([issue 60](https://github.com/JorisJonkers-dev/estate-kit/issues/60)).
A rustdoc-based check is built only when the number of ports justifies it.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Fakes without a contract suite | Fakes drift from the systems they stand for | The failure [workspace ADR-0022](https://github.com/JorisJonkers-dev/workspace/blob/main/docs/decisions/ADR-0022-tests-specify-behaviour.md) records |
| Mocks per test (`mockall`) | Every test restates the port's behaviour | One hand-written fake per port is the rule |
| Integration tests only | Use-case tests need Docker and minutes | The unit gate must run without Docker |
| A `cargo xtask check-ports` over rustdoc output | A bespoke analysis to build and maintain for a handful of ports | A convention and a grep-level check enforce the same rule until more ports justify it |

## Consequences

- Easier: use cases are tested in milliseconds against fakes that are held to
  the real systems; a port, its fake and its suite are found by name.
- Harder: a port change touches the trait, the fake, the suite and the
  adapter in one pull request, and a name that breaks the convention fails
  the check.
- Forbidden: a port without a fake or a contract suite; a fake that is not run
  through the suite; a mock in place of a fake; a test that compares against
  an oracle away from the four seams.

## Confirmation

A grep-level script, run in the Lint job, lists every trait in an application
crate that is a port (every public trait except the `Ports` bundle) and fails
when it finds no `Fake<Port>` or no `<port>_contract` for one, or when the
suite is not called from both the fake's tests and an adapter crate's
integration tests. Its test suite holds one failing fixture per rule, so a
rule that can no longer fire fails its own test.

---
status: accepted  # proposed | accepted | locked
date: 2026-10-29
rests-on: [6, 13, 17]
lessons: [CS-5, CS-6, TM-3]
---

# The service links the compiler's crates; the CLI's JSON output is for CI only

## Context

The earlier design ran the compiler as a subprocess over a directory and a
`result.json` file, so CI and the service ran identical code across two
languages, and committed `result.json` fixtures held the TypeScript output to
what the Go service read. With every program in Rust
([record 13](0013-every-program-is-rust.md)) and one lockstep version, the
service and the CLI can call the same function. A wire contract between two
halves of one workspace would be upkeep with no reader outside it.

The reasons a subprocess was attractive were isolation: a panic, a runaway
allocation or a hang in the compiler cannot take the service down.

## Decision

The service depends on the `compiler` application crate and calls the same
use cases the CLI calls (`validate`, `plan`, `compose`). Composition runs on a
blocking thread under `catch_unwind`, behind an input budget (document size,
nesting depth, node count) enforced by the YAML reader, and a wall-clock
deadline. A panic or a budget breach fails that composition with an internal
problem and leaves the service running. The compiler crates stay pure: no I/O,
no clock, no environment, so linking them gives the service nothing it can
misuse.

The CLI's `--json` output keeps a committed schema, because the reusable
workflows and the GitHub annotations read it. The service does not read it.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Subprocess of the same binary, directory in and out, `result.json` | A serialized wire format, a schema, consumer fixtures, temp directories and process management inside one workspace | Isolation is had more cheaply with `catch_unwind`, budgets and a deadline |
| A separate compile worker pod | A queue, a second deployment and its RBAC | One composition runs at a time; there is nothing to scale |

## Consequences

- Easier: one call, typed end to end; no `result.json` consumer fixtures; the
  service's tests use the real compiler with fake ports.
- Harder: a compiler bug that corrupts memory could affect the service. Rust's
  `unsafe_code = "forbid"` in every compiler crate rules that out in our code.
- Forbidden: I/O, a clock or the environment inside a compiler crate.
  Everything the compiler reads is in its pinned input set
  ([record 6](register.md)).

## Confirmation

`cargo xtask check-layers` refuses a dependency from any compiler crate on
`tokio`, `reqwest`, `std::fs`-using crates, or any adapter crate, and clippy's
`disallowed-methods` refuses `std::env`, `std::fs` and `SystemTime::now` in
them. A service test feeds a fragment that trips the budget and asserts that
the composition fails and the next one succeeds.

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
blocking thread, contained in-process by four limits:

- An input budget (document size, nesting depth, node count) enforced by the
  YAML reader, and a wall-clock deadline.
- A step budget threaded through the transformation kit
  ([record 14](0014-the-compiler-is-a-chain-of-typed-models-one-crate-per-step.md)). Every transformation
  spends from it, so a loop ends as a diagnostic instead of a hang.
- An aggregate memory cap per Composition, counted over everything one
  Composition allocates, so many small inputs cannot add up to a large one.
- The release profile sets `panic = "unwind"`, so a panic fails only the
  Composition that raised it. An abort (out of memory, stack overflow) is not
  caught: the pod restarts and [record 63](0063-the-service-has-one-writer-and-reconciles-from-observed-state.md)'s
  reconcile resumes from observed state.

A budget breach is authored input, not a service fault. It is refused with its
own refusal code and a primary location on the document, and the service
reports it as a 4xx problem. A panic fails that Composition with an internal
problem and leaves the service running. The compiler crates stay pure: no I/O,
no clock, no environment, so linking them gives the service nothing it can
misuse.

The CLI's `--json` output keeps a committed schema, because the reusable
workflows and the GitHub annotations read it. The service does not read it.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Subprocess of the same binary, directory in and out, `result.json` | A serialized wire format, a schema, consumer fixtures, temp directories and process management inside one workspace | Isolation is had more cheaply with budgets, a deadline and unwinding panics |
| A separate compile worker pod | A queue, a second deployment and its RBAC | One composition runs at a time; there is nothing to scale |

## Consequences

- Easier: one call, typed end to end; no `result.json` consumer fixtures; the
  service's tests use the real compiler with fake ports.
- Harder: a compiler bug that corrupts memory could affect the service.
  `unsafe_code = "forbid"` in every compiler crate rules out unsafe code in
  our crates only, not in their dependencies; those are vetted when they are
  added. An abort takes the pod down until it restarts.
- Forbidden: I/O, a clock or the environment inside a compiler crate.
  Everything the compiler reads is in its pinned input set
  ([record 6](register.md)).

## Confirmation

`cargo xtask check-layers` and cargo-deny bans refuse a dependency from any
compiler crate on `tokio`, `reqwest` or any adapter crate, and clippy's
`disallowed-methods` refuses `std::env`, `std::fs` and `SystemTime::now` in
them. Three service tests each fail one Composition and assert that the next
one succeeds: a looping input (the step budget trips), an oversized input (the
memory cap trips) and a transformation that panics. The first two assert the
budget refusal code, its document location and a 4xx problem; the third
asserts an internal problem. A check refuses a release profile without
`panic = "unwind"`.

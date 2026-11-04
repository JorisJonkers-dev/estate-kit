---
status: accepted  # proposed | accepted | locked
date: 2026-11-04
rests-on: [50, 63, 68, 80]
amends: [68]
lessons: [TM-4]
---

# Every reconciler estate-kit owns passes crash-point, stale-read and safety tests before it takes production responsibility

## Context

estate-kit owns several reconcilers. The six components each reconcile one
outside system through the shared `reconcile` decide step
([Mail and components](../design/mail-and-components.md#components)). Each node
runs a host applier
([record 30](0030-a-host-applier-on-each-node-pulls-its-signed-host-tag.md)).
Delivery rebuilds unfinished Rollouts from observed state
([record 63](0063-delivery-has-one-writer-and-reconciles-from-observed-state.md)),
and the tenancy context runs Tenant operations whose five participants each
hold a finalizer
([record 80](0080-a-tenant-is-a-custom-resource-in-a-sixth-bounded-context-tenancy.md)).

[Record 68](0068-every-fake-passes-its-port-s-contract-suite.md) holds each
fake to its adapter with a contract suite. That proves the fake behaves like the
outside system. It does not prove that a reconciler converges after a crash
between two writes, under a stale view, after a lost response or a duplicate
request, or from an arbitrary earlier state. Nor does it prove safety: no change
to the wrong Tenant, no finalizer released before its cleanup, no destructive
migration run twice (the architecture evaluation of 2026-11-04, section 3.11).
[Record 63](0063-delivery-has-one-writer-and-reconciles-from-observed-state.md)
kills Delivery after each write in one end-to-end scenario; nothing does the
same for the others.

The literature finds these bugs in mature controllers. "Automatic Reliability
Testing for Cluster Management Controllers" (Sieve, 2022) found 46 new bugs in
ten controllers by exposing them to intermediate, stale and unobserved states,
and only five of the 46 showed as an exception or a crash. "Acto" (2023) found 56
new bugs in eleven operators. "Anvil" (2024) reports that 70 of the bugs those
two tools found, 69% of them, were controllers that never reach the desired
state. Those tools target Go operators, and Anvil's proofs need a verifier;
estate-kit can take their lesson, not their tooling.

## Decision

This record extends
[record 68](0068-every-fake-passes-its-port-s-contract-suite.md). The
foundation crate `testkit` gains a crash-point harness. It drives a reconciler
over its port fakes, stops it after every write and restarts it, drops a
response, repeats a request, serves it a stale or incomplete view, and starts it
from any intermediate state the run produced. Once the faults stop, the
reconciler must reach its declared state, and at every step it must keep its
safety predicates. Each reconciler declares its own predicates beside it, at
least: it changes only the Tenant it was asked about, releases a finalizer only
after its cleanup is recorded, never runs a migration revision twice unless the
revision is idempotent, never deletes what it does not own, and never deletes a
durable object without a Retirement tombstone
([record 105](0105-removal-is-a-retire-lifecycle-with-durable-retirement-tombstones-and-declared-moves-and-prune-protected-kinds-never-prune.md)).
Tests target convergence; they do not prove it.

Every reconciler estate-kit owns passes these tests before it takes production
responsibility: each component, the host applier, the Tenant operations and
Delivery's own reconcile. The destructive reconcilers go first:
`migration-run`, `backup`, `database-catalog` and `mailbox`. The harness and
the tests for all four exist before the cutover's first handover, and each of
the four passes them before it replaces its Go or Python program.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Contract suites only (today) | Fakes match the systems, but no test drives a reconciler through a crash or a stale view | Convergence and safety bugs are what the studies find, and few show as a crash |
| Run Sieve or Acto | Tools built for Go operators and their cluster state, not Rust reconcilers over ports | The lesson transfers; the tooling does not |
| Verify liveness formally, as Anvil does | A proof per reconciler in a verifier, at a cost no single maintainer can carry | A harness catches the common cases for far less |
| Test after the cutover | The destructive reconcilers take production responsibility untested | A lost database or mailbox cannot be rolled back |
| Rely on the end-to-end suite | Each fault needs a cluster run, and few of them can be placed | The harness places a fault after every write in milliseconds |

## Consequences

- Easier: a reconciler that leaves a half-done state, or acts on a stale view,
  fails in a unit test; each reconciler's safety rules are written down beside
  it.
- Harder: each reconciler declares its predicates and keeps its writes
  observable to the harness; the destructive four need their tests before they
  can replace a Go or Python program.
- Forbidden: a reconciler in production without passing crash-point and
  stale-read tests; a safety predicate that no deliberately broken reconciler
  shows can fail.

## Confirmation

The **Reconciler crash-point tests** fail when a reconciler, stopped after any
write, given a lost response or a duplicate request, does not reach its declared
state once the faults stop, or breaks a safety predicate at any step. The
**Reconciler stale-read tests** fail when a reconciler given a stale or
incomplete view acts unsafely, or does not converge once its view is current.
The **Reconciler harness coverage** check fails when a crate that drives the
`reconcile` decide step has no crash-point or stale-read suite, or when a safety
predicate has no deliberately broken reconciler that the harness catches. The
**Port contract script** still holds each fake to its adapter, and a scenario of
the **E2E scenarios** still kills Delivery after each write
([record 69](0069-the-deploy-path-is-tested-end-to-end.md)).

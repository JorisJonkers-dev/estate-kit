---
status: accepted  # proposed | accepted | locked
date: 2026-10-29
rests-on: [13, 68]
lessons: [TM-1, DO-4, PR-3]
---

# Every Go and Python program is characterized before it is rewritten in Rust

## Context

Every program in estate-kit is Rust ([record 13](0013-every-program-is-rust.md)).
The programs it replaces carry behaviour that no specification states:
delivery's Release Gate answers Flagger with status codes, fails closed and
caches for 15 seconds; its Reporter keeps GitHub Deployment statuses per stage;
its vault-policy job compares policy text byte for byte with what Vault holds;
liquibase-runner promises that the same proof means the same bytes;
stalwart-provisioner validates manifests by hand-written rules. delivery's
coverage gate was 80%, and none of them had mutation testing.

## Decision

Before a program is rewritten, its behaviour is recorded as characterization
fixtures in `oracles/characterization/<program>/`, from the program itself:
HTTP exchanges for the Release Gate, the Reporter and the dashboard's API;
inputs and outputs for the Collector, the jobs and the provisioner; the bytes
of each output whose format is a contract (the migration proof, Vault policy
text). Each fixture is labelled characterization, not independent (TM-1). The
Rust program passes them before it replaces the old one, and they are deleted
when the old program is archived. A behaviour the rewrite changes on purpose
is listed with its reason, never silently dropped.

The dashboard's session cookie is not characterized: sessions are reset once at
the switch.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Port and compare by hand | No proof the Release Gate kept its answers | The gate's answers decide every traffic switch |
| Specify each program first, then implement | A specification written from memory of the code | The running program is the better witness |
| Keep the old programs running beside the new ones | Two of everything until an undefined date | Every program is Rust |

## Consequences

- Easier: each rewrite has a finish line set by the program it replaces.
- Harder: recording fixtures needs each old program run against envtest,
  testcontainers or a recorded exchange.
- Forbidden: archiving a program whose characterization fixtures the Rust
  rewrite does not pass, unless each failure is listed as an intended change.

## Confirmation

Each component's and the service's CI runs its characterization fixtures; the
archive checklist (#53) refuses a program with a failing fixture or an
unlisted change.

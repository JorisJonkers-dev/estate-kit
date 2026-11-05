---
status: proposed  # proposed | accepted | locked
date: 2026-11-05
rests-on: [64, 67]
amends: [67]
lessons: [TM-1, DO-4]
---

# The rewritten oracles have one independent witness, a Project switches after twenty distinct clean input digests, and only the maintainer adds an expected-differences ledger entry

## Context

The architecture and design review of 2026-11-04 found three gaps in
[record 67](0067-the-compiler-is-written-to-the-1-0-contract.md). The format
proof is circular: the rendered oracles are rewritten by the `canonical`
crate, and the Rust output is then byte-compared with them, so one
implementation of the style is checked against another copy of itself (TM-1).
The shadow's exit was never a number: the plan held "an agreed number of
days", and clean had no countable meaning. And the expected-differences ledger
named its closed set of causes but not who adds an entry, or on what evidence
an entry is allowed.

The maintainer settled all three on 2026-11-04: the `canonical` crate writes
the rewritten oracles, checked once against one independent witness; a
Project's switch is gated by 20 distinct clean input digests, a nightly shadow
and a logged override; and only the maintainer adds a ledger entry, in a
`contract-change` pull request with an evidence line. A handover is proved by a
value a consumer reads, after a one-off diff, and finished in one change
(DO-4).

## Decision

This amends
[record 67](0067-the-compiler-is-written-to-the-1-0-contract.md) in three
sentences.

1. **The rewritten oracles are checked once against one independent witness.**
   The witness is the one
   [record 64](0064-renders-use-a-canonical-yaml-style-specified-on-one-page.md)
   writes down: a rendered ConfigMap in the canonical style, read through the
   Kubernetes API server, must read back equal to its rendered value. The
   check runs once, in the pull request that rewrites the oracles. The API
   server is a consumer of the format and neither `canonical` nor the compiler,
   so the format proof is not circular.
2. **A Project switches after twenty distinct clean input digests.** The
   shadow runs nightly, and a Project switches only after its shadow render has
   been clean over at least 20 distinct input digests since the Project's last
   unexplained difference. A switch is a reviewed pull request that adds the
   Project to the committed switched list and states its run; the maintainer
   may override the run and switch earlier when the override is logged in that
   pull request, and no override excuses a difference: an unexplained
   difference stops the switch whatever the count.
3. **Only the maintainer adds an expected-differences ledger entry.** An entry
   is added in a pull request that carries the maintainer's `contract-change`
   label, and it states one evidence line: the difference the entry explains,
   where the difference was seen, and what caused it.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| The byte comparison alone proves the format | `canonical` agrees with itself twice | A reader outside the implementation witnesses the style once |
| A counted run of clean days | A quiet Project passes without exercising inputs | Distinct input digests make the run about inputs, not the calendar |
| Any reviewer may shorten a run without logging it | The gate's history dies with the switch | The override lives in the switch pull request, and excuses no difference |
| Anyone may add a ledger entry | An entry drifts in with the difference it hides | The maintainer's label and one evidence line make each entry a reviewed act |
| A second witness kept forever | Two consumers to track through every format change | The witness is checked once, on the rewrite; the specification holds after that |

## Consequences

- Easier: "clean" is a countable number a switch pull request states; the
  format proof stands on a consumer outside the rewrite; every ledger entry
  had a maintainer's approval and an evidence line.
- Harder: the rewrite pull request needs an API server for its one witness
  check; a quiet Project waits for 20 distinct inputs to reach its switch.
- Forbidden: a switch without its clean run, or with an unlogged override; a
  rewrite of the rendered oracles with no witness check; a ledger entry in a
  pull request without the `contract-change` label or without its evidence
  line; an override that excuses a difference.

## Confirmation

The **Canonical YAML tests** hold the witness through the API server's
ConfigMap round trip. The **Shadow comparison** fails a switch pull request
without its clean run of 20 distinct input digests and its logged override,
and fails a ledger entry that carries no evidence line. The **Contract gate**
holds the label: only a pull request that carries `contract-change` changes
`shadow/expected-differences.yaml`.

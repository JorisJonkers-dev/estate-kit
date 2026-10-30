---
status: accepted  # proposed | accepted | locked
date: 2026-10-30
rests-on: [13, 50]
lessons: [TM-4, TM-5]
---

# Every gate has a speed budget; coverage and mutation are ratchets

## Context

A gate that is too slow is skipped or resented, and one that has only ever
passed is untested (TM-4). deploy-kit learned this with mutation testing: a
full run per pull request cost 9 to 18 minutes and took 80% of its CI minutes,
and its spurious failures sat in files the pull request had not changed
([deploy-kit ADR 0063](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/architecture/0063-coverage-and-mutation-are-ratchets.md);
TM-5). The workspace's small crates ([record 50](0050-five-bounded-contexts.md))
make per-crate runs cheap, if the graph is kept that way.

## Decision

Every gate has a time budget, stated on
[code shape and speed](../design/code-shape-and-speed.md#speed-budgets), and a
gate that exceeds its budget is fixed or split, not dropped.

Coverage and mutation score are ratchets: each crate's measured value may only
rise. A crate joins the 100% gate when its tests are in; until then it reports.

Mutation runs with cargo-mutants on every push to main, limited to the lines
changed since the last green report and sharded, never on a pull request. A
weekly full run, sharded, opens an issue per survivor. An equivalent mutant is
rewritten, not excluded, and the number of exclusions is held at zero.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Mutation on every pull request | Minutes added to every review and failures from files the change did not touch | deploy-kit measured 80% of its CI minutes |
| Mutation weekly only | A weak test survives a week before anyone knows | Changed code is cheap to check on main |
| A fixed coverage threshold with no ratchet | A crate can fall back to the threshold after reaching 100% | The measured value only rises |
| No budgets, only thresholds | A slow gate is discovered when people skip it | Every gate has a budget |

## Consequences

- A pull request waits only for lint, unit and integration tests.
- A weak test is found on main within one run, and a full audit happens weekly.
- A budget breach is a defect in the gate, with an owner.
- Excluding a mutant needs a reason and an issue; it is a design smell first.

## Confirmation

- The workflow that runs mutation triggers on `push` to main and `schedule`,
  never on `pull_request`; the **Mutation trigger lint** fails on any other
  trigger.
- The **Ratchet step** compares each crate's coverage and mutation score with the
  committed baseline and fails on a drop; a negative fixture lowers a baseline
  and expects the failure.
- The **Mutation exclusion count** checks the exclusions in
  `.cargo/mutants.toml` against zero.

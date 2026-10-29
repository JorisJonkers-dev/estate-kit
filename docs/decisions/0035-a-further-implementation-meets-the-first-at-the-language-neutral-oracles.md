---
status: proposed  # proposed | accepted | locked
date: 2026-10-29
rests-on: [15, 36, 64, 67]
lessons: [MD-1, TM-1, TM-2]
---

# A further implementation, if one is ever written, meets the first at the language-neutral oracles

## Context

The coursework built the model twice, in TypeScript and in EMF, and the second
reading found real gaps in the specification, at twice the cost (MD-1). The
Rust compiler meets deploy-kit 1.0 this way now
([record 67](0067-the-compiler-is-written-to-the-1-0-contract.md)). Other
implementations may follow: an editor plugin that validates, a library in
another language that reads renders.

## Decision

Any further implementation of the model, in any language, is held to the
same contract as the Rust compiler and nothing else: the committed schemas and
their corpus verdicts and diagnostic sets ([record 15](0015-the-rust-types-agree-with-the-committed-schemas-on-their-corpus.md)),
every refusal oracle's code and path, the expected models as parsed JSON, and
the rendered files in the canonical format ([record 64](register.md)), compared
structure first, then bytes. Oracles are never regenerated from either
implementation.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Test a second implementation against the first's output | Two implementations agreeing with each other's bugs | Oracles are written before the code (TM-1) |
| No rule until a second implementation exists | The contract drifts toward Rust specifics | The contract must stay language-neutral |

## Consequences

- Easier: a second implementation knows exactly what to meet.
- Harder: every oracle stays language-neutral; no Rust-only expectation may
  enter `oracles/`.
- Forbidden: an oracle written by running an implementation and saving its
  output.

## Confirmation

The oracle check refuses an oracle file changed in the same pull request as
the code it tests, unless the pull request is labelled as an oracle review.

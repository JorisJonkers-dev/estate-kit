---
status: proposed  # proposed | accepted | locked
date: 2026-10-29
rests-on: [13, 16, 47]
lessons: [CS-3, MD-2, TM-1]
---

# The Rust types agree with the committed schemas on their corpus

## Context

The committed JSON Schemas are the contract ([record 16](register.md)). deploy-kit
generates them from zod and holds them, not to their bytes, but to a
hand-written accept/refuse corpus, because byte equality only proves that the
generator ran: zod dropped a refinement and the published schema accepted
documents the model refused, while the byte check stayed green
([deploy-kit ADR 0088](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/architecture/0088-the-committed-schemas-and-their-corpus-are-the-contract.md)).

In Rust, serde's derived deserializer stops at the first error and reads an
explicit `null` as an absent `Option`; a schema derived from the Rust types
with schemars would not be structurally equal to the committed one
([model-compiler-3](../research/review/model-and-compiler.md)).

## Decision

- **The committed schemas stay the source of the contract**, with their
  corpus. No language generates its types from them, and no test compares
  generated schema bytes.
- **The read step validates before it converts.** Authored YAML is checked
  against the committed schema with every error collected at its JSON
  Pointer, and only valid input is converted into the hand-written Rust
  types, which refuse `null` and unknown keys.
- **The types agree with the schema on the corpus.** Every corpus document
  gets the same verdict from the schema and from the typed conversion.
  Property tests add generated documents to the corpus run.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Generate Rust types from the schemas (typify) | Generated types without newtypes or closed enums | The model's types carry its vocabulary |
| Derive the schemas from the Rust types and compare bytes | Fails on day one; ties every implementation to one generator | [deploy-kit ADR 0088](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/architecture/0088-the-committed-schemas-and-their-corpus-are-the-contract.md) |
| serde as the validator | One error per run; `null` accepted | Every error must be reported at once (CS-3) |

## Consequences

- Easier: editors, other languages and the compiler enforce the same
  contract; every authored error is reported in one run.
- Harder: a model change edits the schema, the corpus and the type, and the
  corpus test holds them together.
- Forbidden: a type that accepts a document the schema refuses, or the
  reverse.

## Confirmation

The corpus-agreement test fails on any corpus document whose verdict differs
between the schema and the typed conversion.

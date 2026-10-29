---
status: accepted  # proposed | accepted | locked
date: 2026-10-29
rests-on: [13, 47]
lessons: [CS-3, MD-2, TM-1]
---

# The Rust types agree with the committed schemas on their corpus

## Context

The committed JSON Schemas are the contract, and the estate holds the Rust
types to them. deploy-kit
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
- **The committed schemas and their corpus are the contract.** Editors, other
  languages and the compiler read the same schemas, and the corpus is what
  holds a change to them.
- **Agreement is one-directional.** The typed conversion refuses at least
  everything the schema refuses, and may refuse more. A document the schema
  refuses and the types accept is a defect; a document the schema accepts
  and the types refuse is allowed, because the types carry rules a schema
  cannot say.
- **Each corpus document records its expected verdict and its full
  diagnostic set.** For a refused document that is every diagnostic, each at
  its model path, not only the first or the fact of refusal. The schema
  validator's errors, including its `required` errors, map to those model
  paths. Property tests add generated documents to the corpus run.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Generate Rust types from the schemas (typify) | Generated types without newtypes or closed enums | The model's types carry its vocabulary |
| Derive the schemas from the Rust types and compare bytes | Fails on day one; ties every implementation to one generator | [deploy-kit ADR 0088](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/architecture/0088-the-committed-schemas-and-their-corpus-are-the-contract.md) |
| serde as the validator | One error per run; `null` accepted | Every error must be reported at once (CS-3) |
| Require the same verdict in both directions | Types may not refuse what a schema cannot express | Agreement is one-directional |
| Assert only the verdict | A wrong or missing diagnostic passes | The whole diagnostic set is asserted |

## Consequences

- Easier: editors, other languages and the compiler enforce the same
  contract; every authored error is reported in one run.
- Harder: a model change edits the schema, the corpus and the type, and the
  corpus test holds them together.
- Forbidden: a type that accepts a document the schema refuses, and a corpus
  document that records a verdict without its diagnostic set.

## Confirmation

The corpus-agreement test fails on a corpus document the schema refuses and
the typed conversion accepts, and on any document whose diagnostics, as a
whole set with their model paths, differ from the set recorded beside it.

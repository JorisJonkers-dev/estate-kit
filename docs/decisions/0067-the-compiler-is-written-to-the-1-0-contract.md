---
status: accepted  # proposed | accepted | locked
date: 2026-10-29
rests-on: [3, 5, 6, 13, 15, 68]
lessons: [PR-3, TM-1, TM-2, MD-1, MD-5]
---

# The Rust compiler implements the 1.0 specification, and the shadow compares structure

## Context

deploy-kit released 1.0.0 on 2026-10-27. That release is the contract step of
deploy-kit#373: it cut the model to what 1.0 keeps (the reconciliation
ledgers, `alertClass`, per-cluster env overlays and the rest are refused),
and the model version is now the package version. What remains of #373 is
step 8: handing Projects over one at a time, with additive releases that
model what each handover needs.

The 1.0 specification is language-neutral in most of its evidence. `spec/v1`
holds the chapters, eight committed JSON Schemas with their accept/refuse
corpus ([deploy-kit ADR 0088](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/architecture/0088-the-committed-schemas-and-their-corpus-are-the-contract.md)),
196 refusal and 41 schema-refusal oracles that record only a code, a document
and a path, 19 expected models in canonical JSON, and 504 rendered files.
Only the rendered files are tied to TypeScript: they are eemeli/yaml 2.9.1's
YAML 1.1 output, which no Rust crate reproduces
([model-compiler-5](../research/review/model-and-compiler.md)).

Other implementations may follow: an editor plugin that validates, a library
in another language that reads renders. The coursework built the model twice,
in TypeScript and in EMF, and the second reading found real gaps in the
specification, at twice the cost (MD-1).

The TypeScript compiler is not kept in estate-kit
([record 13](0013-every-program-is-rust.md)). deploy-kit keeps serving
production until the switch.

## Decision

1. **The Rust compiler implements `spec/v1` at 1.0 and the additive releases
   after it**, chapter by chapter. The specification, schemas, corpus and
   oracles move into estate-kit at the import and are the contract from then
   on. Nothing 1.0 refused is ported.
2. **Language-neutral oracles are met exactly**: the corpus verdicts and diagnostic sets, every
   refusal's code and path, and the expected models compared as parsed JSON.
3. **Rendered files are met in structure, not in bytes.** A test parses each
   1.0 rendered oracle and the Rust output and diffs them object by object
   (TM-2). The Rust compiler writes the canonical render format, and the
   rendered oracles are rewritten once in that format, in a reviewed pull
   request. That rewrite is the one place the format is proved: the pull
   request byte-compares the Rust output with the rewritten oracles. The
   format is specified by [record 64](register.md), which is still Proposed;
   this record cites it for that one rewrite and does not rest on it.
4. **Oracles are never regenerated from an implementation.** This holds for
   the Rust compiler and for any further implementation, in any language: it
   meets the same schemas, corpus verdicts and diagnostic sets, refusal codes and paths, expected
   models and rendered oracles, and nothing else (TM-1). No Rust-only
   expectation enters the oracles.
5. **deploy-kit stops taking new concepts** once the Rust compiler meets every
   oracle of the latest deploy-kit release. Until then, an additive release
   lands in the specification first, with its oracles, and the Rust side
   implements it from there.
6. **The shadow compares parsed structure, and is inert.** For each Project
   the shadow render and the production render are diffed object by object.
   The shadow composition writes only unsigned `shadow/<project>` tags that
   Flux never reads, and an admission check refuses a shadow-prefixed source
   in any Flux object, so the proof has no side effect on production.
7. **The expected-differences ledger is a Locked contract with a closed set
   of causes.** The only differences allowed are those listed in the
   committed ledger, each naming one cause from the closed set: a sealed
   image digest, or a registry tag in place of a pin. The canonical format is
   not a cause, because a structural diff never sees it. An unexplained
   difference, or an entry naming a cause outside the set, stops the switch
   for that Project.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Byte parity with the 1.0 rendered files | A bespoke YAML 1.1 emitter kept forever | The structure is the contract; the bytes are a library's style |
| Test a second implementation against the first's output | Two implementations agreeing with each other's bugs | Oracles are written before the code (TM-1) |
| Keep the canonical format as a ledger cause | Every Project's render differs from production in the same way, so the ledger hides real differences | The structural diff never sees the format; it is proved once, on the oracles |
| Freeze deploy-kit now | Handovers stall until the Rust compiler catches up | Production work is not held back ([review](../research/review/README.md) D1) |
| Cut over on deploy-kit's TypeScript binary as a temporary subprocess | TypeScript stays in the deploy path | The maintainer is not keeping the TypeScript tool |
| Let both stacks evolve indefinitely | Two models kept in step with no end date | deploy-kit takes additive releases for the handovers until the Rust compiler meets its latest oracles; then new concepts land here only |
| Compare the shadow in memory only | The diff cannot be inspected afterwards | Unsigned `shadow/<p>` tags that Flux never reads and admission refuses keep the diff inspectable |

## Consequences

- Easier: the model was rewritten once, in TypeScript, where its tests and
  Stryker setup were; Rust implements a finished, specified model.
- Easier: a further implementation knows exactly what to meet.
- Harder: the cutover proof is structural, so the expected-differences ledger
  must be complete; every Project is reapplied by Flux once for the format;
  every oracle stays language-neutral.
- Forbidden: a new concept in deploy-kit after the stop in point 5; a switch
  with an unexplained structural difference; an oracle written by running an
  implementation and saving its output; a shadow tag Flux can read.

## Confirmation

`oracles/parity` fails when a refusal's code or path differs, when an expected
model differs as JSON, or when a rendered object differs in structure. The
shadow's comparison job fails on a difference missing from
`shadow/expected-differences.yaml`, on a ledger entry no difference uses, and
on an entry whose cause is outside the closed set
([#50](https://github.com/JorisJonkers-dev/estate-kit/issues/50)). The
oracle check refuses an oracle file changed in the same pull request as the
code it tests, unless the pull request is labelled as an oracle review. The
admission check refuses a shadow-prefixed source in any Flux object.

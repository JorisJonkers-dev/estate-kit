---
status: accepted  # proposed | accepted | locked
date: 2026-10-29
rests-on: [3, 5, 6, 13, 42]
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

The TypeScript compiler is not kept in estate-kit
([record 13](0013-every-program-is-rust.md)). deploy-kit keeps serving
production until the switch.

## Decision

1. **The Rust compiler implements `spec/v1` at 1.0 and the additive releases
   after it**, chapter by chapter. The specification, schemas, corpus and
   oracles move into estate-kit at the import and are the contract from then
   on. Nothing 1.0 refused is ported.
2. **Language-neutral oracles are met exactly**: the corpus verdicts, every
   refusal's code and path, and the expected models compared as parsed JSON.
3. **Rendered files are met in structure, not in bytes.** The Rust compiler
   writes the canonical render format ([record 64](register.md)); a test
   parses each 1.0 rendered oracle and the Rust output and diffs them object by
   object (TM-2). The rendered oracles are then rewritten once, in the
   canonical format, in a reviewed pull request.
4. **deploy-kit stops taking new concepts** once the Rust compiler meets every
   oracle of the latest deploy-kit release. Until then, an additive release
   lands in the specification first, with its oracles, and the Rust side
   implements it from there.
5. **The shadow compares parsed structure.** For each Project the shadow
   render and the production render are diffed object by object; the only
   differences allowed are those listed in a committed
   *expected-differences ledger*, each naming its cause (the canonical
   format, a sealed image digest, a registry tag in place of a pin). An
   unexplained difference stops the switch for that Project.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Byte parity with the 1.0 rendered files | A bespoke YAML 1.1 emitter kept forever | The structure is the contract; the bytes are a library's style |
| Freeze deploy-kit now | Handovers stall until the Rust compiler catches up | Production work is not held back ([review](../research/review/README.md) D1) |
| Cut over on deploy-kit's TypeScript binary as a temporary subprocess | TypeScript stays in the deploy path | The maintainer is not keeping the TypeScript tool |

## Consequences

- Easier: the model was rewritten once, in TypeScript, where its tests and
  Stryker setup were; Rust implements a finished, specified model.
- Harder: the cutover proof is structural, so the expected-differences ledger
  must be complete; every Project is reapplied by Flux once for the format.
- Forbidden: a new concept in deploy-kit after the stop in point 4; a switch
  with an unexplained structural difference.

## Confirmation

`oracles/parity` fails when a refusal's code or path differs, when an expected
model differs as JSON, or when a rendered object differs in structure. The
shadow's comparison job fails on a difference missing from
`shadow/expected-differences.yaml`, and on a ledger entry no difference uses
([#50](https://github.com/JorisJonkers-dev/estate-kit/issues/50)).

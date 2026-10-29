---
status: accepted  # proposed | accepted | locked
date: 2026-10-29
rests-on: [3, 5, 6, 13, 50]
lessons: [CS-1, CS-2, CS-3, CS-4, MD-2, MD-3, MD-4, MS-1]
---

# The compiler is a chain of plain-Rust typed steps through one trace, one crate per step, with no DSL

## Context

The compiler is a model-to-model chain ending in model-to-text. The
maintainer's coursework built the same chain in Ecore, OCL, QVT-O and
Acceleo, and deploy-kit built it in TypeScript. Both taught the same lessons:
validate before transforming and report every error with its location (CS-3);
lower shared declarations in a step of their own (CS-4); keep every decision
in the resolved model so renderers only serialise (CS-1); trace every output
to its source (MD-3); and choose an implementation whose coverage and
mutation tools reach the transformation itself (MD-4). They also showed what
the dedicated languages cost: QVT-O was invisible to coverage and mutation,
OCL's cross-document guards passed silently on a lone file, and in-place
passes coupled Projects.

deploy-kit's compiler is a chain of typed models: read, check, lower, compose,
resolve, render through adapters, serialize. Each step is a pure function in
its own module and imports only the model; the use case sequences them, and no
step imports another
([deploy-kit ADR 0056](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/architecture/0056-the-compiler-is-a-chain-of-typed-models.md)).
dependency-cruiser held that rule. Its rejected alternative is a warning: seven
hexagonal rings, of which three rings and three of four declared ports stayed
empty while ledger rows enforced rules over nothing.

In Rust a crate is the unit of compilation, of visibility and of a mutant's
rebuild ([record 50](0050-five-bounded-contexts.md)).
Visibility stops at the crate edge, so a phase type cannot be sealed by a
constructor hidden from other crates without making one step depend on
another. The maintainer wants the lessons without the tools and without a
language of their own.

## Decision

The compiler is a chain of plain-Rust typed steps through one `Trace`, and each
arrow is one crate: `step-read` (read and link), `step-check`, `step-lower`,
`step-compose`, `step-resolve`, `step-outputs`, one `render-*` crate per
adapter of the 1.0 registry, and `serialize`. Each step crate depends only on
the model crates (`model-intent`, `model-effective`, `model-resolved`,
`deliverable`) and the foundation; none depends on another step. The
`compiler` application crate sequences them and is what the CLI and the
service call. Each step is an ordinary function from one typed value to the
next plus diagnostics.

Phase types are markers in the model crates. Constructing the next phase takes
a proof token that only the producing step crate can mint, so a skipped step
is a type error and no step crate needs an edge to another
([Transformations without a DSL](../design/transformations.md)).

The rest of the transformation style follows:

- reading split into read, link and check;
- invariants as entries in a static table, each with a code, a context and an
  explicit scope;
- one named function per source-to-target mapping, called explicitly, in two
  phases (allocate, then populate) through one `Trace`;
- out-place only;
- renderers that build a narrow object model, and one canonical emitter.

The only generic machinery is the `trace` crate, because every mapping needs
it, and `macro_rules!` for newtype boilerplate. There is no rule trait, rule
engine, proc macro or DSL.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| One compiler crate, modules per step | Layering held by `pub(crate)` only; any change rebuilds the whole compiler, and every mutant rebuilds it | Compile and mutation cost |
| Three crates by stage (intent, resolved, deliverable) | Steps inside a stage can import each other | The rule that no step imports another needs the crate boundary |
| Phase constructors hidden inside the producing step crate | The model crate holding the type must depend on the step, or the next step must depend on it | A step-to-step edge, which the layer table forbids |
| A generic step trait and a pipeline engine | Indirection with one implementation per step | [deploy-kit ADR 0056](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/architecture/0056-the-compiler-is-a-chain-of-typed-models.md): a generic waits for two uses |
| Use the MDE tools (Ecore, OCL, QVT-O, Acceleo) | Eclipse, Maven, Tycho and a JDK; transformations invisible to coverage and mutation | The coursework measured both costs |
| A Rust DSL (proc macros for rules and invariants) | A language to design, document and debug; macro errors in place of type errors | The maintainer does not want one, and a function is clearer |
| A `Rule` trait with a reflective transformer (SiTra-style) | Indirection with one implementation per rule | Its authors advise explicit invocation, and a generic waits for two mappings to share machinery |
| Upstream client types in renderers | Every field settable | An adapter could invent a decision ([deploy-kit ADR 0058](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/architecture/0058-every-step-links-through-one-trace.md)) |

## Consequences

- Easier: a change to one rule rebuilds one step crate and its dependents;
  steps can be written in parallel by different hands; coverage, mutation and
  the debugger reach every rule, and a rule is read like any other function.
- Harder: a concept that spans steps changes several crates in one pull
  request; what QVT-O's trace did implicitly is now explicit code, and a
  mapping that bypasses the `Trace` is caught only by the trace-completeness
  test; the proof token is a pattern to follow, not a language feature.
- Forbidden: a dependency from one step crate on another; a step that reads
  anything but its typed input; an in-place pass; a renderer that computes a
  value; a check that aborts on the first problem.

## Confirmation

`cargo xtask check-layers` fails on a dependency between two step crates, with
a failing fixture. A compile-fail test in each step crate fails when the next
phase can be built without the producing step's token. The trace-completeness
test fails on a Deliverable without a source or an authored element that
produced nothing. The invariant-table test fails on a catalogue code without
an invariant or a negative fixture.

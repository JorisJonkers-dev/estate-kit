---
status: accepted  # proposed | accepted | locked
date: 2026-10-29
rests-on: [3, 5, 13, 14, 65]
lessons: [CS-1, CS-2, CS-3, CS-4, MD-2, MD-3, MD-4]
---

# Transformations are plain Rust: typed steps, one trace, an invariant table, and no DSL

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

The maintainer wants those lessons without the tools, and without writing a
language of their own.

## Decision

Transformations are ordinary Rust functions, organised as
[Transformations without a DSL](../design/transformations.md) describes:

- one crate per step, each a function from one typed model to the next plus
  diagnostics ([record 14](register.md));
- reading split into read, link and check, with phase types whose
  constructors are private, so no step can be handed input that skipped one;
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
| Use the MDE tools (Ecore, OCL, QVT-O, Acceleo) | Eclipse, Maven, Tycho and a JDK; transformations invisible to coverage and mutation | The coursework measured both costs |
| A Rust DSL (proc macros for rules and invariants) | A language to design, document and debug; macro errors in place of type errors | The maintainer does not want one, and a function is clearer |
| A `Rule` trait with a reflective transformer (SiTra-style) | Indirection with one implementation per rule | Its authors advise explicit invocation; [deploy-kit ADR 0056](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/architecture/0056-the-compiler-is-a-chain-of-typed-models.md) waits for two mappings to share machinery |
| Upstream client types in renderers | Every field settable | An adapter could invent a decision ([deploy-kit ADR 0058](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/architecture/0058-every-step-links-through-one-trace.md)) |

## Consequences

- Easier: coverage, mutation and the debugger reach every rule; a rule is
  read like any other function.
- Harder: what QVT-O's trace did implicitly is now explicit code; a mapping
  that bypasses the `Trace` is caught only by the trace-completeness test.
- Forbidden: an in-place pass; a renderer that computes a value; a check that
  aborts on the first problem.

## Confirmation

The trace-completeness test fails on a Deliverable without a source or an
authored element that produced nothing. The invariant-table test fails on a
catalogue code without an invariant or a negative fixture. `check-layers`
fails on a dependency from one step crate on another.

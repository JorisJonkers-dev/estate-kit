---
status: accepted  # proposed | accepted | locked
date: 2026-10-30
rests-on: [1]
lessons: [MS-4, CS-1]
---

# Three models: Intent, Resolved Deployment, Deliverable Set

## Context

The estate once ran two layers, with resolution private to the renderer. It
produced three incompatible documents that all claimed the same
`apiVersion`, and the vocabulary could not say which was wrong, because "the
deployment" named all three. Every question about where a field belongs was
argued again in each pull request.

## Decision

Deployment is described in three models, each in its own language and joined to
the next by a transformation. They are not metamodels of one another.

- **Intent** is authored by a person and states requirements only: what the
  Application knows and the platform cannot. It holds no mechanism. Project
  Intent is one per Project; Platform Intent is the estate's.
- **Resolved Deployment** is derived. It records every decision the platform
  made on the author's behalf, including each file's path, and nothing is
  decided after it.
- **Deliverable Set** is the serialised files, and holds no decision. Renderers
  print what the Resolved Deployment says.

Every field belongs to exactly one model, found by two questions: must a human
author it, and does it record a decision or only serialise one. The Resolved
Deployment is a contract with its own schema and version, and the only input a
renderer accepts. The models and their metamodels are on
[Models and metamodels](../design/models-and-metamodels.md).

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Two layers, resolution private to the renderer | Field placement is argued per pull request; rival document shapes accumulate | It produced three rival documents |
| Three layers with the middle one unversioned | The documented shape drifts from the real output with nothing to catch it | A boundary that cannot fail is a preference |
| One model with overrides per object | Every derived value can be hand-set, and the rule is lost | Overrides hide a wrong general rule |

## Consequences

- Easier: a reviewer reads the diff of the Resolved Deployment to see what the
  platform decided; each rule has a place to fail.
- Harder: three schemas to keep, and every new field must choose its model.
- Forbidden: a mechanism in Intent; a decision made while rendering; a renderer
  that reads Intent instead of the Resolved Deployment; a field in two models.

## Confirmation

The committed schemas validate each model, and the compiler's step types let a
renderer take only the Resolved Deployment, so a renderer that reads Intent does
not compile ([record 14](0014-the-compiler-is-a-chain-of-typed-models-one-crate-per-step.md),
[record 15](0015-the-rust-types-agree-with-the-committed-schemas-on-their-corpus.md)).

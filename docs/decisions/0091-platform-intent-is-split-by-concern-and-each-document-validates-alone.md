---
status: proposed  # proposed | accepted | locked
date: 2026-11-04
rests-on: [10, 67, 88, 89]
lessons: [CS-6, MS-1]
---

# Platform Intent is split by concern, and each document validates alone

## Context

Platform Intent is one document in the thin estate repository. It admits the
Projects and holds the estate-wide policy, and it is pushed like any Project
([record 10](0010-platform-intent-admits-the-projects-and-is-pushed-like-any-project.md)).
Its metamodel already falls into concerns: admission and UI roles, policies,
cadences, delivery and jobs, providers with the VPN and GPUs, and libraries
([Models and metamodels](../design/models-and-metamodels.md#platform-intent)).

The architecture evaluation of 2026-11-04 (section 3.5) found two defects in
how it stands:

- it cannot validate alone: it refuses `E_UNKNOWN_MACHINERY` unless other
  Projects' fragments are present, and it names four Projects as
  infrastructure;
- provider behaviour sits in it as model meaning, where
  [record 88](0088-the-metamodel-is-layered-core-profiles-and-component-kinds-provider-facts-estate-instance.md)
  puts Provider facts in a layer of their own.

[deploy-kit ADR 0011](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/model/0011-authored-values-name-model-concepts.md) concedes that swapping the substrate "is a v2 migration
rather than an undo". A command that validates only part of what it carries
lets a broken input through to composition, where it fails late (CS-6). One
concept spread over several places makes every change touch all of them
(MS-1).

The authored schema, `spec/v1` at 1.0, must not change before parity
([record 67](0067-the-compiler-is-written-to-the-1-0-contract.md)). Its major
is the Intent contract's own
([record 89](0089-every-persisted-or-externally-read-contract-has-its-own-identifier-contract-major-and-supported-range.md)).
"How do APIs evolve? A story of refactoring" (2006) found that more than 80% of
the breaking changes in five Java libraries were refactorings, which a tool can
apply; it does not justify a general migration framework for a format with one
estate as its user.

## Decision

After the cutover, Platform Intent is split into documents by concern, and each
document validates alone: `estate-kit validate` on one document, with no
Project fragment and no other document present, reports every problem that
document's own content can cause. A check that needs two documents, or a
document and a fragment, moves to composition, where it is a set-wide refusal
that names both locations
([record 71](0071-a-diagnostic-is-a-coded-problem-with-typed-locations.md)).
No document names a Project as infrastructure; it names what it needs, and
composition finds who provides it. Provider facts leave Platform Intent and
become their own pinned input, as
[record 88](0088-the-metamodel-is-layered-core-profiles-and-component-kinds-provider-facts-estate-instance.md)
says.

The documents still arrive together as Platform Intent, pushed and cached as
[record 10](0010-platform-intent-admits-the-projects-and-is-pushed-like-any-project.md)
says; the admission list stays one document. Each change ships as an additive
1.x release where it can, and the rest as Intent contract major 2 with a
migration tool that previews its edit, checks that every value is preserved,
and refuses where it would have to guess intent. The exact list of documents is
set in the 2.0 specification and is not decided here. This work starts after
the cutover and changes nothing in `spec/v1` 1.0 before parity.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Keep one document that needs the fragments to validate | Every Platform Intent change is checked only at composition | A document that cannot validate alone fails late |
| Split before parity, during the port | The shadow compares against a model that moved | [Record 67](0067-the-compiler-is-written-to-the-1-0-contract.md) holds `spec/v1` 1.0 until parity |
| One document per Project's infrastructure use | Admission and policy spread over many small files | The split is by concern, not by Project |
| Split without a migration tool; the maintainer edits by hand | A mechanical edit done by hand, with no preservation check | Most breaking changes are refactorings a tool can apply |
| A general migration framework for every future major | Machinery for migrations that may never come | Tools are built for actual migrations |
| Validate each document against an embedded snapshot of the others | A snapshot to keep current and digest | Cross-document checks belong in composition |

## Consequences

- Easier: a change to one concern is validated in its own pull request without
  the rest of the estate; a provider move edits Provider facts, not model
  meaning; the second-estate Generality test of
  [record 90](0090-three-generality-tests-run-in-ci.md) becomes possible.
- Harder: some refusals move from validation to composition, so an author
  sees them later; a migration tool to write and test once; the estate
  repository's release workflow publishes several documents.
- Forbidden: a Platform Intent document whose validation reads another
  document or a fragment; a Project named as infrastructure; a change to
  `spec/v1` 1.0 before parity.

## Confirmation

The **Platform Intent standalone validation test** fails when validating one
document of the corpus reads another document or a fragment, or when its
diagnostics differ from the set recorded beside it. The **Platform Intent
migration equivalence test** fails when a 1.x fixture, migrated to 2.0, loses a
value or renders differently in structure from the original. The
**Corpus-agreement test** holds each new document's schema.

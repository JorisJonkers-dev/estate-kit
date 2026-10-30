---
status: accepted  # proposed | accepted | locked
date: 2026-10-29
rests-on: [14]
lessons: [CS-3, MS-9]
---

# A diagnostic is a coded problem with typed, plural locations, and the caller resolves the lines

## Context

A diagnostic today carries one file and one model path, and the CLI resolves
the path to a line at the fragment's source commit. Errors are RFC 9457
problems, and the same catalogue serves the binary and the service. This
record folds two earlier rows into one: row 27 (a diagnostic names a model
path, and the caller resolves the line) and row 44 (errors are RFC 9457
problems drawn from one catalogue). Neither had a file.

The resolve step writes through one `Trace`, and each Deliverable keeps the
model paths it came from ([record 14](0014-the-compiler-is-a-chain-of-typed-models-one-crate-per-step.md)).
Four things that the design already promises cannot be built from a single
location:

1. **Conflicts across Projects have two sides.** A Mailbox, a hostname or a
   Surface claimed twice, or an egress without a matching ingress (MS-9),
   is wrong *in relation to* another declaration, often in another
   repository. The mail page promises a diagnostic "that points at both YAML
   lines"; a one-location `Diagnostic` cannot.
2. **Nobody decides who is told.** A conflict found during composition
   involves two Projects; only one deploy job is waiting.
3. **A positional path is unstable.** `/applications/0/processes/1` changes
   when a list is reordered, so it is a poor name for an element outside the
   run that found it.
4. **Not every cause is authored YAML.** A refusal can rest on Platform Intent
   or a ClusterState fact.

The course material solved these in its own vocabulary
([Transformations without a DSL](../design/transformations.md#traceability-in-both-directions)):
Xtext reports against an object and feature and lets the node model give the
line, and EMF diagnostics carry several objects.

Rendering each field with the element that caused it, and `estate-kit explain`,
were once part of this record. They are a separate, deferred question in
[record 72](0072-per-field-provenance-and-explain-are-deferred.md).

## Decision

1. **A diagnostic is a coded problem.** It has one refusal code from the one
   catalogue, a severity, a message and help, and its locations. The code is
   also the problem+json `type`. The binary and the service draw from the
   same catalogue.
2. **Locations are typed and plural.** A diagnostic has one primary location
   and any number of labelled related locations. A location is authored
   (Project, document, model path), Platform Intent (model path), or a
   ClusterState fact (its key in the snapshot).
3. **Two references, each with one job.** The *model path* is positional
   (RFC 6901) and exists to find a line at a commit. The *element reference*
   is keyed by identity (Project, then Application, Process, and so on, then
   the field) and names an element outside the run that found it. The
   compiler maps one to the other within one run.
4. **The caller resolves lines.** A fragment never carries source positions.
   The binary in CI and the UI resolve a model path to a line at the
   fragment's source commit.
5. **Object-level trace stays.** Each Deliverable keeps the model paths of
   the elements it came from ([record 14](0014-the-compiler-is-a-chain-of-typed-models-one-crate-per-step.md)).
   An error the API server reports on an object is shown against those
   elements as a whole.
6. **One rule decides who is told.** In a conflict across Projects, the
   Project whose fragment changed in this composition is refused, with the
   other side as a related location. If both changed, both are refused. The
   other Project's open rollouts and the UI show the same diagnostic as a
   notice, never as a refusal.

The display rules (multi-span snippets, annotations in the same repository,
pinned links across repositories) are on
[Errors in CI](../design/errors-in-ci.md).

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| One location, the related one mentioned in the message | Free text; CI cannot annotate or link the other side | Conflicts across Projects are the cases that most need both sides |
| Source maps in the fragment | Positions travel with every fragment | A fragment stays free of positions; the caller resolves lines |
| Refuse both Projects in every conflict | A Project that changed nothing is blocked by another's change | The Project that introduced the conflict owns fixing it |
| Per-field provenance now | Every setter takes a source; the trace grows from per object to per field | No scenario needs it yet; deferred in [record 72](0072-per-field-provenance-and-explain-are-deferred.md) |

## Consequences

- Easier: every error lands on a YAML line, and a conflict shows both sides.
- Harder: every diagnostic constructor takes a primary location, and every
  cross-Project code takes a related one.
- Forbidden: a cross-Project diagnostic without its related location; source
  positions inside a fragment.

## Confirmation

- The **Diagnostic fixtures**: a refusal fixture for every cross-Project code asserts the primary and the
  related locations, each with its code and path.
- A negative fixture per code asserts exactly that code at exactly that path.
- The **Location resolution test** resolves a model path to a line at a pinned commit and fails if a
  fragment carries a position.

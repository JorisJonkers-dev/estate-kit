---
status: accepted  # proposed | accepted | locked
date: 2026-10-29
rests-on: [27, 44, 66]
lessons: [CS-3, MD-3, TM-2, MS-9]
---

# Every diagnostic names all its locations, and every rendered field traces back to its source

## Context

A diagnostic today carries one file and one model path, and the CLI resolves
the path to a line at the fragment's source commit ([record 27](register.md)).
The resolve step writes through one `Trace`, and each Deliverable keeps the
model paths it came from ([record 66](0066-transformations-are-plain-rust.md)).
Five things that the design already promises cannot be built from that:

1. **Conflicts across Projects have two sides.** A Mailbox, a hostname or a
   Surface claimed twice, or an egress without a matching ingress (MS-9),
   is wrong *in relation to* another declaration, often in another
   repository. The mail page promises a diagnostic "that points at both YAML
   lines"; the `Diagnostic` type holds one location.
2. **Nobody decides who is told.** A conflict found during composition
   involves two Projects; only one deploy job is waiting.
3. **Errors from the API server cannot reach a line.** A server-side dry-run
   refuses a field of an object (`spec.template.spec.containers[0].securityContext`).
   The trace stops at whole Deliverables, so the best it can name is the
   source element as a whole.
4. **A positional path is unstable.** `/applications/0/processes/1` changes
   when a list is reordered. Used as a trace key or a label on a live object,
   it would change every render and defeat "an unchanged render is not
   published".
5. **Not every cause is authored YAML.** A refusal can rest on Platform Intent
   or a ClusterState fact.

The course material solved each of these, in its own vocabulary
([Transformations without a DSL](../design/transformations.md#traceability-in-both-directions)):
Xtext reports against an object and feature and lets the node model give the
line; EMF diagnostics carry several objects; QVT-O traces inputs to outputs
and resolves both ways (`resolveone`, `invresolve`), but admits that objects
made in helpers or nested expressions get no trace; MOFM2T's trace blocks tie
generated text regions to model elements, and its file blocks use ids derived
from element identifiers so they survive a rename; QVT Relations' check-only
mode verifies two existing models against each other.

## Decision

1. **Locations are typed and plural.** A diagnostic has one primary location
   and any number of labelled related locations. A location is authored
   (Project, document, model path), Platform Intent (model path), or a
   ClusterState fact (its key in the snapshot).
2. **Two references, each with one job.** The *model path* is positional
   (RFC 6901) and exists to find a line at a commit. The *element reference*
   is keyed by identity (Project, then Application, Process, and so on, then
   the field) and is what the trace, provenance and live objects use. The
   compiler maps one to the other within one run.
3. **Every rendered field has a source.** The narrow object model's setters
   take the element reference that caused the value, so each Deliverable
   keeps a map from field path to element reference. This is QVT's "every
   traced object is a mapping output", applied to fields.
4. **The trace is used in both directions.** Backwards, an error on a
   rendered field (dry-run, admission, schema) becomes a diagnostic on the
   authored line that set it. Forwards, `estate-kit explain` lists what a
   line produces, and a plan shows each changed object with the lines that
   changed it. In check-only use, the drift check reports each difference
   between a live object and its render on the source line.
5. **Live objects name their source.** Each rendered object carries an
   annotation with its Project and element reference, never a commit or a
   positional path, so it changes only when the source element does. The
   commit stays where it already is, in the signed render's provenance.
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
| Trace per object only | A dry-run error names an element, not a line | The API server's errors are per field |
| Positional paths everywhere | Reordering a list re-renders and re-publishes every object | Unstable keys break the unchanged-render rule |
| Source maps in the fragment | Positions travel with every fragment | [Record 27](register.md) keeps fragments free of positions |
| Refuse both Projects in every conflict | A Project that changed nothing is blocked by another's change | The Project that introduced the conflict owns fixing it |

## Consequences

- Easier: every error, including the API server's, lands on a YAML line;
  every live object and alert leads back to the element that configured it.
- Harder: every renderer passes a source to every setter; the trace grows
  from per object to per field.
- Forbidden: a rendered field without a source; a commit or a positional path
  on a live object; a cross-Project diagnostic without its related location.

## Confirmation

- A property test over every example renders it and fails on any rendered
  field without an element reference.
- A refusal fixture for every cross-Project code asserts the primary and the
  related locations, each with its code and path.
- A test reorders the lists of an example and fails if any annotation or
  render digest changes.
- A dry-run fixture with a refused field asserts the diagnostic's line.

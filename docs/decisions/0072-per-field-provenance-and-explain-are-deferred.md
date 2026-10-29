---
status: proposed  # proposed | accepted | locked
date: 2026-10-29
rests-on: [66, 71]
lessons: [MD-3, TM-2]
---

# Per-field provenance and `estate-kit explain` are deferred until a scenario needs them

## Context

[Record 71](0071-a-diagnostic-is-a-coded-problem-with-typed-locations.md) once
also asked for provenance on every rendered field, `estate-kit explain`, an
annotation on every live object, and drift reported on the source line. The
[review of 2026-10-29](../research/rust-redesign-review.md) found no scenario
that needs them yet, and found two defects in the design:

- A merged field has several sources, but the map held one element reference
  per field.
- The reorder test is wrong for ordered lists: reordering a list that is
  ordered on purpose changes the render.

## Decision

Deferred. Nothing relies on this record, and no code is written for it until
the maintainer accepts it. If it returns:

1. **Provenance on every setter.** The narrow object model's setters take the
   element reference that caused the value. Each Deliverable keeps a map from
   field path to a non-empty set of element references.
2. **`estate-kit explain`.** `explain <element>` lists what an element
   produces; `explain <file>` lists what produced a file.
3. **Drift on the source line.** The drift check reports each difference
   between a live object and its render on the line of the element that set
   the field.
4. **Live objects name their source.** An annotation carries the Project and
   element reference, never a commit or a positional path.
5. **The reorder property is limited to id-keyed lists.** Reordering such a
   list changes no annotation and no render digest. Lists ordered on purpose
   are outside the property.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Build it with the 1.0 port | Every renderer passes a source to every setter | No scenario needs it yet |
| One element reference per field | A merged field loses all but one source | A field can have several |
| Reorder test over every list | Fails for lists ordered on purpose | The property holds for id-keyed lists only |

## Consequences

- Easier, once built: an API-server error on a field reaches the authored line.
- Harder: every renderer passes a source to every setter.
- Forbidden, once built: a rendered field without a source; a commit or a
  positional path on a live object.

## Confirmation

Once accepted:

- A property test renders every example and fails on any rendered field with
  an empty set of element references.
- A test reorders the id-keyed lists of an example and fails if any annotation
  or render digest changes.
- A dry-run fixture with a refused field asserts the diagnostic's line.

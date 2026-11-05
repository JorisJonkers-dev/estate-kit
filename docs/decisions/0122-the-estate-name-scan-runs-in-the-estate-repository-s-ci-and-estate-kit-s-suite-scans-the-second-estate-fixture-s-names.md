---
status: proposed  # proposed | accepted | locked
date: 2026-11-05
rests-on: [85, 90]
amends: [85, 90]
lessons: [TM-4, MS-7]
---

# The Estate name scan runs in the estate repository's CI, and estate-kit's suite scans the second-estate fixture's names

## Context

[Record 90](0090-three-generality-tests-run-in-ci.md) scans compiler and
schema source for "any of this estate's names", reading its list from this
Estate instance, "so it cannot go stale". That holds the scan, but it puts
this estate's names inside estate-kit's own CI: an estate fact in the very
repository [record 85](0085-general-purpose-means-no-estate-fact-in-the-core-the-profiles-or-the-compiler-s-code.md)
keeps free of estate facts, decided by a job that a change in estate-kit can
switch off. The scan to prove generality must not itself break
[record 85](0085-general-purpose-means-no-estate-fact-in-the-core-the-profiles-or-the-compiler-s-code.md)'s
definition.

The estate repository holds Platform Intent and Infrastructure Intent, so it
already holds the names: the estate name, the Projects and their Product
domains, and the node names. The second-estate fixture, whose names no
compiler or schema source may hold either, is committed in estate-kit. Every
gate needs a negative fixture, or it cannot be shown to fire (TM-4); a second
estate stays behind a seam that costs nothing (MS-7).

The maintainer settled the split on 2026-11-04: the Estate name scan runs in
the estate repository's CI over estate-kit's sources, and estate-kit's own
suite scans only the second-estate fixture's names.

## Decision

The Estate name scan splits by whose names it scans, not by what it does: both
halves read the same scope, compiler and schema source outside fixtures and
oracles, and fail on a scanned name found there.

- **The estate repository's CI scans estate-kit's sources for this estate's
  names.** The list of names is read from Platform Intent and Infrastructure
  Intent in the estate repository, so the list lives with the estate and
  estate-kit holds none of it. Nothing in estate-kit's own CI runs this half.
- **Estate-kit's own suite scans the same sources for the second-estate
  fixture's names only.** The names are the lowest-level names of the
  committed second-estate fixture, and estate-kit's half has its fixture: one
  of those names planted in a corpus file the scan reads fails the scan, and a
  scan corpus without the planted name passes.

This amends [record 85](0085-general-purpose-means-no-estate-fact-in-the-core-the-profiles-or-the-compiler-s-code.md)
so that no estate fact reaches estate-kit even for the checks, and
[record 90](0090-three-generality-tests-run-in-ci.md) so that its third
Generality test scans by where each name lives, not from this Estate instance
inside estate-kit.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Keep the whole scan in estate-kit's CI | This estate's names live in estate-kit's CI: an estate fact where [record 85](0085-general-purpose-means-no-estate-fact-in-the-core-the-profiles-or-the-compiler-s-code.md) forbids one, guarded by a job this repository can switch off | The names live in the estate repository, which scans estate-kit from there |
| Scan nothing in estate-kit's own suite | A leak may pass estate-kit's own suite and only surface in the estate repository's job | The second-estate fixture's names are committed here, so its half answers locally |
| A hand-written list of names, in either place | The list drifts from the estate and from the fixture | Each half reads its names from where they live: Platform Intent and Infrastructure Intent there, the fixture here |
| The estate repository scans nothing | Generality against this estate's real names is tested only while estate-kit's job holds | The estate repository's scan is the half that cannot be disabled from estate-kit |

## Consequences

- Easier: estate-kit's CI proves generality without holding one estate fact;
  the estate-side scan is on the same side as the names it scans.
- Harder: two jobs instead of one, and the estate repository's job checks out
  estate-kit's sources to scan them.
- Forbidden: this estate's names inside estate-kit's CI, in its sources, or
  on a hand-written list; a leaked name in compiler or schema source outside
  fixtures and oracles, in either half's scope.

## Confirmation

The **Estate name scan** has two halves: the estate repository's CI scans
estate-kit's compiler and schema source for this estate's names read from
Platform Intent and Infrastructure Intent, and estate-kit's suite scans the
same source for the second-estate fixture's names, with one name planted in a
corpus file as its failing fixture. The **Second-estate fixture test** keeps
the fixture whose names estate-kit's half scans.

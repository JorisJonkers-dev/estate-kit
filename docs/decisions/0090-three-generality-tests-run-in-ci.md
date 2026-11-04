---
status: proposed  # proposed | accepted | locked
date: 2026-11-04
rests-on: [1, 85, 88]
lessons: [TM-4, MS-7]
---

# Three Generality tests run in CI

## Context

[Record 85](register.md) sets what general purpose means: no estate fact in
the core, the profiles or the compiler's code, so another estate with one
maintainer and one cluster could run estate-kit with its own data.
[Record 88](0088-the-metamodel-is-layered-core-profiles-and-component-kinds-provider-facts-estate-instance.md)
gives the facts their places: the core, profiles and Component kinds, Provider
facts and the Estate instance. Neither holds unless something fails when a fact
lands in the wrong place.

The design review's scenario S13 asks that a new kind of thing to deliver, as
Mailboxes were, be added in the model and one adapter, without touching
Delivery or the applier
([scenarios](../research/review/scenarios.md)). The NixOS host target already
exists beside Kubernetes: host data is rendered from Infrastructure Intent
([record 12](0012-infrastructure-intent-declares-sites-nodes-and-maintenance-windows.md)).
[Record 1](0001-one-maintainer-one-cluster-one-estate.md) forbids designing for
a second cluster or a target nobody runs, so no invented second Kubernetes-like
Profile is a fair test.

The architecture evaluation of 2026-11-04 (sections 4.7 and 12.6) weighed three
tests and kept all three, because each catches a different leak: a kind that
needs the core changed, a Kubernetes word in the core, and an estate name in
the compiler. Its migration plan holds the core check from the first model
code and all three by the end of the generality work after the cutover
(section 11.4, M1 and M10). Every gate needs a negative fixture, or it cannot
be shown to fire (TM-4).

## Decision

Three Generality tests run in CI, each a fixture inside the workspace.

1. **A Component kind from existing capabilities.** A fixture adds a `queue`
   Component kind built only from capabilities that exist: a Surface, a Volume
   and a Grant. It is declared through the `kind` seam alone, and the test fails
   if it cannot be expressed, validated and resolved without a change to
   `core`, `step-check` or `step-resolve`. A kind that brings a new capability
   is outside this test by design: it is a model change with its own checks,
   because [record 5](0005-derivation-is-total.md)'s total derivation must hold.
2. **The NixOS target.** Host data is rendered from the same Resolved
   Deployment through the NixOS Profile, and the test fails if that path uses
   anything from the Kubernetes Profile. With
   [record 88](0088-the-metamodel-is-layered-core-profiles-and-component-kinds-provider-facts-estate-instance.md)'s
   core neutrality check, it shows the core is not Kubernetes in disguise.
3. **A second estate.** A fixture estate with other names, addresses and
   Provider facts validates and renders with no change to compiler or schema
   source. A scan fails on any of this estate's names in compiler or schema
   source; the list of names is read from this Estate instance (nodes,
   Projects, domains, the estate name), so it cannot go stale.

The core neutrality check runs from the first model code. Tests 1 and 2 run
from the release in which `kind` and the NixOS Profile exist. Test 3 and its
scan run from the release in which Provider facts are a pinned input
([record 91](0091-platform-intent-is-split-by-concern-and-each-document-validates-alone.md)),
because a second estate cannot differ in its providers before then. The scan
reads compiler and schema source only, never fixtures or oracles. Each test
keeps a negative fixture that breaks it on purpose.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| No test; general purpose as a review rule | The first rushed change puts an estate name in the compiler | A rule with no check is not kept |
| Capability-specific tests only | An estate name in compiler code passes | Each test catches a different leak; the evaluation kept all three |
| An invented second Kubernetes-like Profile | A target designed for nobody, kept forever | [Record 1](0001-one-maintainer-one-cluster-one-estate.md) refuses it; NixOS is a real second target |
| A second real estate or cluster in CI | Infrastructure for a user who does not exist | A fixture estate tests the same property offline |
| A grep for "Kubernetes" over the whole workspace | Fails on every renderer and Profile, which must name their target | The word is wrong only in `core` |
| A hand-kept list of forbidden estate names | The list drifts from the estate | The names are read from the Estate instance |

## Consequences

- Easier: a new Component kind, a provider move or a second installation is
  shown to be data before anyone relies on it; S13 has a test.
- Harder: three fixtures to keep green while the model moves, and a fixture
  estate to keep realistic; a renamed node or domain must not appear in
  compiler source even as a test value outside fixtures.
- Forbidden: this estate's names in compiler or schema source; a Component kind
  built from existing capabilities that changes `core`, `step-check` or
  `step-resolve`; the NixOS path depending on the Kubernetes Profile.

## Confirmation

The **Component kind generality test**, the **NixOS profile generality test**
and the **Second-estate fixture test** are the three tests, each with its
negative fixture. The **Estate name scan** fails on this estate's names in
compiler or schema source. The **Core neutrality check** of
[record 88](0088-the-metamodel-is-layered-core-profiles-and-component-kinds-provider-facts-estate-instance.md)
runs beside them.

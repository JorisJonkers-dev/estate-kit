---
status: proposed  # proposed | accepted | locked
date: 2026-11-04
rests-on: [1]
lessons: [MS-7]
---

# General purpose means no estate fact in the core, the profiles or the compiler's code

## Context

The maintainer asks for estate-kit to be general purpose rather than built for
this estate. The repository does not state that as a goal, and
[record 1](0001-one-maintainer-one-cluster-one-estate.md) forbids designing for
a second cluster, a second operator, or an input that selects among clusters.
Read loosely, the two pull apart: "general purpose" can mean several clusters,
several teams, a plugin interface or a product other people install.

The architecture evaluation of 2026-11-04 (sections 2.4 and 4.1) finds the
model specific in three ways:

- **Substrate.** Tier, listener, `proxiedBy`, L4 addresses, node agents,
  priority classes and mesh enrolment are Kubernetes and k3s concepts wearing
  model words.
- **Provider.** Cloudflare's 100-second idle close drives `proxied: false`;
  `CF-Connecting-IP` drives `proxiedBy`; GitHub Deployments are the Rollout's
  record; ghcr's token model shapes
  [record 9](0009-the-live-render-is-a-signed-registry-tag-per-project-and-environment.md).
- **Estate.** Node names, host paths, gids, CIDRs, OIDC groups, backup
  addresses and the seven-day staleness bound. These belong in the Estate
  instance, pinned and reviewed.

The evaluation reads the first two as defects and the third as how an instance
should look. The defects it names are mistakes this maintainer has made: a
provider limit hidden in compiler code, a document that cannot validate alone,
and an estate name the compiler expects. While they stay, moving to another
provider or forge is a code change. The evaluation marks this reading as
judgement.

`CONTEXT.md` already holds the words for the layers: Model layer, Profile,
Component kind, Provider facts and Estate instance, and the Generality test.

## Decision

In estate-kit, **general purpose** means this: no fact about this estate lives
in the core, the Profiles, the Component kinds or the compiler's code and
schema meaning. Every estate fact is Estate instance data or pinned Provider
facts. So another estate with one maintainer and one cluster could run
estate-kit on its own data without forking the core. An address in pinned
Platform Intent is instance data and belongs there; an address, a provider's
behaviour or a Project name inside compiler code or schema meaning is the
defect.

It does not mean several clusters, several operators or teams, a plugin
interface, or a product supported for others. This amends the wording of
[record 1](0001-one-maintainer-one-cluster-one-estate.md), not its premise:
each installation of estate-kit serves one maintainer, one production cluster
and one estate, and the code holds no fact about which estate that is. That
record's refusal of a second cluster, its ban on team boundaries and its
horizon review stand unchanged, and its sentence is rewritten when this record
is accepted. The Generality tests hold the definition.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Portable within one estate only (the evaluation's first version) | Provider behaviour and estate names may stay in compiler code as long as this estate's data moves | It does not catch the mistakes named above, and the maintainer asks for more |
| No estate facts anywhere, instance data included | Addresses, nodes and groups would need a second home outside pinned, reviewed Intent | Instance data is where an estate fact belongs |
| Several clusters or several estates in one installation | A cluster axis in Intent, rendering and rollout | [Record 1](0001-one-maintainer-one-cluster-one-estate.md) refuses it; nothing on this estate needs it |
| A plugin interface for kinds and targets | A stable binary interface to design, version and test | No second implementation exists to justify the seam |
| Leave the word undefined | Each design question reopens what general purpose means | The scope argument comes back on every record |

## Consequences

- Easier: a change of provider or forge becomes data, not code; a reviewer can
  point at a named fact in compiler code and call it a defect; Platform Intent
  can be tested with a second estate's fixture.
- Harder: provider behaviour that is now a model field must move to Provider
  facts read through ports, and compiler code must take every estate fact as
  input, which is more plumbing during the port.
- Forbidden: a name of this estate's nodes, Projects, domains, groups or
  addresses in compiler or schema source; a provider's behaviour encoded as
  schema meaning; a second cluster, a second operator or a plugin interface
  justified by "general purpose".

## Confirmation

The Generality tests hold this definition. The **Core neutrality check**
fails on a target or provider word in the core. The **Component kind
generality test** fails when a kind built only from existing capabilities
changes a core module. The **NixOS profile generality test** fails when the
NixOS Profile needs a Kubernetes word in the core. The **Second-estate fixture
test** fails when a second estate's fixture does not validate and render
without a change to compiler code, and the **Estate name scan** fails on any of
this estate's names in compiler or schema source. The **Single-cluster fixture** keeps
the one-cluster half of the amended wording. Whether a new concept names the
maintainer mistake it prevents stays a review rule, as in
[record 1](0001-one-maintainer-one-cluster-one-estate.md).

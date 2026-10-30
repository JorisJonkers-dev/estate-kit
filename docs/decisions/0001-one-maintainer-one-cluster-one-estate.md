---
status: accepted  # proposed | accepted | locked
date: 2026-10-30
rests-on: []
lessons: [MS-7]
---

# One maintainer, one cluster, one estate

## Context

The estate is run by one regular human maintainer, on one production cluster,
and holds about thirty Applications in about ten repositories. Every other
author in the estate's repositories is a bot account. The design review of
2026-10-22 found that the earlier design was scaled for an organisation and an
estate that do not exist ([review](../research/review/README.md)), and it cut
what only a team would need.

The scale is a fact about today. It can stop being true, and then decisions that
rest on it need rereading.

## Decision

estate-kit is built for one maintainer, one production cluster and one estate
of about thirty Applications. Each concept, check and ledger stays only if it
catches a mistake that maintainer can make on that estate. A job done once is a
one-off tool, not a permanent rule in the model.

The single cluster is explicit rather than implied: an input that names a second
cluster is refused, so a later extension stays possible but is not designed for.
There is no second tenant, no per-team boundary and no second production
cluster. The premise is reviewed at the horizon of 2028-08-31, or earlier if a
second regular human maintainer or a second production cluster appears.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Design for a team and several clusters | Tenancy, per-team policy and a cluster dimension in every model, paid by one person | None of it catches a mistake on the real estate |
| Leave the scale unstated | Each design question reopens the scale argument | The review's largest root cause was a design scaled to an estate that does not exist |
| A second cluster as a first-class target | A cluster axis in Intent, rendering and rollout | One cluster serves the estate; a seam that costs nothing keeps the door open |

## Consequences

- Easier: every later record can drop machinery that only scale would need, and
  say so by citing this one.
- Harder: a second maintainer or cluster is a redesign of the records that rest
  on this, not a configuration change.
- Forbidden: a model concept, gate or ledger whose only justification is a team,
  a second tenant or a second cluster; an input that selects among clusters.

## Confirmation

A review rule, held by the pull request template: a new concept names the
maintainer mistake it prevents. The compiler refuses a cluster name other than
the estate's one, with a refusing fixture, once the Platform Intent model lands
([record 3](0003-three-models-intent-resolved-deployment-deliverable-set.md)).
The horizon review is the issue that re-counts maintainers and clusters on
2028-08-31.

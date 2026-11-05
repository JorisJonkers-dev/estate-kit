---
status: accepted  # proposed | accepted | locked
date: 2026-11-01
rests-on: [1, 9]
amends: [9]
lessons: [MS-7, MS-4, DO-1]
---

# Three environments run in the one cluster, with a signed tag and a namespace per Project per environment

Amended by [record 132](0132-a-staging-rollout-that-ended-refused-held-on-a-failed-verdict-or-observation-lost-blocks-its-release-s-production-approval-and-a-quiet-held-does-not.md): a staging Rollout that ended Refused, Held on a failed Analysis verdict or Observation lost blocks its release's `production` approval until the maintainer confirms it served, and a quiet Project's Held blocks nothing.

## Context

[Record 9](0009-the-live-render-is-a-signed-registry-tag-per-project-and-environment.md)
gives each Project one signed tag per environment, and names `prod` as the only
environment. [Record 1](0001-one-maintainer-one-cluster-one-estate.md) keeps
the estate to one cluster. The estate now needs a place to try a change before
production, and a place that follows `main`, without a second cluster to run.

The vocabulary already names three Environments: development, staging and
production, lettered `d`, `s` and `p`. Each has its own identity, its own
Tenants and its own data.

## Decision

Development, staging and production run in the one cluster. This amends
[record 9](0009-the-live-render-is-a-signed-registry-tag-per-project-and-environment.md):
the live render of a Project in an Environment is its Environment tag, the
signed tag `render/<project>:<env>`, one per Environment, no longer the Prod tag
alone.

A Project in an Environment has its own namespace, `<project>-<env letter>`:
`-d`, `-s` and `-p`. Production moves once, by a planned migration, from `<project>-system` to `<project>-p`.

A merge to `main` deploys a build of `main` to development. A published
release deploys to staging, then to production after the `production` approval,
with the same digests in both. Nothing is rebuilt between staging and
production.

The staging Rollout of a release gates that release's `production` approval:
a staging Rollout that ended Refused, Held on a failed
[Analysis verdict](../../CONTEXT.md), or Observation lost blocks the approval
until the maintainer confirms the staging Application served the release,
while a staging Rollout Held on an inconclusive verdict, on a Project too
quiet to gather a sample, blocks nothing
([record 132](0132-a-staging-rollout-that-ended-refused-held-on-a-failed-verdict-or-observation-lost-blocks-its-release-s-production-approval-and-a-quiet-held-does-not.md)).

A Project chooses its Environments, and production is required. Between
Environments only replicas, domains and secret paths may differ, plus one env
file per Environment. Any other override is refused.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Production only, one environment name forever | A change meets real data first; no place to rehearse a migration | Production is the only test of a release |
| A second cluster per environment | A second control plane to run and keep current | One maintainer, one cluster ([record 1](0001-one-maintainer-one-cluster-one-estate.md)) |
| One namespace per Project, a label per environment | A policy or a query that forgets the label crosses environments | A namespace is the boundary the cluster enforces |
| A rebuild per environment | Staging does not prove the digest production runs | The same digests must reach production |
| Free overrides per environment | Environments drift apart until staging proves nothing | The compiler derives mechanism; authors do not override it |
| Production optional | A Project can ship with nothing live | A Project that never reaches production is not delivered |

## Consequences

- Easier: a change and a migration are rehearsed in development and staging
  before production; a Rollback names the environment it moves; a staging end
  that did not serve blocks the same release's `production` approval until the
  maintainer confirms it served.
- Harder: three renders and three namespaces per Project, and a planned move of
  production out of `<project>-system`.
- [Record 9](0009-the-live-render-is-a-signed-registry-tag-per-project-and-environment.md) is amended: a Project has an Environment tag in each of its Environments.
- Forbidden: an override beyond replicas, domains, secret paths and the env
  file; a Project without production; staging and production running different digests for one release.

## Confirmation

The **Environment override refusal** refuses any per-environment override beyond
replicas, domains, secret paths and the env file. The **Production required
check** fails a Project that does not declare production. The **Promotion digest
test** fails when staging and production run different digests for one release,
in the **E2E scenarios**
([record 69](0069-the-deploy-path-is-tested-end-to-end.md)).

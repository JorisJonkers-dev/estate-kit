---
status: proposed  # proposed | accepted | locked
date: 2026-10-29
rests-on: [10, 17]
lessons: [DR-1, DR-2, TM-4]
---

# Every caller authenticates with an OIDC token checked against a claim policy

## Context

A Project's CI asks the service to deploy. The first design trusted the token's
repository and a workflow named by a movable ref, and ignored `event_name`, so a
`pull_request_target` run could pass as a release
([review](../research/review/README.md) D8). People use the UI, and GitHub's
claims behave differently under reusable workflows and environments
(spike #11).

## Decision

- **CI calls with a GitHub Actions OIDC token**, audience `estate-kit`, checked
  against one claim policy: `repository_id` and `repository_owner_id` match the
  Project's admission; `job_workflow_sha` is the pinned estate-kit reusable
  workflow; `event_name` is on an allowlist; a deploy needs `ref_type` tag, a
  GitHub-hosted runner and the `production` environment; a pull request may only
  plan or dry-run. `sub` is never used.
- **A deploy job exchanges its token once** for a service-issued token scoped
  to one Project and one rollout, read-only on the stream, so a long rollout
  outlives the GitHub token.
- **People sign in through identity**; group claims map to viewer, operator or
  admin in Platform Intent.
- **Callers that cannot send a token can change nothing.** Flagger's gate
  webhook and Flux get answers computed from cluster state only.

The table of callers is [Identity and access](../design/identity-and-access.md).

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Trust the repository name | A recreated repository with the old name takes the Project over | `repository_id` survives renames; names do not |
| Pin the workflow by ref | A moved tag runs other code with the same claim | `job_workflow_sha` |
| A shared secret per Project | Long-lived secrets in every repository | OIDC needs none |

## Consequences

- Easier: no Project holds a credential for the service.
- Harder: the claim policy is a contract with GitHub's token format, settled by
  spike #11.
- Forbidden: authorising by `sub`; a deploy from a pull request.

## Confirmation

The claim policy has a pass and a fail token fixture for every rule; the
suite fails if a rule has no failing fixture.

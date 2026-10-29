---
status: proposed  # proposed | accepted | locked
date: 2026-10-29
rests-on: [6, 10, 17, 26]
lessons: [CS-5, DR-1, DR-2, TM-4]
---

# A Project's CI proves itself with a pinned-workflow OIDC token, and the service deploys only images its own build registered

## Context

A Project's CI asks the service to deploy. The first design trusted the token's
repository and a workflow named by a movable ref, and ignored `event_name`, so a
`pull_request_target` run could pass as a release
([review](../research/review/README.md) D8). Nothing checked where a sealed
image digest came from either: a fragment could name any digest, and the service
would sign a render that ran it (D8). Image digests used to live in
`images.lock.yml` in the estate repository, apart from the Projects they belong
to, and a render must name every image by digest to be a function of pinned
inputs ([record 6](register.md)). Images are built once and promoted
([record 26](register.md)).

A deploy job also waits on a rollout that can outlast a GitHub OIDC token, and
the service can restart under it (Recreate,
[record 63](0063-the-service-has-one-writer-and-reconciles-from-observed-state.md)).
Whether a waiting job can request a fresh GitHub token is not known: spike #11
settles it.

## Decision

- **CI calls with a GitHub Actions OIDC token**, audience `estate-kit`, checked
  against one claim policy. The policy matches `repository_id` and
  `job_workflow_sha` (the pinned estate-kit reusable workflow) and never `sub`.
  The claims and the rule on each are listed on
  [Identity and access](../design/identity-and-access.md#the-claim-policy).
- **The digest travels with the fragment.** The release's deploy job seals each
  Application's image digests into the Intent Fragment it publishes; no lock
  file exists outside the Project.
- **The build registers what it built.** The build job and the deploy job are
  split. After the build job pushes its images, an attest step calls an
  OIDC-authenticated route on the service that records each digest against the
  Project's `repository_id` and the run, in the event log.
- **The service refuses the rest.** Before composing, the service checks that
  every digest in the fragment was registered by that Project's own build, or
  is on Platform Intent's allowlist of third-party images. Anything else is a
  refusal with the image's location in the fragment.
- **The rollout token exchange is deferred.** A service-minted token, scoped to
  one Project and one rollout and read-only on the stream, is not built until
  spike #11 shows whether a deploy job can request a fresh GitHub OIDC token
  while it waits. Meanwhile the deploy job re-requests a GitHub OIDC token
  whenever it needs one and presents it to the stream; the claim policy checks
  it as on any call.
- **A waiting deploy job keeps authenticating across a service upgrade.** The
  service's Deployment is `Recreate`, so the stream drops while the pod is
  replaced. The job re-requests a GitHub OIDC token, reconnects, and resumes the
  stream by sequence ([record 23](0023-a-rollout-is-an-append-only-event-log-on-the-shared-postgres.md)).
  No token state lives in the service, so nothing is lost by the restart.
- **People sign in through identity**; group claims map to viewer, operator or
  admin in Platform Intent.
- **Callers that cannot send a token can change nothing.** Flagger's gate
  webhook and Flux get answers computed from cluster state only.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Exchange the token once for a service-minted rollout token now | A token store or signing key whose survival across an upgrade must also be designed, for a need spike #11 may remove | Deferred until the spike shows whether a fresh GitHub token can be had while waiting |
| Trust the repository name | A recreated repository with the old name takes the Project over | `repository_id` survives renames; names do not |
| Pin the workflow by ref | A moved tag runs other code with the same claim | `job_workflow_sha` |
| A shared secret per Project | Long-lived secrets in every repository | OIDC needs none |
| GitHub artifact attestations, verified with sigstore | A sigstore verifier and a TUF fetch on the deploy path | Heavier than the problem; a later upgrade, not a blocker |
| Claim policy only | Any admitted Project's CI can seal any digest | The provenance gap D8 named |
| Keep the estate's images lock | A central list outside the Projects | Each Project's state lives with the Project ([record 7](register.md)) |

## Consequences

- Easier: no Project holds a credential for the service; what runs can be
  traced to the build that produced it, and the event log is the record; a
  service upgrade needs no token handover.
- Harder: the claim policy is a contract with GitHub's token format, settled by
  spike #11 (open claim: a job can request a fresh token while it waits; owner:
  the maintainer; the exchange is built only if the spike says it cannot);
  every Project's workflow has a separate build and attest step.
- Forbidden: authorising by `sub`; a deploy from a pull request; a render
  naming a digest that is neither registered by its Project nor allowlisted.

## Confirmation

The claim policy has a pass and a fail token fixture for every rule; the suite
fails if a rule has no failing fixture. A service test composes a fragment with
an unregistered digest and asserts the refusal and its location. The e2e suite
registers, deploys, and then tries the same digest from another Project; its
"service upgraded mid-rollout" scenario replaces the service pod while a deploy
job waits and asserts the job re-authenticates and resumes by sequence
([record 69](0069-the-deploy-path-is-tested-end-to-end.md)).

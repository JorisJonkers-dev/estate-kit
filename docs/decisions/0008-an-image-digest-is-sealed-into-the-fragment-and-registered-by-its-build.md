---
status: accepted  # proposed | accepted | locked
date: 2026-11-04
rests-on: [6, 10, 17, 25, 68]
lessons: [CS-5, DR-1, DR-2, TM-4]
---

# A Project's CI proves itself with a pinned-workflow OIDC token from an admitted issuer, and Delivery deploys only images its own build registered

## Context

A Project's CI asks Delivery to deploy. The first design trusted the token's
repository and a workflow named by a movable ref, and ignored `event_name`, so a
`pull_request_target` run could pass as a release
([review](../research/review/README.md) D8). Nothing checked where a sealed
image digest came from either: a fragment could name any digest, and Delivery
would sign a render that ran it (D8). Image digests used to live in
`images.lock.yml` in the estate repository, apart from the Projects they belong
to, and a render must name every image by digest to be a function of pinned
inputs ([record 6](register.md)). Images are built once and promoted
([record 25](0025-a-dry-run-must-pass-before-anything-is-applied-and-what-dry-ran-is-what-deploys.md)).

A deploy job also waits on a rollout that can outlast a GitHub OIDC token, and
Delivery can restart under it (Recreate,
[record 63](0063-delivery-has-one-writer-and-reconciles-from-observed-state.md)).
Whether a waiting job can request a fresh GitHub token is not known: spike #11
settles it.

GitHub is load-bearing in five places (OIDC identity, Deployments, check runs,
workflow dispatch and release-please), none behind a port. The five are not
equal: CI identity is a security boundary, the status shown on the forge is
cosmetic, and finding a release is cheap (the architecture evaluation of
2026-11-04, sections 3.21 and 5). Self-hosted forges are a normal shape ("The
penumbra of open source", 2022; "Federated software forges with Forgejo",
2025). The maintainer intends to depend less on GitHub: likely Tangled once it
has private repositories, or a self-hosted Forgejo behind a VPN with sign-in
at Traefik.

## Decision

- **Delivery reaches a forge through three Forge ports.** CI identity verifies
  a caller's OIDC token against the claim policy. Rollout projection shows each
  Operation's state on the forge; the event log stays the authority, and a
  failed projection never fails a Rollout. Release source reads a merged
  revision and dispatches a run. GitHub is the first adapter of each: CI
  identity in `adapter-oidc` (renamed from `adapter-github-oidc`), the other
  two in `adapter-forge-github` (renamed from `adapter-github`). The design
  pages use these names. A second adapter is written
  only when a forge move is planned.
- **CI calls with an OIDC token from an admitted issuer**, audience
  `estate-kit`, checked against one claim policy. The policy is scoped by
  issuer: each issuer Platform Intent admits has its own rules, and a token
  is checked only against its own issuer's. Every issuer's rules must state
  the repository's stable id, the pinned estate-kit reusable workflow's commit
  and the event. A forge whose CI cannot issue OIDC tokens that state all
  three is not admitted, and there is no fallback to a long-lived token for
  it. The first issuer is GitHub Actions, where the rules match
  `repository_id` and `job_workflow_sha` and never `sub`. The claims and the
  rule on each are listed on
  [Identity and access](../design/identity-and-access.md#the-claim-policy).
- **The digest travels with the fragment.** The release's deploy job seals each
  Application's image digests into the Intent Fragment it publishes; no lock
  file exists outside the Project.
- **The build registers what it built.** The build job and the deploy job are
  split. After the build job pushes its images, an attest step calls an
  OIDC-authenticated route on Delivery that records each digest against the
  Project's repository id, its issuer and the run, in the event log.
- **Delivery refuses the rest.** Before composing, Delivery checks that
  every digest in the fragment was registered by that Project's own build, or
  is on Platform Intent's allowlist of third-party images. Anything else is a
  refusal with the image's location in the fragment.
- **The rollout token exchange is deferred.** A Delivery-minted token, scoped to
  one Project and one rollout and read-only on the stream, is not built until
  spike #11 shows whether a deploy job can request a fresh GitHub OIDC token
  while it waits. Meanwhile the deploy job re-requests an OIDC token
  whenever it needs one and presents it to the stream; the claim policy checks
  it as on any call.
- **A waiting deploy job keeps authenticating across a Delivery upgrade.** Delivery's Deployment is `Recreate`, so the stream drops while the pod is
  replaced. The job re-requests an OIDC token, reconnects, and resumes the
  stream by sequence ([record 23](0023-a-rollout-is-an-append-only-event-log-on-the-shared-postgres.md)).
  No token state lives in Delivery, so nothing is lost by the restart.
- **People sign in through identity**; group claims map to viewer, operator or
  admin in Platform Intent.
- **Callers that cannot send a token can change nothing.** Flagger's gate
  webhook and Flux get answers computed from cluster state only.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Exchange the token once for a Delivery-minted rollout token now | A token store or signing key whose survival across an upgrade must also be designed, for a need spike #11 may remove | Deferred until the spike shows whether a fresh GitHub token can be had while waiting |
| Trust the repository name | A recreated repository with the old name takes the Project over | `repository_id` survives renames; names do not |
| Pin the workflow by ref | A moved tag runs other code with the same claim | `job_workflow_sha` |
| A shared secret per Project | Long-lived secrets in every repository | OIDC needs none |
| A long-lived token for a forge whose CI cannot issue such an OIDC token | A secret that outlives every run, for the forge least able to protect it | Such a forge is not admitted; no fallback |
| GitHub artifact attestations, verified with sigstore | A sigstore verifier and a TUF fetch on the deploy path | Heavier than the problem; a later upgrade, not a blocker |
| Claim policy only | Any admitted Project's CI can seal any digest | The provenance gap D8 named |
| Keep the estate's images lock | A central list outside the Projects | Each Project's state lives with the Project ([record 7](register.md)) |
| A digest in the Project file, or a lock block in it | Authors edit what a build should fix, and nothing proves the build made it | The digest is sealed into the fragment and registered by its build |
| GitHub wired into Delivery with no port | A forge move rewrites Delivery's core | The maintainer intends to move; the ports cost little now |
| One broad Forge port | A security boundary and a cosmetic status share one contract, and a second forge must implement all of it | The three differ in risk and in how a second forge meets them |
| One claim policy for every issuer | A token from one issuer can pass on another's rules | Claims mean different things per issuer |
| A second adapter now (Forgejo), or ForgeFed | Code and fixtures for a forge not yet chosen | Written when a move is planned |

## Consequences

- Easier: no Project holds a credential for Delivery; what runs can be
  traced to the build that produced it, and the event log is the record; a
  Delivery upgrade needs no token handover; a forge move adds adapters and an
  issuer, and leaves Delivery's core alone.
- Harder: the claim policy is a contract with each issuer's token format,
  settled for GitHub by spike #11 (open claim: a job can request a fresh token
  while it waits; owner: the maintainer; the exchange is built only if the
  spike says it cannot); a forge whose CI cannot issue such a token cannot
  deploy; every Project's workflow has a separate build and attest step.
- Forbidden: authorising by `sub`; a deploy from a pull request; a
  long-lived token in place of an OIDC token; admitting an issuer whose
  tokens cannot state the repository's stable id, the pinned workflow's
  commit and the event; a render
  naming a digest that is neither registered by its Project nor allowlisted;
  a token checked against another issuer's rules; a forge name in Delivery's
  domain or application crates.

## Confirmation

The **Claim-policy fixtures** hold a pass and a fail token fixture for every
rule of every admitted issuer, including a token from one issuer presented
under another's rules; the suite fails if a rule has no failing fixture, if
Platform Intent admits an issuer whose rules do not state all three claims, or
if a call with a long-lived token is accepted. The
**Digest registration test** composes a fragment with an unregistered digest
and asserts the refusal and its location. The **Port contract script** fails
if a Forge port lacks its fake or its contract suite, and
**`cargo xtask check-layers`** fails if Delivery's domain or application
crates depend on a forge adapter. The **E2E scenarios** register, deploy, and
then try the same digest from another Project; the "Delivery upgraded
mid-rollout" scenario replaces Delivery pod while a deploy job waits and
asserts the job re-authenticates and resumes by sequence
([record 69](0069-the-deploy-path-is-tested-end-to-end.md)).

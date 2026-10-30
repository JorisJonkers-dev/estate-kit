---
status: accepted  # proposed | accepted | locked
date: 2026-10-30
rests-on: [6, 9]
lessons: [DR-1]
---

# A dry-run must pass before anything is applied, and images are built once and promoted, so what dry-ran is what deploys

## Context

Offline checks catch model errors but not what only the API server knows:
admission webhooks, CRD schemas, immutable fields, quota and field conflicts.
The estate can also change between a release pull request merging and its
deploy running, so one early check is not enough.

A dry-run proves a render only if the render it checked is the one that ships.
If the release rebuilt its images, the digests that dry-ran would not be the
digests that deploy, and a render must name every image by digest to be a
function of pinned inputs ([record 6](register.md)). The signed tag that makes
a render live ([record 9](0009-the-live-render-is-a-signed-registry-tag-per-project-and-environment.md))
must only move for a render that has passed.

## Decision

Nothing is signed, tagged or applied unless the service's dry-run passed. The
service composes, then sends every changed object to the live API server with
`dryRun=All`, and a dry-run must pass twice: on the release pull request, and
again right before any tag moves.

Images are built once and promoted. The release pull request's build job builds
candidate images by digest and registers them; the release promotes those same
digests and never rebuilds. A dry-run is the `deploy` workflow with
`dry-run: true`, identical except that nothing is signed, tagged or applied, and
it leaves no Deployment record, so production history holds real deploys only
([Releasing](../design/releasing.md#what-a-dry-run-is)).

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Offline schema checks only | Webhooks, immutable fields and quota fail at apply time, in production | The server-side dry-run catches them |
| Dry-run once, on the release pull request | The estate can change between merge and deploy | A second dry-run before each tag move closes the gap |
| Rebuild images at release | The digests that dry-ran are not the digests that deploy | What dry-ran must be what deploys |
| A dry-run environment with its own Deployment record | Production history mixes real and rehearsed deploys | A dry-run records no Deployment |

## Consequences

- Easier: a failed dry-run blocks the merge and the tag move, and a release
  deploys the artifact that was checked.
- Harder: every release pull request builds images and needs the cluster
  reachable for the dry-run.
- Forbidden: moving a tag without a dry-run that passed just before, and
  rebuilding an image between the release pull request and the release.

## Confirmation

`estate-kit / deploy (dry-run)` is a required check on the release pull
request. The service refuses to sign a render whose dry-run did not pass in
the same deploy, and refuses a digest that was not registered by the Project's
own build ([record 8](0008-an-image-digest-is-sealed-into-the-fragment-and-registered-by-its-build.md)).
The end-to-end suite ([record 69](0069-the-deploy-path-is-tested-end-to-end.md))
covers a rejected dry-run leaving the tag where it was.

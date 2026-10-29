---
status: proposed  # proposed | accepted | locked
date: 2026-10-29
rests-on: [6, 22, 26]
lessons: [CS-5, DR-1]
---

# An image's digest is sealed into the Intent Fragment, and its build registered it

## Context

Today image digests live in `images.lock.yml` in the estate repository, apart
from the Projects they belong to. A render must name every image by digest to
be a function of pinned inputs ([record 6](register.md)). Images are built once
and promoted ([record 26](register.md)), but nothing checked where a sealed
digest came from: a fragment could name any digest, and the service would sign
a render that ran it ([review](../research/review/README.md) D8).

## Decision

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

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| GitHub artifact attestations, verified with sigstore | A sigstore verifier and a TUF fetch on the deploy path | Heavier than the problem; a later upgrade, not a blocker |
| Claim policy only | Any admitted Project's CI can seal any digest | The provenance gap D8 named |
| Keep the estate's images lock | A central list outside the Projects | Each Project's state lives with the Project ([record 7](register.md)) |

## Consequences

- Easier: what runs can be traced to the build that produced it; the event log
  is the record.
- Harder: every Project's workflow has a separate build and attest step.
- Forbidden: a render naming a digest that is neither registered by its
  Project nor allowlisted.

## Confirmation

A service test composes a fragment with an unregistered digest and asserts the
refusal and its location; the e2e suite registers, deploys, and then tries the
same digest from another Project.

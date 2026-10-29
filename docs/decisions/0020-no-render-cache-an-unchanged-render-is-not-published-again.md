---
status: proposed  # proposed | accepted | locked
date: 2026-10-29
rests-on: [6, 9, 17]
lessons: [CS-5]
---

# No render cache: an unchanged render is not published again

## Context

The first design looked each Project's render up in ghcr by a render key, the
digest of its fragment, Platform Intent, the ClusterState snapshot and the
compiler version. Because every part ships at one version, every estate-kit
release changes the compiler version in every key, so every lookup misses
after a release; a hit costs a ghcr round trip per Project, while rendering one
Project in memory takes milliseconds ([review](../research/review/README.md) D9,
finding model-compiler-6).

## Decision

There is no render cache. Every composition renders every admitted Project. The
render key is still computed and kept as provenance with each published render.
When a render's digest equals the digest already behind the Project's tag, the
service publishes nothing, signs nothing and moves nothing, and records why.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| A registry lookup by render key | A ghcr call per Project; misses on every release | It saves no time and adds a failure mode |
| A cache on the service's disk | State that a restart or a second pod must agree on | Rendering is cheap |

## Consequences

- Easier: one less state to keep right; a release that changes no output
  republishes nothing, because bytes are deterministic.
- Harder: composition time grows with the estate; at this scale it does not
  matter.
- Forbidden: a cache whose hit skips rendering.

## Confirmation

An e2e scenario deploys twice with no change and asserts that the tag did not
move and no new artifact was pushed; a property test asserts that rendering
the same inputs twice gives the same digest.

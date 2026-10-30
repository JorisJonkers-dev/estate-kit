---
status: accepted  # proposed | accepted | locked
date: 2026-10-30
rests-on: []
lessons: []
---

# Every part of estate-kit, the components included, lives in this repository at one version

## Context

estate-kit holds the compiler, the service, the host applier, the UI and six
components that act on what a render declares. The components were separate
repositories, shared by submodule or by release. A change to the model then
needed a pull request in each, and a compatibility matrix said which component
version worked with which compiler.

## Decision

Components live in this repository, in the one Cargo workspace, and the whole
repository has one version: every binary, image and reusable workflow ships
under it. A change to the model lands in one pull request, and there is no
compatibility matrix to keep. The layout is on
[The Rust workspace](../design/rust-workspace.md) and the components on
[Mail and components](../design/mail-and-components.md).

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Components in separate repositories, as submodules | A model change needs a pull request per repository | A model change lands in one pull request |
| One version per component | A compatibility matrix of component against compiler | No compatibility matrix |

## Consequences

- Easier: a render's provenance names one version; the render key's compiler
  version covers every part.
- Harder: a component with no change still ships under each new version.
- Forbidden: a component version that differs from the workspace's.

## Confirmation

A check over the workspace manifests fails when a member sets its own
`version` instead of inheriting the workspace's. It lands with the first
crates, with the layer check in
[The Rust workspace](../design/rust-workspace.md#the-crates).

---
status: accepted  # proposed | accepted | locked
date: 2026-10-30
rests-on: []
lessons: []
---

# Every part of estate-kit, the components included, lives in this repository at one version

Amended by [record 89](0089-every-persisted-or-externally-read-contract-has-its-own-identifier-contract-major-and-supported-range.md):
this repository keeps one release version, but the major a reader checks is
each contract's own identifier and Contract major, not the release version.

## Context

estate-kit holds the compiler, Delivery, the host applier, the UI and six
components that act on what a render declares. The components were separate
repositories, shared by submodule or by release. A change to the model then
needed a pull request in each, and a compatibility matrix said which component
version worked with which compiler.

## Decision

Components live in this repository, in the one Cargo workspace, and the whole
repository has one version: every binary, image and reusable workflow ships
under it. A change to the model lands in one pull request, and there is no
compatibility matrix to keep. The version a reader checks, though, is not this
one: each persisted or externally read contract has its own identifier,
Contract major and supported range
([record 89](0089-every-persisted-or-externally-read-contract-has-its-own-identifier-contract-major-and-supported-range.md)),
and only estate-kit's own releases are versioned here. The layout is on
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

The **Workspace version check** over the workspace manifests fails when a
member sets its own `version` instead of inheriting the workspace's. It lands
with the first crates, with the layer check in
[The Rust workspace](../design/rust-workspace.md#the-crates).

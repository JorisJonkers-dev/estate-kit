---
status: proposed  # proposed | accepted | locked
date: 2026-10-29
rests-on: [9, 17]
lessons: [DR-1, DR-2]
---

# ghcr tags move with a machine account's token kept in Vault

## Context

The service pushes renders and moves `render/` and `host/` tags on ghcr. The
design assumed a GitHub App token scoped to those packages, but GitHub Packages
documents only classic personal access tokens, and `GITHUB_TOKEN` for packages
linked to the workflow's own repository; App installation tokens are refused
in practice ([review](../research/review/README.md) D3). Spike #10 confirms it.

## Decision

A dedicated machine account holds write access only on the render and host
packages. Its classic token lives in Vault, the service reads it at use, and it
is rotated on a schedule. A check lists the account's package grants and fails
on any other. If spike #10 finds App tokens do work, this record is rewritten.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| A promote workflow with `GITHUB_TOKEN` | GitHub Actions latency on every tag move, rollback included | Rollback must be fast and in the cluster |
| An in-cluster registry mirrored to ghcr | A registry to run; a rebuilt cluster cannot pull its renders | The render store must survive the cluster |

## Consequences

- Easier: tag moves and rollback stay in the cluster.
- Harder: a long-lived secret exists; its scope and rotation are checked.
- Forbidden: any package grant beyond the render and host packages.

## Confirmation

The grant check fails on an extra package; the rotation job alerts when the
token is older than its schedule.

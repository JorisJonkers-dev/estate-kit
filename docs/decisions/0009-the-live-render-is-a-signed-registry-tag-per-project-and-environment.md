---
status: accepted  # proposed | accepted | locked
date: 2026-10-29
rests-on: []
lessons: [DR-1, DR-2]
---

# The live render is a signed registry tag per Project and environment

## Context

The estate used pin commits, written by workflows, to say which render is live.
Without them, something must say it, with no central list to edit and no
second writer of Flux objects. A signed tag on the registry, moved by the
service ([record 17](0017-the-service-runs-in-the-cluster-in-rust.md)), is the
seam Flux already verifies.

The service pushes renders and moves `render/` and `host/` tags on ghcr. The
design assumed a GitHub App token scoped to those packages, but GitHub Packages
documents only classic personal access tokens, and `GITHUB_TOKEN` for packages
linked to the workflow's own repository; App installation tokens are refused
in practice ([review](../research/review/README.md) D3). Spike #10 confirms it.
A token read from Vault at the moment of use would make every tag move,
Rollback included, depend on Vault, which is the part most likely to be sealed
in an incident ([review](../research/review/README.md) D7).

## Decision

The live render of a Project in an environment is one signed registry tag,
`render/<project>:<environment>`. Flux pulls it, and the service moves it. There
is no estate pin commit and no patching of Flux's own objects.

A dedicated machine account holds write access only on the render and host
packages. Its classic token lives in Vault and is rotated on a schedule. The
Vault Secrets Operator syncs it into a Kubernetes Secret, which the service
mounts, so a tag move never reads Vault. A check lists the account's package
grants and fails on any other. If spike #10 finds App tokens do work, the token
half of this record is rewritten.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Estate pin commits | A central list, and a workflow writing it | No central list, and no second writer |
| The service patching OCIRepository | A second writer of Flux objects | Flux objects have one writer |
| The token read from Vault at use | A tag move and a Rollback fail when Vault is sealed | Recovery must not depend on Vault |
| A promote workflow with `GITHUB_TOKEN` | GitHub Actions latency on every tag move, rollback included | Rollback must be fast and in the cluster |
| An in-cluster registry mirrored to ghcr | A registry to run; a rebuilt cluster cannot pull its renders | The render store must survive the cluster |
| A GitHub App token for the tag move | ghcr refuses App tokens | A machine account's classic PAT is what ghcr accepts (D3) |

## Consequences

- Easier: tag moves and Rollback stay in the cluster and work with Vault down
  ([record 28](0028-pause-and-rollback-are-a-cluster-object-per-project.md)).
- Harder: a long-lived secret exists, now also as a Kubernetes Secret; its
  scope and rotation are checked, and the Secret is readable by the service
  alone.
- Forbidden: any package grant beyond the render and host packages; a tag move
  that reads the token from Vault.

## Confirmation

The **Token grant check** fails on an extra package; the **Token rotation
alert** fires when the token is older than its schedule. The end-to-end registry
requires the token, so a tag move that needs Vault fails the
Rollback-with-Vault-sealed scenario of the **E2E scenarios**
([record 69](0069-the-deploy-path-is-tested-end-to-end.md)).

---
status: proposed  # proposed | accepted | locked
date: 2026-10-29
rests-on: [7, 17, 61]
lessons: [DO-1]
---

# Pause and Rollback are a cluster object per Project; a missing object reads as Paused

## Context

Pause and Rollback were pin commits by workflows in the estate repository.
Without the estate pins, the state "this Project is paused, or held at render X"
needs a home. The cluster is the record of what runs, and a lost or unreadable
state must fail safe ([review](../research/review/README.md) D5, D7).

## Decision

Each admitted Project has one `ProjectControl` custom resource in its own
namespace, written only by the service: whether it is Paused, and the render
it is held at after a Rollback. The service creates it when a Project is
admitted. Before any tag move, the service reads it; a missing or unreadable
object reads as Paused, so nothing deploys until the object is restored. It is
a custom resource, not a ConfigMap, so its schema is validated by the API
server and its RBAC can be granted to the service alone.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| A row in the service's Postgres | Pause lives apart from what runs; a lost database un-pauses | The cluster is the record |
| Registry annotations | A second writer on the artifacts | Artifacts are signed and immutable |
| A ConfigMap | No schema; any namespace admin can edit it | A CRD validates and scopes |

## Consequences

- Easier: an operator can read a Project's state with `kubectl`; a lost
  object fails safe.
- Harder: one CRD to install and version with the platform.
- Forbidden: any writer of `ProjectControl` but the service.

## Confirmation

A service test deletes the object and asserts the next deploy is refused as
Paused; an admission policy fixture refuses a write from any other identity.

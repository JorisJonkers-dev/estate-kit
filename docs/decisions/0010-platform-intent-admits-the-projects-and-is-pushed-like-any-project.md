---
status: accepted  # proposed | accepted | locked
date: 2026-10-30
rests-on: [3, 7]
lessons: []
---

# Platform Intent admits the Projects, and it is pushed like any Project; the service's copies are a cache

## Context

The estate needs one reviewed answer to "which Projects may deploy". A Project
is identified by its `repository_id`, and a Project's state lives with the
Project ([record 7](register.md)). Platform Intent is the estate's own
declaration: the list of admitted Projects, the image allowlist and the other
estate-wide policy ([CONTEXT.md](../../CONTEXT.md)). It lives in a thin estate
repository.

The service needs a copy of Platform Intent to compose. If the copy were the
record, the service would hold a mutable central store that nothing reviews.
The estate repository is already a Project with a release workflow that
validates, publishes and calls the service over OIDC, so it can deliver
Platform Intent the way every other Project delivers its fragment.

## Decision

Platform Intent admits the Projects: a Project may deploy only if Platform
Intent lists its `repository_id`. The list is a reviewed file, changed by pull
request. Membership is never derived from the registry or the cluster.

Platform Intent is pushed like any Project. The estate repository's release
workflow validates it, publishes it to the registry and calls the service over
OIDC; the service keeps what it receives as a cache and never as the record.
The registry stays the record, and the nightly drift check compares the cache
with it ([How Platform Intent arrives](../design/where-state-lives.md#how-platform-intent-arrives)).

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Derive membership from the registry or the cluster | Whoever can push a tag or create a namespace becomes admitted | A reviewed list of who may deploy is the point |
| The service's store is the record of Platform Intent | A mutable central store no pull request reviews, and a second source of truth | The registry stays the record |
| The service fetches Platform Intent on its own schedule | A second delivery path, with its own credentials and timing | One path: the push every Project already uses |

## Consequences

- Easier: admitting or removing a Project is a reviewed change; the estate
  repository needs no delivery path of its own.
- Harder: a Project cannot deploy until a pull request admits it.
- Forbidden: a deploy for a Project Platform Intent does not list, and a
  service copy of Platform Intent that is treated as authoritative.

## Confirmation

The **Platform Intent admission test** refuses a Project absent from Platform
Intent. The **Platform Intent drift check** reports any difference between the
cached copy and the registry's, and the **E2E scenarios**
([record 69](0069-the-deploy-path-is-tested-end-to-end.md)) push Platform
Intent through the same workflow as a Project.

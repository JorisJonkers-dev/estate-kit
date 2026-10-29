---
status: proposed  # proposed | accepted | locked
date: 2026-10-29
rests-on: [2, 17, 25]
lessons: [DO-1, TM-6]
---

# Flux is locked down per Project, and the service dry-runs as an identity that cannot write

## Context

Without lockdown, Flux's kustomize-controller applies every render as
cluster-admin, so isolation between Projects rests on the compiler alone. A
server-side dry-run needs the same RBAC as a real write, so a service that
dry-runs holds write access ([review](../research/review/README.md) D4).

## Decision

- **Flux lockdown.** The controllers run with `--no-cross-namespace-refs`,
  `--no-remote-bases` and a default service account with no rights. Each
  Project's Kustomization names its own service account and target namespace,
  derived from the admitted Projects into the platform render.
- **The service dry-runs as itself.** A ValidatingAdmissionPolicy refuses any
  request from the service's identity whose `dryRun` is not set, so the API
  server itself prevents a real write. Spike #13 proves `request.dryRun` is
  reachable from the policy.
- **Pod Security and image policy per Project.** Namespaces are labelled for
  the `restricted` profile and a digest-only image policy, with exemptions
  declared in Platform Intent.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Dry-run by impersonating each Project's account | The service holds write-equivalent rights through every account | A write-capable identity on the deploy path |
| No lockdown | Isolation rests on the compiler alone | D4 |

## Consequences

- Easier: a compromised render can change only its own Project's namespace.
- Harder: the dry-run does not exercise each Project's RBAC; Flux's apply does.
- Forbidden: a cross-namespace reference; a write by the service's identity
  other than its Lease and `ProjectControl`.

## Confirmation

An admission fixture refuses a non-dry-run write from the service's identity;
an e2e scenario renders a cross-namespace reference and asserts Flux refuses
it.

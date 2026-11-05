---
status: accepted  # proposed | accepted | locked | superseded
date: 2026-11-05
rests-on: [107]
amends: [107]
lessons: [MS-9, TM-4]
---

# Network policy is enforced on kube-router, with a declared rollback, starting with the least-connected namespaces

## Context

[Record 107](0107-network-policy-moves-from-render-only-through-a-staged-or-audited-window-to-enforcement.md)
names three paths from render-only to enforcement — Cilium with policy audit
mode; Calico's staged network policies; per-namespace enforcement on the
existing kube-router — with the trial's measurements to choose one. Enforcement
has not started, and the estate stays segmented on paper and open between
Projects in fact.

The review asked whether enforcing with a declared rollback is acceptable on
the kube-router path (the architecture evaluation of 2026-11-04, sections
3.16 and 15, question 28), since kube-router has no audit stage: enforcing
the data Projects' policies would cut live consumers whose flows are missing
from the model, as the missing Postgres egress shows. The maintainer accepted
it: enforcement starts on kube-router with a declared rollback, and no plugin
migration is waited for. The memory a new plugin would need on the estate's
Raspberry Pi nodes also stays unmeasured on the kube-router path.

## Decision

[Record 107](0107-network-policy-moves-from-render-only-through-a-staged-or-audited-window-to-enforcement.md)'s
path is chosen: per-namespace enforcement on the existing kube-router, which
enforces a policy as soon as it selects a pod. Neither the Cilium nor the
Calico trial precedes enforcement; a plugin may still replace kube-router
later, but segmentation no longer waits on one. The path bends
[deploy-kit ADR 0035](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/model/0035-network-policy-is-default-deny-and-render-only.md)'s
audit prerequisite, and the declared rollback below takes the place the audit
stage would have held.

Enforcement starts with the least-connected namespaces, named by the estate
instance: a namespace's window opens only after every namespace with fewer
declared edges has its window closed, and a namespace that another namespace
consumes is never before one that consumes none. The estate instance names
each namespace whose window opens, so the first namespaces are read from it,
never guessed.

The rollback is declared and written before enforcement: enforce is the
estate instance marking the namespace enforced, so the Project's render
applies its NetworkPolicy objects, and kube-router enforces at once. The
rollback removes that mark, and the Project's next render omits the
namespace's NetworkPolicy objects, so kube-router stops selecting the
namespace's pods. The rollback is written beside the mark, before the policies
apply, and running it is one declared change, not an incident improvisation.

The window still gates the mark. A namespace keeps its enforced mark only
after a window of at least 14 days that included normal traffic, a backup, a
restore and a maintenance window, and surfaced no undeclared flow. On
kube-router there is no audit stage, so an undeclared flow surfaces as a cut —
an incident, a failing check or a consumer's report — and every surfaced flow
is fixed in the model, never allowed by hand; while the fix's render lands,
the declared rollback holds the namespace open.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Stay render-only until a plugin is tried | The estate stays open between Projects for want of a measurement | k3s's bundled kube-router enforces at once; a plugin is not the prerequisite |
| Enforce on the existing kube-router with no declared rollback | A cut flow is repaired by an improvised change in the outage's minutes | The rollback is one declared change, written before the mark, and the review accepted enforcement only with it |
| Cilium or Calico first, for an audit stage | A plugin migration on the live cluster, and memory on the Pis unmeasured | The trial postpones segmentation for a fact kube-router's rollback replaces |
| Enforce every namespace at once | Every missing edge cuts at the same time, and the rollback covers everything at once | Least-connected first keeps each step's blast radius one namespace |
| Allow a surfaced flow by hand inside the window | A policy that differs from the model | Every allowed flow is an edge in the model |

## Consequences

- Easier: segmentation becomes real without waiting for a plugin trial; each
  step's blast radius is one namespace; the rollback is declared before it is
  needed.
- Harder: each first namespace enforces before its undeclared flows are all
  known, so the declared rollback may run while a fix lands; the windows, one
  per namespace, still include a backup, a restore and a maintenance window.
- Forbidden: enforcing a namespace whose rollback was not written first;
  enforcing a namespace before the missing Postgres egress is fixed; a
  namespace keeping its mark without a window of at least 14 days that
  included a backup, a restore and a maintenance window; allowing a surfaced
  flow by hand.

## Confirmation

The **Enforcement promotion check** fails when the estate instance marks a
namespace enforced without a declared rollback written before the mark, or
without a recorded window that lasted at least 14 days, included a backup, a
restore and a maintenance window, and surfaced no undeclared flow. The
**Policy edge pairing test** still checks every rendered edge at both ends,
before enforcement begins in any namespace.

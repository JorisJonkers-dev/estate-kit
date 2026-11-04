---
status: accepted  # proposed | accepted | locked
date: 2026-11-04
rests-on: [2, 5]
lessons: [MS-9]
---

# Network policy moves from render-only, through a staged or audited window, to enforcement

## Context

Network policy is default-deny, derived from the edges Projects declare, and
rendered but never applied
([deploy-kit ADR 0035](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/model/0035-network-policy-is-default-deny-and-render-only.md)).
That record moves policy through render-only, audit and enforce, and waits on a
network plugin with an audit stage; it names Cilium as the candidate. Until then
the estate is segmented on paper and open between Projects in fact.

Enforcement itself is not the blocker. k3s's bundled kube-router enforces a
policy as soon as the policy selects a pod. Neither `networking.k8s.io/v1` nor
kube-router has an audit stage, so enforcing the data Projects' policies on day
one would cut live consumers. The rendered egress rules already miss both
Postgres servers
([deploy-kit#737](https://github.com/JorisJonkers-dev/deploy-kit/issues/737)).
A gap of the same kind went unseen before: one policy allowed no inbound traffic
while its consumers were allowed to send to it (lesson MS-9).

"Network Policies in Kubernetes: Performance Evaluation and Security Analysis"
(2021) found a negligible overhead from network policies, but it measured the
eBPF data planes of Calico and Cilium, not kube-router, and not on hardware like
the estate's Raspberry Pi nodes. It says nothing about a new plugin's memory
there (the architecture evaluation of 2026-11-04, sections 3.17 and 5).

## Decision

Network policy moves from render-only to enforcement through a window in which
policies are staged or audited but drop nothing, one namespace at a time:

1. The missing Postgres egress
   ([deploy-kit#737](https://github.com/JorisJonkers-dev/deploy-kit/issues/737))
   is fixed first, and the compiler checks every edge at both ends.
2. Three paths are tried on a throwaway k3s with the Pis' memory: Cilium with
   policy audit mode; Calico's staged network policies; and per-namespace
   enforcement on the existing kube-router, least-connected namespaces first,
   with a declared rollback. The third needs no plugin change, but it has no
   audit stage, so it bends
   [deploy-kit ADR 0035](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/model/0035-network-policy-is-default-deny-and-render-only.md)'s
   audit prerequisite and must say so if chosen. The trial's measurements choose
   the path.
3. On the chosen path, each namespace's policies run through a window of at
   least 14 days that includes normal traffic, a backup, a restore and a
   maintenance window. Every observed flow that matches no rendered edge is
   fixed in the model, not allowed by hand.
4. A namespace is enforced only after its window saw no undeclared flow. The
   estate instance records which namespaces are enforced, so the state of
   enforcement is never a guess.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Stay render-only | The estate stays open between Projects; rendered gaps stay hidden | Policy that is never applied protects nothing |
| Enforce everything at once on kube-router | Live consumers are cut, as the missing Postgres egress shows | No audit stage finds the gaps first |
| Cilium by default, with a fixed audit window | A plugin migration on a live cluster, and memory on the Pis unmeasured | One candidate among three; a trial decides |
| A window that skips backup and restore | The rarest flows are cut on the day they are needed | Restore is when a cut costs most |
| A window shorter than 14 days | A flow that runs once a week may be seen once or not at all before enforcement | At least 14 days, and it must still include a backup, a restore and a maintenance window |
| Allow an undeclared flow by hand | A policy that differs from the model | Every allowed flow is an edge in the model |

## Consequences

- Easier: segmentation becomes real one namespace at a time; a missing edge is
  found in the window, not in an outage; the enforced namespaces are written down.
- Harder: a trial, a window per namespace including a backup and a restore, and
  possibly a plugin migration.
- Forbidden: enforcing a namespace without a window of at least 14 days that
  included a backup, a restore and a maintenance window and saw no undeclared
  flow; allowing a flow that is not an edge in the model; enforcing before the
  missing Postgres egress is fixed.

## Confirmation

The **Policy edge pairing test** fails when a rendered policy allows an egress
with no matching ingress at the other end, or the reverse. The **Undeclared flow
report** fails when a flow observed during a namespace's window matches no
rendered edge. The **Enforcement promotion check** fails when the estate
instance marks a namespace enforced without a recorded window that lasted at
least 14 days, included a backup, a restore and a maintenance window, and saw
no undeclared flow.

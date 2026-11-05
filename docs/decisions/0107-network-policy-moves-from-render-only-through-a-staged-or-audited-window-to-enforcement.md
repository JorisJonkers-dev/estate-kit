---
status: accepted  # proposed | accepted | locked
date: 2026-11-04
rests-on: [2, 5]
lessons: [MS-9]
---

# Network policy moves from render-only, through a staged or audited window, to enforcement

Amended by [record 126](0126-network-policy-is-enforced-on-kube-router-with-a-declared-rollback.md):
the chosen path is per-namespace enforcement on the existing kube-router, with
a declared rollback written before the mark, starting with the least-connected
namespaces.

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

Network policy moves from render-only to enforcement on k3s's bundled
kube-router, one namespace at a time, with a declared rollback written before
the mark ([record 126](0126-network-policy-is-enforced-on-kube-router-with-a-declared-rollback.md)):

1. The missing Postgres egress
   ([deploy-kit#737](https://github.com/JorisJonkers-dev/deploy-kit/issues/737))
   is fixed first, and the compiler checks every edge at both ends.
2. Enforcement runs on the existing kube-router, per-namespace,
   least-connected namespaces first, with a declared rollback written beside the
   enforced mark before the policies apply
   ([record 126](0126-network-policy-is-enforced-on-kube-router-with-a-declared-rollback.md)).
   A plugin may later replace kube-router, but segmentation waits on no trial;
   on the kube-router path there is no audit stage, so the declared rollback
   takes the place the audit stage would have held, and the path bends
   [deploy-kit ADR 0035](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/model/0035-network-policy-is-default-deny-and-render-only.md)'s
   audit prerequisite.
3. Each namespace keeps its mark only through a window of at least 14 days
   that includes normal traffic, a backup, a restore and a maintenance window.
   An undeclared flow surfaces as a cut, an incident or a failing check; each
   one is fixed in the model, not allowed by hand, and the declared rollback
   holds the namespace while the fix's render lands.
4. The estate instance records which namespaces are enforced, so the state of
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
  surfaced in the window and fixed in the model; the enforced namespaces are
  written down; the rollback is declared before it is needed.
- Harder: a window per namespace including a backup and a restore, enforcement
  before every undeclared flow is known, and possibly a plugin migration later.
- Forbidden: enforcing a namespace whose declared rollback was not written
  first, or that kept no window of at least 14 days that
  included a backup, a restore and a maintenance window and surfaced no
  undeclared flow; allowing a flow that is not an edge in the model; enforcing
  before the missing Postgres egress is fixed.

## Confirmation

The **Policy edge pairing test** fails when a rendered policy allows an egress
with no matching ingress at the other end, or the reverse. The **Undeclared flow
report** fails when a flow observed during a namespace's window matches no
rendered edge. The **Enforcement promotion check** fails when a namespace
keeps its enforced mark without a declared rollback written before the mark and
a recorded window that lasted at
least 14 days, included a backup, a restore and a maintenance window, and
surfaced no undeclared flow.

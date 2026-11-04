---
status: accepted  # proposed | accepted | locked
date: 2026-11-04
rests-on: [33, 50, 74, 82]
lessons: [DO-4]
---

# Active checks run in the owning components, Observation reads their results, and one heartbeat lives outside the cluster

## Context

Observation is its own process, reads, and has one named write: it creates and
expires Alertmanager silences
([record 50](0050-six-bounded-contexts-in-five-layers.md),
[record 74](0074-the-release-gate-and-observation-each-have-a-named-write.md)).
It holds no credential that can deploy, pause or roll back.

Some failures are silent. "Mutiny! How does Kubernetes fail, and what can we do
about it?" (2024) found that when the observed state did not match the desired
state, the user received no error in more than 85% of its experiments unless
monitoring was set up for it. A backup that writes an unreadable copy, or a
Mailbox that can no longer deliver, shows no error until someone needs it. The
only way to know is an active check: restore a Backup generation into a
throwaway instance, or send a probe mail and see it arrive. An active check has
side effects. It needs the backup's decryption key or the mail server's
credentials, which belong to the `backup` and `mailbox` components
([record 82](0082-backups-are-per-tenant-generations-and-mirrors-refresh-staging-and-development.md),
[record 33](0033-a-mailbox-is-declared-by-its-local-part-and-owned-by-one-project.md)).

Version 1 of the architecture evaluation put these checks in Observation; its
version 2 moved them to the owning components, because Observation would need
those credentials and new writes (the architecture evaluation of 2026-11-04,
sections 3.16 and 9.12). An in-cluster checker also cannot report its own
disappearance: if the cluster or the telemetry stack goes silent, nothing inside
raises an alert.

## Decision

This record confirms
[record 50](0050-six-bounded-contexts-in-five-layers.md) and
[record 74](0074-the-release-gate-and-observation-each-have-a-named-write.md):
Observation stays read-only apart from silences and the cost ledger of
[record 92](0092-capacity-is-in-the-resolved-deployment-cost-is-estimated-outside-the-render-key-and-recorded-from-bills.md),
and gains no credential and no write for an active check.

An active check runs in the component that owns the outside system it touches.
`backup` restores a Backup generation into a throwaway instance on a schedule
and checks what it reads back; `mailbox` sends a probe mail and checks that it
arrives. Each component publishes every result, with its time and outcome, where
Observation can read it. Observation reads those results, evaluates the passive
checks it has the meaning for (an applied migration is present in the schema;
what runs matches what was declared), alerts on a failed or missing result with
the owning Project and its runbook, and checks that its own telemetry pipeline
keeps the records it is sent.

One heartbeat lives outside the cluster. It is Alertmanager's Watchdog alert,
which always fires while the alerting pipeline works. Alertmanager sends it on
a schedule to a hosted dead-man's switch from an EU-based provider, such as
healthchecks.io, and when it stops arriving, that service raises the alert from
outside. The service shares no machine with the control plane. The heartbeat
holds no estate data, so the rule that a store of estate data runs on an
EU-controlled provider or on owned hardware does not bind it; an EU-based
service is still preferred.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Observation runs the active checks | Observation holds backup keys and mail credentials and writes to both systems | It would hold credentials [record 50](0050-six-bounded-contexts-in-five-layers.md) keeps out of it, and writes [record 74](0074-the-release-gate-and-observation-each-have-a-named-write.md) does not list |
| A separate checker component | One more process with every component's credentials | The owner already holds the credential and knows the meaning |
| Passive checks only | A backup that cannot restore looks healthy until it is needed | Only a restore proves a backup |
| Health inside the cluster only | A silent cluster raises no alert | A checker cannot report its own disappearance |
| A scheduled job on a machine the maintainer runs off the cluster | One more machine to keep up, whose own failure is silent | A hosted dead-man's switch is someone else's uptime |
| A hosted uptime check that probes the cluster from outside | An open endpoint, and a probe that passes while alerting is broken | The Watchdog proves the whole alerting path, not only reachability |

## Consequences

- Easier: a backup that cannot be restored, or mail that cannot be delivered, is
  found on a schedule; Observation keeps one write; a silent cluster pages.
- Harder: `backup` and `mailbox` each schedule, run and publish a check; the
  heartbeat depends on a hosted service and its account.
- Forbidden: an active check in Observation; a credential or a write for
  Observation beyond silences and the cost ledger and read-only billing
  credentials of
  [record 92](0092-capacity-is-in-the-resolved-deployment-cost-is-estimated-outside-the-render-key-and-recorded-from-bills.md);
  a heartbeat that runs on the cluster it watches.

## Confirmation

The **RBAC fixtures** still fail when Observation's credential grants anything
beyond its named writes, and **`cargo xtask check-layers`** still refuses an
edge from Observation to a component's adapters. The **Active check result
tests** fail when `backup` or `mailbox` runs its check without publishing a
result with its time and outcome, or publishes a pass for a failed restore or
an undelivered probe. The **Silent failure scenarios** fail when a seeded
failure (an unreadable Backup generation, an undelivered probe mail, a
telemetry pipeline that drops records, a running state that differs from the
declared one) raises no alert. The **External heartbeat drill** fails when
stopping the Watchdog heartbeat raises no alert from the hosted dead-man's
switch within its bound.

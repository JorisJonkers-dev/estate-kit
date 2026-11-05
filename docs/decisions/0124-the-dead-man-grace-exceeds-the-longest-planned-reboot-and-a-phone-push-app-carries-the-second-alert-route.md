---
status: accepted  # proposed | accepted | locked | superseded
date: 2026-11-05
rests-on: [12, 87, 108]
amends: [108]
lessons: [DR-2, TM-4]
---

# The dead-man grace exceeds the longest planned reboot, and a phone push app carries the second alert route

## Context

[Record 108](0108-active-checks-run-in-the-owning-components-observation-reads-their-results-and-one-heartbeat-lives-outside-the-cluster.md)
keeps one heartbeat outside the cluster: Alertmanager's Watchdog alert, sent on
a schedule to a hosted dead-man's switch that raises the alert when it stops
arriving. The Watchdog stops for a planned reason too: a host rollout reboots
nodes inside their maintenance windows
([record 12](0012-infrastructure-intent-declares-sites-nodes-and-maintenance-windows.md)),
and the node that runs the telemetry stack takes its reboot with it. A grace
shorter than that reboot pages the maintainer for maintenance. No host reboot
has been measured yet: neither [Infrastructure Intent](../../CONTEXT.md) nor
any design page states one.

The architecture evaluation of 2026-11-04 (sections 3.16 and 15, question 28)
finds that how a person is reached, and how silence is noticed, is undefined:
no second alert route exists, and the heartbeat's grace is unstated. The
maintainer settled both answers, with the grace above the longest planned
reboot so a planned reboot does not page while a real outage still does.

## Decision

Two rules extend
[record 108](0108-active-checks-run-in-the-owning-components-observation-reads-their-results-and-one-heartbeat-lives-outside-the-cluster.md).

The dead-man switch's grace is stated in minutes, and exceeds the estate's
longest planned reboot, measured from a node's drain to its healthy new
generation. The number is fixed from the measured host reboot time. No host
reboot has been measured yet, so the grace is an open measurement with a date:
the first host rollout measures a node's reboot by 2027-03-01 and the grace
follows; until then the dead-man switch holds the longest grace its provider
allows. A planned reboot then never pages, and a real outage alerts after the
grace.

Alerts also leave the estate on a second route: a phone push app on the
maintainer's phone, run outside the estate, so an outage that takes the
estate's Mailbox, or an Application that carries it, still reaches the
maintainer. Its delivery is proved, not assumed: the yearly drill on the real
estate ([record 87](0087-recovery-time-and-recovery-point-are-stated-per-recovery-class.md))
sends a test alert on the second route, and the maintainer confirms by hand
that it arrived on the phone. A drill that sends no test alert, or whose
delivery is not confirmed, fails the route.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| A grace at or under the longest planned reboot | Every host rollout pages the maintainer, and the page becomes habit before the outage arrives | The Watchdog stops by design while the telemetry stack's node reboots |
| Pause the heartbeat by maintenance window | One more step to forget, and a real outage inside a window is silent | The grace absorbs the planned outage with no step to run |
| The estate's Mailbox as the second route | The outage being reported may have taken the mail path with it | A phone push app is carried by no Application of the estate |
| A probe that polls the route | An uptime probe passes while the alerting pipeline is broken | The drill proves delivery on the route the alerting pipeline uses |

## Consequences

- Easier: a host rollout never pages; an outage that takes the estate's own
  mail path still alerts; the grace is one number, compared once.
- Harder: the grace is open until the first host rollout measures a reboot, a
  real outage alerts late by the grace, and the maintainer carries one more
  app and confirms its delivery yearly.
- Forbidden: a grace at or under the estate's longest planned reboot; a second
  alert route carried by an Application of the estate; a yearly drill with no
  test alert on the second route or no confirmed delivery.

## Confirmation

The **Heartbeat grace fixture** fails when the dead-man switch's grace is not
longer than the longest planned reboot the Observation record states in
minutes, or when its fixture shows the heartbeat check firing during a planned
reboot — a heartbeat stopped for a planned reboot's length raises the alert —
and one stopped past the grace raising none. The **Second route delivery
confirmation** fails when the yearly drill sends its test alert and the phone
push app's delivery is not confirmed by hand.

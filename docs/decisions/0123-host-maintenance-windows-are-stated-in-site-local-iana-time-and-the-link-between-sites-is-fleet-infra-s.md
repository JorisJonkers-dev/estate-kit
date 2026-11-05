---
status: proposed  # proposed | accepted | locked | superseded
date: 2026-11-05
rests-on: [12, 59]
amends: [12]
lessons: [MS-4, MS-6]
---

# Host maintenance windows are stated in site-local IANA time, and the link between sites is fleet-infra's

## Context

[Record 12](0012-infrastructure-intent-declares-sites-nodes-and-maintenance-windows.md)
declares a maintenance window per site, with a node override, but does not say
which time the hours are named in. The estate's sites sit in more than one
country: hours without a zone are ambiguous, and hours in UTC stop being the
site's quiet hours when local time shifts for summer time. The architecture
evaluation of 2026-11-04 marks the question open with the underlay (question
A4 Q9): what computes a window, and who owns the link between sites.

The host applier gates its Lease and drain on the window opening
([record 30](0030-a-host-applier-on-each-node-pulls-its-signed-host-tag.md)),
so a wrong computation reboots a node outside the site's quiet hours. The
same evaluation asks whether estate-kit owns the link between sites; the
estate's operations are decided in fleet-infra, as
[record 59](0059-vault-unseal-and-datastore-backup-are-assumed-from-fleet-infra.md)
records for Vault unseal and the datastore backup.

## Decision

This amends
[record 12](0012-infrastructure-intent-declares-sites-nodes-and-maintenance-windows.md):
a site states its maintenance window in site-local time by naming an IANA
time-zone identifier, and a node override names one too. The window is
computed in that zone, so the same declared hours mean the same local time
through a daylight-saving change; hours are never unzoned and never UTC. No
other document states a zone.

The link between sites, the underlay that carries the estate's traffic
between them, is fleet-infra's, decided there like Vault unseal and the
datastore backup. estate-kit assumes it, and treats reachability as a
declared input in Infrastructure Intent: what each site can reach across the
link, including the cluster's API server, the registry and the binary cache,
is declared with the site, and the compiler and the host appliers read that
declaration. Nothing probes the network to learn it
([record 30](0030-a-host-applier-on-each-node-pulls-its-signed-host-tag.md)).

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Hours stated in UTC | The site's quiet hours move by an hour at each local clock change, or the window shrinks to the intersection of summer and winter | The window is the site's local quiet hours |
| Unzoned hours, read as whatever zone the node happens to be in | Two nodes of one site compute different windows | The site states one zone in authored intent |
| estate-kit models or manages the link between sites | Two owners of one network, and estate credentials beside fleet-infra's | The estate's operations are fleet-infra's ([record 59](0059-vault-unseal-and-datastore-backup-are-assumed-from-fleet-infra.md)) |
| Each applier probes for reachability | A rollout keys on a measurement that changes under it, and probes differ per node | Reachability is a declared input, like every other input (MS-4) |

## Consequences

- Easier: a window needs no per-node clock question and no edit when local
  time shifts; the underlay keeps one owner.
- Harder: the component that computes a window needs the IANA zone database;
  a fleet-infra change to the link can break a declared assumption without a
  pull request here.
- Forbidden: unzoned window hours; window hours in UTC; a compiler or applier
  that probes for reachability; a design page that treats the link between
  sites as estate-kit's to run.

## Confirmation

The **Maintenance-window time test** fails when a window computed in
site-local time disagrees across a daylight-saving change. The
**Corpus-agreement test** shows a site's zone and reachability validate, and
a site without either is refused
([record 15](0015-the-rust-types-agree-with-the-committed-schemas-on-their-corpus.md)).

---
status: accepted  # proposed | accepted | locked
date: 2026-11-05
rests-on: [59, 87, 116]
amends: [116]
lessons: [DR-1]
---

# Ownership decides the EU rule: the EEA and Switzerland count, key services are inside it, and every exception ends on a calendar date

## Context

[Record 116](0116-every-store-of-estate-data-runs-on-an-eu-controlled-provider-or-on-owned-hardware.md)
runs every store of estate data on an EU-controlled provider or on owned
hardware, but its definition names only incorporation in an EU member state.
Whether a provider incorporated in an EEA state or in Switzerland counts, and
whether one incorporated in the United Kingdom does, is open — and sanctions
follow the country of the company that controls the provider, not the country
its servers stand in, so the definition decides more than a list of member
states.

The rule's reach is open in two more places. The service that unseals Vault
([record 59](0059-vault-unseal-and-datastore-backup-are-assumed-from-fleet-infra.md)),
fleet-infra's Cloud-KMS, holds key material, but the rule names only stores of
estate data. And the rule's exceptions have no ends the register can read: the
ghcr exception ends at milestone M5, a milestone no record dates and
[the plan](../plan/port.md) numbers among phases, and the forge, CI and DNS
"move off US providers over time, with no deadline".

The maintainer settled all of this on 2026-11-04, in answer to the design
review's sovereignty questions.

## Decision

**Ownership, not location, decides.** An EU-controlled provider is a company
incorporated in an EU member state, a fellow EEA state or Switzerland that no
company outside them controls, wherever its servers stand. A provider
incorporated in the United Kingdom counts as outside, and an EU region of a
provider controlled from elsewhere still does not count.

**Key services holding key material are inside the rule.** The service that
unseals Vault is one: fleet-infra's Cloud-KMS runs on an EU-controlled
provider or on owned hardware, and manual unseal is the fallback for a cold
rebuild while it does not.

**The forge, CI and DNS are stores under the rule.** The forge holds each
Project's repository and fragment, the estate repository's Platform Intent
and the Rollouts' GitHub Deployments; CI holds each Project's builds; DNS
holds the estate's zones. Project images and fragments are pushed by each
Project's CI, so they move with the forge and CI.

**Every exception ends on a calendar date.** The registry and DNS move before
the cutover, by 2027-05-31; the forge and CI follow, by 2027-12-31.
[Record 116](0116-every-store-of-estate-data-runs-on-an-eu-controlled-provider-or-on-owned-hardware.md)
now lists every store and key service in one provider-and-exit table, each
with its provider and its exit date, and the word M5 leaves the records. The
dates follow [the plan](../plan/port.md)'s budget at ten hours a week,
from 2026-11-05: the datastore backup, the open item
[record 87](0087-recovery-time-and-recovery-point-are-stated-per-recovery-class.md)
dates, is due 2027-04-30; the cutover, phase 9, starts when 310 of the 365
hours are spent, about 2027-06-10, so the registry and DNS exit on 2027-05-31,
before it; the forge and CI leave after the cutover, by 2027-12-31.

Platform Intent's provider register keeps the rule once estate data is
placed, as [record
116](0116-every-store-of-estate-data-runs-on-an-eu-controlled-provider-or-on-owned-hardware.md)
already states: each entry names its provider, and Provider facts state the
jurisdiction, with the closed set of exceptions this record settles.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Location decides: any EU or EEA region of any provider counts | A provider controlled from outside follows its home country's sanctions wherever the data lies | Ownership beats location; this was already true of a US-controlled provider's EU region |
| The UK counts as EU-controlled | The UK is outside the EU and the EEA, and its providers follow its own sanctions regime | Settled on 2026-11-04: the EEA and Switzerland count, the UK does not |
| Key services exempt from the rule | The unseal KMS holds the key material a cold rebuild needs first | Manual unseal is the fallback for a cold rebuild, not an exemption |
| Keep M5 as the ghcr exception's end | No record dates M5, and the plan numbers phases, not milestones | A calendar date in the provider-and-exit table |
| Undated exits for the forge, CI and DNS | An exception with no end is the defect the review named | Every exception carries its exit date |

## Consequences

- Easier: the rule means one thing for any provider; every store and key
  service is listed with its provider and its calendar exit date in one
  table; the Provider register lint reads a closed set of exceptions.
- Harder: providers incorporated in the United Kingdom do not qualify,
  wherever their servers stand; each key service's provider must be reviewed
  against the rule; the provider-and-exit table must be kept complete as
  stores are added.
- Forbidden: a store of estate data or a key service holding key material at
  a provider that is neither EU-controlled nor owned, outside the listed
  exceptions' exit dates; an exception without its row in the
  provider-and-exit table; renders or host tags on ghcr after 2027-05-31; the
  forge, CI, Project images, fragments or the estate's DNS still at GitHub,
  ghcr or a US provider after 2027-12-31.

## Confirmation
The **Provider-and-exit table check** fails when a store or key service is
listed in the provider-and-exit table of
[record 116](0116-every-store-of-estate-data-runs-on-an-eu-controlled-provider-or-on-owned-hardware.md)
without its provider or a real calendar exit date, and when the table is
missing. The **Provider register lint** fails when a store of estate data or
a key service holding key material names a provider whose jurisdiction is
neither EU-controlled nor owned, other than a listed exception, and when a
listed exception is still listed once its exit date has passed. Whether a
provider is truly EU-controlled stays a review rule when its Provider facts
are written ([the table of checks](../design/code-shape-and-speed.md#the-checks)).

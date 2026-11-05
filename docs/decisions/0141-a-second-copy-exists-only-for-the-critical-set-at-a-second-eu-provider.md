---
status: accepted  # proposed | accepted | locked | superseded
date: 2026-11-05
rests-on: [21, 87, 116]
amends: [87]
lessons: [DR-1, DR-2]
---

# A second copy exists only for the Critical set, at a second EU provider

## Context

[Record 116](0116-every-store-of-estate-data-runs-on-an-eu-controlled-provider-or-on-owned-hardware.md)
puts every store of estate data at an EU-controlled provider or on owned
hardware, one provider each: the backups, the WAL archive, the registry and
the binary cache. Losing the provider that holds them — an account loss, or
the provider losing the backup store — takes the keys to everything else,
because nothing says what is copied anywhere else.

The design review of 2026-11-04 (its second-copy question) asked whether a
second copy reopens, and the maintainer settled it the same day: a second copy,
but only of the small critical set — the Vault snapshot, the signing and
repository credentials, and the datastore snapshot — at a second EU provider.
[Record 87](0087-recovery-time-and-recovery-point-are-stated-per-recovery-class.md)'s
table holds no row for it.

## Decision

**Only the Critical set.** The
[Critical set](../../CONTEXT.md) — the Vault snapshot, the signing and
repository credentials, and the datastore snapshot — is the only set with a
second copy: the items whose loss takes the estate's keys to everything else,
the render and host signing keys and the credentials that move its tags among
them ([record 21](0021-renders-and-host-tags-are-signed-by-separate-keys-with-an-offline-recovery-key.md)).
Every other store keeps the one copy [record 87](0087-recovery-time-and-recovery-point-are-stated-per-recovery-class.md)
names: a render can be composed again from its pinned inputs, a closure
rebuilt in CI, a Tenant export re-taken; the estate's low-attention budget
([record 86](0086-the-estate-states-its-defaults-for-a-low-attention-week.md))
is not spent copying them twice.

**At a second EU provider.** Each item's second copy sits at a second EU
provider, other than the provider of its first copy, and is a store of estate
data under [record 116](0116-every-store-of-estate-data-runs-on-an-eu-controlled-provider-or-on-owned-hardware.md):
its entry in the provider register comes before any item lands there. The
Vault snapshot's and the datastore snapshot's second copies are written with
the copies their rows name, as one more destination of the same snapshots
([record 59](0059-vault-unseal-and-datastore-backup-are-assumed-from-fleet-infra.md));
the signing and repository credentials' second copy is written by the custody
procedure of [record 140](0140-break-glass-custody-is-written-and-drilled-and-a-named-successor-holds-a-sealed-copy-of-the-recovery-key.md).
A named holder keeps the second copy reachable while the first provider lives
on, and usable when it does not; the holder is not yet chosen: an open item,
due 2027-04-30.

**Held to a stated age.** Each item's second copy carries the age its row in
[record 87](0087-recovery-time-and-recovery-point-are-stated-per-recovery-class.md)
states, so a second copy never trails the recovery point of the class it
copies: within 6 hours, for the Vault snapshot and the datastore snapshot,
and within 24 hours of any change, for a credential. The
**Second-copy freshness check** fails when an item's newest second copy is
older than its stated age, or an item has no second copy at all.

This amends [record 87](0087-recovery-time-and-recovery-point-are-stated-per-recovery-class.md),
whose recovery table now carries the Critical set and its second copy.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| No second copy; the accepted single provider | One provider's loss, or one account's, takes the keys to everything else | The Critical set is small enough to copy twice |
| A second copy of every store | Every backup, render and closure held and paid for twice, and a second copy's freshness watched everywhere | The Critical set answers the loss that matters; the rest is rebuildable |
| A second region of the same provider | One provider's account loss or freeze still takes both copies | The second copy must answer a provider's loss, not a region's |
| A second copy at an owned second site | A machine the estate keeps up, off the estate's providers, for a copy nothing serves from daily | An EU-controlled provider holds it at the same protection for less work |
| A second copy with no stated age | A copy that silently rots behind the first, and the drill's word that it exists | A second copy whose age no check reads is a claim, not a copy |

## Consequences

- Easier: one provider's loss loses no key to the estate; the Critical set is
  small enough that its second copy is one bucket, one vault entry and two
  snapshot destinations.
- Harder: a second copy to write beside every first, a second provider's
  account and register entry, the holder open item to settle, and the
  freshness check to run.
- Forbidden: a second copy of anything but the Critical set; a second copy at
  the same provider as the first; a second copy with no stated age; a store of
  the estate at a provider that is neither EU-controlled nor owned.

## Confirmation

The **Second-copy freshness check** fails when an item of the Critical set has
no second copy at the second EU provider, or its newest copy is older than the
age its row in [record 87](0087-recovery-time-and-recovery-point-are-stated-per-recovery-class.md)
states — 6 hours for the Vault snapshot and the datastore snapshot, 24 hours
after a change for a credential. That the holder is named and reachable is a
review rule and the yearly drill, with the succession drill of
[record 140](0140-break-glass-custody-is-written-and-drilled-and-a-named-successor-holds-a-sealed-copy-of-the-recovery-key.md);
no script can hold a person's naming.

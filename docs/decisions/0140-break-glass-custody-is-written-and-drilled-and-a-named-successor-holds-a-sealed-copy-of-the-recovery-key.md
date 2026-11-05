---
status: accepted  # proposed | accepted | locked | superseded
date: 2026-11-05
rests-on: [1, 21]
amends: [21, 87]
lessons: [DR-1, DR-2]
---

# Break-glass custody is written and drilled, and a named successor holds a sealed copy of the recovery key

## Context

[Record 1](0001-one-maintainer-one-cluster-one-estate.md) keeps one maintainer,
and [record 21](0021-renders-and-host-tags-are-signed-by-separate-keys-with-an-offline-recovery-key.md)
trusts an offline recovery key beside the online keys, signing only in a
break-glass, when Vault is gone. The restore order takes that key, with the
other offline credentials, from the maintainer's offline store
([operating page](../design/operating.md#restore-order-and-drill-cadence)).
Nothing writes where the key lives, who opens it if the maintainer cannot, what
the offline store holds, or the loss case; the design review of 2026-11-04
(break-glass custody, its question 16) marks the gap strong, and counts it
against [record 87](0087-recovery-time-and-recovery-point-are-stated-per-recovery-class.md)'s
drill, which has no person behind one of its inputs.

The maintainer settled the question on 2026-11-04: a named successor holds a
sealed copy of the recovery key, and custody is written down and drilled
yearly.

## Decision

**Custody is written down.** One section of the
[operating page](../design/operating.md#break-glass-custody) holds the
custody of the offline store: where the recovery key lives, who opens it if the
maintainer cannot, what the offline store holds (the offline credentials the
restore order names), and the loss case — the maintainer's absence. The
recovery key never leaves the offline store except sealed: the successor's
copy is sealed, and is opened only in a break-glass the maintainer cannot
reach.

**A named successor holds a sealed copy.** A recovery-key successor — a named
person with their own sealed copy of the recovery key — answers the loss case:
with the maintainer absent, the successor signs in a break-glass, and the
estate survives its one maintainer's absence. The successor is not yet named
and no sealed copy is held yet: both are open items, due 2027-04-30, held
beside the second copy's holder of
[record 141](0141-a-second-copy-exists-only-for-the-critical-set-at-a-second-eu-provider.md).
Until then the loss case stands unanswered, and the yearly drill says so.

This amends
[record 21](0021-renders-and-host-tags-are-signed-by-separate-keys-with-an-offline-recovery-key.md),
whose recovery-key bullet now names the successor and the sealed copy, and the
drill sentence of
[record 87](0087-recovery-time-and-recovery-point-are-stated-per-recovery-class.md),
whose results now cover succession. The successor naming adds no Recovery
class: the offline store is not a store of estate data in
[record 87](0087-recovery-time-and-recovery-point-are-stated-per-recovery-class.md)'s
table, and it keeps no row there.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| An accepted risk: the maintainer alone opens the recovery key | The estate cannot break-glass through the one event it holds the key for — the maintainer's absence | Custody with a successor costs one sealed copy |
| A sealed, time-locked release, with no successor | The key opens on a timer the estate never chose, to whoever holds it | A named person answers the loss case a timer cannot |
| A sealed escrow service holding the key | A third party outside the estate's trust, and a new account to keep | The successor holds the sealed copy themselves |
| Two successors, each with a sealed copy | Two people to keep, and two copies that can leak | One successor answers the loss case |

## Consequences

- Easier: a break-glass survives the maintainer's absence; the yearly drill has
  a person behind its keystone step; the custody of the offline store is read
  in one place.
- Harder: a successor to name, brief and keep; a sealed copy to verify in
  every yearly drill; the open item's date to meet.
- Forbidden: an unsealed copy of the recovery key outside the offline store; an
  online escrow of the recovery key; a custody the yearly drill has not
  exercised.

## Confirmation

That the successor is named, that a sealed copy is held, and that the custody
page answers where the key lives, who opens it, what the offline store holds
and the loss case, is a review rule and the yearly drill, which the maintainer
runs on the real estate and records ([record 87](0087-recovery-time-and-recovery-point-are-stated-per-recovery-class.md));
no script can hold a person's naming. The drill verifies the sealed copy
still opens the key it is a copy of, and records the successor's rehearsal of
its use.

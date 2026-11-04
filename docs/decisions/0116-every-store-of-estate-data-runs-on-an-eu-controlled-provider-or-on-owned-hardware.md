---
status: proposed  # proposed | accepted | locked | superseded
date: 2026-11-04
rests-on: [9, 31, 82]
lessons: [DR-1]
---

# Every store of estate data runs on an EU-controlled provider or on owned hardware

## Context

The estate keeps its data in a few stores outside the cluster. Backups and the
WAL archive go off the cluster
([record 82](0082-backups-are-per-tenant-generations-and-mirrors-refresh-staging-and-development.md)).
Renders and host tags live on ghcr
([record 9](0009-the-live-render-is-a-signed-registry-tag-per-project-and-environment.md)),
and [record 99](0099-renders-and-host-tags-live-in-an-off-cluster-registry-chosen-by-its-features.md)
plans an off-cluster registry to replace it in milestone M5, after the
cutover. Host closures live in a binary cache on object storage
([record 31](0031-host-closures-are-built-in-ci-and-cached-outside-the-cluster.md)),
whose location Platform Intent names. No record says which providers may hold
any of them.

A provider controlled from outside the EU must follow its own country's
sanctions, wherever its servers stand. The maintainer wants the estate's data
protected against US sanctions. GitHub is load-bearing as the forge, the CI and
ghcr today, and DNS is also at a US provider; the architecture evaluation of
2026-11-04 (section 3.21) counts the places that depend on GitHub, none of them
behind a port.

[Record 85](0085-general-purpose-means-no-estate-fact-in-the-core-the-profiles-or-the-compiler-s-code.md)
keeps estate facts out of estate-kit's code: they live in the Estate instance
and in Provider facts.

## Decision

**Every store of estate data runs on an EU-controlled provider or on owned
hardware.** A store of estate data is any place the estate keeps its data:
backups (fleet-infra's datastore and Vault copies among them), the WAL archive,
the render registry and the binary cache. An EU-controlled provider is one
incorporated in an EU member state and not controlled by a company outside
the EU; an EU region of a provider controlled from elsewhere does not count.
Owned hardware is a machine the maintainer owns. The reason is protection
against US sanctions.

**One named exception, with an end.** ghcr keeps renders and host tags until
milestone M5, when the registry of
[record 99](0099-renders-and-host-tags-live-in-an-off-cluster-registry-chosen-by-its-features.md),
which must itself be EU-controlled or owned, replaces it. The exception ends
with M5. No other exception exists without a record.

**The rest moves over time.** The forge, CI and DNS move off US providers over
time, with no deadline. Project images and fragments are pushed by each
Project's CI, so they move with the forge and CI.

**A provider register holds the rule.** Platform Intent lists each store of
estate data with its provider, and the provider's Provider facts state its
jurisdiction: EU-controlled, owned, or other. Platform Intent states the
allowed jurisdictions and the ghcr exception with its end, so estate-kit's
code holds no estate fact. A new store gets its entry before it holds data.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Any provider with an EU region | A provider controlled from the US follows US sanctions wherever the data lies | Control, not the region, decides |
| Owned hardware only | Every store needs a machine kept up, off the site it backs up | An EU-controlled provider gives the same protection for less work |
| Move the forge, CI and DNS now | Every Project's CI and the deploy path change before the cutover | They move over time; the stores move first |
| Move renders and host tags off ghcr now | The registry move before its spike and before the cutover | ghcr is a named exception until M5, when [record 99](0099-renders-and-host-tags-live-in-an-off-cluster-registry-chosen-by-its-features.md) replaces it |
| A rule in review only, with no register | A store at a US provider is noticed after it holds data | A register and a lint fail the change |

## Consequences

- Easier: the estate's data stays reachable whatever US sanctions do; a review
  of a new store has one rule and one list.
- Harder: some products and managed services cannot be used; an EU provider may
  cost more or offer less; the register must be kept complete.
- Forbidden: a store of estate data at a provider that is neither EU-controlled
  nor owned, outside the named exception; the ghcr exception after M5; a new
  exception without a record.

## Confirmation

The **Provider register lint** fails when a store in the provider register
names a provider whose jurisdiction is neither EU-controlled nor owned, unless
it is the ghcr exception for renders and host tags; when the ghcr exception is
still listed once milestone M5 is closed; or when a store in the copy inventory
of [record 110](0110-a-purge-erases-backup-generations-and-mirrors-from-an-inventory-of-every-copy.md)
or a Recovery class of
[record 87](0087-recovery-time-and-recovery-point-are-stated-per-recovery-class.md)
has no entry. Whether a provider is truly EU-controlled is a review rule when its
Provider facts are written.

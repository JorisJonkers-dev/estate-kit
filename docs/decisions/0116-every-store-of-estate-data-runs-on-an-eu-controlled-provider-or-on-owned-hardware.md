---
status: accepted  # proposed | accepted | locked | superseded
date: 2026-11-04
rests-on: [9, 31, 82]
lessons: [DR-1]
---

# Every store of estate data runs on an EU-controlled provider or on owned hardware

Amended by [record 133](0133-ownership-decides-the-eu-rule-and-every-exception-ends-on-a-calendar-date.md): ownership decides the EU-controlled set (the EEA and Switzerland count, the United Kingdom does not), key services holding key material are inside the rule, the forge, CI and DNS are stores, and every store and key service is listed with its provider and a calendar exit date.

## Context

The estate keeps its data in a few stores outside the cluster. Backups and the
WAL archive go off the cluster
([record 82](0082-backups-are-per-tenant-generations-and-mirrors-refresh-staging-and-development.md)).
Renders and host tags live on ghcr
([record 9](0009-the-live-render-is-a-signed-registry-tag-per-project-and-environment.md)),
and [record 99](0099-renders-and-host-tags-live-in-an-off-cluster-registry-chosen-by-its-features.md)
plans an off-cluster registry to replace it, moved before the cutover,
by 2027-05-31. Host closures live in a binary cache on object storage
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
backups (fleet-infra's datastore and Vault copies among them), the WAL
archive, the render registry and the binary cache. The forge, CI and DNS are
stores too: the forge holds each Project's repository and fragment, the
estate repository's Platform Intent and the Rollouts' GitHub Deployments; CI
holds each Project's builds; DNS holds the estate's zones. Ownership, not
location, decides: an EU-controlled provider is a company incorporated in an
EU member state, a fellow EEA state or Switzerland that no company outside
them controls, wherever its servers stand; a provider incorporated in the
United Kingdom counts as outside, and an EU region of a provider controlled
from elsewhere does not count. Owned hardware is a machine the maintainer
owns. The reason is protection against US sanctions.

**Key services holding key material are inside the rule.** The service that
unseals Vault ([record 59](0059-vault-unseal-and-datastore-backup-are-assumed-from-fleet-infra.md)),
fleet-infra's Cloud-KMS, holds key material: it runs on an EU-controlled
provider or on owned hardware, and manual unseal is the fallback for a cold
rebuild while it does not.

**Every exception is a row with a calendar exit date.** ghcr keeps renders
and host tags, and each Project's CI keeps its images and fragments there,
until the registry move, which happens before the cutover and completes by
2027-05-31; DNS moves with the registry, on the same date; the forge and CI
follow, by 2027-12-31. Project images and fragments are pushed by each
Project's CI, so they move with the forge and CI. No exception exists
without a row in the provider-and-exit table below, and no new exception
exists without a record.

**A provider register holds the rule.** Platform Intent lists each store of
estate data and each key service holding key material with its provider,
and the provider's Provider facts state its jurisdiction: EU-controlled,
owned, or other. Platform Intent states the allowed jurisdictions and the
listed exceptions with their exit dates, so estate-kit's code holds no
estate fact. A new store gets its entry before it holds data.

### The provider-and-exit table

Every store of estate data and every key service holding key material is
listed here against the rule, each with its provider and its exit date: the
date by which the store is inside the rule. The date 2026-11-05, the day the
rule took this shape, names a store that never left it; a future date is the
end of that store's exception. The dates follow [the plan](../plan/port.md)'s
budget at ten hours a week, as [record
133](0133-ownership-decides-the-eu-rule-and-every-exception-ends-on-a-calendar-date.md)
settles them.

| Store or key service | What it holds | Provider | Exit date |
| --- | --- | --- | --- |
| Backups | One Kopia repository per Environment: Tenant exports, every Postgres server's capture, volume contents | Scaleway Object Storage (nl-ams), EU-controlled | 2026-11-05 |
| The WAL archive | One locked bucket per Environment, beside the backups | Scaleway Object Storage (nl-ams), EU-controlled | 2026-11-05 |
| The datastore backup and Vault's off-cluster copies | The k3s datastore; Vault's raft snapshots | [fleet-infra's backup](0059-vault-unseal-and-datastore-backup-are-assumed-from-fleet-infra.md); the datastore backup is [the open item](https://github.com/JorisJonkers-dev/estate-kit/issues/41), none written today | 2027-04-30 |
| Renders and host tags | Signed renders, their signatures, numbered host tags | ghcr, until the registry [record 99](0099-renders-and-host-tags-live-in-an-off-cluster-registry-chosen-by-its-features.md) names — itself EU-controlled or owned — takes them, before the cutover | 2027-05-31 |
| Project images and fragments | Each Project's images and fragments, pushed by its own CI | ghcr, until they move with the forge and CI | 2027-12-31 |
| The forge | Each Project's repository and fragment, the estate repository's Platform Intent, GitHub Deployments | GitHub | 2027-12-31 |
| CI | Each Project's build and release workflow; the closure builder runs on owned hardware | GitHub Actions | 2027-12-31 |
| DNS | The estate's DNS zones | A US provider today, moving with the registry | 2027-05-31 |
| The binary cache | Host closures ([record 31](0031-host-closures-are-built-in-ci-and-cached-outside-the-cluster.md)) | Object storage Platform Intent names; EU-controlled or owned under this rule, before it holds data | 2026-11-05 |
| Vault's unseal service | The key material that unseals Vault ([record 59](0059-vault-unseal-and-datastore-backup-are-assumed-from-fleet-infra.md)) | fleet-infra's Cloud-KMS, EU-controlled or owned under this rule, with manual unseal as the cold-rebuild fallback | 2026-11-05 |

Every other store — the Project databases, platform-postgres, Vault's own
data, the k3s datastore, Garage objects and local-path volumes — lives on
the estate's own nodes and is inside the rule by the machines it runs on:
Infrastructure Intent declares them, and they run on an EU-controlled provider
or on owned hardware under the same rule. A store or key service that does
not serve the estate's own data — a Project's own third-party services — is
not the estate's to place.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Any provider with an EU region | A provider controlled from the US follows US sanctions wherever the data lies | Control, not the region, decides |
| Owned hardware only | Every store needs a machine kept up, off the site it backs up | An EU-controlled provider gives the same protection for less work |
| Move the forge, CI and DNS now | Every Project's CI and the deploy path change before the cutover | They move after the registry and DNS, by 2027-12-31 |
| Move renders and host tags off ghcr now | The registry move before its spike and before the cutover | ghcr is a listed exception until the registry move, by 2027-05-31, when [record 99](0099-renders-and-host-tags-live-in-an-off-cluster-registry-chosen-by-its-features.md) replaces it |
| A rule in review only, with no register | A store at a US provider is noticed after it holds data | A register and a lint fail the change |

## Consequences

- Easier: the estate's data stays reachable whatever US sanctions do; a review
  of a new store has one rule, one list and one dated end.
- Harder: some products and managed services cannot be used; an EU provider may
  cost more or offer less; the register must be kept complete.
- Forbidden: a store of estate data or a key service holding key material at
  a provider that is neither EU-controlled nor owned, outside the listed
  exceptions' exit dates; the ghcr exceptions after 2027-05-31, and the
  forge, CI, DNS, Project images and fragments after 2027-12-31; a new
  exception without a record and a row.

## Confirmation
The **Provider-and-exit table check** fails when a store or key service is
listed in the provider-and-exit table above without its provider or a real
calendar exit date, or when the table is missing. The **Provider register
lint** fails when a store of estate data or a key service holding key material
in the provider register names a provider whose jurisdiction is neither
EU-controlled nor owned, other than a listed exception — ghcr for renders,
host tags, Project images and fragments; the forge; CI; DNS; when a listed
exception is still listed once its exit date has passed; or when a store in
the copy inventory of
[record 110](0110-a-purge-erases-backup-generations-and-mirrors-from-an-inventory-of-every-copy.md)
or a Recovery class of
[record 87](0087-recovery-time-and-recovery-point-are-stated-per-recovery-class.md)
has no entry. Whether a provider is truly EU-controlled is a review rule when
its Provider facts are written.

---
status: accepted  # proposed | accepted | locked
date: 2026-11-01
rests-on: [10, 75, 76]
lessons: [MS-4, MS-7]
---

# Product domains are admitted by Platform Intent and named by a Project, and Tenant hosts are derived from them

## Context

Hosts are written by hand, one per Application. A multi-tenant Project has a
Tenant per organisation, and with more than 1000 Tenants no one writes their
hosts. [Record 76](0076-tenants-are-the-organisations-the-estate-serves.md)
gives each Tenant a Tenant handle that its people see in URLs, and
[record 75](0075-three-environments-run-in-the-one-cluster.md) gives the estate
three Environments that share one cluster, so a staging host must never be a
production host.

[Record 10](0010-platform-intent-admits-the-projects-and-is-pushed-like-any-project.md)
makes Platform Intent the reviewed answer to which Projects may deploy. The
domains the estate owns are the same kind of answer: only the maintainer may
admit one.

The multi-cluster research asks the estate to have one stable name now, shaped
like a cluster ID, so that a second cluster or estate can later use it without
renaming anything.

## Decision

Platform Intent lists the estate's domains and, for each, the Projects admitted
to use it. A Project cannot use a domain that Platform Intent does not admit for
it.

An Application in a multi-tenant Project names its Product domain. The Tenant
host is derived, never written:

| Environment | Tenant host |
| --- | --- |
| production | `<handle>.<product domain>` |
| staging | `<handle>-staging.<product domain>` |
| development | `<handle>-dev.<product domain>` |

Every Tenant host sits one level below the Product domain, so one single-level
wildcard certificate covers every Environment. A handle that ends in `-staging`
or `-dev` is already refused by
[record 76](0076-tenants-are-the-organisations-the-estate-serves.md), so no
production host equals another Environment's host.

A per-environment override may name another Product domain, if Platform Intent
admits it for the Project. Domains are one of the fields that
[record 75](0075-three-environments-run-in-the-one-cluster.md) lets differ
between Environments.

Two Projects that claim one Product domain are refused with a contention
diagnostic that points at both locations.

A host resolves to a Tenant through a lookup, never by parsing the host. The
Gate and the libraries ask the lookup. Custom domains can later be added as
more rows of it, and nothing that reads a host changes.

Platform Intent also gains the estate's stable name: a DNS-style name of at most
32 characters. It changes nothing today. It is the seam that a later second
cluster or estate can use as its cluster ID and trust domain.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Hosts written by hand per Application | One edit per Tenant; a typo or a takeover is found in production | With more than 1000 Tenants no one writes them |
| A Project claims any domain, unchecked | A Project can take a domain another Project or the estate relies on | Only the maintainer may admit a domain, as with Projects in [record 10](0010-platform-intent-admits-the-projects-and-is-pushed-like-any-project.md) |
| `<env>.<handle>.<domain>` for staging and development | Two levels, so one wildcard certificate no longer covers every Environment | One single-level wildcard per domain is simpler to issue and renew |
| A separate domain per Environment | The estate owns, admits and certifies three domains per product | One domain with a host suffix does the same with one certificate |
| Parse the Tenant handle out of the host | A custom domain has no handle to parse, and the rule must be copied into every library | A lookup keeps custom domains possible and keeps the rule in one place |
| Leave the estate unnamed until a second cluster exists | Naming it later renames cluster-wide identifiers | A name of at most 32 characters costs nothing now and fits the shapes the research names |

## Consequences

- Easier: an Application names one domain and every Tenant host follows; a
  takeover of a domain fails at compile time; one certificate per Product domain
  serves every Environment.
- Harder: Platform Intent carries the estate's domains and which Projects use
  them, and the host lookup is a row per host that must stay in step with the
  Tenant handle.
- Forbidden: a Product domain that Platform Intent does not admit for the
  Project; two Projects claiming one Product domain; a Tenant host written by
  hand; a Tenant found by parsing a host; an estate name longer than 32
  characters or not DNS-style.

## Confirmation

The **Product domain admission** check refuses a Product domain that Platform
Intent does not admit for the Project. The **Product domain contention** check
refuses two Projects that claim one Product domain, with both locations. The
**Tenant host derivation test** fails when a Tenant host differs from
`<handle>.<product domain>` in production or from `<handle>-staging.<product domain>`
or `<handle>-dev.<product domain>` elsewhere, or sits more than one level below
its domain. The **Host lookup test** fails when a host resolves to a Tenant by
any route but the lookup. The **Estate name check** refuses an estate name that
is longer than 32 characters or is not DNS-style.

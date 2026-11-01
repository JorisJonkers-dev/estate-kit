---
status: accepted  # proposed | accepted | locked
date: 2026-11-01
rests-on: [33, 76, 77, 80]
lessons: [DR-1, DO-2]
---

# A Tenant sends mail as its product domain until it verifies its own domain

## Context

[Record 33](0033-a-mailbox-is-declared-by-its-local-part-and-owned-by-one-project.md)
gives an Application a Mailbox on the estate's one mail domain. A Tenant is an
organisation the estate serves ([record 76](0076-tenants-are-the-organisations-the-estate-serves.md)),
and its people will receive mail from an Application. They should see the
Tenant's name, and a Tenant that cares should be able to send from its own
domain.

A message passes DMARC when its From domain aligns with a validated DKIM domain
or the SPF domain, and large receivers require it. So a Tenant domain needs its
own DKIM key published in its DNS. In Stalwart a domain that needs its own
DKIM alignment must be its own Domain object, and per-domain DKIM is in the
community edition. Stalwart's Enterprise tenant feature adds isolation, quotas
and mailboxes per Tenant, which nothing here needs
([multi-tenancy research, section 7](../research/multi-tenancy.md#7-mail-sent-as-a-tenants-domain)).

[Record 77](0077-product-domains-are-admitted-by-platform-intent.md) gives
every multi-tenant Project a Product domain, and
[record 80](0080-a-tenant-is-a-custom-resource-in-a-sixth-bounded-context-tenancy.md)
makes the Tenant a custom resource that the mailbox component reconciles and
holds a finalizer on.

## Decision

A Tenant without a Verified domain sends from `noreply@<product domain>`, with
the Tenant's display name as the sender name. This amends
[record 33](0033-a-mailbox-is-declared-by-its-local-part-and-owned-by-one-project.md):
the Mailbox is still declared by its local part and owned by one Project, and
it now also exists on each of the Tenant's Verified domains.

A Tenant Admin can ask to verify a domain of the Tenant's own. The platform
names the DKIM, SPF and DMARC records to publish, checks them in DNS, and
records the domain as verified on the Tenant resource only when all three are
found. A domain that has not passed is not used to send.

The mailbox component reconciles each Verified domain from the Tenant resource
as its own Stalwart Domain object, with its own DKIM key. It does not make an
alias of another domain, because an alias is signed with the primary domain's
keys. The Tenant's Verified domains are removed from Stalwart at Purge, and the
mailbox component releases its finalizer only after that.

Stalwart's community edition is enough. Its Enterprise tenant feature, and
hosted mailboxes for a Tenant's people, are out of scope. They need a record of
their own if they are ever wanted.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Every Tenant sends from the estate's one mail domain | No Tenant can send as itself, and one bad sender harms the estate's name | A Tenant that wants its own domain has no way to have it |
| A domain of the Tenant's own as an alias of the product domain | Mail is signed with the product domain's keys, so it does not align with the Tenant's From domain | DMARC alignment fails, which is the reason to have the domain |
| Stalwart Enterprise tenants | A commercial licence per mailbox, for isolation nothing needs yet | Community's per-domain DKIM covers outbound mail |
| An external sender such as Amazon SES | A second system, with its own identities and cost, beside the one mail server | The estate runs Stalwart already; reputation isolation is not needed yet |
| Hosted mailboxes for a Tenant's people | Quotas, directories and support for real inboxes | Applications only send; out of scope |

## Consequences

- Easier: a Tenant sends as itself without any work by the maintainer, and the
  default needs no DNS at all.
- Harder: the platform checks DNS, and a Tenant that publishes the wrong
  records stays on the product domain until it fixes them.
- The sending reputation of every Tenant is shared on one IP. A Tenant that
  abuses it harms the others; isolating reputation would be a new record.
- [Record 33](0033-a-mailbox-is-declared-by-its-local-part-and-owned-by-one-project.md) is amended: a Mailbox of a multi-tenant Project also exists on each Verified domain the Tenant resource holds.
- Forbidden: sending as a domain that has not been verified, an alias used in
  place of a Domain object, and a Verified domain left in Stalwart after a Purge.

## Confirmation

The **Tenant sender fixtures** fail when a Tenant without a Verified domain sends
from anything but `noreply@<product domain>` with its display name, or when a
domain that has not passed verification is used to send. The **Domain
verification test** fails when a domain is recorded as verified with any of its
DKIM, SPF or DMARC records missing or wrong. The **Tenant mail domain
lifecycle test** fails when a Verified domain is not its own Stalwart Domain
object with its own DKIM key, or when a Purge leaves it behind.

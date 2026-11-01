---
status: proposed  # proposed | accepted | locked
date: 2026-11-01
rests-on: [1, 75]
lessons: [MS-7, MS-6]
---

# Tenants are the organisations the estate serves, one per environment

## Context

[Record 1](0001-one-maintainer-one-cluster-one-estate.md) builds the estate for
one maintainer and one cluster, and says "there is no second tenant". It meant
no second operator and no second team. The estate is now to serve many
organisations, with a horizon of more than 1000 Tenants over the coming years,
and nothing in the model yet names one.

[Record 75](0075-three-environments-run-in-the-one-cluster.md) gives the estate
three Environments. Each has its own identity and its own data, so an
organisation known to two Environments is not one thing but two.

## Decision

A Tenant is an organisation that the estate's Applications serve, within one
Environment. The same organisation in staging and in production is two Tenants.

This replaces the words "no second tenant" in
[record 1](0001-one-maintainer-one-cluster-one-estate.md) with "no second
operator or team". A Tenant is a different thing: it is served by the estate and
does not run it. The estate still has one maintainer, whatever the number of
Tenants, and the rest of [record 1](0001-one-maintainer-one-cluster-one-estate.md) stands.

A Tenant has an immutable Tenant key, `<env letter>_<name>`, where the letter is
that of its Environment and the name matches `^[a-z][a-z0-9]{1,15}$`. The
estate uses the key everywhere inside it, never shows it to the Tenant's people,
and never reuses it, even after a Purge.

A Tenant also has a Tenant handle, which its people see in URLs. It is unique
within its Environment and can change. A former handle redirects for a grace
period of 90 days, then is free again. A handle that ends in `-staging` or `-dev` is
refused, because the hosts of those Environments end that way.

A User has one account per Environment and holds Memberships in many Tenants.

Tenancy is something a Project opts into. A Project that does not opt in is
unchanged and stays single-tenant. Kotlin services stay single-tenant until
they are rewritten in Rust.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Keep "no second tenant" and serve one organisation | The estate's products cannot be sold to another organisation | The maintainer set the direction, with a horizon of more than 1000 Tenants |
| One Tenant across all Environments | Staging data and production data share an identity, and a test touches a real organisation | An Environment has its own identity and data ([record 75](0075-three-environments-run-in-the-one-cluster.md)) |
| The handle as the identifier | A rename changes every database name, key prefix and log line | Names that appear in data must never change; the handle is for people only |
| A mutable Tenant key | An old backup, log line or message can name a different Tenant | The key must name one Tenant for ever |
| Reusing a key after a Purge | A stale message or restored backup reaches the new Tenant | A key is never reused |
| A user account per Tenant | One person signs in again for each Tenant and holds many passwords | One User per Environment holds Memberships in many Tenants |
| Every Project multi-tenant | The media apps and platform tools pay for isolation they do not need | Tenancy is opt-in; one maintainer keeps single-tenant Projects as they are |

## Consequences

- Easier: one organisation can be created, suspended and purged by its key; a
  rename touches a handle, never data; a production Tenant cannot be created by
  accident in staging.
- Harder: every multi-tenant Project carries a Tenant key through its data, and a
  handle change keeps a redirect for its grace period.
- On acceptance, [record 1](0001-one-maintainer-one-cluster-one-estate.md) is edited so that its "no second tenant" becomes "no second operator or team".
- Forbidden: a Tenant key outside the grammar, with an Environment letter that
  differs from its Environment, or reused; a handle that ends in `-staging` or
  `-dev`, or one that two Tenants of an Environment hold at once; a Tenant that
  spans two Environments.

## Confirmation

The **Tenant key grammar test** refuses a key outside `<env letter>_<name>`, and
a key whose letter differs from its Environment. The **Tenant key reuse test**
fails when a Purged Tenant's key is accepted again. The **Tenant handle test**
refuses a handle that ends in `-staging` or `-dev` or that another Tenant of the
Environment holds, and fails when a former handle stops redirecting before its
grace period ends or still redirects after it. The horizon of more than 1000
Tenants is held by no check: it is a review rule, read again with the premise of
[record 1](0001-one-maintainer-one-cluster-one-estate.md).

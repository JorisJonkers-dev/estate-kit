---
status: accepted  # proposed | accepted | locked
date: 2026-11-01
rests-on: [75, 76]
lessons: [MS-4, MS-6]
---

# Secrets are scoped by environment in their Vault path, and Tenant secrets live beneath their Project

## Context

[Record 75](0075-three-environments-run-in-the-one-cluster.md) gives the estate
three Environments in the one cluster, each with its own identity, data and
namespaces. A staging Application must never read a production secret. Vault is
shared, so the separation has to be in the path and in the role that reaches it.

[Record 76](0076-tenants-are-the-organisations-the-estate-serves.md) adds
Tenants. A multi-tenant Application holds integration keys that belong to one
Tenant, and they cannot be written at deploy time because the Tenant did not
exist then. They must be written at runtime, and a Purge must be able to find
and remove them.

## Decision

Every Vault path an Application reads is `secret/<env>/<project>/…`. The
platform derives the `<env>` and `<project>` parts. A secret grant keeps
authoring its path relative to its Project and Environment and never writes the
Environment itself, which is what [record 75](0075-three-environments-run-in-the-one-cluster.md)
allows to differ between Environments.

Each Environment's Applications have a Vault role that reaches only that
Environment's paths, and within them only their own Project's. A staging role
has no policy on a production path.

A multi-tenant Application writes Tenant-specific secrets at runtime under
`secret/<env>/<project>/tenants/<tenant key>/`. The path carries the Tenant
key, never the handle, so a handle change moves nothing. A Purge of the Tenant
([record 76](0076-tenants-are-the-organisations-the-estate-serves.md))
removes everything beneath that path.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| One path per Project for all Environments, told apart by a role | A wrong role or policy reads production from staging | The path itself should refuse it, not only the role |
| The author writes the Environment in each path | A typo or a copied value points staging at production | The platform derives what an author could get wrong |
| Tenant secrets in the Tenant's database | A database backup and a Mirror copy the keys to other Environments | A Tenant's integration keys stay out of its database |
| Tenant secrets beside the Project's, with no Tenant segment | A Purge cannot tell which secret is the Tenant's | The Tenant key in the path makes a Purge a single removal |
| A Vault path per Tenant outside the Project | A Project's policy cannot cover its Tenants' secrets, and the Project loses its boundary | Tenant secrets live beneath their Project |
| Tenant secrets written by deploy-time grants | A grant cannot name a Tenant created later | The Tenant is created at runtime, so its secrets are too |

## Consequences

- Easier: a staging Application cannot read a production secret even with a
  wrong configuration; a Purge removes a Tenant's secrets by one path.
- Harder: a multi-tenant Application needs a runtime write grant on its
  `tenants/` subtree, and a role is made per Environment per Project.
- Forbidden: a path that names an Environment in a grant, a role that reaches
  another Environment's path, a Tenant secret written outside its Tenant's
  subtree, and a handle in a Vault path.

## Confirmation

The **Secret path derivation test** fails when a grant's path is not derived
from its Environment and Project, or names either itself. The **Vault role reach
test** fails when an Application's role in one Environment reads or lists a path
of another Environment or Project. The **Tenant secret path test** fails when a
Tenant secret is written outside its Tenant's subtree, or when a Purge leaves
one behind.

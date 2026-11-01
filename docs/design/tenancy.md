# Tenancy

The estate learns what a Tenant is: an organisation its Applications serve,
within one Environment. This page is the home of that design. It holds one
section per decision, and each section is filled when its record is written.
Until then a section only says which ticket fills it. The decisions are the
Proposed records that the [register](../decisions/register.md) plans as rows
75 to 84; where a page and a record disagree, the record wins and the page is
what gets fixed. The terms are those of the [vocabulary](../vocabulary.md):
Environment, Tenant, Tenant key, Tenant handle, Tenant database, Database
server, Backup generation, Mirror, Membership, Behind, Tenant lock, Tenant
hook, Tenant Admin, Suspended, Purge and Causation id.

The whole design is the spec in
[issue 137](https://github.com/JorisJonkers-dev/estate-kit/issues/137). Two
research notes back it, with sources:
[multi-tenancy](../research/multi-tenancy.md) and
[multi-cluster](../research/multi-cluster.md). Tenancy is something a Project
opts into: media apps and platform tools stay single-tenant. Everything is
designed now and ships as additive 1.x releases of the model after the
cutover, so the shadow's parity with deploy-kit 1.0 is not disturbed.

## Who must act

| Who | What changes for them |
| --- | --- |
| estate-kit | The model gains Environments, Tenants and product domains; a sixth bounded context, tenancy, holds the lifecycle; the platform components reconcile a Tenant |
| identity (Go) | One identity per Environment, Memberships in many Tenants, Tenant Admins, and change events for Applications |
| go-commons | The tenancy library for Go: pick the database and key prefix per request or message, and refuse work without exactly one Tenant |
| rust-commons | The same library for Rust, held to the same language-neutral conformance vectors |
| Multi-tenant Applications | Keep one Tenant database per Tenant, take the Tenant from the principal, and implement the Tenant hooks they declare |

## Environments

Decided in [record 75](../decisions/0075-three-environments-run-in-the-one-cluster.md), which amends [record 9](../decisions/0009-the-live-render-is-a-signed-registry-tag-per-project-and-environment.md).

Development, staging and production run in the one cluster. Each Project in each Environment has its own signed tag, `render/<project>:<env>`, and its own namespace, `<project>-<env>`. Production moves once from `<project>-system` by a planned migration.

A merge to `main` deploys to development. A published release deploys to staging, then to production after the `production` approval, with the same digests each time. A Project chooses its Environments, and production is required. Between Environments only replicas, domains and secret paths may differ, plus one env file per Environment. Any other override is refused.

## Tenants

Decided in [record 76](../decisions/0076-tenants-are-the-organisations-the-estate-serves.md), which rewords [record 1](../decisions/0001-one-maintainer-one-cluster-one-estate.md)'s "no second tenant" as "no second operator or team".

A Tenant is an organisation the estate's Applications serve, within one Environment. The same organisation in staging and in production is two Tenants. A Tenant is served by the estate and does not run it, so the estate still has one maintainer. The design is meant to hold more than 1000 Tenants.

A Tenant has a Tenant key, `<env letter>_<name>`, that never changes and is never reused. Its name matches `^[a-z][a-z0-9]{1,15}$`. It also has a Tenant handle, which its people see in URLs. The handle is unique within its Environment and can change; a former handle redirects for a grace period. A handle that ends in `-staging` or `-dev` is refused.

A User has one account per Environment and Memberships in many Tenants. Tenancy is something a Project opts into, and a Project that does not is unchanged. Kotlin services stay single-tenant until they are rewritten in Rust.

## Domains and hosts

Decided in [record 77](../decisions/0077-product-domains-are-admitted-by-platform-intent.md), which rests on [record 10](../decisions/0010-platform-intent-admits-the-projects-and-is-pushed-like-any-project.md).

Platform Intent lists the estate's domains and the Projects admitted to use each. An Application in a multi-tenant Project names its Product domain, and its Tenant hosts are derived: `<handle>.<product domain>` in production, `<handle>-staging.<product domain>` in staging and `<handle>-dev.<product domain>` in development. Every host sits one level below the domain, so one single-level wildcard certificate covers every Environment. A per-environment override may name another Product domain that Platform Intent admits for the Project.

A Product domain that Platform Intent does not admit is refused. Two Projects that claim one Product domain are refused with a contention diagnostic that points at both. A host resolves to a Tenant through a lookup, never by parsing the host, so custom domains can later be added as more rows.

Platform Intent also holds the estate's stable name, a DNS-style name of at most 32 characters. It is the seam a later second cluster or estate can use as its cluster ID.

## Tenant data

Decided in [record 78](../decisions/0078-a-multi-tenant-project-keeps-one-tenant-database-per-tenant.md).

Each multi-tenant Project keeps one Tenant database per Tenant, named `<tenant key>_<project>` with `-` in the Project name written as `_`, such as `p_acme_tribelt`. It lives on the Database server recorded with the Tenant, never one derived from the key. The shared library opens a pool for a Tenant database on first use and closes it when idle.

Each Environment has its own Postgres server and its own Valkey, with keys prefixed `<app>:<tenant key>:` and one ACL user per Application limited to `<app>:*`. Each has one RabbitMQ vhost with shared queues. Each Project has one Garage bucket per Environment, with each Tenant's objects under its key.

The [research](../research/multi-tenancy.md#1-data-isolation-on-postgres) recommends shared tables and counts the costs of this choice: about 8 MB per empty database, a pool per database, no query across Tenants, and a migration per database. The maintainer chose it for one implementation instead of a pool and a silo, and met the costs with lazy pools and the recorded Database server.

## The Tenant of a request

Decided in [record 79](../decisions/0079-the-tenant-of-a-request-comes-only-from-the-signed-principal.md).

A request's Tenant comes from one place: the Gate's signed Principal. The Gate
looks the host up to find the Tenant, checks that the User has a Membership in
it, and signs the Tenant key and that Tenant's App Roles into the Principal and
the token. An Application trusts nothing else. A service that calls another
passes that token, or an RFC 8693 exchange of it that keeps the Tenant.

Every request and every message names exactly one Tenant. The shared libraries
refuse work with none and work with two. A producer sets a Tenant header on
each message, which belongs to no one broker, and a consumer sends a message
without one to its dead-letter queue.

A Causation id travels unchanged through every request, job and message a
chain causes. Each step keeps its own trace, linked to its cause. The Tenant
key and the Causation id go on logs and spans, never on general metric labels.

The tenancy contract and its language-neutral conformance vectors are planned.
The Rust library, the Go library and identity run them, and the contract is
Locked by default once written.

## The Tenant resource

Planned as row 80 of the [register](../decisions/register.md), filled by
[#144](https://github.com/JorisJonkers-dev/estate-kit/issues/144). A Tenant as a custom resource, Tenant hooks and finalizers, and the sixth bounded context. Amends [record 50](../decisions/0050-five-bounded-contexts.md).

_Empty until its record is written._

## Migrations

Planned as row 81 of the [register](../decisions/register.md), filled by
[#145](https://github.com/JorisJonkers-dev/estate-kit/issues/145). Waves that continue past failure, Behind, and managed Liquibase migrations.

_Empty until its record is written._

## Backups and Mirrors

Planned as row 82 of the [register](../decisions/register.md), filled by
[#146](https://github.com/JorisJonkers-dev/estate-kit/issues/146). Backup generations, schedules, the central catalogue, restores and Mirrors.

_Empty until its record is written._

## Secrets

Decided in [record 83](../decisions/0083-secrets-are-scoped-by-environment-and-tenant-secrets-live-beneath-their-project.md).

Every Vault path an Application reads is `secret/<env>/<project>/…`. The platform derives the environment and the Project, so a secret grant still writes its path relative to its Project and never names the Environment. Each Environment's Applications have a Vault role that reaches only their own Environment's paths, so a staging Application cannot read a production secret.

A multi-tenant Application writes Tenant-specific secrets at runtime under `…/tenants/<tenant key>/`, beneath its Project's path. The path uses the Tenant key, never the handle. A Purge removes everything beneath it.

## Mail

Planned as row 84 of the [register](../decisions/register.md), filled by
[#148](https://github.com/JorisJonkers-dev/estate-kit/issues/148). Sending as the product domain, and a verified domain of the Tenant's own. Amends [record 33](../decisions/0033-a-mailbox-is-declared-by-its-local-part-and-owned-by-one-project.md).

_Empty until its record is written._

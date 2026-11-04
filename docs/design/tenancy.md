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
| estate-kit | The model gains Environments, Tenants and Product domains; a sixth bounded context, tenancy, holds the lifecycle; the platform components reconcile a Tenant |
| identity (Go) | One identity per Environment, Memberships in many Tenants, Tenant Admins, and change events for Applications |
| go-commons | The tenancy library for Go: pick the database and key prefix per request or message, and refuse work without exactly one Tenant |
| rust-commons | The same library for Rust, held to the same language-neutral conformance vectors |
| Multi-tenant Applications | Keep one Tenant database per Tenant, take the Tenant from the principal, and implement the Tenant hooks they declare |

## Environments

Decided in [record 75](../decisions/0075-three-environments-run-in-the-one-cluster.md), which amends [record 9](../decisions/0009-the-live-render-is-a-signed-registry-tag-per-project-and-environment.md).

Development, staging and production run in the one cluster. Each Project in each Environment has its own signed Environment tag, `render/<project>:<env>`, and its own namespace, `<project>-<env letter>`: `-d`, `-s` and `-p`. Production moves once from `<project>-system` to `<project>-p` by a planned migration.

A merge to `main` deploys a build of `main` to development. A published release deploys to staging, then to production after the `production` approval, with the same digests in both. A Project chooses its Environments, and production is required. Between Environments only replicas, domains and secret paths may differ, plus one env file per Environment. Any other override is refused.

## Tenants

Decided in [record 76](../decisions/0076-tenants-are-the-organisations-the-estate-serves.md), which rewords [record 1](../decisions/0001-one-maintainer-one-cluster-one-estate.md)'s "no second tenant" as "no second operator or team".

A Tenant is an organisation the estate's Applications serve, within one Environment. The same organisation in staging and in production is two Tenants. A Tenant is served by the estate and does not run it, so the estate still has one maintainer. The design is meant to hold more than 1000 Tenants.

A Tenant has a Tenant key, `<env letter>_<name>`, that never changes and is never reused. Its name matches `^[a-z][a-z0-9]{1,15}$`. It also has a Tenant handle, which its people see in URLs. The handle is unique within its Environment and can change; a former handle redirects for a grace period of 90 days. A handle that ends in `-staging` or `-dev` is refused.

A User has one account per Environment and Memberships in many Tenants. Tenancy is something a Project opts into, and a Project that does not is unchanged. Kotlin services stay single-tenant until they are rewritten in Rust.

## Domains and hosts

Decided in [record 77](../decisions/0077-product-domains-are-admitted-by-platform-intent.md), which rests on [record 10](../decisions/0010-platform-intent-admits-the-projects-and-is-pushed-like-any-project.md).

Platform Intent lists the estate's domains and the Projects admitted to use each. An Application in a multi-tenant Project names its Product domain, and its Tenant hosts are derived: `<handle>.<Product domain>` in production, `<handle>-staging.<Product domain>` in staging and `<handle>-dev.<Product domain>` in development. Every host sits one level below the domain, so one single-level wildcard certificate covers every Environment. A per-environment override may name another Product domain that Platform Intent admits for the Project.

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

Decided in [record 80](../decisions/0080-a-tenant-is-a-custom-resource-in-a-sixth-bounded-context-tenancy.md), which amends [record 50](../decisions/0050-six-bounded-contexts-in-five-layers.md): the workspace has six bounded contexts, and tenancy is the sixth.

A Tenant is a custom resource, one per Tenant in its Environment. Only Delivery writes it. The platform components that hold the Tenant's data (database-catalog, identity, mailbox, backup and secret-grant) reconcile it, and each holds a finalizer, so a Purge completes only when every one has cleaned up.

The tenancy context holds the Tenant model and the Tenant operations, listed in [record 80](../decisions/0080-a-tenant-is-a-custom-resource-in-a-sixth-bounded-context-tenancy.md). Every operation is safe to retry. Each step, with its full error output, goes to an append-only operation log on the shared platform-postgres. The lifecycle API is part of Delivery's OpenAPI contract, and the maintainer and a product's sign-up flow both call it.

A multi-tenant Application takes part through the Tenant hooks it declares, which [record 80](../decisions/0080-a-tenant-is-a-custom-resource-in-a-sixth-bounded-context-tenancy.md) lists. A hook is an HTTP call with a signed machine token, the Tenant key and an operation id. A failed lock or prepare-restore hook aborts before any data changes; a failed after hook flags the Tenant. During a Tenant lock the Gate serves a standard maintenance page and a 503 with Retry-After, and the libraries hold the Tenant's work. Ending a Tenant is Suspend, a grace period of 30 days, then Purge.

![State machine: a Tenant](../diagrams/png/state-tenant.png)

## Migrations

Decided in [record 81](../decisions/0081-migrations-reach-tenant-databases-in-waves.md).

A multi-tenant Project must declare a Liquibase changelog. The compiler refuses `migration: self` and `migration: none` there.

The `migration-run` component runs each revision on every Tenant database of the Project in an Environment, in Migration waves. In production the first wave is the Canary Tenants, and the other waves follow in parallel. In development and staging all Tenant databases run in one wave. A new Tenant's databases are migrated to the current revision before after-create runs.

A failure does not stop the wave. The database is marked Behind at its last good revision, and the full output goes into the operation log. The current version keeps serving it. The Release Gate then refuses a new version of the Project in that Environment until no Tenant database there is Behind, because expand/contract only guarantees that two adjacent versions work together. The refusal is a read of cluster state, so it adds no write to [record 74](../decisions/0074-the-release-gate-and-observation-each-have-a-named-write.md).

## Backups and Mirrors

Decided in [record 82](../decisions/0082-backups-are-per-tenant-generations-and-mirrors-refresh-staging-and-development.md).

A Backup generation is a logical dump of every Tenant database of one Tenant, taken together on that Tenant's own schedule. It records each database's migration revision, is encrypted, copied off the cluster and listed in one central catalogue. This replaces the backup component's scope per Project for a multi-tenant Project. Each Postgres server also archives WAL for point-in-time recovery, for disaster only.

A restore locks the Tenant, runs the prepare-restore hook, replaces the databases, migrates each up to the target Environment's revision, runs the after-restore hook and unlocks. A generation newer than the target is refused, and the refusal names both revisions.

A staging or development Tenant may Mirror one production Tenant on a schedule. The data loads where no person can read it and is masked before the target is exposed. Development is always masked; staging is masked only when it says so. Each Project declares masking rules for its own tables, and a Project with none is not loaded into a development Mirror. Staging and production Tenants exist independently.

A Backup generation may be restored into its own Tenant or into another Tenant of an equal or lower Environment.

An unmasked staging Mirror puts production personal data in staging, so staging access must be treated like production access: who may sign in, where logs go, and how long data is kept.

## What identity must do

Identity has its own repository, which records these in its own decisions. They are obligations on identity, not estate-kit records.

- Identity runs once per Environment, each with its own Issuer.
- It holds Tenants, Memberships, Tenant-scoped Assignments and the Tenant Admin.
- The Gate resolves a host to a Tenant by lookup, checks the Membership, and signs the Tenant key and that Tenant's App Roles into the Principal and the tokens.
- An Application refreshes its extended profile from the token at every sign-in. Identity publishes UserChanged, UserRemoved and Membership-removed events on RabbitMQ, keyed by subject and carrying only the synced fields (email and name).
- Break-glass Memberships for the maintainer are time-limited and audited.
- Client redirect validation accepts the Tenant hosts under the Client's Product domain.

## Secrets

Decided in [record 83](../decisions/0083-secrets-are-scoped-by-environment-and-tenant-secrets-live-beneath-their-project.md).

Every Vault path an Application reads is `secret/<env>/<project>/…`. The platform derives the environment and the Project, so a secret grant still writes its path relative to its Project and never names the Environment. Each Environment's Applications have a Vault role that reaches only their own Environment's paths, so a staging Application cannot read a production secret.

A multi-tenant Application writes Tenant-specific secrets at runtime under `…/tenants/<tenant key>/`, beneath its Project's path. The path uses the Tenant key, never the handle. A Purge removes everything beneath it.

## Mail

Decided in [record 84](../decisions/0084-a-tenant-sends-mail-as-its-product-domain-until-it-verifies-its-own.md). Amends [record 33](../decisions/0033-a-mailbox-is-declared-by-its-local-part-and-owned-by-one-project.md).

A Tenant without a Verified domain sends from `noreply@<Product domain>`, with its display name as the sender name. A Tenant Admin can verify a domain of the Tenant's own: the platform names the DKIM, SPF and DMARC records to publish, checks them, and records the domain as verified only when all three are right. The mailbox component then reconciles it from the Tenant resource as its own Stalwart domain with its own DKIM key, and removes it at Purge.

Stalwart's community edition is enough. Its Enterprise tenant feature, and hosted mailboxes for a Tenant's people, are out of scope.

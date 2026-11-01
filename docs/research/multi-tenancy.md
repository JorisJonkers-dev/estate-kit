# Multi-tenancy

What primary sources say about serving many Tenants from one estate: about 30 Applications in Rust and Go on one Kubernetes cluster, with Postgres, Kafka and RabbitMQ, one Go OIDC provider, and development, staging and production side by side. The target is more than 1000 Tenants over several years. Research as of 2026-11-01. Every claim cites its source. A sentence that starts with **Inference** is a conclusion drawn from the sources, not something a source says.

## 1. Data isolation on Postgres

### The three models

| | Database per Tenant | Schema per Tenant | Shared tables, `tenant_id` and RLS |
|---|---|---|---|
| Isolation the database enforces | Strongest. A connection can reach only one database ([PostgreSQL](https://www.postgresql.org/docs/current/manage-ag-overview.html)) | Weak. "There is no database-level enforcement of preventing access to the wrong schema" ([PlanetScale](https://planetscale.com/blog/approaches-to-tenancy-in-postgres)) | Policy-enforced, default-deny once enabled ([PostgreSQL](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)) |
| Scale guidance | "if you anticipate 50 customers or more steer clear" ([Crunchy Data](https://crunchydata.com/blog/designing-your-postgres-database-for-multi-tenancy)) | "likely won't scale beyond a few hundred tenants" ([PlanetScale](https://planetscale.com/blog/approaches-to-tenancy-in-postgres)); "generally not to exceed several thousand" ([Crunchy Data](https://crunchydata.com/blog/designing-your-postgres-database-for-multi-tenancy)); 1 to 10,000 on Azure elastic clusters ([Azure](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/service/postgresql)) | Recommended "if you're anticipating millions of tenants" ([Crunchy Data](https://crunchydata.com/blog/designing-your-postgres-database-for-multi-tenancy)) |
| Pooling | One PgBouncer pool per database and user pair ([PgBouncer](https://www.pgbouncer.org/config.html)) | Shared pool, but `search_path` state is the hazard (below) | Shared pool; per-transaction `set_config` |
| Migrations | Once per database, plus one at every Tenant's creation ([PlanetScale](https://planetscale.com/blog/approaches-to-tenancy-in-postgres)) | Once per schema ([Crunchy Data](https://crunchydata.com/blog/designing-your-postgres-database-for-multi-tenancy)) | Once per shared table ([PlanetScale](https://planetscale.com/blog/approaches-to-tenancy-in-postgres)) |
| Per-Tenant export | `pg_dump` dumps exactly one database ([PostgreSQL](https://www.postgresql.org/docs/current/app-pgdump.html)) | `pg_dump -n`, with no guarantee the dump restores alone ([PostgreSQL](https://www.postgresql.org/docs/current/app-pgdump.html)) | Restore elsewhere and copy the Tenant's rows ([Azure](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/approaches/storage-data)) |
| Offboarding | `DROP DATABASE` | `DROP SCHEMA ... CASCADE` is one operation ([PlanetScale](https://planetscale.com/blog/approaches-to-tenancy-in-postgres)) | `DELETE` across every table keyed by `tenant_id` |

### Database per Tenant: connections and catalog

PostgreSQL states that "it is not possible to access more than one database per connection" ([PostgreSQL](https://www.postgresql.org/docs/current/manage-ag-overview.html)). PgBouncer keeps "a pool (a specific database/user pair)", and `default_pool_size` caps server connections "per user/database pair" at 20 by default ([PgBouncer](https://www.pgbouncer.org/config.html)). PlanetScale names this the main blocker: per-database pools "will quickly exceed your `max_connections` limit", and each `CREATE DATABASE` copies the template, "consuming roughly 8 MB" ([PlanetScale](https://planetscale.com/blog/approaches-to-tenancy-in-postgres)). Cross-Tenant queries become impossible inside Postgres ([PlanetScale](https://planetscale.com/blog/approaches-to-tenancy-in-postgres)). Postgres runs one process per connection, so many idle connections are inefficient ([Azure](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/service/postgresql)).

**Inference:** at 1000 Tenants and about 30 Applications, database per Tenant means tens of thousands of databases and pools. One maintainer cannot run that.

### Schema per Tenant: catalog, locks and `search_path`

Every table, index and sequence of every schema lives in the shared system catalogs, which grow "into millions of rows" and slow the planner and migrations ([PlanetScale](https://planetscale.com/blog/approaches-to-tenancy-in-postgres)). The lock table holds `max_locks_per_transaction` objects per process (default 64), and a transaction touching many tables may need it raised ([PostgreSQL](https://www.postgresql.org/docs/current/runtime-config-locks.html)). A case study of 17,000 to 19,000 schemas in one cluster reports a cross-schema `DO` block that exhausted the lock manager, autovacuum that "falls structurally behind", and a 12 TB backup set with no retention ([Command Prompt](https://www.commandprompt.com/about/success-stories-case-studies/from-unrecoverable-to-under-control-taming-multi-tenant-postgresql-at-17000-schemas/)). That source is a vendor case study.

Switching schemas with `search_path` collides with transaction pooling. PgBouncer marks `SET`/`RESET` as never supported in transaction mode ([PgBouncer](https://www.pgbouncer.org/features.html)). It skips `server_reset_query` in transaction mode, and it tracks `search_path` only on PostgreSQL 18 and later. On older servers, values changed with `SET` "leak to other clients sharing the server connection" ([PgBouncer](https://www.pgbouncer.org/config.html)). A transaction-local setting is safe: `set_config(..., is_local => true)` applies "only during the current transaction" ([PostgreSQL](https://www.postgresql.org/docs/current/functions-admin.html)). Protocol-level prepared statements work in transaction mode when `max_prepared_statements` is non-zero (default 200) ([PgBouncer](https://www.pgbouncer.org/config.html)). PostgreSQL also warns that putting a schema on `search_path` "effectively trusts all users having `CREATE` privilege on that schema" ([PostgreSQL](https://www.postgresql.org/docs/current/ddl-schemas.html)).

### Shared tables with row-level security

Once RLS is enabled with no policy, "a default-deny policy is used". Superusers and `BYPASSRLS` roles always bypass it. Table owners bypass it unless the table has `FORCE ROW LEVEL SECURITY`. `TRUNCATE` and `REFERENCES` are not subject to it. Unique, primary key and foreign key checks "always bypass row security", which can open "covert channel" leaks ([PostgreSQL](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)). Policies that compare only the current row are "the simplest and best-performing case" ([PostgreSQL](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)), and Azure advises extra indexes and performance tests ([Azure](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/service/postgresql)).

Practitioners differ on how much to lean on RLS. Azure notes that "many multitenant solutions don't use row-level security" because propagating the tenant into each query is complex ([Azure](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/approaches/storage-data)). PlanetScale treats RLS as an optional extra layer and keeps isolation in application code ([PlanetScale](https://planetscale.com/blog/approaches-to-tenancy-in-postgres)). AWS argues the other way: "isolation enforcement should not be left to service developers" but to "some shared mechanism" outside their view ([AWS](https://docs.aws.amazon.com/whitepapers/latest/saas-tenant-isolation-strategies/the-isolation-mindset.html)). Citus puts the tenant column on every table and requires primary and foreign keys to include it ([Citus](https://docs.citusdata.com/en/stable/use_cases/multi_tenant.html)). That also keeps a later move to sharding open.

### Noisy neighbours and tiers

Shared tables mean shared resources. PlanetScale suggests `statement_timeout` and `idle_in_transaction_session_timeout` as guards ([PlanetScale](https://planetscale.com/blog/approaches-to-tenancy-in-postgres)), and Azure suggests throttling or rate limiting ([Azure](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/approaches/storage-data)). AWS names three models. **Silo** gives a Tenant dedicated resources, **pool** shares them, and **bridge** mixes them, even service by service ([AWS SaaS Lens](https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/silo-pool-and-bridge-models.html)). Azure suggests a shared database for most Tenants and dedicated stamps for those "who pay more or who have unusual requirements" ([Azure](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/approaches/storage-data)). Notion keys every row by workspace ID, then spreads 480 logical shards (schemas) over 32 physical databases, 15 per database ([Notion](https://www.notion.com/blog/sharding-postgres-at-notion)). The number of schemas is fixed, and Tenants map onto them.

**Inference:** pool by default: shared tables, `tenant_id` on every table and in every key, and RLS with `FORCE`, under a non-owner role. Keep silo (a dedicated CloudNativePG cluster per Tenant) as a paid tier for the few Tenants who need it. Never create a schema or database per small Tenant.

## 2. Migrations across many Tenants

Azure lists the antipatterns. Manual schema changes are one. An application that depends on a single schema version is another; instead it should be "backwards-compatible with at least one previous schema version", and destructive changes should be sequenced "across multiple versions to support rollbacks". Azure also says to track each Tenant's schema version in a lookup table. As the fleet grows, the application tier, not the pipeline, may be the better place to trigger upgrades ([Azure](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/approaches/storage-data)). That is expand and contract. Add the new form beside the old, migrate the clients, then remove the old form. Finishing the contract step is the main risk ([Fowler](https://martinfowler.com/bliki/ParallelChange.html)).

Atlas is the clearest fan-out tooling found. Each Tenant schema or database is a target in a target group, and deployment time "increases linearly with the number of tenants" ([Atlas](https://atlasgo.io/guides/database-per-tenant/intro)). Groups run in order or by `depends_on`, so canary and internal Tenants go first. `parallel` defaults to 1. Errors either `FAIL` (stop the group) or `CONTINUE`. After a fix, re-running is safe because "targets that already reached the latest version are a no-op". Schemas in one database share an advisory lock unless lock names are set per target ([Atlas](https://atlasgo.io/guides/database-per-tenant/rollout)). Citus avoids fan-out by propagating DDL from the coordinator ([Citus](https://docs.citusdata.com/en/stable/use_cases/multi_tenant.html)). Never migrate many schemas in one transaction: that is how the 17,000-schema cluster ran out of locks ([Command Prompt](https://www.commandprompt.com/about/success-stories-case-studies/from-unrecoverable-to-under-control-taming-multi-tenant-postgresql-at-17000-schemas/)).

**Inference:** with shared tables, a migration runs once per Application database, as today. Tenant count stops mattering. Only the silo tier needs a fan-out with a version table, ordered groups, `FAIL` by default and idempotent reruns.

## 3. Tenant context propagation

### At the edge

| Source | Notes |
|---|---|
| Host or subdomain | Read from `Host` or `X-Forwarded-Host`. Ask whether the tokens carry the domain too ([Azure](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/considerations/map-requests)) |
| Path or query string | Needs a landing page that sends users to the right Tenant ([Azure](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/considerations/map-requests)) |
| Custom header | Only for APIs, or where the client is controlled and no proxy strips it ([Azure](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/considerations/map-requests)) |
| Token claim | A tenant ID claim from the identity system. Ask how a member of several Tenants picks one ([Azure](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/considerations/map-requests)) |
| API key | Look it up in a table, or HMAC-sign a key that embeds the tenant ID ([Azure](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/considerations/map-requests)) |

A hostname that identifies a Tenant does not authorize anything: "Even though the request includes a domain name or other tenant identifier, it doesn't mean you should automatically grant access" ([Azure](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/considerations/map-requests)).

### Between services

AWS calls binding a user to a Tenant a "SaaS identity". The JWT carries tenant claims, and each service forwards it, so a service can apply tenant context "without requiring a roundtrip to another service" ([AWS SaaS Lens](https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/identity-and-access-management.html)). Where a service calls on a user's behalf, OAuth token exchange issues a new token and records the caller in the `act` claim ([RFC 8693](https://www.rfc-editor.org/rfc/rfc8693.html)).

W3C Baggage is the wrong carrier for an authorization fact. The fetched spec is a Candidate Recommendation Snapshot dated 30 May 2024 ([W3C](https://www.w3.org/TR/baggage/)). It lets intermediaries add, change and delete entries, warns that values "can be propagated to other systems", and sets minimum limits of 64 entries and 8192 bytes ([W3C](https://www.w3.org/TR/baggage/)). OpenTelemetry adds that "there are no built-in integrity checks", that baggage can reach third-party APIs, and that it is not copied onto spans unless you add it ([OpenTelemetry](https://opentelemetry.io/docs/concepts/signals/baggage/)).

**Inference:** derive the tenant only from a verified token: the user's JWT, or a token exchanged from it. A gateway may also copy the tenant into a header for logs and metrics. Never authorize on that header or on baggage. A trusted gateway alone is safe only if nothing can reach a service except through the gateway.

### On Kafka and RabbitMQ

Kafka record headers (KIP-82) exist for routing, tracing, audit and signed payloads ([KIP-82](https://cwiki.apache.org/confluence/display/KAFKA/KIP-82+-+Add+Record+Headers)). Kafka's multi-tenancy guide uses topic-name prefixes, enforced by prefixed ACLs ([Kafka 3.1](https://kafka.apache.org/31/operations/multi-tenancy/)). Quotas apply per user and client ID, and are "all the more important in large multi-tenant clusters" ([Kafka](https://kafka.apache.org/43/design/design/)). OpenTelemetry says a producer "SHOULD attach a message creation context to each message", if possible so that "it cannot be changed by intermediaries" ([OpenTelemetry](https://opentelemetry.io/docs/specs/semconv/messaging/messaging-spans/)).

RabbitMQ validates the `user-id` property against the connection's user. Only a user tagged `impersonator` may set another value, and `administrator` does not grant that ([RabbitMQ](https://www.rabbitmq.com/docs/validated-user-id)). Virtual hosts give "logical grouping and separation of resources", not physical separation. They take `max-connections` and `max-queues` limits, and creating one is a blocking, cluster-wide operation of "up to a few seconds" ([RabbitMQ](https://www.rabbitmq.com/docs/vhosts)).

**Inference:** use shared topics and queues with a `tenant` header, and a payload that also carries the tenant, signed or set only by the producing service. Do not use a topic or vhost per Tenant at 1000 Tenants. Consumers treat a message with no tenant as poison and dead-letter it.

### "No tenant, no query"

In Postgres, `current_setting(name)` throws an error when the setting does not exist, unless `missing_ok` is true ([PostgreSQL](https://www.postgresql.org/docs/current/functions-admin.html)). An RLS table with no matching policy returns no rows ([PostgreSQL](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)). Rails' acts_as_tenant shows the library pattern: with `require_tenant`, it raises `NoTenantSet` "whenever a query is made without a tenant set", and `without_tenant` is the explicit escape ([acts_as_tenant](https://github.com/ErwinM/acts_as_tenant)).

Leaks have known routes. A session `SET` leaks through a transaction pooler ([PgBouncer](https://www.pgbouncer.org/config.html)). Table owners and `BYPASSRLS` roles skip RLS, and constraint checks can act as covert channels ([PostgreSQL](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)).

**Inference:** a shared Rust crate and a shared Go module should open every transaction with `set_config('app.tenant_id', $1, true)` and refuse to run without a tenant. RLS backstops that check, and one integration test per Application should prove that a query without a tenant fails.

## 4. Identity

### One person, many Tenants

Azure advises: "Use a single identity for each person when possible". Separate identities fit only work-and-personal splits or strict residency rules. Store mappings by "immutable, unique identifiers for both the tenant and the user". Typically "a tenant identifier claim is added to the token". Users need "a clear mechanism" to switch Tenant, and the design must decide whether profile data one Tenant adds is visible to another ([Azure](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/considerations/identity)). Azure also keeps entitlements in the application or a dedicated service, injected as claims at login, rather than in the identity system ([Azure](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/considerations/identity)). OIDC defines no tenant claim among its standard claims ([OIDC Core](https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims)), so each provider names its own.

### Organisation-aware providers as reference designs

| Provider | Model | Tenant in the token |
|---|---|---|
| Keycloak Organizations (since 25) | Organizations inside one realm. A user can belong to several; per-organization identity providers and groups ([Keycloak](https://www.keycloak.org/2024/06/announcement-keycloak-organizations), [Keycloak](https://www.keycloak.org/2026/04/org-groups)) | `organization` scope. A member of several picks one at login; `organization:<alias>` or `organization:*` requests several ([Keycloak](https://www.keycloak.org/docs-api/latest/javadocs/org/keycloak/organization/protocol/mappers/oidc/OrganizationScope.html)) |
| Zitadel | Instance, then organizations. Each user sits in one organization's pool; project grants share a project with another organization ([Zitadel](https://zitadel.com/docs/concepts/structure/organizations)) | Reserved scope `urn:zitadel:iam:org:id:{id}` ([Zitadel](https://zitadel.com/docs/concepts/structure/organizations)) |
| Auth0 Organizations | "Any user may belong to multiple organizations". Per-organization connections and roles ([Auth0](https://auth0.com/docs/manage-users/organizations/organizations-overview)) | `org_id`. APIs must check that it is "a value already known to the application" and otherwise reject the token ([Auth0](https://auth0.com/docs/manage-users/organizations/using-tokens)) |

### Getting profile fields to Applications

| Mechanism | Strength | Weakness |
|---|---|---|
| Claims at login | No extra moving part; Azure's entitlement pattern ([Azure](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/considerations/identity)) | **Inference:** stale until the next token |
| SCIM 2.0 push | Standard user schema and protocol ([RFC 7644](https://www.rfc-editor.org/rfc/rfc7644)); a deleted resource MUST return 404 and drop out of queries ([RFC 7644 §3.6](https://www.rfc-editor.org/rfc/rfc7644#section-3.6)); `active` marks administrative status ([RFC 7643](https://www.rfc-editor.org/rfc/rfc7643#section-4.1.1)) | **Inference:** each Application has to run a SCIM server |
| Events on Kafka | **Inference:** fits the estate's existing bus; replayable | Needs an outbox and idempotent consumers |

For revocation, OIDC Back-Channel Logout (Final) sends a signed Logout Token from the provider straight to each Relying Party ([OpenID](https://openid.net/specs/openid-connect-backchannel-1_0.html)). CAEP 1.0, final in August 2025 alongside SSF 1.0, defines a `session-revoked` event ([OpenID CAEP](https://openid.net/specs/openid-caep-1_0-final.html), [OpenID Foundation](https://openid.net/three-shared-signals-final-specifications-approved/)). SCIM is the standard way for enterprise customers to automate onboarding and offboarding, and federation is the alternative ([Azure](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/considerations/identity)).

**Inference:** the Go provider should hold one global user and a membership table (Tenant, user, roles), as Keycloak and Auth0 do, and issue an access token scoped to the Tenant the user picked. Applications key their extended profile by (issuer, `sub`, Tenant). They take shared fields from membership events on Kafka, and read only authorization-critical facts from claims. Deprovisioning removes the membership, emits an event, and sends a back-channel logout. SCIM in, from customers' directories, can come later.

## 5. Tenant lifecycle

Azure's stages are trial, onboarding, updates, scaling, moving, merging and splitting, offboarding with a retention period, and deactivation. Deactivation is "intended to be a temporary state" ([Azure](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/considerations/tenant-life-cycle)). AWS's SaaS Builder Toolkit splits a control plane from the application plane. The control plane publishes `onboardingRequest`; the application plane provisions and answers `provisionSuccess`. Offboarding is the same with `offboardingRequest` and `deprovisionSuccess`, and Step Functions run each job ([AWS SBT](https://github.com/awslabs/sbt-aws/blob/main/docs/public/README.md)).

A saga is "a reliably coordinated sequence of local transactions". It is coordinated by events (choreography) or by an orchestrator, undoes completed steps with compensating transactions, and gives up isolation between concurrent sagas ([microservices.io](https://microservices.io/patterns/data/saga.html)). Atlas shows the retry stance: re-running converges, because finished targets are a no-op ([Atlas](https://atlasgo.io/guides/database-per-tenant/rollout)).

Deletion has to reach backups. The ICO expects erasure from backups too. A backup copy may wait until it is overwritten, if it is put "beyond use" and the data subject is told ([ICO](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/individual-rights/right-to-erasure/)). Crypto-shredding encrypts each Tenant's data under its own key and destroys the key. Azure describes this for customer-managed keys: "deleting the associated key ensures that their data is no longer accessible" ([Azure](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/service/postgresql)). For Kafka, an engineering write-up argues it is among the few workable approaches, because a customer's records are interleaved in shared partitions ([Unite](https://techblog.unite.eu/the-right-to-erasure-from-sequential-storages-2fffe822139b)). No regulator ruling was found on whether key destruction alone satisfies Article 17 of the GDPR ([GDPR](https://eur-lex.europa.eu/eli/reg/2016/679/oj)).

**Inference:** model the Tenant as a record with states (Provisioning, Active, Deactivated, Offboarding, Deleted), owned by one orchestrator. Each step calls an idempotent per-Application endpoint, or emits an event keyed by Tenant and step and waits for the acknowledgement. Encrypt personal fields and event payloads under a per-Tenant data key, so that destroying the key covers Kafka retention and physical backups until they age out.

## 6. Backups, and production into staging

CloudNativePG takes physical backups only: base backups of the whole cluster's data files plus a WAL archive. Together they give PITR and, with WAL archiving, an RPO of at most 5 minutes ([CloudNativePG](https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/main/docs/src/backup.md)). Logical `pg_dump` backups are "not suitable for business continuity" and not managed by the operator. Object-store backups have retention policies and volume snapshots do not. Native Barman Cloud support ends at 1.31; from 1.32 the Barman Cloud plugin replaces it ([CloudNativePG](https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/main/docs/src/backup.md)). Recovery is "not performed in-place". It bootstraps a new cluster to a `targetTime`, `targetLSN` or `targetName` ([CloudNativePG](https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/main/docs/src/recovery.md)).

Per-Tenant restore from a shared database means restoring to a separate resource and selectively recovering that Tenant's data ([Azure](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/approaches/storage-data)). Azure lists separate keys, separate backup and restore policies, and data residency as reasons to give a Tenant its own resources ([Azure](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/approaches/storage-data)).

Copying production into staging copies personal data. Pseudonymised data stays personal data (Recital 26). Purpose limitation and data minimisation (Article 5(1)(b) and (c)), data protection by design (Article 25) and security of processing (Article 32) all apply ([GDPR](https://eur-lex.europa.eu/eli/reg/2016/679/oj)). The EDPB adopted pseudonymisation guidelines on 16 to 17 January 2025, covering Articles 5, 25 and 32 ([EDPB](https://edpb.europa.eu/news/news/2025/edpb-adopts-pseudonymisation-guidelines-and-paves-way-improve-cooperation_en)). PostgreSQL Anonymizer declares masking rules in the schema with `SECURITY LABEL`. It offers static masking, dynamic masking, anonymous dumps, replica masking and masking views ([PostgreSQL Anonymizer](https://postgresql-anonymizer.readthedocs.io/en/stable/)).

**Inference:** keep one backup catalogue (the CloudNativePG `Backup` objects plus the object-store retention), whole-cluster per Application database. Restore a Tenant by recovering to a scratch cluster and copying its rows. To refresh staging, recover into an isolated namespace no person can read, run static masking, then expose the masked copy. A masking rule then becomes part of each migration that adds a personal column.

## 7. Mail sent as a Tenant's domain

DMARC is now RFC 9989 (May 2026, Standards Track, obsoleting RFCs 7489 and 9091). A message passes when the From domain aligns with a validated DKIM `d=` domain or the SPF MAIL FROM domain, in relaxed (same organisational domain) or strict (identical) mode ([RFC 9989](https://www.rfc-editor.org/rfc/rfc9989.html)). Gmail requires SPF or DKIM from all senders. Senders of more than 5000 messages a day need both, plus DMARC (policy may be `none`), From alignment, and one-click unsubscribe for marketing mail ([Google](https://support.google.com/a/answer/81126)). So each Tenant domain needs a DKIM key published in its DNS, and an aligned SPF or MAIL FROM.

| | Stalwart Community | Stalwart Enterprise | Amazon SES |
|---|---|---|---|
| License | AGPL-3.0 ([Stalwart](https://stalw.art/compare/)) | Commercial, per mailbox; reverts to Community on cancellation ([Stalwart](https://stalw.art/compare/)) | Pay per use |
| DKIM per domain | Included ([Stalwart](https://stalw.art/compare/)). Keys generated per domain, Ed25519 plus RSA; rotation only with automatic DNS management ([Stalwart](https://stalw.art/docs/mta/authentication/dkim/sign/)) | Same | Per identity ([SES](https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dkim-easy.html)) |
| Tenant isolation | Not included ([Stalwart](https://stalw.art/compare/)) | Tenants with quotas and isolation, per-domain directory backends, SCIM, branding ([Stalwart](https://stalw.art/enterprise/)) | Tenants pause one at a time on bounce or complaint thresholds; per-Tenant suppression lists; activity still rolls up to the account ([SES](https://docs.aws.amazon.com/ses/latest/dg/tenants.html), [AWS](https://aws.amazon.com/about-aws/whats-new/2026/06/amazon-ses-tenant-level-suppression-lists/)) |

In Stalwart, mail from an alias domain is signed with the primary domain's keys, so a domain that needs its own DKIM alignment must be its own Domain object ([Stalwart](https://stalw.art/docs/mta/authentication/dkim/sign/)).

**Inference:** outbound mail from Applications as a Tenant's domain needs only per-domain DKIM, which Community has. Each Tenant domain is one Stalwart Domain object; the Tenant publishes its DKIM, SPF and DMARC records, or delegates them by CNAME. Enterprise pays only once Tenants get mailboxes, per-Tenant quotas or SCIM. Sending reputation stays shared on one IP, which is where SES tenants would help.

## Conclusions for estate-kit

1. Default to the pool model: shared tables, `tenant_id` on every table and key, RLS with `FORCE` under a non-owner role. Keep a dedicated CloudNativePG cluster as a silo tier for Tenants who pay for isolation.
2. Rule out schema per Tenant and database per Tenant for small Tenants at 1000 or more. Catalogs, locks, pools and migration fan-out grow with Tenant count, and one maintainer cannot absorb that.
3. Use PgBouncer in transaction mode, setting the tenant with transaction-local `set_config` in a shared Rust and Go data-access layer that refuses to run without one. Never use session `SET` or `search_path`.
4. Shared tables make migrations independent of Tenant count. Expand and contract stays mandatory, and the silo tier needs a fan-out with a version table and idempotent reruns.
5. The tenant comes from a verified token: the user's JWT, or one exchanged from it. Baggage and plain headers are for observability only.
6. On Kafka and RabbitMQ, use shared topics and queues, with the tenant in a header and in the payload, set only by the producing service. Quotas, prefixed ACLs and RabbitMQ's validated `user-id` protect the producer's identity.
7. Make the Go provider organisation-aware, after Keycloak Organizations: a global user, Tenant memberships, a tenant claim for the selected Tenant, and back-channel logout. Push membership and profile events to Applications.
8. Run the Tenant lifecycle as an orchestrated saga over idempotent per-Application steps. Encrypt under per-Tenant keys so that offboarding reaches Kafka and backups.
9. Backups stay whole-cluster with PITR. Per-Tenant restore is a recover-and-copy, and staging gets only masked copies.
10. Stalwart Community covers sending as a Tenant's domain, with one Domain object per Tenant domain. Enterprise or SES tenants matter only when per-Tenant mailboxes or reputation isolation do.

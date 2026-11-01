---
status: proposed  # proposed | accepted | locked
date: 2026-11-01
rests-on: [75, 76]
lessons: [MS-7, DR-1]
---

# A multi-tenant Project keeps one Tenant database per Tenant, on a Database server recorded with the Tenant

## Context

[Record 76](0076-tenants-are-the-organisations-the-estate-serves.md) makes the
Tenant the unit the estate serves, and [record 75](0075-three-environments-run-in-the-one-cluster.md)
gives each Environment its own data. A multi-tenant Project must now decide where
a Tenant's data lives, and the horizon is more than 1000 Tenants.

The [research](../research/multi-tenancy.md#1-data-isolation-on-postgres) compares
three models, and it recommends shared tables with row-level security as the
default. It names the costs of a database per Tenant:

- Every `CREATE DATABASE` copies the template, which takes about 8 MB, even when
  the database stays empty.
- A connection reaches one database only, and PgBouncer keeps one pool per
  database and user pair. Per-database pools can exceed `max_connections`.
- A query cannot span Tenants inside Postgres.
- A migration runs once per database, and once more at each Tenant's creation.
- At 1000 Tenants and about 30 Applications the research counts tens of
  thousands of databases and pools, and says one maintainer cannot run that.
  That count assumes every Application is multi-tenant. Here only the few
  Projects that opt into tenancy keep Tenant databases, and only for the
  Tenants that use them: at 1000 Tenants and five such Projects, at most
  5000 databases in production.

The maintainer has chosen a database per Tenant regardless, for the reasons below.

## Decision

Each multi-tenant Project keeps one Tenant database per Tenant. It is named
`<tenant key>_<project>`, with `-` in the Project name written as `_`, so the
Tenant database of Tenant `p_acme` for Project `tribelt` is `p_acme_tribelt`, and
all of one Tenant's databases list together by its key.

The Tenant database lives on the Database server recorded with the Tenant. The
estate never derives the server from the Tenant key. Each Environment has its own
Postgres server, so a Tenant's databases sit on a server of its Environment. A
Tenant moves to another server only by an explicit move.

The shared tenancy library keeps a connection pool per Tenant database. It opens
the pool on the first request for that database and closes it after it has been
idle for a set time, so the number of open pools follows the Tenants in use, not
the Tenants that exist.

The other stores are scoped by Environment and carry the Tenant key:

| Store | One per | The Tenant is kept apart by |
| --- | --- | --- |
| Postgres server | Environment | A Tenant database per Tenant |
| Valkey | Environment | Keys prefixed `<app>:<tenant key>:`, and one ACL user per Application limited to `<app>:*` |
| RabbitMQ | Environment, one vhost | Shared queues, with the Tenant key on each message |
| Garage | Project and Environment, one bucket | Each Tenant's objects under its key |

A single-tenant Project is unchanged: it keeps one database and no key prefix.

The research names the cost; the maintainer chose to pay it. One implementation
serves every Tenant, where shared tables for most Tenants and a database for a
few would need a pool and a silo in the same code. A Tenant's data is backed up,
restored and dropped one database at a time, and a connection cannot reach
another Tenant's data. The 8 MB and the pools are met by the lazy,
idle-expiring pools and by the recorded Database server, which lets a full server
be relieved by moving Tenants to a second one.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Shared tables with a Tenant column and row-level security | Isolation rests on a policy on every table, owner and superuser roles bypass it, and a Tenant's backup and Purge become row copies and deletes | The maintainer chose one implementation with isolation by construction, and backup, restore and Purge of one database |
| Shared tables for most Tenants and a database for the few that pay | Two implementations, a pool and a silo, in every library and every migration path | One implementation for every Tenant |
| A schema per Tenant | Weak isolation, catalogs and lock tables that grow with Tenant count, and a `search_path` that leaks under transaction pooling | The database gives no enforcement, and the research counts the scaling costs |
| A Database server derived from the Tenant key | Moving a Tenant means renaming it, and the key encodes a placement | The server is recorded with the Tenant, so a second server is a placement choice |
| A pool open for every Tenant database at start | One pool per database and user pair for every Tenant, which exceeds `max_connections` | Pools open lazily and expire when idle |
| A RabbitMQ vhost or a Valkey instance per Tenant | Tens of thousands of vhosts or instances | One vhost and one Valkey per Environment, with the Tenant key on each message and key |

## Consequences

- Easier: backing up, restoring and dropping one Tenant is one database at a
  time; a connection cannot reach another Tenant's data; one implementation
  serves all Tenants; a full server is relieved by moving Tenants.
- Harder: at 1000 Tenants a Project has 1000 databases, each about 8 MB empty
  and each migrated on its own; the library must keep and expire a pool per
  database; no query spans Tenants inside Postgres, so a report runs one Tenant
  at a time.
- Forbidden: a Tenant database named other than by its Tenant key and Project;
  a Database server derived from a key; a Valkey key without its prefix; an
  Application's ACL user that reaches another Application's keys; a Tenant's
  object outside its key's prefix.

## Confirmation

The **Tenant database name test** refuses a name other than
`<tenant key>_<project>` with `-` written as `_`. The **Database server lookup
test** fails when a library derives the server from the key. The **Tenant pool
lifecycle test** fails when a pool is opened before it is needed or stays open
after its idle expiry. The **Valkey scope test** fails on an unprefixed key or an
ACL user that reaches another Application's keys. The **Environment store
fixtures** fail when an Environment has more than one of a store or a Project has
more than one bucket. The **Object prefix test** fails when an object is written
outside its Tenant's prefix, or a Purge leaves one. The choice itself, a database
per Tenant over shared tables, is a maintainer's decision that no check holds;
it is read again if the research's counts of databases and pools prove wrong.

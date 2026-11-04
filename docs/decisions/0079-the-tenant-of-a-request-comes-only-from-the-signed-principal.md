---
status: accepted  # proposed | accepted | locked
date: 2026-11-01
rests-on: [76]
lessons: [CS-3, TM-4]
---

# The Tenant of a request comes only from the Gate's signed principal, one request or message names exactly one Tenant, and a Causation id ties traces together

Amended by [record 114](0114-multi-tenant-projects-keep-their-tenants-in-shared-tables-separated-by-row-level-security.md):
a multi-tenant Application keeps its Tenants in shared tables, and the tenancy
library sets `SET LOCAL app.tenant_id` from the signed Principal in every
transaction. The text below says so.

## Context

[Record 76](0076-tenants-are-the-organisations-the-estate-serves.md) makes the
Tenant a thing the estate serves, and a multi-tenant Application keeps its
Tenants in shared tables, separated by row-level security
([record 114](0114-multi-tenant-projects-keep-their-tenants-in-shared-tables-separated-by-row-level-security.md)). If a request
could pick its own Tenant, one forged header would read another Tenant's rows. If a message carried no
Tenant, or two, a consumer would have to guess.

Identity already signs a Principal for every request: the Gate signs a header
that applications read through the Principal contract, and the contract has
language-neutral conformance vectors that each adapter must meet. A request
for a Tenant's host also passes the Gate, which can know the host, the User
and the User's Memberships. Today no request, message or log line says which
Tenant it is for, and a trace stops at the first asynchronous hop.

## Decision

The Gate resolves the request's host to a Tenant through a lookup, never by
parsing, and checks that the User holds a Membership in it. It then puts the
Tenant key and that Tenant's App Roles into the signed Principal and into the
token. This is a new minor version of the Principal contract: it only adds
optional fields.

An Application takes the Tenant only from the verified signed Principal or
token, never from a header, path, query or body the caller wrote. A service
that calls another passes the token, or an RFC 8693 exchange of it that keeps
the Tenant. A caller cannot name a different Tenant in the exchange.

A message carries a Tenant header, defined independently of any broker, and
the Causation id. The producer sets both. A consumer sends a message without a
Tenant to its dead-letter queue and never processes it.

Every request and every message names exactly one Tenant. The shared libraries
refuse work that has none and work that has two, and no API accepts two.
The tenancy library carries that one Tenant into the database: it runs
`SET LOCAL app.tenant_id` with it in every transaction, as
[record 114](0114-multi-tenant-projects-keep-their-tenants-in-shared-tables-separated-by-row-level-security.md) sets out.

A Causation id travels unchanged in every outgoing request, job record and
message that a chain causes. Each step keeps its own trace, and starts a new
trace with a link to its cause. The Tenant key and the Causation id go on
every log line and span. They are never general metric labels, because a label
value per Tenant is a series per Tenant.

The tenancy contract, and the language-neutral conformance vectors for every
rule above, are planned in `contracts/`. The Rust library, the Go library and
identity each run the vectors. As a contract it is Locked by default once
written.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| The Tenant from the host, parsed by each Application | Each Application re-implements the lookup, and a custom domain needs code in all of them | The Gate resolves the host once, through a lookup, and signs the answer |
| The Tenant from a request header, checked by the Application | A forged header is one missing check from a breach of another Tenant | An Application trusts only a value identity signed |
| A request that may name several Tenants | A bug in one query touches two Tenants' data, and no backup, lock or Purge can treat a request as inside one | One request or message names exactly one Tenant |
| A message without a Tenant is processed with a default | A missing header touches the wrong Tenant's rows | The consumer refuses it and sends it to the dead-letter queue |
| A Tenant header defined by one broker's own format | Adding Kafka later rewrites every producer and consumer | A broker-neutral header needs only an adapter per broker |
| One trace across a whole chain | A job that runs for hours makes one trace unreadable, and latencies stop meaning anything | A trace per step, tied by the Causation id and a link to its cause |
| The Tenant key as a metric label | One series per Tenant on every metric, past 1000 Tenants | Logs and spans carry the Tenant key; metrics do not |
| A library for Rust only | Go Applications and identity drift from it | Both libraries and identity run the same vectors |

## Consequences

- Easier: an Application keeps no role tables and no host lookup; a forged
  header has nothing to forge; a log line or a span is filtered by Tenant and
  by chain; adding a broker needs only an adapter.
- Harder: the Principal contract gains a minor version that identity, rust-commons
  and go-commons must all pin; every producer must stamp the headers; a Kotlin
  service cannot use the library and stays single-tenant.
- Forbidden: a Tenant from anywhere but the signed Principal or token; a request
  or message with no Tenant or with two; a token exchange that changes the
  Tenant; a message processed without a Tenant header; a Causation id changed
  along a chain; the Tenant key or Causation id as a general metric label.

## Confirmation

The **Tenancy conformance vectors** run in the Rust library, the Go library and
identity, and fail when any of them concludes a different Tenant, refusal or
dead-letter outcome than a vector states: a Tenant read from anywhere but the
signed Principal, a request or message with no Tenant or two, an exchange that
changes the Tenant, and a message without the Tenant header. The **Causation id chain
test** fails when a request, job or message that a chain causes carries a
different Causation id, or a step has no trace of its own or no link to its
cause. The **Tenant telemetry label lint** fails when a metric has the Tenant
key or the Causation id as a label, or a log line or span from a multi-tenant
Application lacks them.

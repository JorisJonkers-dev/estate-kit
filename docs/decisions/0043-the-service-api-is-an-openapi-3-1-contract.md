---
status: accepted  # proposed | accepted | locked
date: 2026-10-30
rests-on: [15, 17]
lessons: [DR-4]
---

# The service API is an OpenAPI 3.1 contract

## Context

The service ([record 17](0017-the-service-runs-in-the-cluster-in-rust.md)) is
called by Project CI, the Vue UI, Observation and the Release Gate. Its payload
shapes are already contract: the committed JSON Schemas
([record 15](0015-the-rust-types-agree-with-the-committed-schemas-on-their-corpus.md)).
Routes, status codes, the stream's event types and pagination are not covered
by schemas alone, and they are what a client breaks on.

Errors reach callers too. The compiler's diagnostics already carry codes from
one catalogue ([record 71](0071-a-diagnostic-is-a-coded-problem-with-typed-locations.md)).

## Decision

The service's API is one OpenAPI 3.1 document, committed under `contracts/`.
It describes every endpoint and every server-sent event type, and references
the committed JSON Schemas for payloads. The axum routes are written from it
and the Vue client is generated from it; neither is the source.

An error is an RFC 9457 problem document whose `type` names one code from the
catalogue that compiler diagnostics also use, so one rendering path serves every
error. The document's detail (paths, pagination, headers) lives in the
committed file and on [conventions](../design/conventions.md), not here.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| JSON Schemas only | Routes and status codes live in code and drift from clients | Routes and status codes are contract too |
| Routes first, document generated from code | The contract is whatever the code does | The committed document is the only interface source |
| A diagnostics list as the only error shape | HTTP errors need a second shape | One rendering path for every error |

## Consequences

- A client change is a document change first, reviewed as a contract.
- The document is Locked by default, so changing it needs the maintainer.
- Every error code needs a catalogue entry and a fixture.

## Confirmation

- The **OpenAPI route contract test** checks the axum routes and their request and response types
  against the committed document, and fails on a route not in it.
- The **OpenAPI lint** runs in CI, including the cursor-pagination rule.
- The **Error catalogue test** checks that every catalogue code has an entry and
  a fixture, and the **UI stub validation** that each UI stub validates against
  the document.

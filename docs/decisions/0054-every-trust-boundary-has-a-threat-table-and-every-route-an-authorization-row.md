---
status: accepted  # proposed | accepted | locked
date: 2026-10-30
rests-on: [17]
lessons: [TM-4]
---

# Every trust boundary has a threat table, and every route an authorization row

## Context

The estate-kit service signs what the clusters and the nodes run, so a
mistake in it reaches every host. Its trust boundaries are named on
[security](../design/security.md#trust-boundaries): runner to edge, browser to
edge, service to Vault, to ghcr and to the API server, Flux and the host
applier to the API, applier to cache, and break-glass. Signing and break-glass
are the paths most worth examining, and a matrix alone does not examine them.

An authorization matrix that nobody tests decays: a new route ships with no
row, and its access is whatever the code happens to do.

## Decision

Each trust boundary has a threat table in STRIDE form: a threat, and the
mitigation that answers it. A new boundary is not added without one.

Every route has exactly one row in the authorization matrix, naming which
callers may act. A route without a row fails a test, and the matrix is tested
against the routes, not only read. Both artefacts live on the security page;
this record fixes that they exist and that tests enforce the matrix.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| The authorization matrix only | The signing and break-glass paths are never examined | Signing and break-glass get examined only by a threat table |
| Threat tables only | A route's access is a sentence nobody runs | A test needs a row per route |
| A review at release time | Findings arrive after the design is built | The tables are written with the boundary |

## Consequences

- A new route needs a row in the same pull request, or its test fails.
- A new boundary or a new mitigation is a change to a table, reviewed with it.
- A mitigation the table names must have a check or test behind it, and the
  threat table points at it.

## Confirmation

- A test lists the OpenAPI document's routes ([record 43](0043-the-service-api-is-an-openapi-3-1-contract.md)),
  fails on a route with no matrix row and on a row with no route.
- For each caller and route, a test asserts the denied rows are refused, with
  a negative fixture for a caller not in the row.

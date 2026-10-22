# Research summary

Three research passes back the design. The papers sit in the private
`papers/` submodule; this page holds only what they imply.

## Hosts and delivery

- **Copy first, then switch.** Copy every node's closure before any switch;
  only the switch or reboot is serialised.
- **Drain through the cluster.** One lock in the API server, eviction through
  the Eviction API so PodDisruptionBudgets hold; never `kubectl drain` over SSH.
- **The window gates the start** of a reboot, not its end; reboot only when the
  booted generation differs.
- **No mutable central store.** Desired state stays in signed renders; observed
  state and locks stay in the cluster.
- **Small level-triggered controllers**, one compiler, coordinating through API
  objects.
- **Mixed versions break upgrades**, hence the k3s version skew check.
- **Test the controller** for crash-between-steps bugs; every step idempotent
  and resumable.

## Contracts, data and architecture

| # | Implication | Status in the design |
| --- | --- | --- |
| 1 | CI checks schema N+1 against N, classifies the change, and fails if the version bump disagrees | Settled |
| 2 | Within a major version only additive changes; renames go alias, deprecate, remove; removed names never reused | Settled |
| 3 | A break is allowed, but it means a major version and a record | Settled |
| 4 | Authored YAML rejects unknown keys; `result.json` readers ignore unknown fields within one major and reject an unknown major | Settled |
| 5 | Each payload carries its contract version; the service accepts the current major and the one before | Settled |
| 6 | The Go service commits contract fixtures for the `result.json` fields it reads; Rust CI verifies its real output against them | Settled |
| 7 | Generated Go types are never edited, with a regenerate-and-diff gate | Settled |
| 8 | Property tests generated from the schemas and the OpenAPI file | Open |
| 9 | Parse, don't validate: one boundary step turns YAML into refined types and reports every error | Settled |
| 10 | Invariants types cannot hold become postconditions of the resolve step | Open |
| 11 | Events are past-tense, typed and versioned, evolved by upcasting; no personal data in events | Settled |
| 12 | The event log stays internal; `result.json` is the published language | Settled |
| 13 | Migrations are typed operation lists, each expand or contract, never both on one object in one release | Partly: expand and contract are already the rule |
| 14 | Bounded contexts: compiler, service, host applier, components; the applier behind an anticorruption layer; a Project is the aggregate root | Settled |
| 15 | Ports are role interfaces the core needs; adapters own third-party clients; boundaries enforced by crates and packages | Settled |

## Redesign practice

See [redesign-practices.md](redesign-practices.md). Two corrections it made to
earlier guidance: "Locked" is not a standard status, so a Locked record is an
accepted MADR record with a Confirmation section; and the IETF Idempotency-Key
draft expired, so deploy calls use the natural key instead.

## Still missing from the papers

| Year | Source | Where |
| --- | --- | --- |
| 2000 | Claessen and Hughes, QuickCheck | ACM Digital Library, 10.1145/351240.351266 |
| 2018 | Ruprecht et al., VM Live Migration at Scale | ACM Digital Library, 10.1145/3186411.3186415 |
| 2013 | van der Burg, A Reference Architecture for Distributed Software Deployment (PhD thesis) | TU Delft repository |

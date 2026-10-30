# Conventions

The rules every part follows, so no part improvises at a seam. Each becomes a
record, and a check enforces it.

| Area | Convention | Enforced by |
| --- | --- | --- |
| Service API | OpenAPI 3.1 for every endpoint and SSE event type, referencing the committed JSON Schemas | A test that the axum routes and their request and response types match the committed document; the Vue client generated from it |
| Errors | RFC 9457 problem+json; `type` names one code from the catalogue the compiler's diagnostics also use | A test that every code has a catalogue entry and a fixture |
| Retries | A deploy call is idempotent on (project, fragment digest); no Idempotency-Key header | A test that a retry returns the same rollout |
| Ordering | Events are ordered by sequence within one rollout | The event log's unique (rollout id, sequence) key |
| Delivery | The stream is at-least-once; clients resume by sequence and drop duplicates | A resume test |
| Lists | Cursor pagination | The OpenAPI lint |
| IDs | UUIDv7, generated in Rust (Postgres 17 has no native generator) | A newtype, not a string |
| Time | RFC 3339 in UTC | The schema lint |
| Empty values | An optional field is absent; `null` is never valid | The schema lint |
| Retention | Rollout events kept 400 days. Renders kept if among a Project's last 20, younger than 90 days, or named by a tag | A nightly job that refuses to delete a tagged render |
| Telemetry | OpenTelemetry traces to Tempo, JSON logs to Loki with `rollout_id`, `project` and `trace_id`; the run id is a span attribute | A log-field lint |
| Configuration | One typed config per binary: flags override `ESTATE_KIT_<SECTION>_<KEY>` environment variables, which override a file; defaults live in code beside the type | A config lint |
| Secrets | Never a value in config, only a reference (a Vault path or a mounted file) | The config lint refuses anything that looks like a secret |
| Never logged | Tokens, private key material, generated secrets | A secret scan of test logs |

## Service levels

| Objective | Target |
| --- | --- |
| Deploy accepted to serving | p95 under 10 minutes |
| Deploy endpoint available | 99% per month, outside maintenance windows |
| Drift found | within 24 hours |

Chosen because they are numbers the maintainer will act on. A host rollout
within one window was rejected as a service level.

## Contracts and their evolution

- **Schemas.** CI diffs each committed schema against the last release,
  classifies the change and fails when the version bump disagrees. Within a
  major version only additive changes; new fields are optional or defaulted. A
  rename goes alias, deprecation, removal, and a removed name is never reused.
  A break needs a major version and a record.
- **Strictness.** Authored YAML rejects unknown keys. Payloads carry their
  contract version; the service accepts the current major and the one before.
- **Consumer contract.** The service links the compiler, so the types are
  shared and need no consumer fixtures ([record 18](../decisions/0018-the-service-links-the-compiler.md)).
  The CLI's `--json` output keeps a committed schema for the workflows that
  read it.
- **Events.** Each event has a type and a version; events are never rewritten,
  and no upcaster is built until a second version exists
  ([record 23](../decisions/0023-a-rollout-is-an-append-only-event-log-on-the-shared-postgres.md)). Events hold no personal data: actors are ids, resolved
  at read time. The event log stays internal.

## Bounded contexts

Five contexts, each boundary its own record
([record 50](../decisions/0050-five-bounded-contexts.md)), drawn on
[The Rust workspace](rust-workspace.md#bounded-contexts). A Project
is the aggregate root; other Projects refer to it by id only.

![Context map](../diagrams/png/context-map.png)

## Port safety

- The shadow composition writes only unsigned `shadow/<project>:<digest>` tags,
  which Flux never reads; an admission check refuses a shadow-prefixed source
  in any Flux object.
- Before delivery, estate-dashboard, liquibase-runner and
  stalwart-provisioner move to Rust, characterization tests record their
  current behaviour: Release Gate answers, Reporter statuses, Collector output,
  the catalog jobs' actions, dashboard API responses, the migration proof and
  the provisioner's verdicts. The port keeps them passing.

## Agent files

A root `AGENTS.md` under 200 lines holds only what the code cannot show: the
locked records, where contracts live, the stop-and-ask rule, and how to propose
a record. Small nested files sit in each context's folder under `crates/`
(`compiler/`, `service/`, `observation/`, `hosts/`, `components/`) and in
`ui/`; `CLAUDE.md` imports `AGENTS.md`. deploy-kit's `adr`,
`spec-change`, `gate-triage` and `new-rule` skills are rewritten for
estate-kit, not copied.

Chosen so agents read the whole file instead of skimming a long one. One
root file for the whole workspace was rejected.

## Primitives

IDs are UUIDv7, times are RFC 3339 in UTC, and an absent field means unset;
`null` is never valid. Chosen because UUIDv7 sorts and has a native Postgres
type, and one null rule needs one lint. ULIDs were rejected.

## Retention

Rollout events are kept 400 days. A render is kept if it is among its
Project's last 20, younger than 90 days, or named by a tag. Chosen so rollback
targets survive and storage stays bounded. Keeping everything, or 90 days of
everything, were rejected.

## Telemetry

OpenTelemetry traces go to Tempo and JSON logs to Loki, and the rollout id
correlates them, so one rollout reads as one trace. Logs and metrics alone
were rejected.

## Configuration

Flags override environment variables, which override a file, and a secret
appears only as a reference. Chosen because it gives one typed config with
nothing secret in it. Environment only was rejected.

## Shared Rust code

Shared Rust code moves into
[rust-commons](https://github.com/JorisJonkers-dev/rust-commons) on its third
consumer, in the pull request that switches that consumer
([workspace ADR-0017](https://github.com/JorisJonkers-dev/workspace/blob/main/docs/decisions/ADR-0017-go-commons-extracts-on-third-use.md)).
Until then it stays in estate-kit's foundation crates.

- **The sign-in kit goes in now** (identity#113). Every Rust application with a
  browser UI needs it, and identity's flow-conformance suite is its contract,
  which CI runs explicitly.
- **rust-commons becomes a workspace of small crates** (`identity`, `signin`,
  and later others) when it gains the kit, so a consumer that reads Principals
  does not compile an OIDC client
  ([record 50](../decisions/0050-five-bounded-contexts.md)). One crate with
  features was rejected: features unify across a workspace.
- **No other module goes in early.** A commons crate for configuration,
  telemetry and test harnesses now would be an interface designed for one
  consumer.
- A rust-commons module with fewer than three consumers is forbidden, apart
  from the identity contract adapters. Reviewers check an extraction in the
  pull request that switches its third consumer.

The sign-in kit stays outside estate-kit because it has a contract outside
estate-kit: identity's suite.

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
- **Events.** Each event has a type and a version; old versions are upcast on
  read, never rewritten. Events hold no personal data: actors are ids, resolved
  at read time. The event log stays internal.

## Bounded contexts

Four contexts, each boundary its own record, and a fifth (Observation)
proposed on [The Rust workspace](rust-workspace.md#bounded-contexts). A Project
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

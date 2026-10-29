# The Rust workspace

Every program in estate-kit is Rust, in one Cargo workspace at one version; the
UI stays Vue ([record 13](../decisions/0013-every-program-is-rust.md)). This
page is how that workspace is organised: its bounded contexts, its layers, the
crates in each, the patterns the code uses, and the rules that keep it fast to
build. [Transformations without a DSL](transformations.md) covers the
compiler's inside, and [Testing and speed](code-shape-and-speed.md) the gates.

## What we carry over, and from where

| Lesson | Source | Here |
| --- | --- | --- |
| A chain of typed models, one pure step per arrow, no step imports another | [deploy-kit ADR 0056](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/architecture/0056-the-compiler-is-a-chain-of-typed-models.md) | One crate per step; Cargo refuses the import |
| Adapters build a narrow object model, never upstream client types | [deploy-kit ADR 0058](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/architecture/0058-every-step-links-through-one-trace.md) | `deliverable` declares only the fields the estate sets; `k8s-openapi` is not a dependency |
| Errors are coded diagnostics in a list; panics are compiler bugs | [deploy-kit ADR 0059](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/architecture/0059-failures-are-a-diagnostic-list.md) | `diagnostics` foundation crate |
| No env, clock, randomness, process or file system inside a step | [deploy-kit ADR 0061](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/architecture/0061-the-process-lives-in-one-boundary-file.md) | clippy `disallowed-methods` per layer |
| Layer and reachability rules live on the module graph, with negative fixtures | [deploy-kit ADR 0060](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/architecture/0060-boundaries-enforced-on-the-graph.md) | `cargo xtask check-layers` ([record 65](../decisions/0065-the-workspace-is-layered-and-the-crate-graph-is-checked.md)) |
| A rule that matches nothing passes silently | blueshell's ArchUnit "controllers do not call services" never fired | Every rule ships with a fixture that must fail |
| Map by hand at boundaries; mapping libraries were removed | [blueshell API ADR-004](https://github.com/ESA-Blueshell/website/blob/main/docs/adr/api/ADR-004-manual-mapping-at-api-boundaries.md) | `From` and `TryFrom` impls, written out |
| No command bus; one use case per command | [blueshell API ADR-002](https://github.com/ESA-Blueshell/website/blob/main/docs/adr/api/ADR-002-command-pattern-with-command-bus.md), translated | One function or struct per use case; cross-cutting work is a tower layer |
| A package moves to commons on its third use, not before | [workspace ADR-0017](https://github.com/JorisJonkers-dev/workspace/tree/main/docs/decisions) | `rust-commons` grows only when a third Rust consumer needs it |
| Contract first: the committed document is the only interface source | [workspace ADR-0016](https://github.com/JorisJonkers-dev/workspace/blob/main/docs/decisions/ADR-0016-go-vue-contract-first-standard.md) | OpenAPI, JSON Schemas and the error catalogue live in `contracts/` |
| Migrations run from their own image, never from the service | [workspace ADR-0021](https://github.com/JorisJonkers-dev/workspace/blob/main/docs/decisions/ADR-0021-liquibase-runner-is-the-one-migration-path.md) | The service's event-store schema ships as a migration-runner image |
| The DB row is the queue; jobs dedupe on a key; a sweeper recovers stale ones | [blueshell API ADR-023](https://github.com/ESA-Blueshell/website/blob/main/docs/adr/api/ADR-023-job-consolidation-and-reliable-execution.md) (reversed RabbitMQ) | The composition queue and component jobs |

## What is being replaced, and where it goes

The inventory of 2026-10-29, counted on each repository's `main`:

| Today | Size | Goes to |
| --- | --- | --- |
| deploy-kit compiler (TypeScript, 1.0.1) | 19.5k source lines, 36.6k test lines; 7 adapters plus grafana | The compiler context, step by step ([record 67](../decisions/0067-the-compiler-is-written-to-the-1-0-contract.md)) |
| delivery Release Gate | 2.4k lines: Flagger webhooks, the tend loop, migration Job unsuspend, traffic probing, warmup | Service: `release-gate` domain, served by `http-api` |
| delivery Reporter | 0.7k: GitHub Deployment statuses per rollout stage | Service: a projection of rollout events through `adapter-github` |
| delivery Collector | 0.3k: the ClusterState snapshot | Service: `adapter-kube` captures it live, digested into the render key |
| delivery vault-policy | 0.7k | Component: `secret-grant` |
| delivery postgres-catalog, garage-catalog | 0.4k each: roles, databases, buckets, keys, grants | Components: `database-catalog`, `bucket-catalog` |
| delivery backup, offcluster | 0.9k: generations, a consistent SQLite copy, age encryption, S3 upload | Component: `backup` |
| estate-dashboard API (Go) and Vue UI | 6k Go hand-written, 12.7k TypeScript and Vue | Observation context for the read views; the Vue UI stays in `ui/` |
| stalwart-provisioner (Python, jq, sh) | 0.6k plus 0.3k shell | Component: `mailbox` |
| liquibase-runner (Go around the Liquibase JVM) | 1.3k | Component: `migration-run`; the Liquibase JVM and squawk stay in its image |

The earlier design named three components; the inventory finds six. They all
have the same shape: read what a render declares, compare it with one outside
system, change what differs, never delete what it does not own. So a
`reconcile` foundation crate holds that loop once (more than three uses).

## Bounded contexts

The four earlier contexts stay and a fifth is added
([record 50](../decisions/0050-five-bounded-contexts.md)): **Observation**, the read side the dashboard serves today. It holds
no credential that can deploy, pause or roll back, as estate-dashboard holds
none now; keeping it out of the Service context keeps the rollout core free
of Prometheus, Loki and Alertmanager. A Project is the aggregate root in the
compiler; a Rollout is the aggregate root in the service.

| Context | Owns | Aggregate roots | Talks to others through |
| --- | --- | --- | --- |
| Compiler | The model: Intent in, Resolved Deployment, Deliverable Set out | Project; the Estate is the set of admitted Projects | Its application crate's use cases (`validate`, `plan`, `compose`, `render_hosts`, `generate`) |
| Service | Rollouts, compositions, admission, Pause and Rollback, the Release Gate | Rollout (event-sourced); Composition | The compiler's use cases, called in-process ([record 18](../decisions/0018-the-service-links-the-compiler.md)) |
| Observation | What runs and how it is doing: units, pods, containers, alerts and silences, logs, health, checks | None: read models only | Ports onto Prometheus, Loki, Alertmanager, Gatus and the cluster; rollout history from the Service's event log |
| Hosts | Generations and their rollout across nodes | NodeRollout | Signed host tags only; never a model type |
| Components | Migrations, secret grants, database and bucket catalogs, backups, Mailboxes | One per component: MigrationRun, SecretGrant, DatabaseGrant, BucketGrant, BackupGeneration, Mailbox | Rendered objects only |

The context map, with the result.json edge replaced by an in-process call:

![Context map](../diagrams/png/context-map.png)

| Upstream | Downstream | Relationship | Published language |
| --- | --- | --- | --- |
| Compiler | Service | Customer and supplier | `compiler::CompositionResult` and `Diagnostic` |
| Compiler | Hosts | Anticorruption layer | Host data (Nix attribute sets), via signed host tags |
| Compiler | Components | Published language | The rendered objects' committed schemas |
| Service | Observation | Published language | Rollout events, read through a query port |
| identity | Service, Observation | Conformist | rust-commons' `Principal` |

## Layers

Each crate is in one context and one layer
([record 65](../decisions/0065-the-workspace-is-layered-and-the-crate-graph-is-checked.md)).
Dependencies point inward and downward only.

![The workspace's layers](../diagrams/png/rust-layers.png)

| Layer | May depend on | Holds | Forbidden |
| --- | --- | --- | --- |
| foundation | foundation | Diagnostics, model paths, digests, canonical YAML and JSON, spanned YAML reading, the trace store, the test kit | Domain words; async; I/O |
| domain | foundation; its context's domain | Model types, invariants, transformation steps, deciders, state machines | `tokio`, `kube`, `sqlx`, `reqwest`, `axum`; `std::env`, `std::fs`, `SystemTime::now` |
| application | domain; foundation | Use cases, port traits, the fakes behind a `fakes` feature | Any adapter crate |
| adapter | its context's application; foundation; external crates | One outside system each | Another adapter; a domain crate's internals |
| binary | anything | `main`, typed configuration, wiring | Logic: a binary is wiring only |

## The crates

Folders mirror the layers. Each crate is named exactly after its folder
(matklad's rule), internal crates stay `publish = false`, and they take the
workspace's one version.

```text
Cargo.toml                    virtual manifest: members, [workspace.dependencies], [workspace.lints]
crates/layers.toml            the layer table check-layers reads
crates/
  foundation/
    diagnostics/              Diagnostic, Code, Severity, Location, ModelPath (RFC 6901), ElementRef, Diagnostics accumulator
    yaml-source/              spanned YAML 1.2 reading with budgets; refuses anchors, aliases, tags, duplicate keys
    canonical/                the canonical YAML and JSON emitters (record 64), and Digest
    trace/                    the trace store: source element to produced element, create-then-link
    reconcile/                observe, decide, act: the loop every component and the host applier share
    testkit/                  read-only oracle harness, structural diff before byte diff, builders
  compiler/
    model-intent/             Project, Platform and Infrastructure Intent as authored
    model-effective/          Intent after lowering
    model-resolved/           the Resolved Deployment and host plans
    deliverable/              the narrow object model of every rendered file
    step-read/                YAML and env files to Intent: schema validation, then conversion
    step-check/               the invariant table over Intent and over the input set
    step-lower/               shared declarations settled into effective values
    step-compose/             the union of admitted Projects: departures, Moves, assets, set-wide refusals
    step-resolve/             derivation of every mechanism; one module per concept
    step-outputs/             what is not a Deliverable: Flux sources, the node contract, labels, host data
    render-kubernetes/        one crate per adapter of the 1.0 registry:
    render-networking/          kubernetes, networking, traefik, vault-policy,
    render-traefik/             flux, vso, prometheus, grafana
    render-vault-policy/
    render-flux/
    render-vso/
    render-prometheus/
    render-grafana/
    serialize/                Deliverable Set to bytes through `canonical`; path ownership; atomic write
    generate/                 an Application's App Roles in its language (go, kotlin, python, rust, ts)
    compiler/                 application: validate, plan, compose, render_hosts, generate, migrate
  service/
    rollout/                  domain: the Rollout decider, events and their upcasters, the composition queue policy
    release-gate/             domain: the Release Gate's answer from a ClusterObservation; probing and warmup rules
    service-app/              application: Deploy, DryRun, Plan, Pause, Resume, Rollback, Admit, Gate; the ports
    adapter-postgres/         the event log and the job table (sqlx)
    adapter-ghcr/             fragments, renders, tags (oci-client) with the machine token
    adapter-vault/            Transit signing and token reads
    adapter-kube/             server-side dry-run, Flux and Flagger status, ClusterState capture, the writer Lease, the Pause object
    adapter-github/           Deployment status, check runs (GitHub App)
    adapter-github-oidc/      the CI token's claim policy
    http-api/                 axum routes from the OpenAPI document, SSE, problem+json
  observation/
    observation-app/          application: the dashboard's read models and their ports
    adapter-prometheus/       health and rollout metrics
    adapter-loki/             logs and streams
    adapter-alertmanager/     alerts, history, silences
    adapter-gatus/            checks
  hosts/
    host-rollout/             domain: node order, the reboot decision, the applier state machine
    host-applier-app/         application: one reconcile step over six ports
    adapter-nix/              fetch and verify a closure; switch-to-configuration
    adapter-host-kube/        Lease, cordon, eviction
    adapter-host-registry/    the signed host tag
  components/                 each component is two crates: <name> (domain) and <name>-app (use case, ports)
    secret-grant/             domain: Vault policies, auth roles, generated keys
    database-catalog/         domain: Postgres roles, databases, grants, Vault database roles
    bucket-catalog/           domain: Garage buckets, keys, grants
    backup/                   domain: generations, retention, off-cluster copies
    mailbox/                  domain: the Mailbox reconciler
    migration-run/            domain: up and down per revision, the stale lock, the proof
    adapter-vault-admin/      policies and roles (not Transit)
    adapter-pg-admin/         roles and databases
    adapter-garage/           Garage's admin API
    adapter-offsite/          age encryption and the S3 upload
    adapter-stalwart/         Stalwart's management API
    adapter-liquibase/        runs the Liquibase JVM and squawk in the image
    adapter-components-kube/  watching the rendered objects
bins/
  estate-kit/                 the CLI: validate, plan, compose, render-hosts, generate, migrate
  estate-kit-service/         the service and the Observation views, with the embedded UI
  estate-kit-host-applier/
  secret-grant/ database-catalog/ bucket-catalog/ backup/ mail-provisioner/ migration-runner/
                              one binary and one image per component, so each carries only its own adapters
xtask/                        check-layers, oracle accept, contracts, release helpers
ui/                           Vue; npm only here
contracts/                    JSON Schemas and corpus, OpenAPI, the error catalogue, custom-resource schemas
oracles/                      hand-reviewed expected outputs, read-only to tests
```

The render crates are the eight adapters of deploy-kit 1.0's closed registry,
one crate each. They implement one `Renderer` port, so that trait has more
than one implementation and earns its place (CS-2). `step-outputs` is the step
#373 introduced for outputs that are not Deliverables; its final name is
settled against `CONTEXT.md` when it is written.

### What goes in rust-commons, and what stays

| Need | Where | Why |
| --- | --- | --- |
| Reading the Principal from the Gate's signed header | rust-commons `identity` (exists) | Already shared |
| Browser sign-in for the UI (OIDC code flow, PKCE, back-channel logout, step-up) | rust-commons, as identity#113's Rust sign-in kit | Every Rust app with a UI needs it; it must pass identity's flow-conformance suite |
| The GitHub OIDC claim policy | estate-kit `adapter-github-oidc` | One consumer |
| Typed configuration, telemetry setup, health endpoints | estate-kit `foundation` until a third Rust service needs them | [workspace ADR-0017](https://github.com/JorisJonkers-dev/workspace/blob/main/docs/decisions/ADR-0017-go-commons-extracts-on-third-use.md): third use |
| Testcontainers harness for Postgres, Vault, a registry | estate-kit `testkit` until a third use | Same rule |

rust-commons is one crate today. When it gains the sign-in kit it should
become a workspace of small crates (`identity`, `signin`), so a consumer that
only reads Principals does not compile an OIDC client.

## Patterns

Each pattern is here because it solves a problem this codebase has. A pattern
that is not on this list needs a reason in its pull request.

| Pattern | Used for | How |
| --- | --- | --- |
| Newtype with a smart constructor | Every name and identifier: `ProjectName`, `ApplicationId`, `Digest`, `RenderKey`, `RolloutId` | A private field and `TryFrom<&str>`; no `Deref` to `String` |
| Closed enum | Every finite set: `Lifecycle`, `Audience`, `AccessTier`, `RefusalCode` | No `_` arm across a closed set (`clippy::wildcard_enum_match_arm`), so a new variant is reviewed everywhere |
| Parse, don't validate | The read step | YAML is checked against the committed schema with every error collected, then converted into types that cannot hold an invalid value |
| No `Default` where absence matters | The model | A missing value is a diagnostic, never a default (CS-3) |
| Typed pipeline | The compiler | Each step is a function from one model to the next plus diagnostics; no step trait, because there is one implementation per step |
| Port and adapter | Every outside system | A trait in the application crate; one adapter crate; one hand-written fake beside the trait ([record 68](../decisions/0068-every-fake-passes-its-port-s-contract-suite.md)) |
| Port bundle | Wiring without generic soup | `trait Ports { type Registry: Registry; type Signer: Signer; … }`; use cases are generic over one `P: Ports`; the binary picks real types, tests pick fakes |
| Decider | The Rollout and the host applier | `decide(&State, Command) -> Result<Vec<Event>, Refusal>` and `evolve(State, &Event) -> State`, both pure; the shell loads, decides, appends, acts |
| Functional core, imperative shell | Reconcilers: host applier, mail provisioner, secret job | Observe, decide (pure), act, one step per tick; a crash resumes from observed state |
| Anticorruption layer | Each adapter | Outside errors become the port's few errors (`NotFound`, `Conflict`, `Unavailable`); no `kube::Error` or `sqlx::Error` crosses a port |
| Upcaster | Rollout events | Each event type has a version; old versions are lifted on read, never rewritten ([record 49](../decisions/register.md)) |
| Table-driven registry | Invariants and refusal codes | A `static` table of named entries, so a test can walk every code and demand its fixture |
| Tower layer | Cross-cutting HTTP work | Authentication, the Principal, timeouts, tracing, problem+json; never in a handler |
| Router that demands a policy | Authorization | A route is added only with its authorization row; there is no unauthenticated default (blueshell's secure-by-default rule, typed) |

Patterns we do not use, and why:

- **No mocking framework.** One fake per port, shared by every test.
- **No command bus or service locator.** Wiring is explicit in `main`.
- **No inheritance-shaped trait hierarchies.** A trait exists when two
  implementations exist.
- **No derive-mapping crates.** Boundaries map by hand.
- **No proc macro of our own.** `macro_rules!` is allowed for one fixed shape
  (the newtype boilerplate); anything larger is a function.

## Errors, in three kinds

| Kind | Type | Where it ends |
| --- | --- | --- |
| Authored input is wrong | `Diagnostic` with a `RefusalCode`, a primary location and any related ones ([record 71](../decisions/0071-a-diagnostic-is-a-coded-problem-with-typed-locations.md)), collected in a list | A YAML line in CI ([Errors in CI](errors-in-ci.md)); a problem+json `type` from the catalogue |
| An outside system failed | A port error (`Unavailable`, `Conflict`, `NotFound`) via `thiserror` | A retry in the adapter if the call is idempotent; otherwise a rollout event and a 503 |
| Our code is wrong | A panic | A failed composition with an internal problem; a test that reproduces it |

`anyhow` is allowed only in `bins/` and `xtask`. A library crate returns its
own `thiserror` enum.

## Keeping builds fast

The maintainer asked that a change not rebuild everything. Cargo rebuilds a
crate when it or a dependency changes, so the graph's shape is the build time.

- **Heavy dependencies stay at the edge.** `kube`, `sqlx`, `axum`, `oci-client`
  and the TLS stack appear only in adapter and binary crates. A change to a
  resolve rule rebuilds `step-resolve`, `compiler` and the binaries, and its
  tests compile without any of them.
- **No `k8s-openapi`.** The narrow `deliverable` model replaces it, which also
  removes the slowest-compiling crate in the Kubernetes ecosystem.
  Rendered objects are checked against pinned Kubernetes and CRD JSON Schemas
  in a test, not by the type system.
- **Proc macros are few.** `serde`, `thiserror` and `tokio::main`. Domain crates
  derive `serde` only where a type is read or written.
- **One feature set.** Features are unified across the workspace so a crate is
  not rebuilt twice with different features; `cargo hakari` keeps a
  workspace-hack crate if that ever stops holding.
- **Per-crate test runs.** CI maps changed paths to crates and runs
  `cargo nextest` on those crates and their dependents only; an unclaimed path
  runs everything (the estate's path-bucket rule).
- **Caches.** `Swatinem/rust-cache` in CI; `sccache` is optional locally.

## Toolchain and gates

The estate's conventions apply unchanged: `mise` pins the toolchain, a
`Taskfile` holds `lint`, `test`, `gen`, `gen:check` and `check`, and `task
check` is exactly what CI runs. rust-commons' settings are the starting point:
edition 2024, `unsafe_code = "forbid"`, `clippy::pedantic` at warn with
`-D warnings` in CI, `missing_docs` on public items, `cargo doc` with
`-D warnings`. estate-kit adds `cargo-deny` (advisories, licences, bans of
`serde_yaml`, `serde_yml` and `openssl`), `cargo-machete` for unused
dependencies, and `unreachable_pub` so nothing is public that nothing outside
uses.

## Open questions

- **The YAML reader.** `saphyr` with markers, or `serde-saphyr` with
  `Spanned<T>`: settled by the spike the review planned, against the criteria
  of [model-compiler-5](../research/review/model-and-compiler.md).
- **Where the composition queue lives.** In memory with the single writer, or
  as rows in Postgres like blueshell's job table. The row survives a restart;
  the single writer already reconciles from observed state
  ([record 63](../decisions/0063-the-service-has-one-writer-and-reconciles-from-observed-state.md)).

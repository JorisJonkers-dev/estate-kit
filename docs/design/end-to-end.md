# End to end, crate by crate

The other pages describe each part. This one follows the main use cases
through the crates of [The Rust workspace](rust-workspace.md), so every
responsibility has exactly one owner and every failure has one place that
handles it. If a step below names no crate, the design has a gap.

## A release, from a Project's CI to Serving

| # | What happens | Crate | Port | On failure |
| --- | --- | --- | --- | --- |
| 1 | The `validate` job runs `estate-kit validate` on the checkout | `bins/estate-kit` → `compiler::validate` → `step-read`, `step-check` | None: offline | Diagnostics with code and model path; the CLI resolves each path to a line and writes annotations ([Errors in CI](errors-in-ci.md)) |
| 2 | The release's `deploy` job builds images by digest, then calls `POST /deploys` with its GitHub OIDC token and the fragment digest | `http-api` | `ClaimPolicy` → `adapter-oidc` | 401 or 403 as problem+json; the claim policy's fixtures name each refusal |
| 3 | The call is accepted idempotently on (Project, fragment digest), and the stream is authenticated by a GitHub token re-requested whenever one is needed | `delivery-app::Deploy` → `rollout::decide` | `EventStore` → `adapter-postgres` | A retry with the same key returns the same rollout ([record 23](../decisions/0023-a-rollout-is-an-append-only-event-log-on-the-shared-postgres.md)) |
| 4 | The fragment is fetched and every image digest checked as registered by this Project | `delivery-app` | `Registry` → `adapter-ghcr` | `Unavailable` retries with backoff inside the adapter; a digest not registered is a refusal event |
| 5 | The composition queue coalesces triggers and runs one composition | `rollout` (queue policy) and `delivery-app` (driver) | `JobStore` → `adapter-postgres` | The queue row survives a restart; after it, the writer re-observes and decides again ([record 73](../decisions/0073-the-composition-queue-is-a-row-in-a-postgres-job-table.md)) |
| 6 | Every admitted Project's fragment is composed in-process, on a blocking thread, under a budget and a deadline | `compiler::compose` → `step-*`, `render-*`, `serialize` | `ClusterStateSource` → `adapter-kube` for the snapshot | A refused fragment is isolated and the others compose; a panic fails this composition only ([record 18](../decisions/0018-delivery-links-the-compiler.md)) |
| 7 | Every changed object is dry-run server-side as Delivery's own identity | `delivery-app` | `Cluster` → `adapter-kube` | Admission, schema and immutable-field errors are shown against the elements the object came from; mapping to the line that set the field is deferred ([record 71](../decisions/0071-a-diagnostic-is-a-coded-problem-with-typed-locations.md)) |
| 8 | The writer Lease is taken. A render whose digest equals the current tag's is skipped; a changed one is signed with the render signing key | `delivery-app` | `WriterLease` → `adapter-kube`; `Signer` → `adapter-vault` | Vault down: the rollout waits and says so; Flux keeps serving the last tags; a lost Lease stops all writing |
| 9 | The render is pushed, the Lease checked again, and `render/<p>:prod` moved by read, verify, write; the tag is read again after the write | `delivery-app` | `Registry` → `adapter-ghcr`; `WriterLease` → `adapter-kube` | ghcr has no compare-and-swap: a different value on the re-read is a lost race, so Delivery re-observes and decides again. The window between the Lease check and the write is stated in [record 63](../decisions/0063-delivery-has-one-writer-and-reconciles-from-observed-state.md) |
| 10 | Flux pulls the tag and applies; Flagger asks the Release Gate before each step | `release-gate` (answer) via `http-api` | `ClusterObservation` → `adapter-kube` | The gate fails closed: 503 with the cause in the log |
| 11 | Delivery watches Kustomization, OCIRepository and Canary status and appends rollout events | `delivery-app` → `rollout::evolve` | `Cluster`, `EventStore` | A stalled rollout times out into a Held event |
| 12 | The deploy job streams events over SSE and resumes by sequence after a drop | `http-api` | `EventStore` | At-least-once; the client drops duplicates |
| 13 | GitHub Deployment status follows each stage (the Reporter today) | `delivery-app` projection | `GitHub` → `adapter-forge-github` | Idempotent upserts; a failed update is retried from the event log |
| 14 | The UI shows the rollout beside pods, alerts, logs and checks. Observation's binary serves the UI and reads; the browser calls Delivery's API for Pause and Rollback | `observation-app` in `bins/estate-kit-observation` | `adapter-prometheus`, `-loki`, `-alertmanager`, `-gatus`, `-observation-kube`, `-delivery-api` | A down source greys out its panel; it never blocks a deploy (DO-7) |

Steps 1 to 6 run the same compiler code in CI and in Delivery, because both
call the `compiler` crate.

## A rollback

1. An Operator signed in to the UI (rust-commons' sign-in kit; group claims map
   to roles in Platform Intent) presses Roll back. `http-api` checks the route's
   authorization row.
2. `delivery-app::Rollback` takes the writer Lease (`adapter-kube`), finds the
   last Serving render from the registry (`adapter-ghcr`), not from Postgres or
   the event log, and dry-runs it (`adapter-kube`). It moves the tag back by
   read, verify, write and re-reads it (`adapter-ghcr`, with the token from the
   mounted Secret), then writes the Project's Pause object (`adapter-kube`). It
   signs nothing and reads nothing from Vault or Postgres, so it works with
   Vault down ([record 28](../decisions/0028-pause-and-rollback-are-a-cluster-object-per-project.md)).
3. If that dry-run fails, it composes again from step 5 above, which is a
   Deploy and waits for Vault.

## A host rollout

1. CI builds every node's closure into the signed binary cache and runs one
   NixOS VM test per node class (`hosts/vm-tests`).
2. `estate-kit render-hosts` (`compiler::render_hosts` → `step-outputs`)
   produced each node's host data, which the hand-written modules consume.
3. Delivery publishes each node's next numbered `host/<node>:<n>` Sequence tag,
   signed with the host key (`delivery-app` → `adapter-vault`, `adapter-ghcr`).
4. Each node's applier (`bins/estate-kit-host-applier`) runs one reconcile
   step per tick (`host-applier-app` over `reconcile`): fetch and verify the
   closure (`adapter-nix`), decide whether it needs a reboot
   (`host-rollout`), wait for the window, take the Lease, evict, switch,
   health-check, release (`adapter-host-kube`). A crash is followed by a fresh observation of the node and a new decision.

## A component

Each component binary watches the objects its Projects render
(`adapter-components-kube`), decides what differs (its domain crate, through
`reconcile`), and changes only that in its one outside system. It never
deletes what it does not own, and reports stale entries instead.

## Scenarios the Accepted records add

The E2E suite ([record 69](../decisions/0069-the-deploy-path-is-tested-end-to-end.md))
runs these scenarios beside the use cases above.

| Scenario | Record |
| --- | --- |
| Postgres is stopped during a rollback, and the Project still rolls back to Serving | [record 28](../decisions/0028-pause-and-rollback-are-a-cluster-object-per-project.md) |
| Delivery is killed after each write | [record 104](../decisions/0104-every-reconciler-estate-kit-owns-passes-crash-point-stale-read-and-safety-tests-before-it-takes-production-responsibility.md) |
| A deploy is interrupted on each side of the Publication point | [record 97](../decisions/0097-the-publication-point-is-named-and-tested-and-a-render-that-introduces-a-kind-is-published-in-two-stages.md) |
| The Release Gate refuses a release while the Project database is marked failed by a migration | [record 114](../decisions/0114-multi-tenant-projects-keep-their-tenants-in-shared-tables-separated-by-row-level-security.md) |
| The weekly restore rehearsal restores each store's latest snapshot into throwaway containers and checks what it reads back | [record 115](../decisions/0115-backups-are-kopia-snapshots-in-one-locked-repository-per-environment-on-an-eu-object-store-with-wal-archived-beside-them.md) |

## What is cross-cutting, and where it lives

| Concern | Where | How |
| --- | --- | --- |
| Authentication | `http-api` tower layers | GitHub OIDC claim policy for CI; rust-commons `PrincipalLayer` and the sign-in kit for people |
| Authorization | `http-api` router | A route is registered only with its row of the authorization matrix ([Security](security.md)) |
| Timeouts | Each adapter, and a tower layer per route | Every outside call has a deadline; none is unbounded |
| Retries | Adapters only, for idempotent calls | Jittered backoff with a cap; a non-idempotent call is never retried |
| Tracing | `tracing` with OpenTelemetry, set up in each binary | One rollout is one trace; `rollout_id`, `project` and `trace_id` on every log line |
| Configuration | Each binary's `config` module | Flags, then `ESTATE_KIT_*` environment, then file; secrets only by reference |
| Errors to callers | `http-api` | One mapping from port errors and diagnostics to RFC 9457 problems, from the catalogue |
| Shutdown | Each binary | Stop accepting, finish or abandon the current step with an event, release the Lease |

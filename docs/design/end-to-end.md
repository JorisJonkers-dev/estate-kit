# End to end, crate by crate

The other pages describe each part. This one follows the main use cases
through the crates of [The Rust workspace](rust-workspace.md), so every
responsibility has exactly one owner and every failure has one place that
handles it. If a step below names no crate, the design has a gap.

## A release, from a Project's CI to Serving

| # | What happens | Crate | Port | On failure |
| --- | --- | --- | --- | --- |
| 1 | The `validate` job runs `estate-kit validate` on the checkout | `bins/estate-kit` → `compiler::validate` → `step-read`, `step-check` | None: offline | Diagnostics with code and model path; the CLI resolves each path to a line and writes annotations ([Errors in CI](errors-in-ci.md)) |
| 2 | The release's `deploy` job builds images by digest, then calls `POST /deploys` with its GitHub OIDC token and the fragment digest | `http-api` | `ClaimPolicy` → `adapter-github-oidc` | 401 or 403 as problem+json; the claim policy's fixtures name each refusal |
| 3 | The call is accepted idempotently on (Project, fragment digest), and the token is exchanged for a rollout token | `service-app::Deploy` → `rollout::decide` | `EventStore` → `adapter-postgres` | A retry with the same key returns the same rollout ([record 45](../decisions/register.md)) |
| 4 | The fragment is fetched and every image digest checked as registered by this Project | `service-app` | `Registry` → `adapter-ghcr` | `Unavailable` retries with backoff inside the adapter; a digest not registered is a refusal event |
| 5 | The composition queue coalesces triggers and runs one composition | `rollout` (queue policy) and `service-app` (driver) | `JobStore` → `adapter-postgres` | The queue row survives a restart; the single writer resumes it |
| 6 | Every admitted Project's fragment is composed in-process, on a blocking thread, under a budget and a deadline | `compiler::compose` → `step-*`, `render-*`, `serialize` | `ClusterStateSource` → `adapter-kube` for the snapshot | A refused fragment is isolated and the others compose; a panic fails this composition only ([record 18](../decisions/0018-the-service-links-the-compiler.md)) |
| 7 | Every changed object is dry-run server-side as the service's own identity | `service-app` | `Cluster` → `adapter-kube` | Admission, schema and immutable-field errors are mapped through each field's provenance to the authored lines that set them ([record 71](../decisions/0071-every-diagnostic-names-its-locations-and-every-output-traces-to-its-source.md)) |
| 8 | A render whose digest equals the current tag's is skipped; a changed one is signed with the render signing key | `service-app` | `Signer` → `adapter-vault` | Vault down: the rollout waits and says so; Flux keeps serving the last tags |
| 9 | The render is pushed, the writer Lease taken, and `render/<p>:prod` moved by compare-and-swap | `service-app` | `Registry` → `adapter-ghcr`; `WriterLease` → `adapter-kube` | A lost compare-and-swap re-reads and decides again; a lost Lease stops writing |
| 10 | Flux pulls the tag and applies; Flagger asks the Release Gate before each step | `release-gate` (answer) via `http-api` | `ClusterObservation` → `adapter-kube` | The gate fails closed: 503 with the cause in the log |
| 11 | The service watches Kustomization, OCIRepository and Canary status and appends rollout events | `service-app` → `rollout::evolve` | `Cluster`, `EventStore` | A stalled rollout times out into a Held event |
| 12 | The deploy job streams events over SSE and resumes by sequence after a drop | `http-api` | `EventStore` | At-least-once; the client drops duplicates |
| 13 | GitHub Deployment status follows each stage (the Reporter today) | `service-app` projection | `GitHub` → `adapter-github` | Idempotent upserts; a failed update is retried from the event log |
| 14 | The UI shows the rollout beside pods, alerts, logs and checks | `observation-app` | `adapter-prometheus`, `-loki`, `-alertmanager`, `-gatus`, `-kube` | A down source greys out its panel; it never blocks a deploy (DO-7) |

Steps 1 to 6 run the same compiler code in CI and in the service, because both
call the `compiler` crate.

## A rollback

1. An Operator signed in to the UI (rust-commons' sign-in kit; group claims map
   to roles in Platform Intent) presses Roll back. `http-api` checks the route's
   authorization row.
2. `service-app::Rollback` reads the last Serving render from the event log,
   dry-runs it (`adapter-kube`), moves the tag back (`adapter-ghcr`) and writes
   the Project's Pause object (`adapter-kube`). It signs nothing new, so it
   works with Vault down ([record 61](../decisions/register.md)).
3. If that dry-run fails, it composes again from step 5 above.

## A host rollout

1. CI builds every node's closure into the signed binary cache and runs one
   NixOS VM test per node class (`hosts/vm-tests`).
2. `estate-kit render-hosts` (`compiler::render_hosts` → `step-outputs`)
   produced each node's host data, which the hand-written modules consume.
3. The service moves each `host/<node>:prod` tag, signed with the host key
   (`service-app` → `adapter-vault`, `adapter-ghcr`).
4. Each node's applier (`bins/estate-kit-host-applier`) runs one reconcile
   step per tick (`host-applier-app` over `reconcile`): fetch and verify the
   closure (`adapter-nix`), decide whether it needs a reboot
   (`host-rollout`), wait for the window, take the Lease, evict, switch,
   health-check, release (`adapter-host-kube`). A crash resumes from observed
   state.

## A component

Each component binary watches the objects its Projects render
(`adapter-components-kube`), decides what differs (its domain crate, through
`reconcile`), and changes only that in its one outside system. It never
deletes what it does not own, and reports stale entries instead.

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

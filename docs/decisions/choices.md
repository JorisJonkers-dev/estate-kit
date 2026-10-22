# Choices made

Every choice settled in the design sessions of 2026-10-22, with what was rejected and why. A choice becomes binding when its record lands in this directory.

| Topic | Chosen | Rejected | Why |
| --- | --- | --- | --- |
| Applier | Service compiles, Flux applies | Service replaces Flux; CI pushes and the service applies | Keeps one proven applier; the signed artifact is already the seam for replacing Flux later |
| Languages | Rust compiler, Go service | Go only; Rust only | Rust's sum types fit the model; Go fits Kubernetes, OCI and the estate's Go code |
| Compiler in the service | Subprocess, same binary as CI | WASM through wazero; cgo FFI | CI and the service run identical code |
| Image lock | Sealed into the fragment | Digest in the project file; a lock block in it | Git holds no digests; authored and derived content stay apart |
| Pin | Signed registry tag per Project | Estate pin commits; the service patching OCIRepository | No central list, no second writer of Flux objects |
| Membership | Admitted Projects in Platform Intent | Derived from the registry or the cluster | A reviewed list of who may deploy |
| Hosting | In the cluster, behind the edge | Outside the cluster | The deploy credential stays inside the cluster |
| Offline validation | Project-local rules only | Embedded estate snapshot; a snapshot file | Deterministic, no extra file |
| Signing | cosign key in Vault Transit | Keyless from the cluster; a GitHub job | The key never leaves Vault |
| Render store | ghcr, which is also the cache | In-cluster zot; both mirrored | A rebuilt cluster can still pull its renders |
| Pause and rollback state | One cluster object per Project | Service Postgres; registry annotations | The cluster is the record of what runs |
| Centralization | Code central, state per Project | Code and state central; code split | No central deploy list, no lock outside a Project |
| Central configuration | Platform Intent in a thin estate repo; toolchain config in estate-kit | Service config file; env files folded in | Estate policy stays apart from tool code |
| Repository | Fresh estate-kit, three repos imported with history | Rename deploy-kit; no history | A clean product name, history kept |
| Rust start | In estate-kit from day one | In deploy-kit, moved later | One copy of the spec and the oracles |
| Imports | deploy-kit, delivery and estate-dashboard at creation | delivery and dashboard later | Service work starts at once |
| Schemas | Committed JSON Schemas stay the contract | Rust types as the source | Language-neutral |
| Rust types | Hand-written serde types with a schema drift test | Generated from the schemas | Readable types with newtypes and closed enums; drift still fails CI |
| Crates | One per step, one per adapter | One crate; three stage crates | Cargo enforces the layers; mutants rebuild little |
| Wire to the service | Directory in and out, plus result.json with its own schema | gRPC over stdio | The same contract as the CLI |
| Caching | Registry is the cache, keyed by input digest | Service disk cache; no caching | No cache store to invalidate |
| Rollout log | Append-only Postgres event log | A Rollout custom resource; in memory | Resumable streams and history |
| Concurrency | One composition at a time, triggers coalesce | Parallel per Project | Estate-wide checks never race |
| UI | Vue, npm confined to the UI build | Go templates with htmx; Leptos | Keeps the dashboard; no npm at runtime |
| Versioning | One lockstep version | Per component | No compatibility matrix |
| Old repos meanwhile | Both stacks evolve; Rust catches up | Fixes only; a hard freeze | Production is not held back |
| Cutover | Shadow first, then a staged switch | Single switch; direct switch | Each step can be reverted |
| Rewrite and parity | Port at parity, cut over, then rewrite | Rewrite during the port | Byte-identical renders are the cutover proof |
| #373 tickets | Tracked in both repositories | estate-kit only | Both stacks may do the work |
| ADRs | Brand-new set in reading order | Imported register | Records read as one story |
| Lessons | A separate lessons file the ADRs cite | Inside each ADR | Lessons stay readable as one piece |
| Rollout visibility | The deploy job owns the Deployment and streams the rollout | Service-created Deployments | Every rollout is a run, with approval gates |
| Diagnostics | Log, annotations, check run, job summary | SARIF; review comments | Nothing lost to the annotation cap |
| Line numbers | Model path in the diagnostic; the binary resolves the line | Source map in the fragment | The fragment stays small |
| Ordinary PRs | Offline validation plus a plan | Offline only; previews | Cross-Project errors before merge |
| Dry-run | Compose plus server-side apply dry-run | Offline schemas; compose only | Catches webhooks and immutable fields |
| Release PR images | Built on the PR, promoted on merge | Rebuilt at release | What dry-ran is what deploys |
| Dry-run gates | Release PR check, and again before each tag move | Only one of the two | The estate can change between merge and deploy |
| Workflow names | validate and deploy; dry-run is a deploy input | A dry-run workflow; a compose workflow | Composition is the service's concern |
| Dry-run record | No Deployment | A dry-run environment | Production history holds real deploys only |
| CI identity | repository_id, pinned workflow, environment | Repository name; any workflow | A renamed repo cannot deploy |
| In-cluster identity | Projected service-account tokens | TokenReview; network policy | No round-trip per call |
| UI roles | Identity-provider groups map to roles | Signed in means operator | One identity system |
| Environments | A tag per environment, prod only | One name forever; staging now | A second environment adds a tag |
| Test doubles | One hand-written fake per port | Generated mocks | A port change touches one file |
| Expected outputs | Oracle files only at the four seams | Snapshot tests | One output change does not churn many fixtures |
| Nix and Kubernetes | One model and compiler; a separate host applier per node | Everything in the in-cluster service; a separate nix project | Split by failure domain, not by model |
| Platform Intent flow | Pushed over OIDC by the estate repo; service copies are a cache | Service store as the record; fetching | No mutable central store; the registry stays the record |
| Helpers | Components in estate-kit, in lockstep | Separate repos as submodules | A model change lands in one PR |
| Nix output | Typed host data consumed by hand-written modules | Full .nix files from string templates | Generated Nix holds data, not logic |
| Host apply | Pull a signed closure; one node at a time under a Lease | Node-to-node push; central push | Works without cross-node credentials |
| Control plane | Accept API downtime in its window | Three servers now | Workloads keep serving; HA is a separate decision |
| Maintenance windows | Infrastructure Intent, per site with node override | Estate-wide; per node only | Sites differ; little repetition |
| Host closures | Built in CI; signed off-cluster binary cache | In-cluster cache; nodes build | Hosts can be fixed while the cluster is down |
| Host gate | Build every closure; VM test per node class | Build only; VM test per node | Catches boot and service failures without emulating GPUs |
| Node order | Derived from the change: k3s bumps go control plane first | Fixed order; declared waves | Respects the Kubernetes version skew policy |
| Host pointer | Signed `host/<node>:prod` moved by the service | CI moves tags; follow main | Same pattern as Projects; the key stays in Vault |
| Mailboxes | Address only; shared within a Project, refused across Projects | Owner plus references; a Project-level block | Least to write; each Mailbox has one owning Project |
| Mailbox provisioning | Each Project renders Mailbox custom resources; a provisioner reconciles | One estate-wide manifest | Each Project controls itself |
| Mail provisioner | Ported to Go as a component | Kept in Python | One toolchain less |
| Source of truth | Markdown in estate-kit docs/, published as a site | Wiki as the source; both edited | PR review and CI checks apply to every decision |
| Decision status | Proposed, Accepted, Locked; a locked record needs a failing check | Accepted only | Agents stop and ask instead of working around a lock |
| Status model | Proposed, Accepted, Locked; Locked is accepted plus a MADR Confirmation check | Proposed and Accepted only | Readers see the lock; tooling still parses the record |
| Shadow | Unsigned `shadow/<p>` tags Flux never reads; admission refuses them | Compare in memory only | The diff stays inspectable |
| Service API contract | OpenAPI 3.1 referencing the JSON Schemas | JSON Schemas only | Routes and status codes are contract too |
| Error model | RFC 9457, codes shared with compiler diagnostics | Diagnostics list only | One rendering path for every error |
| Retention | Events 400 days; renders: last 20, 90 days, or tagged | Keep everything; 90 days of all | Rollback targets survive; storage is bounded |
| Service levels | Deploy p95 under 10 min; 99% availability; drift within 24 h | Host rollout within one window | Numbers the maintainer will act on |
| Telemetry | OpenTelemetry traces to Tempo, logs to Loki, rollout id as correlation | Logs and metrics only | One rollout reads as one trace |
| Primitives | UUIDv7, RFC 3339 UTC, absent means unset | ULIDs | Sortable, native type, one null rule |
| Agent files | Root AGENTS.md plus one per part; skills rewritten | One root file | Short files agents fully read |
| Delivery semantics | Natural keys, per-rollout order, at-least-once with resume | Idempotency-Key header | The draft expired; the natural key already exists |
| Security artefacts | STRIDE per trust boundary plus a tested authorization matrix | Matrix only | Signing and break-glass paths get examined |
| Port safety | Characterization tests before porting Go services | Port and compare by hand | Proof the Release Gate kept its answers |
| Schema evolution | Additive within a major, classified and checked in CI | Breaks allowed with a bump | Readers never face an arbitrary jump |
| Consumer contract | Committed result.json fixtures, verified in Rust CI | Pact message contracts | Both sides in one repository need no broker |
| Event evolution | Versioned events upcast on read; no personal data | Rewrite events in place | History stays immutable; nothing needs erasing |
| Bounded contexts | Compiler, service, host applier, components, with a context map | One context | The applier never imports model types |
| Publishing | GitHub Pages site built from docs/ with mdBook | GitHub wiki via an App token | The default token suffices; no extra credential |
| Configuration | Flags, then environment, then file; secrets only by reference | Environment only | One typed config, nothing secret in it |

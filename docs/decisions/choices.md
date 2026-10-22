# Choices made

Every choice settled in the design sessions of 2026-10-22, with what was rejected and why. A choice becomes binding when its record lands in this directory. Rows the [design review](../research/review/README.md) changed or added name its decision (D1 to D12).

| Topic | Chosen | Rejected | Why |
| --- | --- | --- | --- |
| Applier | Service compiles, Flux applies | Service replaces Flux; CI pushes and the service applies | Keeps one proven applier; the signed artifact is already the seam for replacing Flux later |
| Languages | TypeScript compiler until model 1.0; Go service; a Rust port only if a record after 1.0 justifies it | Rust compiler before the cutover; Go compiler; Rust only | The seam lets the service cut over on today's compiler; a parity port chased a compiler that changes daily ([review](../research/review/README.md) D1) |
| Compiler in the service | Subprocess, same binary as CI | WASM through wazero; cgo FFI | CI and the service run identical code |
| Image lock | Sealed into the fragment, and every digest registered by the Project's own build or on the Platform Intent allowlist | Digest in the project file; a lock block in it; no provenance check | The service signed whatever a fragment named ([review](../research/review/README.md) D8) |
| Pin | Signed registry tag per Project | Estate pin commits; the service patching OCIRepository | No central list, no second writer of Flux objects |
| Membership | Admitted Projects in Platform Intent | Derived from the registry or the cluster | A reviewed list of who may deploy |
| Hosting | In the cluster, behind the edge; ghcr tags moved with a machine account's classic PAT kept in Vault | Outside the cluster; a GitHub App token; a promote workflow | ghcr refuses App tokens; tag moves and rollback stay in the cluster ([review](../research/review/README.md) D3) |
| Offline validation | Project-local rules only | Embedded estate snapshot; a snapshot file | Deterministic, no extra file |
| Signing | Separate render and host keys in Vault Transit, plus an offline recovery key every verifier trusts | One Transit key; keyless from the cluster; a GitHub job | Misuse of one key no longer means every Project and every node; losing Vault is survivable ([review](../research/review/README.md) D10) |
| Render store | ghcr, which is also the cache | In-cluster zot; both mirrored | A rebuilt cluster can still pull its renders |
| Pause and rollback state | One cluster object per Project; a missing object reads as Paused | Service Postgres; registry annotations | The cluster is the record of what runs, and a lost object fails safe ([review](../research/review/README.md) D5, D7) |
| Centralization | Code central, state per Project | Code and state central; code split | No central deploy list, no lock outside a Project |
| Central configuration | Platform Intent in a thin estate repo; toolchain config in estate-kit | Service config file; env files folded in | Estate policy stays apart from tool code |
| Repository | Fresh estate-kit, three repos imported with history | Rename deploy-kit; no history | A clean product name, history kept |
| Rust start | Not before model 1.0, and only from the frozen model | In estate-kit from day one | Porting first delayed every delivery and ported code #373 deletes ([review](../research/review/README.md) D1) |
| Imports | deploy-kit, delivery and estate-dashboard at creation | delivery and dashboard later | Service work starts at once |
| Schemas | Committed JSON Schemas stay the contract | Rust types as the source | Language-neutral |
| Rust types | Hand-written serde types with a schema drift test | Generated from the schemas | Readable types with newtypes and closed enums; drift still fails CI |
| Crates | One per step, one per adapter | One crate; three stage crates | Cargo enforces the layers; mutants rebuild little |
| Wire to the service | Directory in and out, plus result.json with its own schema | gRPC over stdio | The same contract as the CLI |
| Caching | No render cache; publishing is skipped when a render's digest is unchanged, and the render key stays as provenance | Registry is the cache, keyed by input digest; service disk cache | The lookup misses on every lockstep release ([review](../research/review/README.md) D9) |
| Rollout log | Append-only event log in a database on the shared platform-postgres | Its own Postgres; a Rollout custom resource; in memory | The existing dump and restore check covers it ([review](../research/review/README.md) D9) |
| Concurrency | One composition at a time, triggers coalesce | Parallel per Project | Estate-wide checks never race |
| UI | Vue, npm confined to the UI build | Go templates with htmx; Leptos | Keeps the dashboard; no npm at runtime |
| Versioning | One lockstep version | Per component | No compatibility matrix |
| Old repos meanwhile | Both stacks evolve; the compiler is shared code, so nothing is ported forward | Fixes only; a hard freeze | Production is not held back ([review](../research/review/README.md) D1) |
| Cutover | Shadow first, then a staged switch | Single switch; direct switch | Each step can be reverted |
| Rewrite and parity | Cut over on the TypeScript compiler, rewrite to 1.0 in TypeScript, then decide on a Rust port | Port at parity, cut over, then rewrite; rewrite during the port | One port of the final model at most; the cutover proof is the shadow, not byte parity ([review](../research/review/README.md) D1) |
| #373 tickets | Tracked in deploy-kit until the import, then in estate-kit (#55) | Both repositories at once | The rewrite happens where its tests live ([review](../research/review/README.md) D1) |
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
| CI identity | A claim policy: repository_id and owner id admitted, job_workflow_sha pinned, event_name allowlisted, ref_type tag, github-hosted runner, the production environment; never sub | Repository name; any workflow; a workflow pinned by ref | A pull_request_target run must not pass as a release ([review](../research/review/README.md) D8) |
| In-cluster identity | The Release Gate answers from cluster state only; Flux is followed by watching its status | Projected service-account tokens from Flagger and Flux | Flagger and Flux cannot send projected tokens ([review](../research/review/README.md) D9) |
| UI roles | Identity-provider groups map to roles | Signed in means operator | One identity system |
| Environments | A tag per environment, prod only | One name forever; staging now | A second environment adds a tag |
| Test doubles | One hand-written fake per port | Generated mocks | A port change touches one file |
| Expected outputs | Oracle files only at the four seams, in a canonical YAML style specified on one page | Snapshot tests; eemeli/yaml's YAML 1.1 output as the format | Any later implementation can match a one-page spec ([review](../research/review/README.md) D12) |
| Nix and Kubernetes | One model and compiler; a separate host applier per node | Everything in the in-cluster service; a separate nix project | Split by failure domain, not by model |
| Platform Intent flow | Pushed over OIDC by the estate repo; service copies are a cache | Service store as the record; fetching | No mutable central store; the registry stays the record |
| Helpers | Components in estate-kit, in lockstep | Separate repos as submodules | A model change lands in one PR |
| Nix output | Typed host data consumed by hand-written modules | Full .nix files from string templates | Generated Nix holds data, not logic |
| Host apply | Pull a signed closure; decide a reboot before the Lease; stage with boot; test-then-boot live changes; one node at a time under a Lease; built alongside the service, with break-glass on deploy-rs | Lease, drain, switch, then wait; deferring the applier; node-to-node push | No node drains outside its window; the applier is built now by the maintainer's choice ([review](../research/review/README.md) D2, D11) |
| Control plane | Accept API downtime in its window; back the SQLite datastore up off the provider, with a drilled restore | Three servers now; one-member etcd | S8 needs a restore path; HA is a separate decision ([review](../research/review/README.md) D5) |
| Maintenance windows | Infrastructure Intent, per site with node override | Estate-wide; per node only | Sites differ; little repetition |
| Host closures | Built in CI; signed off-cluster binary cache; the signing key an environment-scoped secret, main only, with a reviewer | In-cluster cache; nodes build; the key as a plain CI secret | One workflow secret could sign root code for every host ([review](../research/review/README.md) D10) |
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
| Cluster isolation | Flux lockdown, a service account and target namespace per Project; the service dry-runs as itself and a ValidatingAdmissionPolicy refuses its writes unless dryRun is set | No lockdown; dry-run by impersonating each Project | Isolation no longer rests on the compiler alone ([review](../research/review/README.md) D4) |
| Vault unseal | Cloud-KMS auto-unseal with a scoped, revocable credential as a host secret, and a VaultSealed alert | Manual unseal; an OpenBao static seal | A reboot no longer stops signing until the maintainer is back ([review](../research/review/README.md) D6) |
| Rollback path | Dry-run the last Serving render, move the tag back, set Pause; re-compose only if that dry-run fails | Re-compose only; the service driving Flux suspend | Recovery no longer depends on the parts that may be failing ([review](../research/review/README.md) D7) |
| Service writers | Strategy Recreate plus a Lease before Sign and MoveTag; startup reconcile from observed state | One replica with no leader election | A rolling update ran two writers ([review](../research/review/README.md) D9) |

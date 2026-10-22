# Design review

An ATAM-style review of the whole design, held on 2026-10-22: six independent
reviewers, one per area, each followed by a skeptic that tried to refute every
finding, then a synthesis. Every finding is weighed against the
[quality scenarios](scenarios.md). The decisions it raises are put to the
maintainer; each one that changes a choice becomes a Proposed record.

## Headline

The core of estate-kit is sound and should stay. Flux is the only applier, it pulls signed artifacts named by digest, and images are built once and promoted. The compiler sits behind a language-neutral subprocess seam (a directory in, a directory out, plus result.json). Rendering is deterministic, oracle files exist only at the four seams, CI identity is bound to repository_id, and the host design splits work by failure domain. Three things around that core are weak. First, the order of work. The plan ports about 16,400 lines of TypeScript to Rust at byte parity before delivering anything. The TypeScript compiler it ports changes several times a day, the parity target is a JavaScript YAML 1.1 emitter that no Rust crate reproduces, and much of the ported code is already scheduled for deletion in deploy-kit#373. The seam already lets the Go service cut over on the existing compiler. The host applier, the repository gates, the unit tests behind the 100% mutation gate and the mail provisioner are not scheduled at all. Second, several security mechanisms cannot be built as written: ghcr does not accept GitHub App tokens, Flagger and Flux cannot send projected service-account tokens, and RBAC cannot scope evictions to one node. Isolation also rests only on the compiler being correct. The service's dry-run RBAC equals write access, Flux is never locked down per tenant, and nothing checks where a sealed image digest came from. Third, recovery. The single control-plane node holds the SQLite datastore, a Vault that is unsealed by hand, and the backups. No path restores the k3s datastore. Rollback runs the whole compose, sign and dispatch chain. A k3s minor bump cannot be undone by a generation rollback, and four of the six active nodes have no boot assessment. Most fixes reorder or remove work, or reuse things the estate already runs: deploy-rs, nixos-anywhere, Flux lockdown flags, ValidatingAdmissionPolicy, the shared Postgres, the existing burn-rate alerts and the Vault snapshots. So they reduce maintainer load rather than add to it.

## Areas

| Area | Findings |
| --- | --- |
| [Model, language and compiler](model-and-compiler.md) | 8 kept, 0 refuted |
| [Delivery and GitOps](delivery-and-gitops.md) | 8 kept, 0 refuted |
| [Supply chain and security](supply-chain-and-security.md) | 8 kept, 0 refuted |
| [Hosts and NixOS](hosts.md) | 8 kept, 0 refuted |
| [Operations and recoverability](operations.md) | 8 kept, 0 refuted |
| [Process, testing and the plan](process-and-plan.md) | 8 kept, 0 refuted |

## Themes

### Deliver through the seam first; the parity port is the long pole

Overview steps 2 and 7 and plan/port.md put a full Rust port at byte parity ahead of the service merge. The finding counted 102 files and 16,414 source lines (the process review measured 15,908 lines of src). Neither number includes the 31,415 lines of tests, which do not carry over. The port chases a compiler that took 57 feat or fix commits to src/ in October 2026. #373 already plans its rewrite in TypeScript, and its contract PR deletes ledgers, alertClass, soft placement, the per-cluster overlay and several golden files. deploy-kit's CLI already composes directory to directory with --json. So the service, the switch from pins to tags and the dashboard switch can cut over against the TypeScript binary. Three gaps remain in that path. The TypeScript CLI does not write result.json yet. The staged-switch stages after the first (tags, a sealed images.lock, Admitted Projects) change compiler output and need their own proof, meaning reviewed oracle changes plus an explained shadow diff. And a Rust port after the cutover is the 'second port' that S14 forbids, unless it ports the frozen 1.0 model or never happens. port.md also schedules none of the new concepts (Mailbox, admission and UI roles, Infrastructure Intent, host data), and none of the host applier, the gate scripts, the unit tests behind the 100% mutation gate, or the Go port of the mail provisioner. Per-phase budgets, fallbacks and a concrete shadow exit are missing. The staged switch is ordered by component, while redesign-practices.md 1.1 describes a switch per Project.

Findings: model-compiler-1, model-compiler-4, process-1, process-2, process-4, process-7.

### The language choice has new facts against it, and Rust carries unpriced YAML and serde work

Answers now exist for most of the weak points the overview listed against TypeScript. node --build-sea arrived in Node 25.5 (Stability 1.1, ESM entry through mainFormat), bun build --compile and deno compile also make single binaries, zod checks types at runtime, and startup is about 0.35 s. npm stays for the Vue UI anyway, so Rust adds a third registry rather than replacing one. TypeScript 7 has no stable programmatic API yet, so typed linting still needs TypeScript 6. If Rust stays, the alignment design has gaps. Derived serde deserialization stops at the first error, while the every-offending-value oracle needs all three errors. `Option<T>` accepts null. Byte equality with the schemas zod generates contradicts deploy-kit [deploy-kit ADR 0088](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/architecture/0088-the-committed-schemas-and-their-corpus-are-the-contract.md), which makes the hand-written corpus the contract. The parity target is eemeli/yaml's YAML 1.1 quoting across 198 YAML oracle files, and no crate emits that. serde_yaml is deprecated, serde_yml is unsound (RUSTSEC-2025-0068), and serde-saphyr 2.0 landed on 2026-10-13. A 100% mutation gate on crates that are still being ported means writing unit tests before parity. Go mutation tooling is immature (gremlins v0.6.0). Python already runs estate-kit's docs and CI checks, which undercuts 'one toolchain less' as the reason to port the mail provisioner.

Findings: model-compiler-2, model-compiler-3, model-compiler-5, process-3, process-5, process-8.

### Identity mechanisms that cannot be built as written

GitHub Packages accepts only classic PATs, or GITHUB_TOKEN for packages linked to the workflow's own repository. GitHub App installation tokens are refused (community discussion #171423, still open in September 2026), and package grants are per package, never by name prefix. So 'App token scoped to render/ and host/' cannot be built. Flagger webhooks have no authentication field, and Flux providers send only static headers, an HMAC (generic-hmac) or a client certificate, so 'projected service-account tokens' for in-cluster callers cannot work. RBAC cannot limit pods/eviction by spec.nodeName, and the Node authorizer does not grant evictions, so 'RBAC limits each node to its own pods' cannot be enforced. The design also never says how the host applier authenticates to the API server. The authorization matrix has no rows for host rollout, the rollout-token exchange, Flux events or break-glass. It also lets Admin 'change admissions' in the UI, which bypasses the reviewed Platform Intent.

Findings: delivery-2, supply-3, supply-7, supply-8, hosts-5.

### Cluster blast radius rests on the compiler alone

No page names the identity Flux applies a Project render with. Without lockdown (--no-cross-namespace-refs, --no-remote-bases, --default-service-account plus a per-Project serviceAccountName), kustomize-controller applies as cluster-admin. Dry-run authorization is identical to the real request, so the service needs write power on everything Flux applies, which makes it a second estate-wide writer. One shared signing key and a mutable prod tag mean whoever can write tags can roll back, freeze, or substitute another Project's render (TUF's rollback, freeze and mix-and-match attacks), and the nightly drift check finds it up to a day later. Immutable semver promotion tags do not help, because ghcr has no tag immutability. The real mitigations are a narrow tag-write credential, Flux lockdown, and separate or per-Project keys as defence in depth.

Findings: delivery-1, supply-4, supply-5, delivery-5.

### Provenance and CI claims

S10 says a compromised Project 'cannot sign anything not built from its own sources'. Nothing checks where a sealed image digest came from, so the service will sign a render naming another Project's image or a hand-pushed one. The gate only blocks digests from outside the repository: an attacker who controls the repository still passes provenance. The OIDC check ignores event_name, pins the workflow by a movable ref instead of job_workflow_sha, and does not check ref_type, runner_environment or repository_owner_id. The production environment's required reviewer is real protection here, since the maintainer is the only admin. Most Project repositories are public, so GitHub artifact attestations are free for them. On the host side, the Nix narinfo key is a CI secret, the cache product is unnamed, and a toplevel narHash in the host tag would not cover dependencies.

Findings: supply-1, delivery-8, supply-2, supply-6, hosts-6.

### The single control-plane node is a combined loss with no written restore

frankfurt-contabo-1 holds kine/SQLite, every local-path volume, Vault (with Raft storage, unsealed by hand, pinned to site frankfurt) and the PVC holding the Vault snapshots and pg_dumpall. These are copied off-cluster daily, so the recovery point is about 24 hours. S8 needs a documented restore of the API server, and the design has none. The k3s docs say a datastore copy is useless without the original token, and SQLite needs a consistent copy (sqlite3 .backup). fleet-infra already has a full-cluster rebuild runbook, a 6-hourly Vault raft snapshot and a Vault restore playbook. The design should cite and own them, not rebuild them. Manual unseal means every control-plane reboot (the window, an OOM, a crash) stops signing, secrets, migrations and mail provisioning until the maintainer types keys in, which can take days. The Vault PDB (maxUnavailable 0) also makes a drain of that node hang. A k3s minor bump on the control plane cannot be undone by a generation rollback without a snapshot taken on the old minor. Losing the per-Project Pause and Rollback object in a rebuild lets the next recompose undo an emergency rollback.

Findings: hosts-1, ops-4, ops-1, hosts-3, supply-5.

### Rollback and Pause run through every dependency that might be down

UC-6 re-composes at the old fragment, so it needs the queue, the compiler, the API server, Vault, ghcr and possibly GitHub dispatch all healthy. The old render is already signed, and Flux accepts a tag moved back to it as long as its key is in the verify Secret. A fast path (dry-run the retained render against today's cluster, compare-and-swap the tag, set Pause) needs no Vault and no compose. Old renders carry the Platform Intent and ClusterState of their day, which is why the dry-run must stay. Retention says nothing about keeping signatures and referrers for as long as their renders. No break-glass runbook exists for the case where the service, Vault and GitHub are all down. Kustomization spec.suspend is not equivalent to the design's Pause, because it stops drift correction too.

Findings: delivery-3, ops-2.

### The service is heavier than its job, and its recovery trusts its own log

A one-replica Deployment surges to two pods on every upgrade, and ghcr has no conditional tag write, so two writers can move tags. Appending an event and moving a tag are not atomic, and the in-memory queue is lost on restart. Recovery should reconcile from observed state (the ghcr tag, Flux and Flagger status) as the host applier does. The registry render cache misses on every lockstep release. Until deploy-kit's per-Project artifact independence (#548, #482, #546, #545) lands, its key leaves out other Projects' fragments, so a hit can serve a stale render. Flux event ingestion can be replaced by watching status through client-go, which removes an unauthenticated caller. 'Its own Postgres' should say 'a database on platform-postgres', covered by the existing pg_dumpall and restore check. Reshaping the service into a level-triggered composer saves the SSE stream and the token exchange, but it drops the 'Rollout visibility' approval gate unless that is redesigned. No per-stage deploy budget exists, and a Receiver-triggered reconcile after a tag move is a cheap speed gain.

Findings: ops-3, delivery-4, model-compiler-6, ops-7, delivery-7, supply-7.

### Host rollout mechanics

The state machine drains and holds the estate-wide Lease, then finds out after switching that it must wait for the window, which can block the other site for a day. Reboot need should be decided from the fetched closure before the Lease is taken, and a reboot change staged with switch-to-configuration boot. Four of the six active nodes (three Pis on extlinux, Contabo on BIOS GRUB) have no boot assessment. Cheap fixes exist: test, then health, then boot for live switches; GRUB default=saved with grub-reboot; useBootLoader in VM tests; a wider reboot-need comparison. The node order ignores host-native roles (t1000 is the subnet router and holds Samba and the backup store) and has no canary-eligibility attribute. Enrollment is unspecified. deploy-rs 1.0.0 and nixos-anywhere already run here and fit break-glass and rebuild. kured does not solve eviction scoping, and per-site DaemonSets break one-node-at-a-time. Spegel is optional hardening only.

Findings: hosts-2, hosts-4, hosts-5, hosts-7, hosts-8, ops-5.

### Observability and destructive actions are thin

Three SLOs with no metrics, no alerts and no runbooks. Traces and logs cannot page anyone. The fleet already has burn-rate, VaultSealed, BackupStale and FluxResourceNotReady alerts, and the delivery alert rules read metrics the cutover removes. The new Mailbox lifecycle adds RemoveAccount when a mailbox is 'dropped from intent' (a rename, a dropped admission, a Flux prune), and today's provisioner never deletes accounts. A Vault restore loses keys generated after the snapshot, and the secret job then mints new keys that no longer match the database roles or Stalwart.

Findings: ops-6, ops-8.

### Documentation load and status hygiene

All 57 planned records are marked Accepted before any exists, and some rest on open questions (the Pause object kind, the YAML parser spike, the number of shadow days). That goes against the definition of Accepted and against lesson DR-2. Docs already drift: port.md says `render/<p>:live` on one line and :prod on another. The 31 metamodel diagrams are generated from Ecore files that #373 deletes. They survive at the hand-in tag, and the page should be labelled as a deploy-kit 0.31 snapshot. The rejection of configuration languages and packaging tools (CUE, KCL, Pkl, Nickel, Timoni, kro, KubeVela, Helm) is sound but unrecorded. deploy-kit's docs/research/modelling-languages.md already holds the survey, so it needs one choices.md row citing it.

Findings: process-6, model-compiler-7, model-compiler-8.

## Where the findings pull against each other

- Cutting over on TypeScript (model-compiler-1, process-2) works against S14. A Rust port after the cutover is the 'second port' that S14 forbids. It is acceptable only if it ports the frozen 1.0 model at parity, or if Rust is dropped. The TypeScript path also still needs compiler changes before the cutover (result.json, sealed digests, tag sources, model-path diagnostics), and those would later be ported again.
- On the ghcr credential, delivery-2 prefers a promote workflow using GITHUB_TOKEN (option a). That puts GitHub Actions and runner start-up on every tag move, rollback included, which conflicts with the fast rollback path (delivery-3, ops-2) and with S12 and S7. supply-3 prefers a machine-account classic PAT in Vault, which keeps tag moves in the cluster but adds a broad long-lived secret.
- For the service's dry-run identity, delivery-1 has the service impersonate per-Project ServiceAccounts, while supply-4 step 3 has a ValidatingAdmissionPolicy deny the service's own non-dry-run writes. These are mutually exclusive. Under impersonation, admission sees the Project's account, and that account is also the one Flux applies with. Pick one.
- The fast rollback (delivery-3, ops-2) pulls against choices.md 'Dry-run gates' and the Render key semantics. Moving a tag back with no compose restores old Platform Intent and ClusterState. The compromise is to dry-run the retained render against today's cluster, skip compose and sign, and set Pause so the next recompose does not move the tag forward again.
- Pause in the design means 'stop moving the tag, Flux keeps serving'. Kustomization spec.suspend (delivery-3) stops all reconciliation, and it would make the service a writer of Flux objects, which the 'Pin' choice rejected. The two are not interchangeable. Break-glass by a human is a documented exception, not an argument against the single-writer rule.
- hosts-4 suggests treating every host change as stage-then-reboot. hosts-2 shows that four of the six active nodes have no boot assessment, so more reboots means more unprotected boot-path risk, more USB flash wear on the Pis, and API pauses on the single control plane for OS-only changes.
- hosts-5 and process-4 propose kured, or comin plus kured, to cut bespoke code. The verifications show kured needs a cluster-wide eviction grant (so it does not fix scoping), that per-site DaemonSets break one-node-at-a-time (S9), and that comin has no cross-node coordination. Keeping deploy-rs until after the cutover is the low-effort option that does not weaken S9.
- delivery-4 reshapes the service so that publishing a fragment is the deploy request. That drops the production-environment approval carried by the deploy job's OIDC token, unless the composer verifies the signer identity and environment. It also reopens 'Rollout visibility', which the finding brings no new fact against.
- supply-1 and delivery-8 propose verifying Sigstore attestations in the service. That puts a TUF trusted-root fetch on the deploy path, which S7 must absorb. A service-side register-build route avoids that but is bespoke. Kyverno verifyImages adds a webhook and controllers on Pi workers, while built-in ValidatingAdmissionPolicy plus Pod Security Admission adds no component but cannot verify signatures.
- ops-1 calls a cloud-KMS seal the cheapest auto-unseal. On a Contabo VPS without workload identity it needs a static cloud credential on disk, so its trust is close to OpenBao's static seal, and it adds a startup dependency on the KMS. That pulls against recoverability under S7 and S8.
- process-8 and process-4 want the mail provisioner to stay in Python. choices.md 'Mail provisioner' ports it to Go for 'one toolchain less'. Python already runs estate-kit's docs and CI checks, so the stated benefit does not exist.
- process-6 wants just-in-time records with a soft cap. The decision register and AGENTS.md treat records as the normative source, and choices.md already says a choice binds only when its record lands. The disagreement is over the status label and reading load, not over whether to write records.

## Outcomes

The maintainer decided all twelve on 2026-10-22. Each changes or adds to a
choice in [`choices.md`](../../decisions/choices.md); the records that carry
them are Proposed until they are written and accepted.

| Decision | Chosen | Against the recommendation? |
| --- | --- | --- |
| D1: order of the cutover and the compiler language | TypeScript to 1.0 through the subprocess seam; a Rust port of the frozen 1.0 model only if a later record justifies it | No |
| D2: when the host applier is built | Build it as designed, alongside the service: a per-node credential, the eviction scope held by a ValidatingAdmissionPolicy on `spec.nodeName`, break-glass on deploy-rs | Yes: the review recommended deferring it and keeping deploy-rs |
| D3: write access to `render/` and `host/` tags | A machine account's classic PAT in Vault, limited to those packages, rotated and checked; the App-token drill runs first | No |
| D4: what a signed render and the dry-run can change | Flux lockdown, per-Project service accounts and target namespaces; the service dry-runs as itself, and a ValidatingAdmissionPolicy refuses its writes unless `dryRun` is set | No |
| D5: restoring the API server's datastore | Keep SQLite; a timer copies a `.backup` and the server token off the provider; a restore runbook, drilled once in a VM | No |
| D6: Vault unseal | Cloud-KMS auto-unseal with a scoped, revocable credential as a host secret, and a VaultSealed alert | No |
| D7: the rollback path | Dry-run the last Serving render, move the tag back, set Pause; re-compose only when that dry-run fails; a break-glass runbook | No |
| D8: legitimacy of image digests and CI tokens | A claim policy with token fixtures, a build job split from the deploy job, and a route that registers built digests | No |
| D9: the service's state and recovery | Recreate plus a Lease before Sign and MoveTag, startup reconcile from observed state, Flux status watched, no render cache, the event log on the shared Postgres | No |
| D10: keys | Separate render and host keys, an offline recovery key, the Nix key as an environment-scoped secret, the signature format fixed by a contract test | No |
| D11: how a node switches and reboots | Decide the reboot before the Lease, stage with `boot`, test-then-boot for live changes, per-bootloader fallbacks, minor k3s bumps behind a snapshot and approval | No |
| D12: what defines a render's bytes | A canonical YAML style, specified on one page and introduced in deploy-kit#373's contract pull request | No |

D1 and D2 pull against each other: D1 drops the Rust port to save effort,
while D2 adds the largest bespoke component back into the early phases. The
plan has to budget for the host applier explicitly.

## Decisions for the maintainer

### D1: In what order do the cutover and the compiler language happen?

For reordering: the subprocess seam already lets the Go service run any compiler that honours the directory and result.json contract, and deploy-kit 0.31's CLI already composes directory to directory with --json. Every problem in port.md except 'no single binary' is solved by the service and the registry tags. A single binary is now possible with node --build-sea or bun build --compile. Porting about 16k lines at byte parity, against a compiler that took 57 feat or fix commits in October, delays all delivery value, and much of the ported code is deleted in #373's contract PR. Lesson MD-5 asks for a walking skeleton first. For the current plan: byte parity is a clean proof that separates a language change from a meaning change. Rust's sum types fit the model. The maintainer has already sustained lockstep parity with the EMF implementation at October's rate. Changes to the TypeScript compiler before the cutover (result.json, sealed digests, tag sources) will have to be ported later. A Rust port after the cutover conflicts with S14 unless it ports the frozen 1.0 model. Whichever option is chosen, add a sequencing table to port.md that marks each new concept and each pinned-input change as additive (allowed before the cutover) or a change of meaning (waits for the rewrite), names the proof for every staged-switch step after the first, and gives each phase an hours budget, a fallback and a concrete shadow exit.

**Reopens:** choices.md 'Rewrite and parity', 'Rust start', 'Old repos meanwhile', '#373 tickets' and 'Languages'; overview.md 'Order of work' steps 2 and 7

- **A: TypeScript to 1.0, Rust optional after** (recommended): Walking skeleton: the Go service shells out to the existing TypeScript compiler, shipped as a single binary or an image, and writes shadow tags. Merge the Go services, shadow, then switch Project by Project. Do the #373 rewrite in TypeScript, where its tests and Stryker setup live. Port to Rust only from the frozen 1.0 model against the TypeScript 1.0 oracles, and only if a Proposed record then justifies it.
- **B: Rust first, with convergence rules**: Keep the Rust port before the service. Freeze one concept at a time while it is being ported, count port-forward debt in CI, and stop the port and fall back to A if the debt grows for six weeks running.
- **C: TypeScript permanently**: As A, but close Rust in the record now. The compiler stays TypeScript, with a trimmed npm tree (oxlint or Biome, --ignore-scripts, minimumReleaseAge).
- **D: Go compiler**: Port the compiler to Go so there is one backend toolchain with the service. It is still a full port, with no sum types and immature mutation tooling.

Findings: model-compiler-1, model-compiler-2, model-compiler-4, process-1, process-2, process-7, process-8.

### D2: When is the host applier built, and what covers hosts until then?

For deferring: port.md never schedules the host applier. It is a new bespoke agent with six ports, a per-node API credential the design does not specify, and an eviction scope that RBAC cannot enforce. It would replace a working deploy-rs path with magic rollback during the cutover. deploy-rs 1.0.0 (2026-10-19) and nixos-anywhere already run in nix-config, and compiled host data can generate their configuration for break-glass and enrollment. For building now: the pull model has real benefits (no push credentials, works without the operator's machine), and Infrastructure Intent and host data are already specified in deploy-kit spec 15. Both kured and comin plus kured weaken S9 (separate locks, no cross-node coordination) and do not solve eviction scoping. Whatever is built later needs an answer for how a break-glass push and the pull applier reconcile.

**Reopens:** choices.md 'Host apply' (timing) and overview.md 'Order of work'; plan/port.md 'Order of work' (applier unscheduled)

- **A: Defer, keep deploy-rs** (recommended): Hosts stay on deploy-rs push with magic rollback until after the cutover. The compiler emits deploy-rs and nixos-anywhere targets from host data. Break-glass and enrollment use these tools. The host applier is a Proposed record for later.
- **B: Build the applier as designed**: Build it alongside the service, with a per-node credential, the eviction scope enforced by a ValidatingAdmissionPolicy on spec.nodeName, and break-glass on deploy-rs.
- **C: kured plus a small host stager**: kured does lock, drain and window, and a host-side stager verifies the tag and stages with switch-to-configuration boot. Accept per-site locks and kured's cluster-wide grant.

Findings: process-4, hosts-5, hosts-7, hosts-2.

### D3: How does the service get permission to write render/ and host/ tags on ghcr?

GitHub Packages documents only classic PATs, plus GITHUB_TOKEN for packages linked to the workflow's own repository, and App installation tokens are denied in practice. So the designed 'App token scoped to render/ and host/' does not exist. For a PAT on a machine account: the tag move stays in the cluster, rollback stays fast, and grants can be limited to the render and host packages by a check that lists them. Against it: it is a long-lived secret (the App key already is one). For a GITHUB_TOKEN promote workflow: no long-lived credential, and per-package Actions access. Against it: GitHub Actions and runner latency sit on every tag move, rollback included. For an in-cluster registry: the service pushes with its own identity. Against it: a stateful component to run, and 'Render store' was rejected so that a rebuilt cluster can still pull renders.

**Reopens:** choices.md 'Hosting' ('the deploy credential stays inside the cluster') holds under A; C reopens 'Render store'; identity-and-access.md row 'Service to GitHub and ghcr' and the security.md 'Service to ghcr' mitigation must be rewritten

- **A: Machine-account PAT in Vault** (recommended): A dedicated bot account with write only on the render and host packages. Its classic PAT lives in Vault and rotates on a check. A check fails on any extra package grant. Run the App-token drill first.
- **B: Promote workflow with GITHUB_TOKEN**: The service signs in the cluster and dispatches an estate-kit workflow that moves the tag with GITHUB_TOKEN and per-package Actions access.
- **C: In-cluster registry mirrored to ghcr**: Reopen 'Render store': zot in the cluster with a nightly mirror to ghcr. The service pushes with its own identity.

Findings: delivery-2, supply-3, supply-5.

### D4: What limits what a signed render, and the service's dry-run, can change in the cluster?

Without Flux lockdown, kustomize-controller applies every render as cluster-admin, and a dry-run needs the same RBAC as a real write. Flux lockdown (--no-cross-namespace-refs, --no-remote-bases, --default-service-account, per-Project serviceAccountName and targetNamespace) is cheap and should happen in every option. The real choice is how the service dry-runs. With its own identity, a ValidatingAdmissionPolicy can deny every non-dry-run write from that identity, so the API server itself prevents real writes. The cost is that the dry-run does not exercise per-Project RBAC. Impersonating each Project's account makes the dry-run prove that RBAC too. But impersonating accounts that can write is, in effect, write power, and the platform Project's account is near cluster-admin. Per-Project Transit keys are optional defence in depth once targetNamespace confines a substituted render.

**Reopens:** No choices.md row; fills a gap under 'Hosting' and 'Applier' and adds rows to the security.md trust-boundary table

- **A: Lockdown, own identity, dry-run-only VAP** (recommended): Flux lockdown. The service dry-runs with its own identity. A ValidatingAdmissionPolicy denies writes from that identity when request.dryRun is false, with a fixture that proves request.dryRun is reachable. Pod Security Admission and a digest-only image policy are labelled per Project, with exemptions in Platform Intent.
- **B: Lockdown, impersonation**: Flux lockdown. The service dry-runs by impersonating each Project's ServiceAccount and accepts write-equivalent rights through that account.
- **C: As designed**: No lockdown. The service holds write RBAC, and isolation rests on the compiler.

Findings: delivery-1, supply-4, delivery-5.

### D5: How is the API server's datastore backed up and restored after losing frankfurt-contabo-1?

S8 needs a documented restore, and there is none. For keeping SQLite with a timer: it is the smallest change. A sqlite3 .backup plus the token goes off the node and off the provider beside the existing Vault snapshots, and the fleet-infra rebuild runbook and Vault restore playbook already exist and only need citing. It also makes the pre-switch snapshot for a k3s minor bump trivial. For one-member etcd: built-in snapshots, S3 upload and a documented cluster-reset restore, and a path to HA. Against it: it is a one-way production conversion, etcd is sensitive to fsync latency on a VPS disk, and it costs more memory. Three servers need low-latency peers the estate does not have. In every option the service must treat a missing per-Project object as Paused, and k3s minor bumps on the control plane need a snapshot first and Operator approval.

**Reopens:** choices.md 'Control plane' (adds a restore path to 'accept API downtime'); 'Pause and rollback state' (a missing object must default to Paused)

- **A: Keep SQLite, add a backup timer** (recommended): A NixOS timer runs sqlite3 .backup and copies the server token to off-provider object storage. A restore runbook built on nixos-anywhere, the off-cluster cache, the datastore copy and the Vault playbook. A restore drill in a VM.
- **B: Convert to one-member etcd**: Restart with --cluster-init. Scheduled etcd snapshots with --etcd-s3 off-site. Restore with cluster-reset.
- **C: Three servers now**: k3s HA with embedded etcd.

Findings: hosts-1, ops-4, hosts-3.

### D6: How does Vault unseal after the control-plane node restarts?

Today Vault is unsealed by hand. Every reboot of frankfurt-contabo-1 in its window, every OOM and every crash leaves signing, secrets, migrations and mail provisioning stopped until the maintainer types keys in. For one person with a few hours a week that can be days, which undermines S7 and S8. vault-0 cannot move, because it is pinned to the only frankfurt node, and its PDB makes a drain of that node hang. Auto-unseal removes the wait on a person. A cloud KMS seal keeps the key off the node and the access is revocable and audited, but on Contabo it needs a static cloud credential and a reachable KMS at startup. OpenBao's static seal has no external dependency, but the key sits on the node's disk and it needs a move from Vault to OpenBao. Keeping manual unseal is honest and costs nothing, but recovery then depends on the maintainer being available.

**Reopens:** No choices.md row; amends overview.md Risks 'Vault on the deploy path' and touches 'Signing' (Vault availability)

- **A: Cloud-KMS auto-unseal** (recommended): Vault Community with an awskms or gcpckms seal. A scoped, revocable credential as a NixOS host secret. A VaultSealed alert and a 'Vault sealed' failure sequence in releasing.md.
- **B: OpenBao static seal**: Move to OpenBao (its Transit API is the same, and cosign supports openbao://). The static key is a NixOS host secret. Record the trust trade-off.
- **C: Keep manual unseal**: Document it as an accepted limit. Alert on the sealed state, and have the host applier halt rather than reboot the control plane while unseal cannot be confirmed.

Findings: ops-1, supply-5.

### D7: What path does a rollback take?

UC-6 re-composes, dry-runs, signs through Vault and moves the tag, so the recovery tool depends on the same things that are failing during an incident. Every render that ever served is already signed, and Flux accepts a tag moved back to it while its key is in the verify Secret. Against a bare tag move: the old render carries old Platform Intent and ClusterState, and 'Dry-run gates' requires a dry-run before every tag move. A fast path that dry-runs the retained render against today's cluster and sets Pause keeps that rule while dropping compose, Vault and dispatch. Signatures and referrers must then be retained exactly as long as their renders. A human break-glass (flux suspend, or OCIRepository spec.ref.digest) stays a documented exception and does not make the service a writer of Flux objects.

**Reopens:** Keeps choices.md 'Dry-run gates' and 'Pin'; amends 'Pause and rollback state' and 'Retention'; C reopens 'Pin' (no second writer of Flux objects)

- **A: Fast path, then re-compose** (recommended): Dry-run the last Serving digest, compare-and-swap the prod tag back to it, and set Pause. Fall back to re-compose only if that dry-run fails. Retain signatures with their renders. Write a break-glass runbook that works with the service, Vault and GitHub all down, and test S3 with Vault scaled to zero.
- **B: Re-compose only**: Keep UC-6 as designed and add only the signature retention and the break-glass runbook.
- **C: The service drives Flux suspend and digest**: Implement Pause and Rollback as writes to Kustomization spec.suspend and OCIRepository spec.ref.digest.

Findings: delivery-3, ops-2, ops-8.

### D8: How does the service know an image digest, and the CI token behind it, are legitimate?

Nothing checks where a sealed image digest came from, and the OIDC check ignores event_name and pins the workflow by a movable ref. Hardening the claims costs one contract test: event_name allowlist, job_workflow_sha, ref_type=tag for deploys, runner_environment=github-hosted, repository_owner_id, and never sub. The environment claim stays as one input, because its reviewer is the maintainer. For a register-build route: it works on any plan, adds no TUF fetch to the deploy path, and the event log doubles as the S15 record. Against it: it is bespoke and not portable SLSA provenance. For GitHub attestations: standard SLSA, and free for the mostly public Project repositories. Against it: sigstore-go verification and a cached trusted root on the deploy path. Both need the build job split from the job that requests the token, and an allowlist of third-party images by digest in Platform Intent.

**Reopens:** choices.md 'CI identity' (adds event_name and job_workflow_sha) and 'Release PR images'/'Image lock' (adds a provenance gate)

- **A: Claim policy and a register-build route** (recommended): Claim policy table with pass and fail token fixtures. The build job and the attest-and-deploy job are split. The attest job registers its pushed digests through an OIDC-authenticated route. The service refuses any digest that is unregistered or off the allowlist.
- **B: Claim policy and GitHub attestations**: Same claim policy. actions/attest in the pinned reusable workflow. The service verifies the bundles with sigstore-go before composing.
- **C: Claim policy only**: Harden the token check and accept the provenance gap for now.

Findings: supply-1, delivery-8, supply-2.

### D9: How should the service hold its state and recover?

Several cheap fixes have no real downside. Use strategy Recreate plus a coordination Lease checked right before Sign and MoveTag, because a one-replica Deployment surges to two pods. Rebuild unfinished rollouts at startup from the ghcr tag and Flux and Flagger status, or end them with an Abandoned event. Watch Flux status instead of taking unauthenticated Flux events. Put the event log in a database on platform-postgres, covered by the existing dump and restore check. Drop the registry render cache: it misses on every lockstep release and can serve stale renders until the per-Project independence work lands. Keep the Render key as provenance, and skip publishing on digest equality. The bigger option, a level-triggered composer where publishing a fragment is the deploy request, removes the SSE stream and the token exchange. But it drops the approval gate that 'Rollout visibility' carries unless the composer verifies signer identity and environment, and it brings no new fact against that choice.

**Reopens:** choices.md 'Caching' (drop the lookup), 'In-cluster identity' (watch status instead of events, since projected tokens cannot be sent), 'Rollout log' (clarify the database location); B also reopens 'Rollout visibility' and 'Delivery semantics'

- **A: Harden the designed service** (recommended): Recreate plus Lease, startup reconcile from observed state, watch Flux status, no render cache, the event log as a database on platform-postgres, the Release Gate answered from cluster state only, and a Receiver-triggered reconcile after each tag move.
- **B: Reshape into a level-triggered composer**: Publishing a fragment is the deploy request. Progress is written as conditions and GitHub Deployment statuses. Postgres becomes a disposable cache.
- **C: As designed**: Keep one replica with no leader election, the cache lookup and event ingestion.

Findings: ops-3, delivery-4, model-compiler-6, ops-7, supply-7, delivery-7.

### D10: Which keys do Flux, the host appliers and the Nix cache trust, and where do they live?

One Transit key signs both renders and host tags, so misuse of that key means every Project plus root on every node. With no recovery key, losing Vault means break-glass on every node. Separate keys for render and host, plus an offline recovery key trusted alongside each (Flux accepts several .pub files), are cheap. Vault Raft snapshots already exist, so what is missing is a written restore. The signature format should be fixed: legacy .sig tag or bundle referrer, with tlog upload off so repository names stay out of public Rekor. A contract test should sign with the service's signer and verify with the pinned Flux and the host verifier. The Nix narinfo key sits in CI. It belongs to the private, maintainer-only estate or nix-config repository, so it is not exposed to S10, and an environment-scoped secret with a reviewer is the cheap fix. A cache that signs on the server (niks3 v1.15.0) moves the key out of GitHub, but it is an off-cluster service with S3 and Postgres to run. Per-Project keys are optional.

**Reopens:** choices.md 'Signing' (one key) and 'Host closures' (key custody and cache product unnamed); 'Host pointer'

- **A: Split keys, recovery key, scoped Nix secret** (recommended): A render key and a host key in Transit, plus an offline hardware recovery key trusted everywhere. The Nix key becomes an environment-scoped secret limited to main with a reviewer. Two trusted-public-keys. Name the cache in a record. Fix the signature format with a contract test.
- **B: A, plus per-Project keys and a server-signing cache**: Add per-Project Transit keys and move the Nix key into niks3 signing on the server with OIDC push.
- **C: As designed**: One Transit key, and a Nix key held as a CI secret.

Findings: supply-5, supply-6, hosts-6.

### D11: When the host applier is built, how does a node switch and reboot?

This applies once the applier exists (see D2). The current state machine drains and holds the estate-wide Lease, then finds out after switching that it must wait for the window. Four of the six active nodes have no boot assessment. Rebooting every change gives every generation a boot test and removes live-switch hazards, but on nodes without boot counting it multiplies unprotected reboots, wears Pi flash, and pauses the API for OS-only changes. The mixed approach decides reboot need from the fetched closure before taking the Lease, and stages reboot changes with 'boot' so drain and Lease happen only inside the window. It also applies live changes as test, then health, then boot, and needs per-bootloader handling: GRUB saved default and grub-reboot on Contabo, bootCounting on systemd-boot, and a documented reflash on the Pis. A k3s minor bump on the control plane needs a datastore snapshot and Operator approval, and a two-node mixed-version VM test.

**Reopens:** choices.md 'Host apply', 'Maintenance windows' and 'Node order'

- **A: Decide before the Lease, stage, test-then-boot** (recommended): Decide reboot need before the Lease, comparing kernel, initrd, modules, params and dtbs. Stage with 'boot', and take the Lease and drain only in the window. Live changes go test, then health, then boot. Per-bootloader fallbacks. Gate minor bumps with a snapshot and approval. Add canary eligibility and host-native probes to Infrastructure Intent.
- **B: Stage-then-reboot every change**: Every host change is staged with 'boot' and rebooted in the window. Live 'test' switches only for urgent fixes.
- **C: As designed**: Lease, drain, switch, then wait for the window.

Findings: hosts-4, hosts-2, hosts-3, hosts-8.

### D12: What exact byte format defines a render, if a second compiler implementation remains possible?

This only matters if D1 keeps any port. Today's render bytes are eemeli/yaml 2.9.1's YAML 1.1 quoting (lineWidth 0) across 198 YAML oracle files, and no Rust crate reproduces it. A canonical YAML subset described on one page, or RFC 8785 JSON (which is valid YAML), makes parity cheap in any language. The cost: every oracle changes once in a hand-reviewed PR, with TM-2's structural diff as the proof that nothing semantic changed, and every Project is reapplied by Flux once. The best moment is #373's contract PR, which rewrites oracles anyway. Copying the exercised YAML 1.1 subset in Rust avoids the oracle churn but makes a bespoke emitter permanent upkeep. Whatever the choice, a Renovate rule must hold yaml at 2.x, because 3.0 is in prerelease.

**Reopens:** choices.md 'Rewrite and parity' (what 'byte-identical' is measured against) and 'Expected outputs'

- **A: Canonical YAML subset in #373's contract PR** (recommended): Specify a small canonical style (quoting rules, block literals for multi-line strings) and implement it in TypeScript as part of the #373 contract PR. A future port implements the same spec, with a differential test.
- **B: RFC 8785 JSON renders**: Emit canonical JSON for every Deliverable. Byte determinism comes free across languages, but diffs are harder to read.
- **C: Match eemeli/yaml 1.1 in Rust**: Keep today's output and write a Rust emitter that reproduces the exercised YAML 1.1 subset.

Findings: model-compiler-5, process-3, model-compiler-3.

## Spikes

| Spike | Question | Approach | Effort |
| --- | --- | --- | --- |
| ghcr App-token drill | Can a GitHub App installation token push and move a tag on an org ghcr package, and can any token type be limited to the render and host packages? | In a throwaway org package, try docker login and a crane tag with an App installation token. Then try a classic PAT on a bot account granted write on one package only, and confirm it is refused on another package. Write down the exact errors. | 1 hour |
| TypeScript walking skeleton through the seam | Can the existing deploy-kit compiler run as one binary on linux-arm64 behind the Go service and produce byte-identical renders, and how long does it take? | Bundle the CLI and build it with node --build-sea (ESM through mainFormat), and also with bun build --compile. Have a 30-line Go program exec 'compose --fragments ... --out ... --json' on the 'minimal' example. Diff the output against the npm run, and record binary size and wall time on a Pi. | Half a day |
| Dry-run fidelity and dry-run-only identity | Does a ValidatingAdmissionPolicy see request.dryRun and block the service's real writes while allowing its dry-runs? How do a CRD-plus-CR render and a new-namespace render behave under dry-run? | In kind with k3s's Kubernetes version, write a VAP keyed on the service's user and request.dryRun, and run a dryRun=All apply and a real apply as that user. Dry-run a render containing a new CRD with a CR, and a namespace with objects in it. Record the error shapes for an 'unverifiable' outcome. | Half a day |
| Signature replay and rollback behaviour in Flux | Does Flux 2.9.6 accept a tag moved back to an old signed digest, and another Project's render copied with its signature? Does cosign v3 with tlog off verify under each format? | In kind with Flux 2.9.6, sign two renders with one key in the legacy .sig format and as a bundle with tlog upload off. Point an OCIRepository at a tag, move it back, then copy the other render across. Repeat with two keys in the verify Secret. Record which cases verify. | Half a day |
| k3s SQLite restore and minor-version rollback | Does a sqlite3 .backup plus the token restore a working API server on a fresh host? Does a minor-bump rollback work with a pre-switch snapshot and fail without one? | NixOS VM test: boot the control-plane class on k3s 1.36, back up, then upgrade to 1.37. Restore onto a fresh VM, then roll back with and without the snapshot. Assert the API comes up and a pod schedules with an old-version agent. | 1 day |
| Vault auto-unseal on restart | How long does Vault take to come back unsealed after a pod or node restart under a cloud-KMS seal, and what happens when the KMS cannot be reached? | Run a dev Raft Vault in a VM with an awskms or gcpckms seal and a scoped credential. Kill the pod, reboot the VM, and block KMS egress. Record the time to unsealed and the failure mode. | 2 hours |
| OIDC claims under pull_request_target | What claims does a token minted in a pull_request_target job that calls a reusable workflow with environment production carry, and does the approval gate hold? | In a scratch public repository, trigger pull_request_target from a fork, call a reusable workflow that prints the decoded token claims (no secrets), and compare them with a release-triggered run. Check event_name, ref, job_workflow_sha and environment. | 1 to 2 hours |
| Boot assessment on the bootloaders the fleet uses | Can a bad generation on BIOS GRUB fall back automatically with default=saved and grub-reboot, and what does an extlinux Pi do with a broken kernel? | NixOS VM tests with virtualisation.useBootLoader=true: a BIOS GRUB machine boots a deliberately broken generation once through grub-reboot and must come back to the old one. On a spare Pi, try a generation with a bad initrd and time how long a reflash takes. | 1 day |
| Rust YAML gap measurement (only if a port survives D1) | How many of the 198 oracle YAML files does serde-saphyr 2.0 reproduce byte for byte, and how large is a canonical-subset emitter? | Parse each oracle into a value with saphyr, re-emit it with serde-saphyr defaults, and count differing files and the quoting cases. Then write the canonical-subset emitter in about 100 lines and count its lines and cases. | 1 day |
| KVM on GitHub's arm64 runners | Does ubuntu-24.04-arm expose /dev/kvm, so that an aarch64 NixOS VM test fits the 2-minute and 10-minute budgets? | A one-job workflow that runs 'ls -l /dev/kvm' and a minimal nixosTest, and records the wall time. | 30 minutes |

## Keep

- Flux as the only applier, pulling only signed artifacts named by digest. Images are built once on the release PR and promoted by digest, so what dry-ran is what deploys (where-state-lives.md, releasing.md 'The three runs').
- The subprocess seam: a directory in, a directory out, and a schema-validated result.json, with the same binary in CI and in the service. It is what makes the language and order decisions cheap to reopen (inside-the-compiler.md 'The wire to the service').
- Determinism rules (BTreeMap, RFC 8785 JSON in ConfigMaps, double render). Hand-reviewed oracle files only at the four seams, never rewritten by CI. Unit tests that assert properties, never snapshots.
- Committed JSON Schemas as the language-neutral contract, with additive-only evolution and unknown keys refused. Diagnostics that carry a model path the caller resolves to a line, keeping source positions out of fragments. Adopt deploy-kit [deploy-kit ADR 0088](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/architecture/0088-the-committed-schemas-and-their-corpus-are-the-contract.md)'s accept/refuse corpus as the drift test.
- A bespoke derivation model over CUE, KCL, Pkl, Nickel, Timoni, kro, KubeVela or Helm. The model's work is total derivation plus refusal codes, not templating. Record the rejection by citing deploy-kit's modelling-languages survey.
- CI identity bound to repository_id, a pinned reusable workflow and the production environment. A dry-run before every tag move, and nothing signed unless it is accepted.
- The signing key as a non-exportable Vault Transit key through cosign's hashivault:// provider, and digest-only admission. Flux's multi-key verification allows rotation without downtime.
- Idempotent deploy calls on (project, fragment digest), compare-and-swap tag moves, cancelling a job only detaching it, and resume by sequence number.
- An inert shadow: unsigned `shadow/<p>` tags that admission refuses. A staged switch with a revert at each step, best run per Project as redesign-practices.md 1.1 describes.
- No central pin repository, and a nightly drift check that reports differences rather than repairing them silently.
- Host design split by failure domain. Closures built in CI into an off-cluster cache. Fetch before any disruption. The window gates only the start of a reboot. Node order derived from the change with a version-skew check. Typed host data consumed by hand-written Nix modules. One server rather than a WAN quorum or etcd on Pi storage.
- A STRIDE table per boundary and an authorization matrix with a test that fails on any route without a row. Most designs at this size have neither. Extend it rather than replace it.
- Error codes only for authored input that does real harm, each with a firing fixture. Compiler invariants are tests.
- Quality scenarios S1 to S15 with numeric budgets, Locked records mapped onto MADR Confirmation with a failing check each, and lessons DR-1 and DR-2 requiring claims to settle on a source or a drill.

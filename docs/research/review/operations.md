# Review: operations and recoverability

Part of the [design review](README.md). Each finding was checked by a second
reviewer that tried to refute it; its verdict and corrections follow the finding.

## Verdict

The design separates serving from delivery. Flux keeps applying the last signed tag whatever happens to the service. The host applier resumes from what it observes on the node, and that is the right base. Recovery is weaker because almost every recovery action (Rollback, Pause, a re-signed render) goes through the dependencies that fail: Vault, which today must be unsealed by hand; GitHub workflow dispatch; and a single service replica nothing stops from running twice. Three things are missing outright: a restore path for the k3s control-plane datastore (S8), a backup story that survives losing frankfurt-contabo-1, and any metric or alert that would tell a one-person on-call that an SLO is being missed. Most fixes reuse things the estate already runs (the shared Postgres and its verified restore script, the burn-rate alerts, Alertmanager to Discord, Flux multi-key verification, the k3s embedded mirror and etcd snapshots), so they lower the maintainer's load instead of raising it.

## What the design gets right

- Serving is decoupled from delivery: Flux keeps serving the last signed render when the service, Vault, GitHub or Postgres fails (overview.md Risks; inside-the-service.md One replica).
- Deploy calls are idempotent on the natural key (project, fragment digest), and the stream is at-least-once with resume by sequence, both with named tests (conventions.md Retries/Delivery; releasing.md Failure paths).
- The host applier is level-triggered and resumes from the node's observed state. Its Lease has a TTL, and break-glass needs neither the cluster nor Vault (hosts.md When an applier crashes, When the cluster is down). This is the right model, and the service should copy it (see ops-3).
- Renders live in ghcr, signed and named by digest, so a rebuilt cluster can still pull them, and the retention job refuses to delete a tagged render (choices.md Render store; conventions.md Retention).
- Drift is reported and never repaired silently, and a timer heals missed triggers by scanning the registry (where-state-lives.md The nightly drift check; operating.md Rollouts no Project run started).
- A dry-run runs before every tag move, and nothing is signed unless it is accepted, so a stale estate cannot be signed into production (releasing.md What a dry-run is).
- Events hold no personal data and carry the rollout id as the correlation key across traces and logs, which keeps restore and retention free of erasure work (conventions.md Events, Telemetry).

## Findings

### ops-1: Vault is unsealed by hand, and the design's own host rollouts will seal it

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| risk | high | S7, S6, S3, S9 | weakened | high |

**Concerns:** overview.md Risks ('Vault on the deploy path'); hosts.md A host rollout (pods leave through the Eviction API); mail-and-components.md Components (secret-job, migration-runner and mail-provisioner all read Vault)

Today Vault (vault-0 in data-system) is unsealed manually with Shamir shares (fleet-infra/cluster/bootstrap/README.md 'Vault unseal'). Any restart of vault-0 leaves it sealed: an eviction, an OOM, a node reboot or the control plane's monthly window. The host applier evicts every pod from each node it switches, so a routine host rollout will at some point restart vault-0 and seal it. From then until the maintainer types unseal keys, nothing is signed (deploys and UC-6 Rollback), the migration runner cannot read its owner credential, the secret job and the mail provisioner fail, and VSO cannot refresh secrets. The design names 'Vault down' as a risk but treats it as an outage that resolves itself. With a manual unseal it waits on a person, and for one maintainer with a few hours a week that can mean days.

**Recommendation.** Make Vault auto-unseal before the cutover and record the choice. The cheapest path is a cloud-KMS seal, which HashiCorp Vault Community supports (AWS KMS, GCP Cloud KMS and others; only PKCS#11 is Enterprise). Its only new dependency is a KMS call at startup. The alternative is OpenBao's built-in static seal, with the key delivered as a NixOS host secret (sops-nix or agenix). That is weaker, so record the trust trade-off. Add a 'Vault sealed' failure sequence to releasing.md: the deploy fails loudly with a problem+json code, and the Project stays on its current tag. Add a host-applier rule: refuse to drain a node that hosts vault-0 unless Vault reports unsealed and auto-unseal is configured, or else move vault-0 first.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| HashiCorp Vault cloud-KMS auto-unseal (awskms, gcpckms, azurekeyvault, ocikms) | Vault v2.2.0 released 2026-10-15; the KMS seals are not marked Enterprise in the seal docs (only HSM PKCS11 is) | Small cost and an external dependency at Vault startup only; unseal no longer needs a person |
| OpenBao static seal | OpenBao v2.7.1 released 2026-10-01 (Linux Foundation project); static key unseal added in the 2.4 line | No cloud dependency, but the AES key sits on a node's disk, so the seal is only as strong as that host secret; it also means migrating from Vault to OpenBao |
| Vault Transit auto-unseal from a second Vault | Supported in Community | Needs a second, always-up Vault off the cluster, which means more to run, not less |

**Verification (weakened).** The core risk holds and is the most serious one in this area. fleet-infra/scripts/ops/unseal-vault.sh says 'There is no auto-unseal'. The Vault HelmRelease (fleet-infra/cluster/flux/apps/data/vault/release.yaml) pins the server to site frankfurt, and its comment says Vault's 'pod restart would seal it'. inventory/node-contract.lock.yml lists frankfurt-contabo-1, the only control-plane node, as the only frankfurt node. So any restart of the control plane seals Vault: a reboot in the maintenance window, an OOM, a crash. hosts.md also sends k3s bumps to the control plane first. The design's Risks entry ('Flux keeps serving the last tags') never says that recovery waits on a person. The mechanism, though, is wrong. With ha.replicas: 1, the Vault chart's vault.pdb.maxUnavailable template renders a PodDisruptionBudget with maxUnavailable 0. The Eviction API therefore always refuses vault-0, and a drain that goes through the Eviction API (as hosts.md specifies) never evicts it. A host rollout stalls on frankfurt-contabo-1 instead of sealing Vault through eviction. Vault seals only when the reboot goes ahead anyway or the pod dies another way. The recommendation 'or else move vault-0 first' cannot be done: the nodeSelector and the raft data tie Vault to the one frankfurt node. Calling cloud KMS the 'cheapest path' is also overstated. A Contabo VPS has no workload identity with AWS or GCP, so it needs a static cloud credential on the node, plus an outside account. Its trust ends up close to the OpenBao static seal, and Vault stays sealed whenever the KMS cannot be reached at startup. Version facts check out: Vault v2.2.0 (15 Oct 2026, latest), OpenBao v2.7.1 (1 Oct 2026), static seal added in OpenBao 2.4.0, and only PKCS#11 and seal HA are marked Enterprise.

**Corrections.** A host rollout does not seal Vault through eviction. The chart's PDB (maxUnavailable 0 at one replica) makes the Eviction API refuse vault-0, so draining frankfurt-contabo-1 hangs and blocks the rollout at the control plane, which k3s bumps visit first. Vault seals on the node's reboot, a crash or an OOM, not on eviction. vault-0 cannot be moved: the nodeSelector is site frankfurt, and frankfurt-contabo-1 is the only frankfurt node. A cloud-KMS seal on Contabo needs a long-lived cloud credential on disk, so its trust is close to a static seal. The design should also say what the host applier does when a PDB blocks a drain: a timeout, then halt.

Sources:

- `JorisJonkers-dev/fleet-infra: cluster/bootstrap/README.md`
- `JorisJonkers-dev/fleet-infra: cluster/flux/apps/observability-rules/platform-alerts.yaml`
- <https://developer.hashicorp.com/vault/docs/configuration/seal>
- <https://github.com/hashicorp/vault/releases>
- <https://openbao.org/docs/configuration/seal/static/>
- <https://openbao.org/docs/release-notes/2-4-0>
- <https://github.com/openbao/openbao/releases>
- `JorisJonkers-dev/fleet-infra: scripts/ops/unseal-vault.sh`
- `JorisJonkers-dev/fleet-infra: cluster/flux/apps/data/vault/release.yaml`
- `JorisJonkers-dev/fleet-infra: inventory/node-contract.lock.yml`
- <https://raw.githubusercontent.com/hashicorp/vault-helm/main/templates/_helpers.tpl>

### ops-2: Rollback depends on every failing dependency; add a fast path that only moves a tag

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| weakness | high | S3, S7, S5 | weakened | high |

**Concerns:** operating.md UC-6 Roll back a Project; diagrams seq-rollback (dispatch deploy via GitHub); conventions.md Retention

UC-6 re-composes at the old fragment, dispatches the Project's deploy workflow through GitHub, dry-runs, signs through Vault and then moves the tag. The operator's main recovery tool therefore needs GitHub Actions, the GitHub App, the compiler, the API server, Vault and ghcr all healthy at the same moment. S3 asks for under 5 minutes, and S7 assumes some of these are down. Yet every render that ever served is already signed by digest, and cosign signatures attach to the digest. Flux will accept a tag moved back to any of those digests without a new signature, and Flux verification can hold several public keys, so older artifacts stay valid after a key rotation. Nothing in the design states that signature artifacts are retained together with the renders they sign.

**Recommendation.** Add an 'emergency rollback' to UC-6: move `render/<p>:prod` back to the last digest that reached Serving, with no compose, sign or dispatch. It needs only ghcr write and is recorded as an event and, when GitHub is up, as a Deployment. Keep the re-compose rollback as the normal path. State in conventions.md Retention that a render's signature and attestations are kept exactly as long as the render, and test that the retention job never removes a `.sig` or referrer of a kept digest. Write a key-rotation runbook: add the new public key to Flux's verify Secret beside the old one, then rotate Transit. Keep the Transit key recoverable through Vault raft snapshots, and test the restore (see ops-4).

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| Flux OCIRepository cosign verification with several keys in one Secret | Documented in current Flux source-controller docs: Flux 'will loop over the public keys' so older artifacts verify while their key is present | Allows key rotation and an old-digest rollback with no re-signing |
| flux suspend plus a pinned digest in the OCIRepository (manual) | Standard Flux CLI | Works with the service down, but adds a second writer of Flux objects, which choices.md rejects; keep it as break-glass only |

**Verification (weakened).** The Flux claim is verified: the OCIRepository docs (v1 API, Flux 2.9) say Flux 'will loop over the public keys' so that 'older artifacts [stay] valid as long as the right key is in the secret'. The retention gap is also real: conventions.md Retention protects tagged renders but says nothing about signatures or referrers. The rest is overstated. S3's state is 'Normal operation', not an outage, so S3 does not assume that dependencies are down. S7 asks only that deploys fail loudly and resume. The design re-composes on purpose. An old render carries the Platform Intent, ClusterState snapshot and compiler version of its day (CONTEXT.md, Render key). Moving the tag back without compose or dry-run can roll back estate-wide inputs, or apply against a cluster that has since changed. It would also go around the settled 'Dry-run gates ... again before each tag move' choice without bringing a new fact. 'Needs only ghcr write' does not buy much under S7: ghcr is part of GitHub, so a GitHub outage often takes ghcr with it. The fast path also needs a credential that can write ghcr tags outside the service, which makes a second writer of the pin. The seq-rollback diagram in specs.py shows only the dispatch and watch steps, not compose or sign, so 'signs through Vault' is an inference from the dry-run-before-every-tag-move rule. It is a reasonable inference. A narrower fix holds up better: keep each signature and referrer for as long as its render, document key rotation with two keys in the verify Secret, and offer a break-glass tag move only behind an operator flag that also sets Pause.

**Corrections.** S3 is defined under normal operation, not under dependency outages. A tag move with no re-compose skips the dry-run that choices.md requires before every tag move. It also restores the old Platform Intent and ClusterState baked into that render. ghcr usually fails together with GitHub, so the fast path does not get around a GitHub outage. Any emergency move must also set Pause, or the next nightly recompose moves the tag forward again.

Sources:

- <https://fluxcd.io/flux/components/source/ocirepositories/>
- `JorisJonkers-dev/estate-kit: docs/design/operating.md`
- `JorisJonkers-dev/estate-kit: docs/diagrams/specs.py`
- `JorisJonkers-dev/estate-kit: CONTEXT.md`
- `JorisJonkers-dev/estate-kit: docs/decisions/choices.md`

### ops-3: 'One replica, no leader election' can run two writers, and restart recovery trusts the log over reality

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| weakness | high | S6, S2 | confirmed | high |

**Concerns:** inside-the-service.md One replica, The rollout core (in-memory coalescing queue); identity-and-access.md Authenticating a deploy job (rollout token)

(a) A Kubernetes Deployment with one replica and the default RollingUpdate strategy rounds maxSurge 25% up to 1 and maxUnavailable down to 0. Every upgrade of the service therefore starts the new pod before the old one stops, and for a while two instances compose and move tags. A pod on an unreachable node is also not deleted automatically, so a partitioned old pod can outlive its replacement. ghcr offers no compare-and-swap on a tag, so the registry cannot stop the second writer. (b) The page says 'the event log says where each rollout stood', but appending an event and moving a tag are not atomic. A crash after MoveTag and before the 'tag moved' event leaves a log that says Signed while ghcr says Applying. The coalescing queue is in memory and is lost on restart. If the key that signs rollout tokens is generated at startup, every waiting deploy job loses its reconnect. The design does not say whether a rollout found unfinished at startup resumes or fails, and S6 requires one of the two, done cleanly.

**Recommendation.** Run the service either as a StatefulSet of one, which gives the 'at most one' guarantee, or as a Deployment with strategy Recreate. Also hold a coordination Lease through client-go leaderelection even at one replica, and check it immediately before Sign and MoveTag. Let the service recover the way the host applier does: at startup, for each rollout that has not finished, read the observed state (the prod tag digest in ghcr, Flux and Flagger status) and either drive the rollout forward from there or end it with an explicit 'Abandoned' event and fail the job cleanly. The log is the journal; ghcr and the cluster are the truth. Re-enqueue unfinished rollouts from the log. Persist the rollout-token signing key in a Secret, or let the job re-request its GitHub OIDC token on reconnect. Add 'service restarts mid-rollout' and 'two instances during an upgrade' failure sequences to releasing.md; both are listed as missing in redesign-practices.md gap 5.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| StatefulSet with replicas: 1 | Core Kubernetes; the at-most-one guarantee is documented | No surge on upgrade; failover after a node loss waits until the Node object is deleted, which is acceptable for a deploy path |
| client-go leaderelection with a coordination.k8s.io Lease | Core client-go, used by every controller | About 30 lines; not true fencing, so the check must sit right before the tag move |
| controller-runtime manager (leader election built in) | kubernetes-sigs, actively released | A larger dependency; worth it only if the service grows reconcilers |

**Verification (confirmed).** inside-the-service.md 'One replica' says 'no leader election' and 'the event log says where each rollout stood'. It does not say whether an unfinished rollout resumes or fails, and S6 requires one of the two. A Deployment with one replica and default RollingUpdate rounds maxSurge up to 1 and maxUnavailable down to 0, so every upgrade briefly runs two pods. A pod on an unreachable node is not confirmed deleted, so a partitioned old pod can outlive its replacement. ghcr has no conditional tag write. Appending an event and moving a tag are separate operations, so the log can lag what ghcr holds. The host applier already recovers from observed state (hosts.md 'When an applier crashes mid-rollout'), and the service should do the same. The recommendation's core is cheap: Recreate or a Lease, a check right before MoveTag, and reconcile from observed state at startup. It fits the one-maintainer budget.

**Corrections.** redesign-practices.md gap 5 lists only 'a service restart mid-rollout', not 'two instances during an upgrade'. The design never names the workload kind, so the RollingUpdate surge is conditional on it being a Deployment. Do not combine a StatefulSet with a Lease. After a node loss a StatefulSet replacement waits for a manual force-delete or the Node object's deletion, which is manual work for one maintainer. strategy: Recreate plus a coordination Lease checked right before Sign and MoveTag gives automatic failover. The rollout-token key point is conditional, since identity-and-access.md does not say where that key lives.

Sources:

- <https://kubernetes.io/docs/concepts/workloads/controllers/deployment/>
- <https://kubernetes.io/docs/tasks/run-application/force-delete-stateful-set-pod/>
- `JorisJonkers-dev/estate-kit: docs/research/redesign-practices.md`

### ops-4: S8 has no restore path: the k3s datastore is a single SQLite file, and the backups share its node

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| missing | high | S8, S6, S7 | weakened | high |

**Concerns:** hosts.md Known limit: one control plane; choices.md Control plane, Pause and rollback state ('the cluster is the record of what runs'); where-state-lives.md Every fact

The design accepts a single control plane but has no backup or restore of the API server's datastore. The cluster runs k3s on kine/SQLite (fleet-infra docs/runbooks/apiserver-watch-cache-wedge.md). For SQLite, k3s has no snapshot command: a backup is a copy of /var/lib/rancher/k3s/server/db/ plus the server token, and 'if you do not use the same token value when restoring, the snapshot will be unusable'. Pause and RolledBack live only in a cluster object that the service writes, which is not in git. A rebuild through Flux bootstrap therefore brings back every Project as Active at latest, and the next nightly recompose or Platform Intent change silently undoes an emergency rollback or pause. On top of that, the observability-backups PVC (pg_dumpall, the Vault raft snapshots every 6 h) is local-path and pinned to frankfurt-contabo-1, the control-plane node. Losing that one node loses the API server, the Vault snapshots and the Postgres dumps at once, leaving only that node's daily off-cluster copy. That is roughly a 24 h recovery point for Vault, the signing key included.

**Recommendation.** Write a 'Recover the control plane' page and record it. Convert the server to embedded etcd by restarting k3s with --cluster-init. That gives scheduled snapshots, every 12 h by default, with built-in S3 upload, and a documented `k3s server --cluster-reset --cluster-reset-restore-path` restore. It is also the prerequisite for three servers later, and it likely ends the kine compaction wedge that the runbook describes. Ship the etcd snapshots, the k3s token and the Vault raft snapshots to object storage off the node and off the provider. Make the service fail safe on missing state: an admitted Project with no cluster object is treated as Paused until an operator confirms, never as Active. Prove the whole path with a scheduled restore drill, as verify-backup-restore.sh already does for Postgres.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| k3s embedded etcd with etcd-snapshot to S3 | k3s v1.37.1+k3s1 released 2026-09-30; snapshots and S3 replication are documented and on by default once etcd is in use | etcd is more sensitive to fsync latency on a VPS disk than SQLite; in return it brings first-class snapshot and restore commands |
| Keep SQLite; back up the db directory and token by a NixOS timer (sqlite3 .backup) to off-site storage | Documented by k3s as the SQLite backup method | Least change; a hand-made restore; no path to HA |
| Velero for API objects | CNCF-adjacent, actively released | Another operator to run; it overlaps with a datastore snapshot on one cluster |

**Verification (weakened).** The gap is real. hosts.md 'Known limit: one control plane' has no datastore backup or restore. The cluster runs kine on SQLite (apiserver-watch-cache-wedge.md). The k3s docs confirm the SQLite backup is a copy of server/db plus the token, and that a different token makes the backup 'unusable'. backup-coverage.md confirms that pg_dumpall and the 6-hourly Vault raft snapshots sit on a local-path PVC pinned to frankfurt-contabo-1, copied off-cluster daily, which gives roughly a 24 h recovery point if that node is lost. The k3s facts check out: v1.37.1+k3s1 was released on 30 Sep 2026, '--cluster-init' converts an SQLite server to etcd, and snapshots run every 12 h with 5 kept. Several claims are overstated. A rebuild does not bring every Project back 'Active at latest'. The prod tags live in ghcr, and where-state-lives.md calls ghcr the record, so Flux re-pulls the rolled-back digests. What is lost is the Pause and Rollback cluster object, and with it the guard against the next recompose. fleet-infra already has a documented rebuild-from-git path (docs/runbooks/full-cluster-rebuild.md). Under estate-kit, that path plus the ghcr tags restores most state, so 'no restore path' is too strong. What the estate-kit pages lack is a reference to it and to the Pause objects. S3 replication is not on by default: only local snapshots are, and S3 needs flags or a config Secret. 'Likely ends the kine compaction wedge' is speculation. The conversion carries some risk for one maintainer: etcd is sensitive to fsync latency on a VPS disk, and the conversion is one-way in practice.

**Corrections.** The prod tags survive in ghcr, so a rebuild keeps rolled-back digests serving. Only the Pause and Rollback flags in the per-Project cluster object are lost. fleet-infra already documents a full-cluster rebuild from git. k3s etcd snapshots are on by default, but S3 upload is not. That etcd fixes the kine compaction wedge is unproven. The cheapest step that fits one maintainer is a NixOS timer that copies the SQLite db and the token off the node and off the provider, together with the Vault snapshots. The service should also treat a missing per-Project object as Paused.

Sources:

- <https://docs.k3s.io/datastore/backup-restore>
- <https://docs.k3s.io/datastore/ha-embedded>
- <https://docs.k3s.io/cli/etcd-snapshot>
- <https://github.com/k3s-io/k3s/releases>
- `JorisJonkers-dev/fleet-infra: docs/runbooks/apiserver-watch-cache-wedge.md`
- `JorisJonkers-dev/fleet-infra: docs/runbooks/backup-coverage.md`
- `JorisJonkers-dev/fleet-infra: cluster/bootstrap/data-services-playbook.md`
- `JorisJonkers-dev/fleet-infra: docs/runbooks/full-cluster-rebuild.md`

### ops-5: 'Serving is unaffected' when ghcr is down holds only until a pod moves, and host rollouts move them

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| risk | medium | S7, S9, S8 | weakened | medium |

**Concerns:** overview.md Risks; hosts.md A host rollout (eviction), When the cluster is down; choices.md Render store (rejected in-cluster zot)

Project images and renders both come from ghcr. During a ghcr or GitHub outage, any pod that is rescheduled, by a host rollout's eviction, a node failure, an OOM or a Flagger canary, needs an image pull on its new node. If the image is not cached there, the pod stays in ImagePullBackOff. The host applier drains a node without checking that the registry can be reached, so under S7 the design's own rollout turns a deploy outage into a serving outage. The rejection of an in-cluster zot rested on 'a rebuilt cluster can still pull its renders'. A new fact changes that cost: k3s embeds a Spegel peer-to-peer mirror, which has been GA since the v1.29.12, v1.30.8 and v1.31.4 releases of December 2024. Nodes then pull images from each other with no registry to store or operate.

**Recommendation.** Enable the k3s embedded registry mirror (`embedded-registry: true` on the server, plus `mirrors: {"ghcr.io": {}}` in registries.yaml on each node) and keep ghcr as the one store. The design then stays 'ghcr is the store and the cache'. Add a precondition to the host applier: before taking the Lease, check that ghcr and the binary cache answer, and halt the rollout (not the node) if they do not. Add a 'ghcr unavailable' failure sequence: deploys fail with a named code, the host rollout pauses, and serving is unaffected.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| k3s embedded registry mirror (Spegel) | GA in k3s since December 2024; documented in current k3s docs; off by default | Stateless with nothing to back up; needs TCP 5001 and 6443 between nodes; covers only images some node already has, and does not share `latest` tags |
| Standalone Spegel | Open-source DaemonSet, actively developed | Same idea, but another chart to keep updated when k3s already embeds it |
| zot pull-through cache | CNCF Sandbox project | Holds every image, but is a stateful store to back up, which is what choices.md rejected |

**Verification (weakened).** The facts are correct. The k3s docs state that the embedded Spegel mirror was experimental from January 2024 and went GA in v1.29.12, v1.30.8 and v1.31.4+k3s1. It is off by default and needs TCP 5001 and 6443 between nodes. The risk is overstated, though. The host applier finds a new rollout by polling `host/<node>:prod` in ghcr, and it fetches the closure from the binary cache before it drains ('Each applier fetches its closure first, which disrupts nothing'). A rollout therefore does not start while ghcr or the cache is down. Only a rollout already in progress when ghcr fails is exposed, and the proposed preflight is mostly redundant. Spegel helps only when a peer node of the same architecture already holds the image. The estate mixes an amd64 VPS with arm64 Pis across two sites over Tailscale, so the drained node is often the only holder. The k3s docs also say the mirror 'assumes equal privilege and trust among all cluster members', which matters when a public VPS and home Pis share one mirror. Renders are pulled by Flux source-controller, not containerd, so Spegel does not cover them. Severity medium is too high: the scenario needs a GitHub outage and a host rollout at the same moment.

**Corrections.** A host rollout already depends on ghcr for the tag poll and on the cache for the closure fetch before any drain, so a ghcr outage mostly prevents rollouts rather than breaking them halfway. Spegel covers only images that a node of the same architecture already caches, does not cover Flux render artifacts, and comes with a flat trust model across sites. It is a cheap optional hardening, not a needed fix.

Sources:

- <https://docs.k3s.io/installation/registry-mirror>
- `JorisJonkers-dev/estate-kit: docs/design/hosts.md`

### ops-6: The SLOs cannot be measured, and the cutover drops the alerts the old stack had

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| best-practice-gap | medium | S5, S7, S2, S12 | confirmed | high |

**Concerns:** conventions.md Service levels, Telemetry; choices.md Telemetry (traces and logs, 'logs and metrics only' rejected)

The design names three objectives (deploy p95 under 10 minutes, 99% availability, drift within 24 h) but emits no metrics, has no alert rules, names no owner of the error budget and has no runbook. Traces in Tempo and logs in Loki cannot page anyone. The fleet already runs Prometheus with burn-rate alerts (ServiceErrorBudgetFastBurn/SlowBurn), VaultSealed, BackupStale/BackupNeverSucceeded, FluxResourceNotReady and Alertmanager to Discord. deploy-kit's estate-delivery spec also shipped Prometheus rules for held releases, failed analysis, failed migration and Down Jobs, signature-verification failure and a stale snapshot. estate-kit does not mention any of these, so the cutover risks removing exactly the signals a returning maintainer (S5) depends on. OpenTelemetry Go metrics have been Stable for a while; only logs are at release candidate.

**Recommendation.** Amend the Telemetry record: OTel metrics, exported for Prometheus scraping, with a deploy-duration histogram, rollout outcomes by terminal state and code, dependency errors by port, and the age of the oldest unfinished rollout. Write the SLOs as recording rules plus burn-rate alerts in the existing fleet pattern. Port the deploy-kit delivery alerts as a named list. Add a 'rollout stuck past N minutes' alert and a 'drift check did not run in 26 h' alert. Give every alert a runbook link, and add a lint that fails on an alert without one: rule plus check, as AGENTS.md asks. Keep it to six to eight alerts, each one something the maintainer will act on.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| OpenTelemetry Go metrics SDK with Prometheus exporter | Traces and Metrics Stable, Logs release candidate (opentelemetry.io Go page) | One SDK for traces and metrics; scraped by the existing metrics-stack |
| Tempo metrics-generator (span metrics) | Optional Tempo component, writes over Prometheus remote write | RED metrics without code, but SLIs then depend on trace sampling and a Tempo setting; prefer explicit metrics |
| Sloth or Pyrra SLO generators | Open source, moderately active | Generate burn-rate rules from an SLO spec; probably overkill for three SLOs |

**Verification (confirmed).** A search of estate-kit's docs finds no metrics, alert rules or Alertmanager anywhere in the design. conventions.md sets three service levels but names nothing that measures them. The fleet has a working pattern: platform-alerts.yaml holds ServiceErrorBudgetFastBurn and SlowBurn, VaultSealed, BackupStale, FluxResourceNotReady and KubeJobFailed. The OpenTelemetry Go page lists Traces and Metrics as Stable and Logs as Release candidate. Choosing traces did not rule out metrics. The 'logs and metrics only' option was rejected because it lacked traces. A short list of six to eight actionable alerts with runbook links fits one maintainer.

**Corrections.** The delivery alert rules (held release, failed analysis, failed migration and Down Jobs, signature verification, stale snapshot) were specified as Assets of the observability project's metrics stack in the estate repo (estate#4), not as part of deploy-kit. The cutover does not delete the rule files themselves. What it removes is the metrics they read from delivery and the Release Gate, plus estate-dashboard's alert inbox and silences, which estate-kit's UI does not carry. lesson-candidates.md also records that #373 cuts alertClass. The rules should be ported against the new service's metric names.

Sources:

- <https://opentelemetry.io/docs/languages/go/>
- <https://grafana.com/docs/tempo/latest/metrics-from-traces/>
- `JorisJonkers-dev/deploy-kit: docs/specs/estate-delivery.md`
- `JorisJonkers-dev/fleet-infra: cluster/flux/apps/observability-rules/platform-alerts.yaml`

### ops-7: Put the event log on the shared Postgres as a journal, not 'its own Postgres' with a growing set of upcasters

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| alternative | medium | S6, S5, S4, S15 | weakened | medium |

**Concerns:** inside-the-service.md The event log; where-state-lives.md Inside the cluster ('its own Postgres'); conventions.md Contracts and their evolution (Events); choices.md Rollout log, Event evolution

'Its own Postgres' adds a second database instance to back up, upgrade and restore, and the fleet already has one with a daily pg_dumpall, a 30-day archive, PostgresDown alerts and a restore check that has been run (verify-backup-restore.sh). That check exists because a dump was once silently failing. The event log's real jobs are stream resume and the UI's history: S15 is also answered by GitHub Deployments. Recovery should not depend on it (ops-3). Upcasters kept for 400 days are code that grows with every event change, for an internal log with one reader. A new fact also confirms rejecting the Rollout custom resource: this cluster's kine/SQLite datastore already wedges on compaction, so streaming events through the API server would make things worse.

**Recommendation.** Keep the append-only table, but in a database on the existing shared Postgres server, covered by the existing backup CronJob and restore check, with the service's database added to the drill. State the recovery point (24 h) and why it is acceptable: the log is a journal, and observed state rebuilds rollouts. Close redesign-practices.md item 28 with forward-only schema migrations, embedded and run at startup (goose or golang-migrate). Limit upcasting to the current and previous event version. When a third version would appear, run a one-off SQL migration over the rows and record it. Make the deploy path fail loudly with a named code when Postgres is down, and add that to S7's list.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| Existing shared Postgres plus pg_dumpall and verify-backup-restore.sh | Already in production in fleet-infra | No new component; the shared server becomes a deploy-path dependency, as auth-api already is for the UI |
| CloudNativePG with WAL archiving | CloudNativePG v1.30.1 released 2026-09-23; CNCF project | Point-in-time recovery and declarative backups, but a new operator to run for one small table; not worth it for this log |
| Embedded SQLite plus Litestream | Litestream v0.5.17 released 2026-08-31; the 0.5 line had a bumpy migration in 2025 | Fits one replica, continuous backup to S3; but node-bound local-path storage on a Pi and one more tool |

**Verification (weakened).** The core claim likely misreads the design. where-state-lives.md says 'its own Postgres', and specs.py labels the store 'Postgres 17', the same version as the shared platform Postgres. The estate's convention, which estate-dashboard already follows (estate-delivery.md: 'its own project database on platform-postgres'), is a database of its own on the shared server, not a second instance. The useful part of the finding is to make that explicit, add the database to the existing pg_dumpall job and to verify-backup-restore.sh, and close item 28 with forward-only migrations. The upcasting recommendation ('run a one-off SQL migration over the rows' when a third version appears) reopens the settled Event evolution choice, which rejected 'Rewrite events in place' to keep history immutable, and it brings no new fact. The kine compaction wedge only supports the existing rejection of a Rollout custom resource and changes nothing. The 24 h recovery point is acceptable only if the service rebuilds rollouts from observed state (ops-3). Version checks: CloudNativePG v1.30.1 (23 Sep 2026) and Litestream v0.5.17 (31 Aug 2026) are both current. Neither is needed here, and the finding says so.

**Corrections.** The design does not say the event log gets a separate Postgres instance. 'Its own Postgres' most likely means its own database on platform-postgres, as estate-dashboard has today, so the design should state that rather than change it. Rewriting events on a third version contradicts the settled Event evolution record without a new fact. Limiting upcasters to the current and previous version is acceptable only if older events stay readable, for example through a frozen archive format.

Sources:

- `JorisJonkers-dev/fleet-infra: docs/runbooks/backup-coverage.md`
- `JorisJonkers-dev/fleet-infra: docs/runbooks/apiserver-watch-cache-wedge.md`
- <https://github.com/cloudnative-pg/cloudnative-pg/releases>
- <https://github.com/benbjohnson/litestream/releases>
- <https://mtlynch.io/notes/hold-off-on-litestream-0.5.0/>
- `JorisJonkers-dev/estate-kit: docs/diagrams/specs.py`
- `JorisJonkers-dev/deploy-kit: docs/specs/estate-delivery.md`

### ops-8: The components can destroy data on rollback, prune or a Vault restore, and the guards from deploy-kit are not carried over

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| risk | medium | S3, S2, S7, S13 | weakened | medium |

**Concerns:** mail-and-components.md Components (migration-runner 'up and down per revision'), States of a Mailbox (Provisioned to Removed 'dropped from intent'), Inside the mail provisioner (RemoveAccount); operating.md UC-6; CONTEXT.md

(a) Migrations: deploy-kit's estate-delivery spec says a Rollback keeps 'the schema at its newest', is offered only to a release proven against the current schema (the Migration Proof), and runs Down only under the Release Gate's guard. estate-kit's UC-6 says only 're-composes at that fragment', mail-and-components.md says 'up and down per revision', and CONTEXT.md has no Rollback, Pause or Migration Proof term. Byte parity keeps the renders, but not the rule an agent or a returning maintainer must follow. (b) Mailboxes: a Mailbox custom resource that leaves the render (a renamed local part, a removed unit, a Project dropped from admission, or a botched cluster rebuild followed by a Flux prune) drives RemoveAccount on Stalwart. That is a destructive action with no grace period. (c) Generated keys: restoring Vault from a raft snapshot that is up to 6 h old, or 24 h after ops-4's node loss, drops keys generated since. An idempotent 'create if absent' secret job then mints new ones that no longer match the database roles or the Stalwart passwords already in use.

**Recommendation.** Bring Rollback, Pause, Migration Proof and Down into CONTEXT.md and UC-6 as written rules with their checks. Refuse a rollback across a schema change unless it is proven, and have the migration runner take a pre-`up` dump of the Project database to object storage. Give external deletions a Retain policy, like a PersistentVolume's reclaim policy: a Mailbox dropped from intent is disabled and its account kept for a stated period, then purged only by an explicit operator action, and Mailbox objects carry `kustomize.toolkit.fluxcd.io/prune: disabled` or a finalizer that only disables. Write a 'Vault restored' runbook that runs the secret job, then pushes each regenerated key outward (database role passwords, Stalwart), and test it once.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| Flux per-object prune opt-out (kustomize.toolkit.fluxcd.io/prune: disabled) | Documented in current Flux kustomize-controller docs | Simple; orphaned objects then need explicit cleanup |
| Expand/contract migrations only (no automatic Down) | Already the stated rule in research/summary.md item 13 | Safer rollbacks; schema clean-up waits one release |

**Verification (weakened).** Part (b) is real and new. The Mailbox state machine in specs.py has 'Provisioned to Removed: dropped from intent', and the provisioner port has RemoveAccount. The current stalwart-provisioner (workspace/tools/stalwart-provisioner) has no account deletion; it even leaves pre-existing accounts unmanaged. estate-kit therefore introduces a new destructive path, reachable by renaming a local part or by a Flux prune. A disable-then-retain policy is cheap and fits S2 and S13. Part (c) is plausible: a Vault restore loses keys generated since the snapshot, and the secret job then mints new ones that do not match. That makes it worth one runbook. Part (a) misreads CONTEXT.md. Its preamble says deploy-kit's terms 'keep their meaning until this file says otherwise'. Rollback (schema newest, proven releases only, pre-rollback backup, pauses its Project), Pause and Migration Proof are written in deploy-kit's CONTEXT.md (estate-delivery.md, item 293), so they are inherited, not lost. 'up and down per revision' in mail-and-components.md describes the runner's two verbs, the same contract as liquibase-runner, not a rule to run Down on rollback. UC-6 should still cite the inherited Rollback rule and add its check, but this is a documentation gap, not a dropped guard.

**Corrections.** CONTEXT.md explicitly inherits deploy-kit's Rollback, Pause and Migration Proof terms, so the rules are not absent, only not restated in UC-6. The strongest part of this finding is the Mailbox deletion on 'dropped from intent'. The current provisioner never deletes accounts, so estate-kit adds this behaviour, and it should lead the finding.

Sources:

- `JorisJonkers-dev/deploy-kit: docs/specs/estate-delivery.md`
- `JorisJonkers-dev/liquibase-runner: README.md`
- <https://fluxcd.io/flux/components/kustomize/kustomizations/>
- `JorisJonkers-dev/fleet-infra: cluster/bootstrap/data-services-playbook.md`
- `JorisJonkers-dev/estate-kit: CONTEXT.md`
- `JorisJonkers-dev/workspace: tools/stalwart-provisioner/bin/stalwart-provisioner`
- `JorisJonkers-dev/fleet-infra: cluster/flux/apps/mail/stalwart/provisioner-manifest-configmap.yaml`

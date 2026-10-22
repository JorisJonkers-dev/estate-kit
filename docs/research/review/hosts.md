# Review: hosts and nixos

Part of the [design review](README.md). Each finding was checked by a second
reviewer that tried to refute it; its verdict and corrections follow the finding.

## Verdict

The host design gets the structure right: it splits work by failure domain, builds closures in CI into an off-cluster cache, fetches before switching, lets the window gate only when a reboot starts, and orders nodes by version skew. It is weakest on the two scenarios that matter most. For S8, the control-plane node also holds the SQLite datastore, Vault and every local-path volume, and no restore path is written down. For S9, "boots its previous generation" has no mechanism on four of the seven nodes. A k3s minor bump on the control plane cannot be undone by a generation rollback at all, and the state machine drains a node and holds the Lease while it waits hours for a window. The bespoke applier also does the cluster-side work (lock, drain, window) on the host. That goes against prior-art takeaways 3 and 4, and it needs a per-node API credential that RBAC cannot scope. Handing that half to kured and keeping a small host-side stager would cut the bespoke code and the credential problem together. comin, Clan, NixOps4 and Talos should not replace it today. deploy-rs (1.0.0, 2026-10-19) and nixos-anywhere should become the break-glass and rebuild paths, so neither has to be built.

## What the design gets right

- Splitting the appliers by failure domain is sound: Flux handles Projects in the cluster, and a host-side agent handles the nodes beneath it and still works when the cluster is down (hosts.md, One model, two appliers).
- The rollout fetches every closure first and serialises only the switch or reboot. That makes the harmless phase free and the disruptive phase short (hosts.md, A host rollout; prior-art takeaway 2).
- Closures are built in CI and kept in an off-cluster binary cache, so a node can be fixed or reinstalled while the cluster is down. That is the precondition for any S8 path.
- The maintenance window gates only when a reboot starts, and a reboot happens only when the booted and new generations differ. This matches the semantics of kured, system-upgrade-controller and system.autoUpgrade.
- Node order is derived from the change, and a check refuses targets that break the Kubernetes version skew policy. This is better than the fixed order hard-coded in today's nix-config scripts/deploy/deploy-all.sh.
- Host data is typed, and hand-written modules consume it. No Nix is generated from string templates, so logic stays reviewable Nix.
- The applier reconciles one idempotent step at a time, resumes after a crash, and has one fake per port. This is the shape the Sieve and Anvil findings ask for (prior-art takeaway 8).
- The design rejects three servers for now. A control-plane quorum stretched across Frankfurt and Enschede over the WAN, or etcd on Pi USB storage, would be less reliable than one server. The estate's own legacy README and the k3s docs both warn against it.

## Findings

### hosts-1: Losing frankfurt-contabo-1 loses the datastore, Vault and the signing path together, and no restore path is written down

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| risk | high | S8, S7, S6 | weakened | high |

**Concerns:** design/hosts.md, sections 'Known limit: one control plane' and 'When the cluster is down'; decisions/choices.md row 'Control plane'

S8 requires 'a documented path restores the API server'. The hosts page covers only a planned API pause during the control plane's own window. On frankfurt-contabo-1, k3s runs without --cluster-init, so the datastore is kine/SQLite (the estate's own fleet-infra runbook apiserver-watch-cache-wedge.md says so). Every PersistentVolume is local-path on that node's system disk (inventory/nodes/frankfurt-contabo-1.yml). Vault runs on the same node's storage with Raft and manual unseal (legacy personal-stack README). Losing the node therefore takes, in one event: the API server, all cluster state, the k3s server token that decrypts it, Vault (and with it the only cosign key that can move a host tag), and the service. Host tags cannot move again until Vault is restored. Per the k3s docs, restoring onto a new host needs the datastore copy or snapshot and the original server token, and a snapshot is unusable without that token. None of these backups appears in the design.

**Recommendation.** Keep one server, and make its loss a rehearsed procedure rather than a known limit. (1) Choose the datastore backup explicitly. Either restart k3s with --cluster-init, which converts SQLite to single-member embedded etcd per the k3s docs, and use the scheduled --etcd-snapshot plus --etcd-s3 to an off-site bucket. Or keep SQLite and run a systemd timer that copies /var/lib/rancher/k3s/server/db and the token off-site. (2) Ship Vault Raft snapshots and the unseal material's recovery procedure to the same off-site store; that part may belong to another area, but the host rollout depends on it. (3) Write the runbook as: reinstall with nixos-anywhere from the closure already in the off-cluster cache, restore the token and datastore, restore Vault, then let agents reconnect. (4) Give the rule its check. Add a scheduled NixOS VM test that boots the control-plane class, restores the latest snapshot with 'k3s server --cluster-reset --cluster-reset-restore-path', and fails if the API does not come up. Revisit HA only when a second Frankfurt-site server exists. Embedded etcd across the WAN or on Pi USB storage is worse than one server.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| k3s HA with embedded etcd (three servers) | k3s v1.37.1+k3s1 released 2026-09-30; the docs require three or more servers and warn about etcd on slow Pi storage | Real API availability, but it needs three servers within low latency of each other. The estate has one Frankfurt VPS, and the Enschede nodes are Pis or reached over the Tailscale WAN. That means more nodes to patch, and quorum loss replaces single-node loss as the failure mode. |
| Single server with --cluster-init (one-member etcd) and --etcd-s3 snapshots | Documented k3s feature; SQLite-to-etcd conversion by restarting with --cluster-init | Built-in scheduled off-site snapshots and a documented cluster-reset restore. etcd uses more memory and I/O than SQLite. Recommended. |
| Keep SQLite plus a backup timer | Documented: back up server/db and the token | Simplest, but the timer, consistency of the copy, and retention are bespoke. Copy with sqlite3 .backup, not cp. |
| Talos Linux for the control plane or workers | Active, v1.14.4 released 2026-10-16 | An immutable OS with an API-driven upgrade, but Talos nodes join only a Talos-bootstrapped control plane (inferred from Talos's scaling-up docs; not confirmed by a source). Adopting it means replacing k3s, and it cannot host the host-native Samba, Tailscale subnet router, btrfs backups and ROCm services the Enschede nodes run. Rejected. |

**Verification (weakened).** The core gap is real. design/hosts.md 'Known limit: one control plane' and 'When the cluster is down' cover only a planned API pause and break-glass, so S8's 'a documented path restores the API server' has nothing behind it in the design. The datastore facts check out: the fleet-infra runbook apiserver-watch-cache-wedge.md says 'single-node on kine/SQLite', and nix-config inventory/nodes/frankfurt-contabo-1.yml says every PV is local-path on the system disk. The k3s docs confirm the token requirement ('If you do not use the same token value when restoring, the snapshot will be unusable') and the --cluster-init conversion (ha-embedded page). The finding overstates the risk, though. It treats 'no restore path written down' as true of the estate, but it is only true of the estate-kit design. The estate already runs a vault-raft-snapshot CronJob every 6 hours, with 14-day retention, onto the observability-backups PVC. That PVC is pinned to frankfurt-contabo-1 because that node 'has daily off-cluster copies' (fleet-infra docs/runbooks/backup-coverage.md, cluster/bootstrap/data-services-playbook.md). There is also a Vault raft restore playbook (cluster/bootstrap/legacy-backup-restore-playbook.md), so recommendation (2) mostly exists already; the design should cite and own it, not rebuild it. The node-level off-cluster copy probably already captures server/db and the token, but a raw copy of a live SQLite file may not be consistent, so a consistent datastore backup is still the real gap. On cost for one maintainer: converting production to one-member etcd is a cluster change with more memory and I/O for a one-node gain. A scheduled VM restore test is real recurring upkeep. The cheapest fix that meets S8 is an sqlite3 .backup plus a token copy into the existing off-cluster path, and a written runbook.

**Corrections.** Vault is not unprotected. It is snapshotted every 6 h, with off-cluster copies via the Frankfurt node's daily backup, and a restore playbook exists in fleet-infra. The gap is that the estate-kit design neither references those backups nor names the k3s datastore and token backup. The inventory path is nix-config/inventory/nodes/frankfurt-contabo-1.yml. The Talos claim is an unsupported inference: the scaling-up page does not say Talos nodes can join only a Talos control plane. It does not affect the verdict, because Talos is rejected anyway.

Sources:

- <https://docs.k3s.io/datastore/backup-restore>
- <https://docs.k3s.io/cli/etcd-snapshot>
- <https://docs.k3s.io/datastore/ha-embedded>
- <https://github.com/k3s-io/k3s/releases>
- <https://github.com/nix-community/nixos-anywhere>
- <https://docs.siderolabs.com/talos/v1.13/deploy-and-manage-workloads/scaling-up>
- <https://github.com/siderolabs/talos/releases>

### hosts-2: 'Boots its previous generation' has no mechanism on the bootloaders four of the seven nodes use

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| weakness | high | S9, S8 | weakened | high |

**Concerns:** design/hosts.md, section 'States of the host applier' (HealthCheck -> RolledBack) and 'A host rollout'; diagrams/specs.py state-host-applier

The design assumes an unhealthy node rolls back. The applier can do that only if the new generation boots far enough to run the applier with the network up. The fleet is headless (nix-config flake.nix: 'None can be recovered at a console'). The Pis boot through U-Boot and generic-extlinux-compatible, and frankfurt-contabo-1 uses GRUB in BIOS mode. nixpkgs has automatic boot assessment (boot.loader.systemd-boot.bootCounting) only for systemd-boot. On the four extlinux and GRUB nodes, a kernel, initrd or network regression that hangs boot leaves the new generation as the default entry, and nothing local reverts it. The Pis have already lost their NIC in production (bcmgenet TX wedge, 2026-10-19). Today deploy-rs magic rollback with confirmTimeout=180 is the safety net, and the design replaces it without naming an equivalent. The reboot-need test ('kernel or initrd differs') also misses kernel-modules, kernel params and the generation device tree the Pis use.

**Recommendation.** Make one rule an invariant with a check: the new generation never becomes the boot default until it has proved healthy. (a) For a change without a reboot, run 'switch-to-configuration test' (the bootloader stays untouched), then a local health check: k3s Ready, tailscaled up, the gateway reachable, the applier able to reach ghcr. Only then run 'switch-to-configuration boot'. If the check fails, run the old generation's test and leave the default unchanged. This is deploy-rs magic rollback done locally, as comin's testing branches also do. (b) For a reboot-requiring change, boot the new entry once: bootCounting with health ordered before boot-complete.target on the systemd-boot nodes; GRUB default='saved' with grub-reboot on Contabo; on the Pis, the hardware watchdog (systemd.watchdog.runtimeTime) plus Raspberry Pi firmware tryboot, or else document SD-image reflash as the accepted recovery. (c) Compare initrd, kernel, kernel-modules, kernel-params and dtbs, as system.autoUpgrade does for the first three. (d) Set virtualisation.useBootLoader = true (useEFIBoot where relevant) in each class's VM test, so the bootloader path itself is exercised. By default VM tests boot the kernel directly.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| deploy-rs magic rollback | v1.0.0 released 2026-10-19, the first versioned release, now on crates.io; actively maintained | Proven confirm-or-revert, but push-driven: it needs the operator's machine to confirm. Copy the semantics, not the tool, into the pull path. |
| systemd-boot automatic boot assessment (bootCounting) | Present in nixpkgs nixos-unstable after an earlier merge and revert | Fully local and standard, but EFI and systemd-boot only. It does not cover the Pis or the BIOS VPS. |
| Switch every node to systemd-boot | Contabo firmware is BIOS-only; the Pis use U-Boot | Not possible for four of the seven nodes without changing hardware or provider. |

**Verification (weakened).** The bootloader facts are right. The three Pis use generic-extlinux-compatible (nix-config nix/hosts/enschede-pi-*/default.nix), and frankfurt-contabo-1 uses GRUB on SeaBIOS (nix/hosts/frankfurt-contabo-1/default.nix and disko.nix). nixpkgs nixos-unstable has boot.loader.systemd-boot.bootCounting only for systemd-boot, and system.autoUpgrade compares initrd, kernel and kernel-modules. The real new risk is unattended reboots with no boot assessment on 4 nodes. Three claims are overstated. First, deploy-rs magic rollback never covered reboots: it confirms an activation, which is the no-reboot path. The design does cover that path with HealthCheck -> RolledBack in state-host-applier, so 'replaces it without naming an equivalent' is true only for the reboot path, which deploy-rs never protected either. Second, the bcmgenet TX wedge (raspberry-pi-recovery.nix) is a runtime driver hang handled by a watchdog script, not a boot regression, so it is weak evidence here. Third, the Pi recommendation is heavy for one maintainer. RPi tryboot needs autoboot.txt and A/B boot partitions alongside U-Boot and extlinux. A hardware watchdog only catches kernel hangs, not a node that boots without network. Documenting SD-image or USB reflash as the accepted recovery is the realistic choice. The parts that hold and are cheap: 'test' then health then 'boot' for live switches, GRUB default='saved' with grub-reboot on Contabo (the option exists in grub.nix), the wider reboot-need comparison, and useBootLoader in VM tests.

**Corrections.** Only 6 of the 7 nodes are active (enschede-rx7900xtx-1 is planned and never installed), so the bootloader gap covers 4 of 6 active nodes. Magic rollback is not a reboot safety net today, and the design already has HealthCheck -> RolledBack for the live-switch path. comin's testing branches use 'switch-to-configuration test' as a manual staging step, not an automatic health-then-promote loop.

Sources:

- <https://raw.githubusercontent.com/NixOS/nixpkgs/nixos-unstable/nixos/modules/system/boot/loader/systemd-boot/systemd-boot.nix>
- <https://systemd.io/AUTOMATIC_BOOT_ASSESSMENT/>
- <https://raw.githubusercontent.com/NixOS/nixpkgs/nixos-unstable/nixos/modules/tasks/auto-upgrade.nix>
- <https://raw.githubusercontent.com/NixOS/nixpkgs/nixos-unstable/nixos/modules/virtualisation/qemu-vm.nix>
- <https://github.com/serokell/deploy-rs/releases/tag/v1.0.0>
- <https://raw.githubusercontent.com/nlewo/comin/main/docs/howtos.md>
- <https://raw.githubusercontent.com/NixOS/nixpkgs/nixos-unstable/nixos/modules/system/boot/loader/grub/grub.nix>

### hosts-3: A k3s minor bump on the control plane cannot be undone by a generation rollback

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| risk | high | S9, S8, S4 | confirmed | high |

**Concerns:** design/hosts.md, section 'Order of nodes' (k3s bumps go control plane first) and 'States of the host applier'

For a k3s change, the derived order switches the control plane first, and S9 promises the node 'rolls back to its last generation'. Per the k3s docs, a minor-version rollback needs a datastore snapshot taken on the old minor, followed by a restore: 'If you cannot restore the database, you cannot roll back to a previous minor version.' A NixOS rollback swaps the k3s binary but leaves the SQLite or etcd data the newer API server already wrote. So the one node whose failure is S8 is also the one node where the generic rollback is wrong. The VM test per node class checks each class's end state, not the mixed state of a new server with old agents. Prior-art takeaway 10 names that mixed state as the main source of rolling-upgrade failures.

**Recommendation.** Encode this in the model and the applier. (1) When the control plane's k3s minor version changes, the applier takes a datastore snapshot (etcd-snapshot, or a SQLite copy plus the token) as a required step before switching, and records its id in the rollout's events. Rollback for that node is then the binary plus the datastore restore, as a documented procedure. (2) Patch bumps follow the derived order automatically. Minor bumps require an explicit Operator approval, like a production environment approval. (3) Add a two-node NixOS VM test to the host gate: the new control-plane closure and an old-generation worker, asserting the node joins and a pod schedules. nixpkgs already ships k3s multi-node and per-version tests (nixos/tests/rancher) to adapt.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| system-upgrade-controller with k3s server and agent Plans | v0.20.2 released 2026-09-23; the documented k3s upgrade path | Orders servers before agents natively, but it upgrades the k3s binary in place, which conflicts with k3s being part of the NixOS closure. It does not solve the datastore rollback either. |

**Verification (confirmed).** The k3s rollback docs say this verbatim: 'When rolling back to a previous Kubernetes minor version, you must have a datastore snapshot taken on the Kubernetes minor version you wish to roll back to' and 'If you cannot restore the database, you cannot roll back to a previous minor version'. They also say this applies to single-node SQLite clusters, where the restore means replacing the .db file. design/hosts.md 'Order of nodes' puts the control plane first for a k3s change, and 'States of the host applier' gives every node the same rollback, booting the previous generation. A generation rollback swaps the binary but not the datastore, so the claim holds. The mixed state (new server, old agents) exists in production for the length of every k3s rollout, and a per-class VM test never exercises it, which matches prior-art takeaway 10. nixpkgs nixos/tests/rancher has multi-node.nix to adapt. The recommendation is cheap for one maintainer: a pre-switch SQLite .backup plus a token copy only for minor bumps, an approval gate a few times a year, and one more VM test. system-upgrade-controller v0.20.2 (2026-09-23) is current, and it is rightly dismissed because it replaces the k3s binary in place.

**Corrections.** Minor: the snapshot step needs a consistent copy (sqlite3 .backup, not cp), plus /var/lib/rancher/k3s/server/token.

Sources:

- <https://docs.k3s.io/upgrades/roll-back>
- <https://docs.k3s.io/cli/etcd-snapshot>
- <https://kubernetes.io/releases/version-skew-policy/>
- <https://raw.githubusercontent.com/NixOS/nixpkgs/nixos-unstable/nixos/tests/rancher/default.nix>
- <https://github.com/rancher/system-upgrade-controller/releases>

### hosts-4: The state machine drains a node and holds the only Lease while it waits for the window

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| weakness | high | S9, S12, S5 | weakened | high |

**Concerns:** design/hosts.md, section 'States of the host applier'; diagrams/specs.py state-host-applier (Draining -> Switching -> AwaitingWindow)

The applier takes the Lease and drains before it switches, and only after switching does it find 'kernel changed' and wait for the window. Outside the window, then, a node sits cordoned and drained for up to a day. It runs a live-switched userspace on the old kernel. And it holds the one estate-wide Lease, blocking every other node, including nodes in another site whose window is open. A Lease with a time-to-live (security.md) either expires during that wait, so a second node starts disrupting, or must be renewed for hours. The live switch is also where this fleet has broken before: restarting tailscaled took k3s down (raspberry-pi-recovery.nix).

**Recommendation.** Decide whether a reboot is needed from the fetched closure before taking the Lease. If one is needed, stage it with 'switch-to-configuration boot' at fetch time (no disruption), and take the Lease and drain only once the node's window is open. Release the Lease after the health check of the booted generation. Take the simpler option seriously: treat every host change as stage-then-reboot inside the window. Every generation is then boot-tested, live-switch hazards disappear, and the state machine loses its Switching/AwaitingWindow fork. The design already rejected 'host rollout within one window' as an SLO, so latency is not the binding constraint. Keep a live 'test' switch only for urgent fixes.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| NixOS system.autoUpgrade with allowReboot and rebootWindow | Part of nixpkgs | Has the right per-node window semantics, but no cross-node lock and no drain. |

**Verification (weakened).** The finding reads the diagram correctly. In docs/diagrams/specs.py, state-host-applier goes WaitingForLease -> Draining -> Switching -> AwaitingWindow ('kernel changed'), with no uncordon or Lease release before the window. That leaves a node drained and holding the one estate-wide Lease for up to a day, blocking the other site. This is a real design bug. Deciding reboot need from the fetched closure before taking the Lease, and staging with 'switch-to-configuration boot', is a cheap and sound fix. Three parts are overstated. First, a renewed Lease is normal Lease semantics, not a defect: 'expires or must be renewed for hours' only matters because the hold is pointless. Second, raspberry-pi-recovery.nix records the pi-net-recovery script restarting tailscaled and taking k3s down, not a NixOS live switch breaking the fleet. Third, the 'every host change is stage-then-reboot' option conflicts with hosts-2. It multiplies unattended reboots on the 4 active nodes that have no boot assessment. It puts more reboot wear on Pis booting from USB flash. And it makes every OS-only change pause the API on the single control plane. The SLO argument also does not settle it, because rejecting 'within one window' as an SLO does not mean extra reboots are free.

**Corrections.** The tailscaled incident was a network-recovery script restarting tailscaled, not a live switch (nix-config nix/modules/roles/raspberry-pi-recovery.nix lines 4-6). The 'reboot everything' simplification trades live-switch hazards for more boot-path risk on nodes without boot counting. It should not be presented as risk-free.

Sources:

- <https://raw.githubusercontent.com/NixOS/nixpkgs/nixos-unstable/nixos/modules/tasks/auto-upgrade.nix>
- <https://kured.dev/docs/configuration/>

### hosts-5: Drain and lock sit on the host, against the design's own prior art, and need a credential RBAC cannot scope

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| alternative | medium | S4, S5, S10, S9 | weakened | medium |

**Concerns:** design/hosts.md, sections 'Inside the host applier' (six ports) and 'Where the host parts run'; design/security.md rows 'Applier to API'; research/prior-art.md takeaways 3 and 4

Prior-art takeaway 3 says drain belongs to 'a cluster-side controller holding a lock, not ... the host', and takeaway 4 calls the DaemonSet-plus-lock the existing pattern. Yet the host applier holds the Lease, evicts and cordons through its own API credential. security.md's mitigation, 'RBAC limits each node to its own pods', cannot be built. RBAC grants pods/eviction by namespace and resource name, not by spec.nodeName. The Node authorizer that does scope kubelets by node does not grant evictions. Each node would also need a long-lived API credential on disk, provisioned at enrollment, which the design does not describe. Four of the six ports (Lease, Evictor, WindowPolicy, plus the lock and uncordon logic) re-implement kured, which is a CNCF Sandbox project at v1.23.0 (2026-06-30) and active in 2026-10.

**Recommendation.** Split the host work along the cluster boundary. The host side stays bespoke and small, with no API credential: verify the signed host tag, realize the closure, run 'switch-to-configuration boot', handle health and local rollback (hosts-2), and signal readiness through a sentinel. The cluster side is kured, one DaemonSet per site so each site gets its own window. It uses --reboot-sentinel-command (booted differs from the staged generation), --start-time, --end-time, --time-zone and --reboot-days for the window, --lock-ttl, --drain-timeout, --blocking-pod-selector, and --prometheus-url, so a firing alert on a just-rebooted node halts the rollout. The service enforces order by moving host tags in waves: the control plane first for a k3s bump, then a canary, then the rest, waiting on each node's reported generation. The appliers then derive nothing. When the cluster is down nothing reboots, which is the break-glass case anyway.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| kured | CNCF Sandbox; v1.23.0 released 2026-06-30; repository pushed 2026-10-21 | Lock, drain through the Eviction API, window, alert-gating and lock TTL, all maintained upstream. It only reboots, so it fits the stage-then-reboot model of hosts-4. It is an in-cluster component the hosts depend on for coordination only. |
| Rancher system-upgrade-controller | v0.20.2 released 2026-09-23; active | Concurrency, drain, a window, and server-before-agent Plans. But each upgrade runs as a privileged Job that would need Nix and host /nix mounts to switch a NixOS generation. More moving parts than kured for this fleet. |
| comin | v0.14.0 released 2026-07-19; active (pushed 2026-10-18) | A mature pull agent with signature checks, deploy confirmers, switch inhibitors, post-deployment hooks and metrics. But it evaluates and builds on the node (heavy on 3.8 GiB Pis), has no auto-reboot and no cross-node coordination, and its no-evaluation mode (PR #207, niks3 pins) is open and untested. Revisit as the host-side half when #207 ships. |
| Cachix Deploy | Commercial, active | Its agent pulls a prebuilt closure with no evaluation on the node, the model prior-art takeaway 1 endorses. It is hosted and has no drain or window, so it would still need kured. |

**Verification (weakened).** Two sub-claims survive. RBAC cannot scope pods/eviction by spec.nodeName, so security.md's 'RBAC limits each node to its own pods' cannot be built as written. The Node authorizer grants kubelets writes to nodes, pods (pods bound to the node, via NodeRestriction) and events, and does not list evictions. The design also never says how a systemd applier gets an API credential. The kured recommendation does not fix either problem, and parts of the reasoning misread the prior art. (1) kured's own ClusterRole grants cluster-wide pods list/delete, pods/eviction create and nodes patch (kured-rbac.yaml), which is broader than per-node, so the scoping problem stays. Only the credential's custody moves, to a projected service-account token. (2) kured does the drain from its DaemonSet pod on the node being rebooted. That is takeaway 4's pattern, which the design's applier already follows apart from being a systemd unit. So 'against the design's own prior art' is overstated. (3) kured's lock is an annotation on one DaemonSet (--ds-name/--ds-namespace). One DaemonSet per site gives two locks, so two nodes can be disrupted at once. That breaks the design's one-node-at-a-time rule and weakens S9. (4) kured only reboots, which forces the every-change-reboot model hosts-4 hedges on. It also moves ordering into service-side tag waves, which is new bespoke logic, not less. The facts are current: kured is CNCF Sandbox (accepted 2022-09-14) at v1.23.0 (2026-06-30), and the cited flags exist. The net upkeep saving for one maintainer is smaller than claimed.

**Corrections.** kured needs a cluster-wide eviction and pod-delete grant itself, so adopting it does not scope evictions per node. Per-site kured DaemonSets would hold separate locks, not one estate-wide lock. Takeaway 4 already describes a worker on the node it changes with the lock in the API server, which is what the design's applier is.

Sources:

- <https://kured.dev/docs/configuration/>
- <https://github.com/kubereboot/kured/releases>
- <https://github.com/rancher/system-upgrade-controller/releases>
- <https://kubernetes.io/docs/reference/access-authn-authz/node/>
- <https://kubernetes.io/docs/reference/access-authn-authz/rbac/>
- <https://github.com/nlewo/comin>
- <https://github.com/nlewo/comin/pull/207>
- <https://docs.cachix.org/deploy/>
- <https://raw.githubusercontent.com/kubereboot/kured/main/kured-rbac.yaml>
- <https://www.cncf.io/projects/kured/>

### hosts-6: The signed host tag does not bind closure content, and custody of the Nix signing key is unstated

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| best-practice-gap | medium | S11, S10 | weakened | medium |

**Concerns:** design/security.md, row 'Applier to cache: Tampering'; design/hosts.md, 'A host rollout'; decisions/choices.md rows 'Host closures' and 'Host pointer'

The host tag is cosign-signed by Vault and names a store path. NixOS system paths are input-addressed: the hash covers the build recipe, not the output. Content integrity therefore rests only on the Nix signature over each path's NarHash, from a key the design says CI uses ('built and signed in CI'), which in practice means a GitHub secret. If that key and cache write access are taken, an attacker can pre-upload malicious content under store paths that a future legitimate closure will reference. Those paths are predictable from public nixpkgs and the config. Nodes would accept them under a correctly Vault-signed tag, so S11's 'refuse it on signature or digest' fails for hosts. The design also never names the cache product, which decides where that key lives.

**Recommendation.** (1) Make the signed host tag carry a closure manifest: every store path in the closure with its narHash and narSize. After realization, the applier verifies the realized closure (nix path-info --json --recursive) against the manifest before staging. Vault becomes the single trust root, and the Nix key becomes defence in depth. (2) Keep the Nix signing key out of GitHub. Use a cache that signs on the server and accepts CI pushes by GitHub OIDC, and add a rule that no workflow secret holds a Nix secret key. (3) Pin nodes to require-sigs with only the estate key and cache.nixos.org in trusted-public-keys. (4) Choose the cache now, in a record.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| niks3 | v1.15.0 is the latest tag; repository pushed 2026-10-20; used by Clan infra and Numtide | S3 or R2 storage, GitHub OIDC push, reference-tracking garbage collection, and pins (a named pointer to a closure, the same idea as the host tag). It needs a Postgres and a server running off-cluster, which is one more thing to keep alive. Its README does not say who holds the signing key. |
| Cachix (hosted) | Client v1.13.0; active | No server to run, and it has pins and Deploy. It is a paid external dependency on the S8 path, and the cache contents sit with a third party. |
| Attic | Active repository (pushed 2026-10-20) but no tagged releases | Self-hosted, multi-tenant and signs on the server, but without releases it is harder to pin and audit. |
| harmonia | v3.3.0 released 2026-09-18 | Serves an existing Nix store over HTTP. It is not an off-cluster object-store cache on its own. |

**Verification (weakened).** Key custody is a real, cheap gap. design/hosts.md 'A host rollout' says CI 'builds and signs every node's closure into an off-cluster binary cache', no page names the cache, and today's nix-config trusts only cache.nixos.org and deploy-rs.cachix.org. But the claim that 'S11 fails for hosts' is overstated. S11 is a tampered artifact in the registry or cache. Without the Nix secret key, the narinfo signature (whose fingerprint covers storePath, narHash, narSize and references) refuses it, as security.md's 'Applier to cache' row says. The attack described needs theft of the Nix signing key plus cache write, which is a compromised-CI (S10) scenario. The closure manifest also adds less than claimed. It would be produced by the same estate CI that holds the key and builds the closure, so a compromise of that CI can produce a matching manifest. The manifest helps only when the key leaks some other way. It is extra bespoke verification for a narrow gain, so the stronger, cheaper fix is (2)-(4): keep the key out of GitHub, sign on the server or by OIDC, and choose the cache in a record. On the alternatives: niks3's README shows no releases section and does not say who signs, so 'v1.15.0 latest tag' could not be verified. comin #207 (niks3 support) is still an untested draft.

**Corrections.** The threat is S10 (compromised estate CI or a stolen Nix key), not S11. Ordinary tampering in the cache is already refused by the Nix signature check. A manifest computed in the same CI that holds the key does not defend against that CI being compromised.

Sources:

- <https://github.com/Mic92/niks3>
- <https://github.com/Mic92/niks3/wiki/Pinning>
- <https://github.com/zhaofengli/attic>
- <https://github.com/nix-community/harmonia/releases>
- <https://docs.cachix.org/>
- <https://github.com/nlewo/comin/pull/207>

### hosts-7: Bootstrap, enrollment and break-glass are designed from scratch when the estate already runs tools for them

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| missing | medium | S8, S5, S4 | weakened | high |

**Concerns:** design/hosts.md, sections 'When the cluster is down', 'UC-12 Switch a node by hand' and 'UC-10 Declare a node'

UC-10 renders host data but never says how a new or reinstalled node gets its first generation, its trusted Nix key, the cosign public key and any credential the applier needs. The break-glass command is a new tool. Today nix-config already has deploy-rs with magic rollback and a learned confirmTimeout of 180 s, nixos-anywhere with disko, and SD-image outputs for the Pis. The break-glass row in security.md requires 'a signed generation'. If verifying it needs Vault or ghcr, break-glass fails in exactly the S8 case where Vault is down with the control plane.

**Recommendation.** Make break-glass and bootstrap generated configuration for existing tools, not new code. The compiler emits deploy-rs node entries and nixos-anywhere and disko targets from host data. Break-glass is 'deploy-rs to one node with magic rollback', verifying only the Nix signature, plus the last host tag cached on the node and checked against a public key baked into the closure, so it works with Vault and the cluster down. Enrollment is nixos-anywhere with the trust roots baked into the closure. With hosts-5, the host side then needs no cluster credential. Drop the bespoke command from UC-12.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| deploy-rs | v1.0.0 released 2026-10-19 (first versioned release, crates.io); active | Already in production here with magic rollback. Push over SSH needs the operator's machine and reachability, which suits break-glass. Today's flake pins its nixpkgs to stay substitutable from deploy-rs.cachix.org. |
| nixos-anywhere | Latest release 1.13.0 (2025-11-13); repository pushed 2026-10-21 | Already used here for installs. It is the natural rebuild step in the hosts-1 runbook. |
| Colmena | v0.5.0 released 2026-09-22 under nix-community | Parallel push with tags and an apply-local mode, but no magic rollback. No better than deploy-rs here. |
| Clan | Young, very active (GitHub mirror pushed 2026-10-22) | Covers inventory, vars and secrets, and installs through nixos-anywhere. It would replace Infrastructure Intent and the compiler's host half with its own model, so the 'one model' choice would have to reopen. |
| NixOps4 | README says 'Status: in development'; no releases | Not usable as a dependency for a one-maintainer estate today. |

**Verification (weakened).** The enrollment gap holds. UC-10 'Declare a node' says the node is rendered and VM-tested, but not how a new or reinstalled node gets its first generation, its trusted Nix key, the cosign public key or the applier's credential. Reusing the tools already in production is good one-maintainer advice. nix-config has deploy-rs with magicRollback and confirmTimeout=180, nixos-anywhere, disko and piSdImages. deploy-rs v1.0.0 (2026-10-19, first crates.io release), nixos-anywhere 1.13.0 and colmena v0.5.0 (2026-09-22) are current. Three parts are overstated. First, design/hosts.md 'When the cluster is down' says 'A documented break-glass command'; it never says new code, so 'the break-glass command is a new tool' is the reviewer's reading. Second, the S8 failure path is speculative. Verifying a cosign signature needs only Vault's public key, not Vault online. UC-12 switches to 'a given generation', not to a host tag, so ghcr is not needed either. Third, the recommendation leaves out the interaction a push-based break-glass has with the pull applier. When the cluster returns, the applier will try to converge the node back to its host tag unless break-glass marks the node or the tag is moved afterwards. That needs designing whichever tool does the push.

**Corrections.** The design does not specify a bespoke break-glass tool. Cosign verification of a generation works with Vault down if the public key is baked into the closure, which the design does not forbid. The missing piece is how break-glass and the pull applier reconcile afterwards.

Sources:

- <https://github.com/serokell/deploy-rs/releases/tag/v1.0.0>
- <https://github.com/nix-community/nixos-anywhere>
- <https://github.com/nix-community/colmena/releases>
- <https://clan.lol>
- <https://github.com/nixops4/nixops4>
- <https://github.com/nix-community/nixos-anywhere/releases>

### hosts-8: The node order and the VM-test gate ignore host-native roles and the hardware the VMs cannot emulate

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| weakness | medium | S9, S12 | weakened | medium |

**Concerns:** design/hosts.md, sections 'Order of nodes' and 'One model, two appliers' (gate row); decisions/choices.md row 'Host gate'

The derived order knows only 'k3s changed' versus 'OS changed', and the canary is 'one canary worker'. Drain through the Eviction API protects pods only. enschede-t1000-1 is the LAN subnet router and was the DNS dependency. Today's deploy-all.sh deploys it last for that reason. Other nodes run host-native Samba, btrfs backups and ROCm services, which no PodDisruptionBudget covers. Picking t1000 as the canary would cut the home network. A VM test per class cannot exercise Pi firmware, U-Boot or the bcmgenet NIC, the NVIDIA or AMD stacks, or disko layouts. Hosted aarch64 GitHub runners may lack /dev/kvm (unverified), which would make an aarch64 VM test slow under emulation.

**Recommendation.** Add per-node rollout attributes to Infrastructure Intent and give each a check. One is canary eligibility, false for nodes that hold LAN-critical host services. Another is a 'last in site' rank. A third is a list of host-native health probes (subnet route advertised, Samba responding) that the local health check runs. State plainly that the per-class VM test proves configuration and services, and that the real S9 gate for hardware classes is the canary's boot-and-health. Measure /dev/kvm on the chosen aarch64 runner before committing to an aarch64 VM test in the 2-minute or 10-minute budgets.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| kured --blocking-pod-selector or --prometheus-url | kured v1.23.0 | Can stop a reboot while a critical host-service alert fires, but only for services exposed as metrics or pods. |

**Verification (weakened).** The core claim holds. 'Order of nodes' derives order only from 'k3s changed' versus 'OS changed' and says 'one canary worker'. That loses the hand-learned order in nix-config scripts/deploy/deploy-all.sh, which deploys enschede-t1000-1 (subnet router for 192.168.0.0/24) and frankfurt-contabo-1 last. Drain protects only pods, and t1000 runs host-path Samba, the btrfs backup store (/srv/backup) and media (inventory/nodes/enschede-t1000-1.yml). A canary-eligibility attribute and host-native probes are cheap. Three parts are overstated or poorly sourced. First, 'picking t1000 as canary would cut the home network': AdGuard no longer depends on t1000 alone, since two instances now float behind MetalLB VIPs (enschede-pi-1.yml). The subnet router carries tailnet access to the LAN, not the LAN itself. Rebooting t1000 drops remote LAN access, Samba, media and the backup target. Second, the design already concedes the VM gate does not emulate hardware ('Host gate' row: 'without emulating GPUs'), so this extends a stated limit rather than finding a new one. Third, the /dev/kvm source (actions/partner-runner-images issue 52) returns 404, and no primary source settles whether ubuntu-24.04-arm exposes /dev/kvm. The advice to measure it first is still right.

**Corrections.** t1000 is no longer the LAN's sole DNS. Losing its subnet route affects tailnet-to-LAN access, not the home network. The cited GitHub issue URL is dead. The design already states the VM test does not cover GPUs.

Sources:

- <https://kured.dev/docs/configuration/>
- <https://github.com/actions/partner-runner-images/issues/52>
- <https://raw.githubusercontent.com/NixOS/nixpkgs/nixos-unstable/nixos/modules/virtualisation/qemu-vm.nix>
- <https://docs.github.com/en/actions/reference/runners/github-hosted-runners>

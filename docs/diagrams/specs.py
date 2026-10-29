"""Every diagram except deploy-kit's metamodels (metamodels.py), one declaration each.

Run it to regenerate raw/, then build.py to lay the sources out and export them.
"""

from gen import Graph, classes, sequence, states, use_case, write_all

# ---------------------------------------------------------------------------------------------
# Use cases: one per diagram.
# ---------------------------------------------------------------------------------------------

use_case("uc1-validate", "Use case 1: validate a change", ["Application author", "Project CI"],
         "Validate a change", ["Validate offline", "Plan without the cluster", "Resolve model paths to YAML lines"])
use_case("uc2-dry-run", "Use case 2: dry-run a release", ["Project CI"], "Dry-run a release",
         ["Build candidate images", "Compose the estate", "Server-side apply dry-run"], secondary=[(2, "API server")])
use_case("uc3-deploy", "Use case 3: deploy a release", ["Project CI", "Environment approver"], "Deploy a release",
         ["Promote candidate digests", "Server-side apply dry-run", "Sign and move the prod tag", "Watch the rollout live"],
         secondary=[(2, "Vault Transit")])
use_case("uc4-watch", "Use case 4: watch a rollout live", ["Application author", "Operator"],
         "Watch the rollout live", ["Resume from the last event"])
use_case("uc5-pause", "Use case 5: pause or resume a Project", ["Operator"], "Pause or resume a Project",
         ["Sign in through auth-api", "Write the Project object"])
use_case("uc6-rollback", "Use case 6: roll back a Project, on the fast path", ["Operator"], "Roll back a Project",
         ["Sign in through auth-api", "Dry-run the last Serving render", "Move the prod tag back",
          "Set the Project to Paused", "Re-compose only if the dry-run fails"], secondary=[(1, "API server")])
use_case("uc7-admit", "Use case 7: admit a Project", ["Admin"], "Admit a Project",
         ["Edit Platform Intent", "Derive the Flux source"])
use_case("uc8-apply", "Use case 8: pull and apply a render", ["Flux"], "Pull and apply a render",
         ["Verify the signature", "Apply and prune"], secondary=[(0, "ghcr")])
use_case("uc9-gate", "Use case 9: gate a traffic switch", ["Flagger"], "Gate a traffic switch",
         ["Authenticate by service-account token", "Check every Release Unit member"])
use_case("uc10-declare-node", "Use case 10: declare a node", ["Admin"], "Declare a node",
         ["Edit Infrastructure Intent", "Render host data", "Build and VM-test its class"])
use_case("uc11-roll-out-hosts", "Use case 11: roll out a host change", ["Project CI", "Host applier"],
         "Roll out a host change",
         ["Derive the node order", "Take the Lease, evict pods", "Switch the generation", "Reboot inside the window"],
         secondary=[(1, "API server")])
use_case("uc12-break-glass", "Use case 12: switch a node by hand", ["Operator"], "Switch a node by hand",
         ["Verify the closure signature", "Switch without the Lease"], system="host applier")
use_case("uc13-mailbox", "Use case 13: declare a Mailbox", ["Application author"], "Declare a Mailbox",
         ["Generate its password", "Provision the account"], secondary=[(1, "Stalwart")])

# ---------------------------------------------------------------------------------------------
# Sequences: one interaction each.
# ---------------------------------------------------------------------------------------------

sequence("seq-deploy-1-admit", "Deploy, step 1 of 3: the deploy job hands a release to the service",
         [("CI", "deploy job"), ("R", "compiler binary"), ("O", "ghcr"), ("S", "estate-kit service")],
         [("CI", "R", "validate offline"), ("R", "CI", "no diagnostics", "reply"),
          ("CI", "O", "promote digests, publish the Intent Fragment"),
          ("CI", "S", "deploy (GitHub OIDC token)"), ("S", "CI", "rollout id, event stream opens", "reply")])
sequence("seq-deploy-2-dryrun", "Deploy, step 2 of 3: compose, dry-run, sign and move the prod tag",
         [("S", "estate-kit service"), ("R", "compiler binary"), ("K", "API server"), ("V", "Vault Transit"), ("O", "ghcr")],
         [("S", "O", "pull the admitted fragments"), ("S", "S", "every digest registered by its Project?"),
          ("S", "R", "compose the estate"),
          ("R", "S", "renders, diagnostics", "reply"), ("S", "K", "apply, dryRun=All, as the dry-run identity"),
          ("alt", "dry-run accepted",
           [("K", "S", "accepted", "reply"), ("S", "V", "sign with the render key"),
            ("S", "O", "push, move the prod tag (compare-and-swap)")],
           "dry-run rejected",
           [("K", "S", "rejected", "reply"), ("note", "S", "Project isolated, prod tag unchanged")])])
sequence("seq-deploy-3-switch", "Deploy, step 3 of 3: Flux applies and Flagger switches traffic",
         [("F", "Flux"), ("O", "ghcr"), ("K", "API server"), ("FG", "Flagger"), ("S", "estate-kit service"), ("CI", "deploy job")],
         [("F", "O", "pull the prod tag, verify its signature"), ("F", "K", "apply"),
          ("FG", "S", "Release Gate webhook"), ("S", "FG", "promote once every member is healthy", "reply"),
          ("S", "CI", "settled: Serving or Held", "reply")])
sequence("seq-dry-run", "Dry-run of a release pull request",
         [("CI", "deploy job, dry-run"), ("S", "estate-kit service"), ("K", "API server"), ("GH", "GitHub")],
         [("CI", "CI", "build candidate images"), ("CI", "S", "deploy, dry-run (GitHub OIDC token)"),
          ("S", "K", "compose, apply dryRun=All"), ("K", "S", "accepted or rejected", "reply"),
          ("S", "CI", "diagnostics, render diff", "reply"), ("CI", "GH", "annotations, check run, job summary")])
sequence("seq-rollback", "Roll back a Project: the fast path signs and composes nothing",
         [("@Op", "Operator"), ("S", "estate-kit service"), ("K", "API server"), ("O", "ghcr"), ("GH", "GitHub")],
         [("@Op", "S", "roll back"), ("S", "K", "dry-run the last Serving render"),
          ("alt", "dry-run accepted",
           [("K", "S", "accepted", "reply"), ("S", "O", "move the prod tag back (compare-and-swap)"),
            ("S", "K", "set the Project to Paused"), ("S", "@Op", "rolled back, Paused", "reply")],
           "dry-run rejected",
           [("K", "S", "rejected", "reply"), ("S", "GH", "dispatch deploy in watch mode: re-compose")])])
sequence("seq-auth", "Authenticate a deploy call with a GitHub OIDC token",
         [("CI", "deploy job"), ("GO", "GitHub OIDC"), ("S", "estate-kit service")],
         [("CI", "GO", "request an ID token, audience estate-kit"), ("GO", "CI", "JWT", "reply"),
          ("CI", "S", "deploy, Bearer JWT"), ("S", "S", "repository_id and owner id admitted?"),
          ("S", "S", "claim policy: event_name, job_workflow_sha, ref_type, runner, environment"),
          ("S", "CI", "rollout id", "reply")])
sequence("seq-cache", "Skip publishing an unchanged render",
         [("S", "estate-kit service"), ("R", "compiler binary"), ("O", "ghcr")],
         [("S", "R", "render this Project"), ("R", "S", "render, digest", "reply"),
          ("S", "O", "digest behind render/<p>:prod?"), ("O", "S", "current digest", "reply"),
          ("alt", "same digest", [("S", "S", "publish nothing, move nothing, record why")],
           "different digest", [("S", "O", "push, sign, move the tag after the dry-run")])])
sequence("seq-host-rollout", "Roll out a host change, one node at a time",
         [("CI", "CI"), ("C", "binary cache"), ("S", "estate-kit service"), ("O", "ghcr"), ("A", "host applier"), ("K", "API server")],
         [("CI", "C", "push signed closures"), ("CI", "CI", "VM test per node class"),
          ("CI", "S", "host rollout (GitHub OIDC token)"), ("S", "O", "move host/<node>:prod"),
          ("A", "O", "poll the tag, verify it"), ("A", "C", "fetch and verify the closure"),
          ("A", "A", "reboot needed? stage with boot, wait for the window"),
          ("A", "K", "take the Lease, evict pods"), ("A", "A", "switch or reboot, health check"),
          ("A", "K", "uncordon, release the Lease")])
sequence("seq-mailbox", "Provision a Mailbox",
         [("S", "estate-kit service"), ("F", "Flux"), ("K", "API server"), ("M", "mail provisioner"), ("ST", "Stalwart"), ("V", "Vault")],
         [("S", "F", "Project render with Mailbox objects"), ("F", "K", "apply the Mailbox"),
          ("M", "K", "watch Mailboxes by label"), ("M", "V", "read the generated password"),
          ("M", "ST", "create or update the account"), ("M", "K", "write status")])
sequence("seq-platform-push", "Push Platform Intent like any Project",
         [("CI", "estate repo CI"), ("O", "ghcr"), ("S", "estate-kit service"), ("R", "compiler binary")],
         [("CI", "R", "validate Platform Intent"), ("CI", "O", "publish the platform fragment"),
          ("CI", "S", "deploy (GitHub OIDC token, platform)"), ("S", "S", "cache the new copy"),
          ("S", "R", "compose the estate"), ("S", "CI", "rollout stream", "reply")])
sequence("seq-drift-check", "Nightly drift check",
         [("S", "estate-kit service, nightly"), ("G", "GitHub"), ("O", "ghcr"), ("DB", "service cache")],
         [("S", "G", "latest release of each admitted repository"), ("S", "O", "latest fragment and prod tag"),
          ("S", "DB", "cached copies"), ("S", "S", "compare all three"),
          ("opt", "they differ", [("S", "G", "report the drift as an issue or a check")])])
sequence("seq-fail-retry", "Failure: the deploy response is lost and the job retries",
         [("CI", "deploy job"), ("S", "estate-kit service"), ("DB", "event log")],
         [("CI", "S", "deploy (Project, fragment digest)"), ("S", "DB", "rollout created"),
          ("S", "CI", "response lost (timeout)", "reply"), ("CI", "S", "retry: same Project and digest"),
          ("S", "DB", "find the existing rollout"), ("S", "CI", "same rollout id, no second run", "reply")])
sequence("seq-fail-stream", "Failure: the event stream drops and resumes",
         [("CI", "deploy job"), ("S", "estate-kit service"), ("DB", "event log")],
         [("S", "CI", "events 1 to 41", "reply"), ("CI", "CI", "connection drops"),
          ("CI", "S", "watch, resume after 41"), ("S", "DB", "events since 41"),
          ("S", "CI", "events 42 onwards, duplicates dropped", "reply")])
sequence("seq-fail-dryrun", "Failure: the API server rejects the dry-run",
         [("S", "estate-kit service"), ("K", "API server"), ("DB", "event log"), ("CI", "deploy job")],
         [("S", "K", "apply, dryRun=All"), ("K", "S", "rejected: immutable field", "reply"),
          ("S", "DB", "Refused event, Project isolated"), ("S", "CI", "problem+json with the model path", "reply"),
          ("CI", "CI", "annotate the YAML line, fail the job")])
sequence("seq-fail-host-crash", "Failure: the host applier crashes mid-switch and resumes",
         [("A", "host applier"), ("K", "API server"), ("A2", "host applier, restarted")],
         [("A", "K", "take the Lease, cordon, evict"), ("A", "A", "crashes before switching"),
          ("A2", "K", "Lease still mine? node cordoned?"), ("A2", "A2", "resume: switch, health check"),
          ("A2", "K", "uncordon, release the Lease")])

# ---------------------------------------------------------------------------------------------
# State machines.
# ---------------------------------------------------------------------------------------------

states("state-rollout", "State machine: a rollout",
       [("[*]", "Accepted", ""), ("Accepted", "Composing", ""), ("Composing", "DryRun", "render changed"),
        ("Composing", "Serving", "render unchanged"), ("Composing", "Refused", "model error"),
        ("DryRun", "Signed", "accepted"), ("DryRun", "Refused", "rejected"), ("Signed", "Applying", "tag moved"),
        ("Applying", "Switching", "Flux applied"), ("Switching", "Serving", "all healthy"),
        ("Switching", "Held", "analysis failed"), ("Serving", "[*]", ""), ("Refused", "[*]", ""), ("Held", "[*]", "")],
       tones={"Serving": "good", "Refused": "bad", "Held": "warn"})
states("state-project", "State machine: a Project",
       [("[*]", "Active", "admitted"), ("Active", "Paused", "pause"), ("Paused", "Active", "resume"),
        ("Active", "RolledBack", "roll back"), ("RolledBack", "Active", "next release")])
states("state-host-applier", "State machine: the host applier on one node",
       [("[*]", "Current", ""), ("Current", "Fetched", "new host tag, closure verified"),
        ("Fetched", "Staged", "reboot needed: stage with boot"), ("Staged", "WaitingForLease", "window opens"),
        ("Fetched", "WaitingForLease", "live change"), ("WaitingForLease", "Draining", "Lease held"),
        ("Draining", "Switching", "pods evicted"), ("Switching", "HealthCheck", "switched with test, or rebooted"),
        ("HealthCheck", "CurrentNew", "healthy: boot default set"), ("HealthCheck", "RolledBack", "unhealthy"),
        ("CurrentNew", "[*]", ""), ("RolledBack", "[*]", "")],
       labels={"WaitingForLease": "Waiting for the Lease", "HealthCheck": "Health check",
               "CurrentNew": "Current (new generation)", "RolledBack": "Rolled back to the previous generation"},
       tones={"CurrentNew": "good", "RolledBack": "bad", "Staged": "warn"})
states("state-mailbox", "State machine: a Mailbox",
       [("[*]", "Declared", ""), ("Declared", "Provisioned", "account created"),
        ("Declared", "Refused", "local part claimed by another Project"),
        ("Provisioned", "Rotating", "rotation due"), ("Rotating", "Provisioned", "new password delivered"),
        ("Provisioned", "Removed", "dropped from intent"), ("Removed", "[*]", ""), ("Refused", "[*]", "")],
       labels={"Rotating": "Rotating the password"},
       tones={"Provisioned": "good", "Refused": "bad"})

# ---------------------------------------------------------------------------------------------
# Class diagrams of the internals.
# ---------------------------------------------------------------------------------------------

classes("rust-authored-model", "Rust: the authored model, as the read step produces it",
        [("Project", None, ["name: ProjectName", "applications: BTreeMap<ApplicationId, Application>"]),
         ("Application", None, ["id: ApplicationId", "processes: BTreeMap<ProcessName, Process>",
                                "exposures: Vec<Exposure>", "dependencies: Vec<DependencyEdge>"]),
         ("Process", None, ["name: ProcessName", "image: ImageAlias", "lifecycle: Lifecycle", "engine: Option<Engine>"]),
         ("Exposure", None, ["host: Hostname", "audience: Audience", "routes: Vec<Route>"]),
         ("DependencyEdge", None, ["to: ApplicationId", "surface: SurfaceName"]),
         ("Surface", None, ["name: SurfaceName", "port: Port"]),
         ("Grant", None, ["path: SecretPath", "tier: AccessTier", "delivery: Delivery"])],
        [("Project", "Application", "comp", "", "1..*"), ("Application", "Process", "comp", "", "1..*"),
         ("Application", "Exposure", "comp", "", "0..*"), ("Application", "DependencyEdge", "comp", "", "0..*"),
         ("Process", "Surface", "comp", "", "0..*"), ("Process", "Grant", "comp", "", "0..*")])
classes("rust-pipeline-types", "Rust: the types that cross the pipeline's seams",
        [("PinnedInputSet", None, ["fragments: BTreeMap<ProjectName, Pinned<ProjectIntent>>",
                                   "platform: Pinned<PlatformIntent>", "cluster_state: Pinned<ClusterState>",
                                   "render_key(project) RenderKey"]),
         ("Hasher", "trait", ["digest(bytes) Digest"]),
         ("ResolvedDeployment", None, ["applications: BTreeMap<ApplicationId, ResolvedApplication>", "trace: Trace"]),
         ("Renderer", "trait", ["render(ResolvedDeployment) Result<Vec<Deliverable>, Vec<Diagnostic>>"]),
         ("Deliverable", None, ["path: OutputPath", "owner: ProjectName", "object: DeliverableObject",
                                "sources: Vec<ModelPath>"]),
         ("Diagnostic", None, ["code: Code", "severity: Severity", "file: SourceFile", "path: ModelPath", "message: String",
                               "help: String"])],
        [("PinnedInputSet", "Hasher", "dep", "digests through"), ("Renderer", "ResolvedDeployment", "dep", "reads"),
         ("Renderer", "Deliverable", "dep", "emits"), ("Renderer", "Diagnostic", "dep", "or reports")],
        tones={"Hasher": "accent", "Renderer": "accent"})
classes("rust-rollout", "Rust: the rollout decider and the ports its use cases drive",
        [("Rollout", None, ["id: RolloutId", "project: ProjectName", "fragment: Digest", "state: RolloutState"]),
         ("RolloutEvent", "enum", ["rollout: RolloutId", "seq: Seq", "at: Timestamp", "version: u16"]),
         ("Decider", None, ["decide(State, Command) Result<Vec<RolloutEvent>, Refusal>",
                            "evolve(State, RolloutEvent) State"]),
         ("Ports", "trait", ["type EventStore", "type Registry", "type Signer", "type Cluster"]),
         ("EventStore", "trait", ["append(Vec<RolloutEvent>) Result", "since(RolloutId, Seq) Result<Vec<RolloutEvent>>"]),
         ("Registry", "trait", ["fragment(Digest) Result", "push_render(Render) Result<Digest>",
                                "move_tag(Tag, from, to) Result"]),
         ("Signer", "trait", ["sign(Digest, Key) Result<Signature>"]),
         ("Cluster", "trait", ["dry_run(Objects) Result<Vec<Diagnostic>>", "observe(ProjectName) Result<Observation>"])],
        [("Decider", "Rollout", "dep", "folds events into"), ("Rollout", "RolloutEvent", "assoc", "is the fold of", "0..*"),
         ("Ports", "EventStore", "dep"), ("Ports", "Registry", "dep"), ("Ports", "Signer", "dep"),
         ("Ports", "Cluster", "dep")],
        tones={n: "accent" for n in ("Ports", "EventStore", "Registry", "Signer", "Cluster")})
classes("host-applier", "Host applier: one reconcile step and the ports it drives",
        [("Agent", None, ["node: NodeName", "step() one reconcile step"]),
         ("PointerSource", "trait", ["current(NodeName) Result<HostTag>"]),
         ("ClosureFetcher", "trait", ["fetch(StorePath) Result"]),
         ("Lease", "trait", ["acquire() Result", "release() Result"]),
         ("Evictor", "trait", ["drain(NodeName) Result", "uncordon(NodeName) Result"]),
         ("Switcher", "trait", ["switch(Generation) Result", "needs_reboot(Generation) bool"]),
         ("WindowPolicy", "trait", ["open(Timestamp) bool"])],
        [("Agent", p, "dep") for p in ("PointerSource", "ClosureFetcher", "Lease", "Evictor", "Switcher", "WindowPolicy")],
        tones={n: "accent" for n in ("PointerSource", "ClosureFetcher", "Lease", "Evictor", "Switcher", "WindowPolicy")})
classes("mail-provisioner", "Mail provisioner: the reconciler and its ports",
        [("MailboxReconciler", None, ["reconcile(Mailbox) Status"]),
         ("MailboxSource", "trait", ["watch(LabelSelector)"]),
         ("Stalwart", "trait", ["ensure_account(Mailbox) Result", "remove_account(Mailbox) Result"]),
         ("Secrets", "trait", ["password(Mailbox) Result<SecretRef>"])],
        [("MailboxReconciler", p, "dep") for p in ("MailboxSource", "Stalwart", "Secrets")],
        tones={n: "accent" for n in ("MailboxSource", "Stalwart", "Secrets")})

# ---------------------------------------------------------------------------------------------
# C4.
# ---------------------------------------------------------------------------------------------

g = Graph("c4-context", "C4 level 1: estate-kit and everything around it", direction="DOWN", layer_gap=110)
g.person("author", "Application author", "Writes a Project's YAML and releases it")
g.person("op", "Operator, Admin", "Pauses, rolls back, admits Projects")
g.system("gh", "GitHub", "Repositories, Actions, Deployments", kind="external")
g.system("ek", "estate-kit", "Composes, dry-runs and signs renders; rolls out hosts")
g.system("idp", "auth-api", "Signs operators in", kind="external")
g.system("ghcr", "ghcr", "Fragments, renders and tags", kind="external")
g.system("vault", "Vault", "Transit signing, generated secrets", kind="external")
g.system("k8s", "Kubernetes", "Flux, Flagger and the API server", kind="external")
g.system("stal", "Stalwart", "Mail accounts", kind="external")
g.system("nodes", "NixOS nodes", "Run k3s", kind="external")
g.system("cache", "Binary cache", "Signed closures", kind="external")
g.system("obs", "Tempo, Loki, Grafana", "Traces and logs", kind="external")
g.c4_edge("author", "gh", "pushes, releases")
g.c4_edge("gh", "ek", "deploy calls", "HTTPS, OIDC")
g.c4_edge("op", "ek", "uses the UI", "HTTPS")
g.c4_edge("ek", "idp", "signs operators in", "OIDC")
g.c4_edge("ek", "ghcr", "pushes renders, moves tags", "OCI")
g.c4_edge("ek", "vault", "signs renders", "Transit")
g.c4_edge("ek", "k8s", "dry-runs, reads status")
g.c4_edge("ek", "stal", "provisions Mailboxes")
g.c4_edge("ek", "obs", "traces and logs", "OTLP")
g.c4_edge("k8s", "nodes", "runs on")
g.c4_edge("nodes", "cache", "pull closures", "Nix")
g.done()

g = Graph("c4-containers", "C4 level 2: estate-kit's containers and the protocol on each edge", direction="DOWN", layer_gap=110)
g.person("ci", "Project CI", "A GitHub Actions deploy job")
g.person("op", "Operator", "In a browser")
g.group("ek", "estate-kit")
g.system("cli", "estate-kit CLI", "Validates and plans offline", kind="container", tech="Rust, one binary", parent="ek")
g.system("ui", "UI", "Rollouts, Projects, hosts", kind="container", tech="Vue, embedded", parent="ek")
g.system("svc", "service", "Composes, dry-runs, signs, streams rollouts; serves the Observation views", kind="container",
         tech="Rust, links the compiler", parent="ek")
g.system("pg", "event log", "Append-only rollout events", kind="database", tech="platform-postgres", parent="ek")
g.system("applier", "host applier", "Switches one node at a time", kind="container", tech="Rust, systemd", parent="ek")
g.system("comps", "components", "Six reconcilers: migrations, secret grants, database and bucket catalogs, backups, Mailboxes",
         kind="container", tech="Rust, one image each", parent="ek")
g.system("api", "Kubernetes API", "Dry-runs and status", kind="external")
g.system("ghcr", "ghcr", "Fragments, renders, tags", kind="external")
g.system("vault", "Vault Transit", "Signing key", kind="external")
g.c4_edge("ci", "cli", "runs")
g.c4_edge("cli", "svc", "deploy, watch", "HTTPS + SSE, OpenAPI 3.1")
g.c4_edge("op", "ui", "uses", "HTTPS")
g.c4_edge("ui", "svc", "calls", "HTTPS, same origin")
g.c4_edge("svc", "pg", "appends, reads", "SQL")
g.c4_edge("svc", "ghcr", "pushes renders, moves tags", "OCI, machine-account token")
g.c4_edge("svc", "vault", "signs", "Transit")
g.c4_edge("svc", "api", "dry-runs, reads status", "HTTPS")
g.c4_edge("applier", "api", "Lease, Eviction API", "HTTPS")
g.c4_edge("comps", "api", "watch custom resources", "HTTPS")
g.done()

# ---------------------------------------------------------------------------------------------
# Deployment.
# ---------------------------------------------------------------------------------------------

g = Graph("deploy-placement", "Deployment: where each part runs")
g.group("github", "«execution environment» GitHub", kind="node")
g.box("repos", "Project repositories and runners", parent="github")
g.box("estate", "estate repository", parent="github")
g.group("registry", "«device» registry", kind="node")
g.store("ghcr", "ghcr: fragments, renders, tags", parent="registry")
g.group("cluster", "«execution environment» Kubernetes cluster", kind="node")
g.box("edge", "Traefik edge", parent="cluster")
g.box("svc", "estate-kit service", tone="accent", parent="cluster")
g.store("pg", "Postgres", parent="cluster")
g.box("flux", "Flux", parent="cluster")
g.box("flagger", "Flagger", parent="cluster")
g.box("vault", "Vault", parent="cluster")
g.box("idp", "auth-api", parent="cluster")
g.edge("repos", "edge", "deploy calls")
g.edge("estate", "edge", "Platform Intent")
g.edge("edge", "svc")
g.edge("svc", "pg", "event log")
g.edge("svc", "vault", "signs")
g.edge("svc", "idp", "sign-in")
g.edge("svc", "ghcr", "renders, tags")
g.edge("flux", "ghcr", "pulls")
g.edge("flagger", "svc", "webhook")
g.done()

g = Graph("deploy-in-cluster", "Deployment: inside the cluster")
g.group("cluster", "«execution environment» Kubernetes cluster", kind="node")
g.box("svc", "estate-kit service", tone="accent", parent="cluster")
g.store("pg", "platform-postgres: event log", parent="cluster")
g.box("flagger", "Flagger", parent="cluster")
g.box("vault", "Vault Transit", parent="cluster")
g.box("api", "API server", parent="cluster")
g.box("flux", "Flux, locked down per Project", parent="cluster")
g.artifact("obj", "Project objects", parent="cluster")
g.box("idp", "auth-api", parent="cluster")
g.edge("flagger", "svc", "Release Gate webhook")
g.edge("svc", "api", "dry-run, read")
g.edge("flux", "api", "applies")
g.edge("svc", "vault", "sign")
g.edge("svc", "idp", "sign-in")
g.edge("svc", "pg", "appends")
g.edge("svc", "obj", "writes")
g.done()

g = Graph("deploy-hosts", "Deployment: the hosts and what each node runs", direction="DOWN", layer_gap=70)
g.group("ci", "«execution environment» GitHub Actions", kind="node")
g.box("build", "build closures, VM tests", parent="ci")
g.store("cache", "signed binary cache")
g.store("ghcr", "ghcr: host tags")
g.group("cp", "«device» control-plane node", kind="node")
g.box("agentcp", "host applier (systemd)", tone="accent", parent="cp")
g.box("k3scp", "k3s server", parent="cp")
g.group("worker", "«device» worker node", kind="node")
g.box("agentw", "host applier (systemd)", tone="accent", parent="worker")
g.box("k3sw", "k3s agent", parent="worker")
g.store("lease", "Lease, in the API server", tone="plain")
g.edge("build", "cache", "pushes")
g.edge("cache", "agentcp", "closure")
g.edge("ghcr", "agentcp", "host tag")
g.edge("cache", "agentw", "closure")
g.edge("ghcr", "agentw", "host tag")
g.edge("agentcp", "k3scp", "drains, restarts")
g.edge("agentw", "k3sw", "drains, restarts")
g.edge("agentcp", "lease", "holds")
g.edge("agentw", "lease", "holds")
g.done()

# ---------------------------------------------------------------------------------------------
# Flows, inputs and component graphs.
# ---------------------------------------------------------------------------------------------

g = Graph("context", "Context: how a release reaches the cluster")
g.box("ci", "Project CI")
g.box("estate", "estate repository")
g.box("svc", "estate-kit service", tone="accent")
g.store("ghcr", "ghcr")
g.box("flux", "Flux")
g.box("work", "Project workloads")
g.edge("ci", "svc", "deploy (OIDC)")
g.edge("estate", "svc", "Platform Intent")
g.edge("svc", "ghcr", "signed render, prod tag")
g.edge("flux", "ghcr", "pulls")
g.edge("flux", "work", "applies")
g.done()

g = Graph("inputs-compile", "Inputs: what composing a Project reads, and where each comes from")
g.store("prepo", "Project repository", tone="plain")
g.store("erepo", "estate repository", tone="plain")
g.box("cl", "Cluster API", tone="external")
g.artifact("pyaml", "Project YAML, env files")
g.artifact("frag", "Intent Fragment, digests sealed")
g.artifact("pi", "Platform Intent, node contract")
g.artifact("cs", "ClusterState snapshot")
g.artifact("ver", "compiler version")
g.box("validate", "validate, offline", tone="accent")
g.box("compose", "compose: read, check, lower, resolve", tone="accent")
g.box("render", "adapters, serialize the Resolved Deployment", tone="accent")
for a, b, label in [("prepo", "pyaml", ""), ("pyaml", "validate", ""), ("pyaml", "frag", "publish"),
                    ("frag", "compose", ""), ("erepo", "pi", ""), ("pi", "compose", ""), ("cl", "cs", ""),
                    ("cs", "compose", ""), ("ver", "compose", ""), ("compose", "render", "")]:
    g.edge(a, b, label)
g.done()

g = Graph("inputs-deliver", "Inputs: what delivering a render reads, and where each comes from")
g.artifact("render", "render from compose")
g.box("api", "Cluster API", tone="external")
g.box("vaultk", "Vault Transit key", tone="external")
g.store("ghcr", "ghcr prod tag")
g.artifact("events", "Flagger analysis, cluster events")
g.box("dry", "dry-run", tone="accent")
g.box("sign", "sign, push, move the prod tag", tone="accent")
g.box("apply", "Flux applies", tone="accent")
g.box("switch", "switch and report", tone="accent")
for a, b, label in [("render", "dry", ""), ("api", "dry", "dryRun=All"), ("dry", "sign", "accepted"),
                    ("vaultk", "sign", "signs"), ("sign", "apply", ""), ("ghcr", "apply", "pulls"),
                    ("apply", "switch", ""), ("events", "switch", "")]:
    g.edge(a, b, label)
g.done()

g = Graph("inputs-host", "Inputs: what a host rollout reads, and where each comes from")
g.artifact("ii", "Infrastructure Intent")
g.artifact("pi", "Platform Intent")
g.artifact("ver", "k3s and NixOS versions")
g.artifact("mods", "hand-written NixOS modules")
g.box("comp", "compile: host data", tone="accent")
g.box("build", "CI: build closures, VM tests", tone="accent")
g.store("cache", "signed binary cache")
g.box("svc", "service: move host tags", tone="accent")
g.box("agent", "host applier", tone="accent")
for a, b, label in [("ii", "comp", ""), ("pi", "comp", ""), ("ver", "comp", ""), ("comp", "build", "host data"),
                    ("mods", "build", ""), ("build", "cache", "pushes"), ("build", "svc", "passed"),
                    ("svc", "agent", "host tag"), ("cache", "agent", "closure")]:
    g.edge(a, b, label)
g.done()

g = Graph("rust-pipeline", "Rust: each step and the typed model it produces", wrap=True)
g.artifact("yaml", "YAML, env files")
g.box("read", "read: schema, then types", tone="accent")
g.artifact("raw", "Raw Intent, with model paths")
g.box("link", "link: scope table", tone="accent")
g.artifact("linked", "Linked Intent")
g.box("check", "check: invariant table", tone="accent")
g.artifact("diag", "Diagnostic list", tone="bad")
g.artifact("checked", "Checked Intent")
g.box("lower", "lower", tone="accent")
g.artifact("eff", "EffectiveIntent")
g.box("compose", "compose", tone="accent")
g.artifact("set", "ComposedSet")
g.artifact("pinned", "PinnedInputSet")
g.box("resolve", "resolve, through the Trace", tone="accent")
g.artifact("res", "ResolvedDeployment")
g.box("render", "render crates", tone="accent")
g.artifact("del", "DeliverableSet")
g.box("ser", "serialize", tone="accent")
g.artifact("out", "renders in the canonical format")
for a, b in [("yaml", "read"), ("read", "raw"), ("raw", "link"), ("link", "linked"), ("linked", "check"),
             ("check", "checked"), ("checked", "lower"), ("lower", "eff"), ("eff", "compose"), ("compose", "set"),
             ("set", "resolve"), ("pinned", "resolve"), ("resolve", "res"), ("res", "render"), ("render", "del"),
             ("del", "ser"), ("ser", "out")]:
    g.edge(a, b)
g.edge("check", "diag", "read, link and check report", kind="dashed")
g.done()

g = Graph("rust-crates", "Rust: the compiler's crates and what each depends on", direction="DOWN")
g.package("cli", "bins/estate-kit", tone="accent")
g.package("svc", "service-app")
g.package("app", "compiler (use cases)")
g.group("steps", "step and render crates: none depends on another")
STEPS = {"read": "step-read", "check": "step-check", "lower": "step-lower", "compose": "step-compose",
         "resolve": "step-resolve", "outputs": "step-outputs", "render": "render-* (8 crates)", "serialize": "serialize"}
for crate, label in STEPS.items():
    g.package(crate, label, parent="steps")
g.package("models", "model-intent, model-effective, model-resolved", tone="data")
g.package("deliverable", "deliverable", tone="data")
g.package("foundation", "foundation: diagnostics, yaml-source, canonical, trace", tone="data")
g.edge("cli", "app", "depends on", kind="dashed")
g.edge("svc", "app", "links", kind="dashed")
for crate in STEPS:
    g.edge("app", crate, kind="dashed")
    g.edge(crate, "models", kind="dashed")
g.edge("render", "deliverable", "builds", kind="dashed")
g.edge("serialize", "deliverable", "writes", kind="dashed")
g.edge("models", "foundation", kind="dashed")
g.done()

g = Graph("rust-service-crates", "Rust: the service's crates and what each depends on", direction="DOWN")
g.package("bin", "bins/estate-kit-service", tone="accent")
g.package("api", "http-api: axum, SSE, problem+json")
g.package("obs", "observation-app")
g.package("app", "service-app: use cases, ports, fakes")
g.package("rollout", "rollout: the decider", tone="data")
g.package("gate", "release-gate", tone="data")
g.package("compiler", "compiler (use cases)", tone="data")
for crate, label in [("oidc", "adapter-github-oidc"), ("ghcr", "adapter-ghcr: oci-client"),
                     ("vault", "adapter-vault: Transit"), ("kube", "adapter-kube: kube-rs"),
                     ("github", "adapter-github: the App"), ("pg", "adapter-postgres: sqlx")]:
    g.package(crate, label)
g.edge("bin", "api", kind="dashed")
g.edge("api", "app", kind="dashed")
g.edge("api", "obs", kind="dashed")
g.edge("app", "rollout", kind="dashed")
g.edge("app", "gate", kind="dashed")
g.edge("app", "compiler", "links", kind="dashed")
for crate in ("oidc", "ghcr", "vault", "kube", "github", "pg"):
    g.edge("bin", crate, "wires", kind="dashed")
    g.edge(crate, "app", "implements a port of", kind="dashed")
g.done()

g = Graph("rust-layers", "Rust: the workspace's layers; every dependency points down", direction="DOWN", layer_gap=70)
g.box("binary", "binary: estate-kit, estate-kit-service, host applier, one per component", tone="accent")
g.box("adapter", "adapter: one outside system each; kube, sqlx, axum, oci-client live only here")
g.box("application", "application: use cases, port traits, one fake per port")
g.box("domain", "domain: models, steps, deciders, invariants; no I/O, no async, no clock")
g.box("foundation", "foundation: diagnostics, yaml-source, canonical, trace, reconcile, testkit", tone="data")
g.edge("binary", "adapter", "wires")
g.edge("adapter", "application", "implements ports")
g.edge("application", "domain", "drives")
g.edge("domain", "foundation", "uses")
g.edge("binary", "application", "calls", kind="dashed")
g.done()

g = Graph("alignment", "Alignment: how YAML, the schemas, the Rust types and the UI stay in step", direction="DOWN")
g.artifact("yaml", "authored YAML")
g.artifact("schemas", "committed JSON Schemas", tone="accent")
g.artifact("corpus", "accept and refuse corpus")
g.box("read", "step-read: validate, then convert")
g.box("types", "Rust model types")
g.artifact("openapi", "committed OpenAPI document", tone="accent")
g.box("api", "http-api routes")
g.box("ui", "Vue client, generated")
g.edge("yaml", "read", "read by")
g.edge("read", "schemas", "validates against")
g.edge("read", "types", "converts into")
g.edge("corpus", "schemas", "same verdict", kind="dashed")
g.edge("corpus", "types", "same verdict", kind="dashed")
g.edge("api", "openapi", "matches, by test", kind="dashed")
g.edge("openapi", "ui", "generates")
g.done()

g = Graph("flow-host-order", "Flow: deriving the node order for a host rollout", direction="DOWN", layer_gap=60)
g.terminal("start", "host rollout accepted")
g.decision("q", "k3s version changes?")
g.box("cp1", "control plane, in its window, after a snapshot and approval", tone="warn")
g.box("can1", "canary worker")
g.box("w1", "remaining workers")
g.box("can2", "canary worker")
g.box("w2", "remaining workers")
g.box("cp2", "control plane, in its window", tone="warn")
g.terminal("end", "every node current", tone="good")
g.edge("start", "q")
g.edge("q", "cp1", "yes")
g.edge("q", "can2", "no")
for a, b in [("cp1", "can1"), ("can1", "w1"), ("w1", "end"), ("can2", "w2"), ("w2", "cp2"), ("cp2", "end")]:
    g.edge(a, b)
g.done()

g = Graph("components", "Components: the parts of estate-kit (blue) and what each acts on", direction="DOWN", layer_gap=70)
# Declared in the order things flow: ELK reads an edge against that order as a back edge. No
# boundary groups the parts: draw.io lays a container out on its own, so edges that leave it
# would run backwards.
g.artifact("intent", "authored intent")
g.box("service", "service (Rust)", tone="accent")
g.box("compiler", "compiler crates (Rust)", tone="accent")
g.box("ui", "ui (Vue)", tone="accent")
g.box("applier", "host applier (Rust)", tone="accent")
g.artifact("renders", "renders, host data")
COMPONENTS = ("migration-runner", "secret-grant", "database-catalog", "bucket-catalog", "backup", "mail-provisioner")
for comp in COMPONENTS:
    g.box(comp, f"component: {comp}", tone="accent")
g.box("nodes", "NixOS nodes", tone="external")
g.edge("intent", "compiler", "reads")
g.edge("service", "compiler", "links")
g.edge("service", "ui", "serves")
g.edge("service", "applier", "host tags, pulled")
g.edge("compiler", "renders", "writes")
for comp in COMPONENTS:
    g.edge("renders", comp, "rendered objects")
g.edge("applier", "nodes", "switches")
g.done()

g = Graph("context-map", "Context map: the bounded contexts and how they relate")
g.box("compiler", "Compiler context: the model", tone="accent")
g.box("service", "Service context: rollouts", tone="accent")
g.box("observation", "Observation context: what runs", tone="accent")
g.box("applier", "Hosts context: generations", tone="accent")
g.box("components", "Component contexts: migrations, secrets, catalogs, backups, mail", tone="accent")
g.edge("compiler", "service", "use cases, in-process (customer, supplier)")
g.edge("service", "observation", "rollout events (published language)")
g.edge("compiler", "applier", "host data through an anticorruption layer")
g.edge("compiler", "components", "rendered objects")
g.done()

g = Graph("trust-boundaries", "Trust boundaries: what crosses each one, and with which credential")
g.group("internet", "internet", kind="trust")
g.box("runner", "GitHub runner", parent="internet")
g.box("browser", "operator's browser", parent="internet")
g.group("cluster", "cluster", kind="trust")
g.box("edge", "Traefik edge", parent="cluster")
g.box("svc", "estate-kit service", tone="accent", parent="cluster")
g.box("vault", "Vault", parent="cluster")
g.box("api", "Kubernetes API", parent="cluster")
g.group("host", "node", kind="trust")
g.box("node", "host applier", parent="host")
g.group("outside", "outside the cluster", kind="trust")
g.store("ghcr", "ghcr", parent="outside")
g.store("cache", "binary cache", parent="outside")
g.edge("runner", "edge", "GitHub OIDC JWT")
g.edge("browser", "edge", "auth-api session")
g.edge("edge", "svc", "TLS")
g.edge("svc", "vault", "service-account token")
g.edge("svc", "api", "service-account token")
g.edge("svc", "ghcr", "machine-account token")
g.edge("node", "api", "node identity")
g.edge("node", "cache", "Nix signature check")
g.done()

if __name__ == "__main__":
    write_all("raw")

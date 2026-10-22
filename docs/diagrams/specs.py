from gen import seq, uc, grid, cls, ACCENT, DATA, BAD, GOOD, WARN

# Use cases: one diagram per use case.
uc("uc1-validate", ["Application author", "Project CI"], "Validate a change",
   ["Validate offline", "Plan without the cluster", "Resolve model paths to lines"])
uc("uc2-dry-run", ["Project CI"], "Dry-run a release",
   ["Build candidate images", "Compose the estate", "Server-side apply dry-run"], side=[(2, "API server")])
uc("uc3-deploy", ["Project CI", "Environment approver"], "Deploy a release",
   ["Promote candidate digests", "Server-side apply dry-run", "Sign and move the prod tag", "Watch the rollout live"],
   side=[(2, "Vault Transit")])
uc("uc4-watch", ["Application author", "Operator"], "Watch the rollout live", ["Resume from the last event"])
uc("uc5-pause", ["Operator"], "Pause or resume a Project", ["Sign in through auth-api", "Write the Project object"])
uc("uc6-rollback", ["Operator"], "Roll back a Project",
   ["Sign in through auth-api", "Dispatch deploy in watch mode", "Server-side apply dry-run", "Sign and move the prod tag"],
   side=[(1, "GitHub")])
uc("uc7-admit", ["Admin"], "Admit a Project", ["Edit Platform Intent", "Derive the Flux source"])
uc("uc8-apply", ["Flux"], "Pull and apply a render", ["Verify the signature", "Apply and prune"], side=[(0, "ghcr")])
uc("uc9-gate", ["Flagger"], "Gate a traffic switch", ["Authenticate by SA token", "Check every Release Unit member"])

# Sequences: one interaction each.
seq("seq-deploy-1-admit",
    [("CI", "deploy job"), ("R", "Rust binary"), ("O", "ghcr"), ("S", "Service")],
    [("CI", "R", "validate offline", False), ("R", "CI", "no diagnostics", True),
     ("CI", "O", "promote digests, publish fragment", False), ("CI", "S", "deploy (GitHub OIDC token)", False),
     ("S", "CI", "rollout token, stream opens", True)])
seq("seq-deploy-2-dryrun",
    [("S", "Service"), ("R", "Rust binary"), ("K", "API server"), ("V", "Vault Transit"), ("O", "ghcr")],
    [("S", "O", "pull admitted fragments", False), ("S", "R", "compose the estate", False),
     ("R", "S", "renders, diagnostics", True), ("S", "K", "apply, dryRun=All", False),
     ("K", "S", "accepted", True), ("S", "V", "sign render", False), ("S", "O", "push render, move prod tag", False),
     ("K", "S", "rejected", True)],
    frames=[("alt", "dry-run accepted", 4, 7, ["S", "O"], 7)],
    notes=[(7, "V", "Project isolated, tag unchanged")])
seq("seq-deploy-3-switch",
    [("F", "Flux"), ("O", "ghcr"), ("K", "API server"), ("FG", "Flagger"), ("S", "Service"), ("CI", "deploy job")],
    [("F", "O", "pull prod tag, verify", False), ("F", "K", "apply", False),
     ("FG", "S", "Release Gate webhook", False), ("S", "FG", "promote when all healthy", True),
     ("S", "CI", "settled: serving or Held", True)])
seq("seq-dry-run",
    [("CI", "deploy job (dry-run)"), ("S", "Service"), ("K", "API server"), ("GH", "GitHub")],
    [("CI", "CI", "build candidate images", False), ("CI", "S", "deploy, dry-run (OIDC)", False),
     ("S", "K", "compose, apply dryRun=All", False), ("K", "S", "accepted or rejected", True),
     ("S", "CI", "diagnostics, render diff", True), ("CI", "GH", "annotations, check, summary", False)])
seq("seq-rollback",
    [("Op", "Operator"), ("S", "Service"), ("GH", "GitHub"), ("CI", "deploy job (watch)")],
    [("Op", "S", "roll back notes", False), ("S", "GH", "dispatch deploy", False),
     ("GH", "CI", "run starts", False), ("CI", "S", "watch (OIDC token)", False),
     ("S", "CI", "events until settled", True), ("CI", "GH", "Deployment status", False)])
seq("seq-auth",
    [("CI", "deploy job"), ("GO", "GitHub OIDC"), ("S", "Service")],
    [("CI", "GO", "ID token, aud estate-kit", False), ("GO", "CI", "JWT", True),
     ("CI", "S", "deploy, Bearer JWT", False), ("S", "S", "repository_id admitted?", False),
     ("S", "S", "pinned workflow, environment?", False), ("S", "CI", "rollout token", True)])
seq("seq-cache",
    [("S", "Service"), ("O", "ghcr"), ("R", "Rust binary")],
    [("S", "S", "render key from input digests", False),
     ("S", "O", "render with this key?", False), ("O", "S", "found: reuse it", True),
     ("S", "R", "not found: render this Project", False)])

# Deployment, split in two.
grid("deploy-placement",
     [("repo", "Project repos and runners", "", 0, 0), ("estate", "estate repo", "", 0, 1),
      ("ghcr", "ghcr: fragments, renders", DATA, 1, 0),
      ("edge", "Traefik edge", "", 2, 0), ("svc", "estate-kit service", ACCENT, 3, 0), ("pg", "Postgres", DATA, 4, 0),
      ("flux", "Flux", "", 2, 1), ("flagger", "Flagger", "", 3, 1), ("vault", "Vault", "", 4, 1), ("idp", "auth-api", "", 2, 2)],
     [],
     boxes=[("GitHub", 0, 0, 0, 1), ("Registry", 1, 0, 1, 0), ("Cluster", 2, 0, 4, 2)],
     cw=250, rh=130, w=200, h=56)
grid("deploy-in-cluster",
     [("pg", "Postgres event log", DATA, 0, 0), ("flagger", "Flagger", "", 1, 0), ("vault", "Vault Transit", "", 2, 0),
      ("svc", "estate-kit service", ACCENT, 1, 1), ("api", "API server", "", 2, 1), ("flux", "Flux", "", 3, 1),
      ("obj", "Project objects", "", 0, 2), ("idp", "auth-api", "", 2, 2)],
     [("flagger", "svc", "webhook"), ("svc", "api", "dry-run, read"), ("flux", "api", "applies"),
      ("svc", "vault", "sign", "exitX=1;exitY=0.15;entryX=0;entryY=0.5;"),
      ("svc", "idp", "sign-in", "exitX=1;exitY=0.85;entryX=0;entryY=0.5;"),
      ("svc", "pg", "appends", "exitX=0;exitY=0.15;entryX=1;entryY=0.5;"),
      ("svc", "obj", "writes", "exitX=0;exitY=0.85;entryX=1;entryY=0.5;")],
     cw=300, rh=140, w=200, h=56)

# States.
DOT = "ellipse;fillColor=#e8e8e8;"
grid("state-rollout",
     [("acc", "Accepted", "", 1, 0), ("comp", "Composing", "", 1, 1), ("dry", "DryRun", "", 1, 2),
      ("sig", "Signed", "", 1, 3), ("app", "Applying", "", 1, 4), ("sw", "Switching", "", 1, 5),
      ("srv", "Serving", GOOD, 1, 6), ("ref", "Refused", BAD, 2, 2), ("held", "Held", WARN, 2, 5)],
     [("acc", "comp", ""), ("comp", "dry", "render changed"), ("dry", "sig", "accepted"), ("sig", "app", "tag moved"),
      ("app", "sw", "Flux applied"), ("sw", "srv", "all healthy"),
      ("comp", "ref", "model error", "exitX=1;exitY=0.5;entryX=0.5;entryY=0;"),
      ("dry", "ref", "rejected"), ("sw", "held", "analysis failed"),
      ("comp", "srv", "render unchanged", "exitX=0;exitY=0.5;entryX=0;entryY=0.5;jettySize=60;")],
     cw=300, rh=120, w=180, h=56)
grid("state-project",
     [("rb", "RolledBack", "", 0, 0), ("act", "Active", "", 1, 0), ("pau", "Paused", "", 2, 0)],
     [("act", "pau", "pause", "exitX=1;exitY=0.3;entryX=0;entryY=0.3;"),
      ("pau", "act", "resume", "exitX=0;exitY=0.7;entryX=1;entryY=0.7;"),
      ("act", "rb", "roll back", "exitX=0;exitY=0.3;entryX=1;entryY=0.3;"),
      ("rb", "act", "next release", "exitX=1;exitY=0.7;entryX=0;entryY=0.7;")],
     cw=360, rh=110, w=180, h=64)
grid("context",
     [("ci", "Project CI", "", 0, 0), ("svc", "estate-kit service", ACCENT, 1, 0), ("ghcr", "ghcr", DATA, 2, 0),
      ("flux", "Flux", "", 3, 0), ("estate", "estate repo", "", 1, 1), ("work", "Project workloads", "", 3, 1)],
     [("ci", "svc", "deploy (OIDC)"), ("svc", "ghcr", "signed render, prod tag"), ("flux", "ghcr", "pulls"),
      ("estate", "svc", "Platform Intent"), ("flux", "work", "applies")],
     cw=430, rh=130, w=200, h=60)

# Inputs for each stage, and where each input comes from.
grid("inputs-compile",
     [("prepo", "Project repo", "", 0, 0), ("erepo", "estate repo", "", 0, 2), ("cl", "Cluster API", "", 0, 4),
      ("pyaml", "Project YAML, env files", DATA, 1, 0), ("frag", "Intent Fragment, digests sealed", DATA, 1, 1),
      ("pi", "Platform Intent, node contract", DATA, 1, 2), ("cs", "ClusterState snapshot", DATA, 1, 4),
      ("ver", "compiler version", DATA, 1, 3),
      ("validate", "validate (offline)", ACCENT, 2, 0), ("compose", "compose: read, check, lower, resolve", ACCENT, 2, 2),
      ("render", "adapters, serialize the ResolvedDeployment", ACCENT, 3, 2)],
     [("prepo", "pyaml", ""), ("pyaml", "validate", ""), ("pyaml", "frag", "publish"), ("frag", "compose", ""),
      ("erepo", "pi", ""), ("pi", "compose", ""), ("cl", "cs", ""), ("cs", "compose", ""), ("ver", "compose", ""),
      ("compose", "render", "")],
     cw=300, rh=110, w=240, h=60)
grid("inputs-deliver",
     [("render", "render from compose", DATA, 2, 0),
      ("api", "Cluster API", "", 1, 1), ("dry", "dry-run", ACCENT, 2, 1),
      ("vault", "Vault Transit key", "", 1, 2), ("sign", "sign, push, move prod tag", ACCENT, 2, 2),
      ("ghcr", "ghcr prod tag", DATA, 1, 3), ("apply", "Flux applies", ACCENT, 2, 3),
      ("events", "Flagger analysis, cluster events", DATA, 1, 4), ("switch", "switch and report", ACCENT, 2, 4)],
     [("render", "dry", ""), ("api", "dry", "dryRun=All"), ("dry", "sign", "accepted"), ("vault", "sign", "signs"),
      ("sign", "apply", ""), ("ghcr", "apply", "pulls"), ("apply", "switch", ""), ("events", "switch", "")],
     cw=380, rh=110, w=240, h=56)

# Rust pipeline: steps alternate with the typed model each produces.
grid("rust-pipeline",
     [("yaml", "YAML, env files", DATA, 1, 0), ("read", "read", ACCENT, 2, 0), ("src", "ProjectIntent, PlatformIntent", DATA, 3, 0),
      ("check", "check", ACCENT, 4, 0),
      ("pinned", "PinnedInputSet", DATA, 0, 1), ("resolve", "resolve", ACCENT, 1, 1), ("eff", "EffectiveIntent", DATA, 2, 1),
      ("lower", "lower", ACCENT, 3, 1), ("diag", "Diagnostic list", BAD, 4, 1),
      ("res", "ResolvedDeployment", DATA, 1, 2), ("adapt", "adapter crates", ACCENT, 2, 2), ("del", "DeliverableSet", DATA, 3, 2),
      ("ser", "serialize", ACCENT, 4, 2), ("out", "renders/, result.json", DATA, 4, 3)],
     [("yaml", "read", ""), ("read", "src", ""), ("src", "check", ""), ("src", "lower", ""), ("lower", "eff", ""),
      ("eff", "resolve", ""), ("pinned", "resolve", ""), ("resolve", "res", ""), ("res", "adapt", ""), ("adapt", "del", ""),
      ("del", "ser", ""), ("ser", "out", ""), ("check", "diag", "", "dashed=1;")],
     cw=250, rh=120, w=200, h=60)
grid("rust-crates",
     [("cli", "cli", ACCENT, 2, 0), ("app", "compose (use-cases)", "", 2, 1),
      ("read", "read", "", 0, 2), ("check", "check", "", 1, 2), ("lower", "lower", "", 2, 2), ("resolve", "resolve", "", 3, 2),
      ("adapters", "adapter-* (7 crates)", "", 4, 2), ("serialize", "serialize", "", 5, 2),
      ("model", "model", DATA, 2, 3), ("objects", "objects", DATA, 4, 3)],
     [("cli", "app", ""), ("app", "steps", "runs each step"), ("steps", "model", "every step depends on"),
      ("adapters", "objects", "builds"), ("serialize", "objects", "writes", "exitX=0.5;exitY=1;entryX=1;entryY=0.5;")],
     boxes=[("steps", "step crates (no step depends on another)", 0, 2, 5, 2)],
     cw=220, rh=150, w=180, h=56)
cls("rust-authored-model", [
    ("proj", "Project", None, ["name: ProjectName", "applications: BTreeMap&lt;ApplicationId, Application&gt;"], 0, 0),
    ("app", "Application", None, ["id: ApplicationId", "processes: BTreeMap&lt;ProcessName, Process&gt;", "exposures: Vec&lt;Exposure&gt;", "dependencies: Vec&lt;DependencyEdge&gt;"], 0, 1),
    ("proc", "Process", None, ["name: ProcessName", "image: ImageAlias", "lifecycle: Lifecycle", "surfaces, grants", "engine: Option&lt;Engine&gt;"], 0, 2),
    ("exp", "Exposure", None, ["host: Hostname", "audience: Audience", "routes: Vec&lt;Route&gt;"], 1, 0),
    ("edge", "DependencyEdge", None, ["to: ApplicationId", "surface: SurfaceName"], 1, 1),
    ("surf", "Surface", None, ["name: SurfaceName", "port: Port"], 1, 2),
    ("grant", "Grant", None, ["path: SecretPath", "tier: AccessTier", "delivery: Delivery"], 1, 3)],
    [("proj", "app", "1..*", "comp"), ("app", "proc", "1..*", "comp"),
     ("app", "exp", "*", "comp", "exitX=1;exitY=0.2;entryX=0;entryY=0.5;"), ("app", "edge", "*", "comp"),
     ("proc", "surf", "*", "comp"), ("proc", "grant", "*", "comp", "exitX=0.5;exitY=1;entryX=0;entryY=0.5;")],
    cw=480, rh=230)

cls("rust-pipeline-types", [
    ("pis", "PinnedInputSet", None, ["fragments: BTreeMap&lt;ProjectName, Pinned&lt;ProjectIntent&gt;&gt;", "platform: Pinned&lt;PlatformIntent&gt;", "cluster_state: Pinned&lt;ClusterState&gt;", "render_key(project) -&gt; RenderKey"], 0, 0),
    ("hasher", "Hasher", "trait", ["digest(&amp;[u8]) -&gt; Digest"], 1, 0),
    ("res", "ResolvedDeployment", None, ["applications: BTreeMap&lt;ApplicationId, ResolvedApplication&gt;", "trace: Trace"], 0, 1),
    ("adapter", "Adapter", "trait", ["render(&amp;ResolvedDeployment)", "  -&gt; Result&lt;Vec&lt;Deliverable&gt;, Vec&lt;Diagnostic&gt;&gt;"], 1, 1),
    ("del", "Deliverable", None, ["path: OutputPath", "object: KubeObject", "source: ElementRef"], 1, 2),
    ("diag", "Diagnostic", None, ["code: Code", "severity: Severity", "file: SourceFile", "path: ModelPath", "message, help"], 0, 2)],
    [("pis", "hasher", "digests via", "dep"), ("adapter", "res", "reads", "dep"),
     ("adapter", "del", "emits", "dep"), ("adapter", "diag", "or", "dep", "exitX=0;exitY=0.75;entryX=1;entryY=0.25;")],
    cw=560, rh=230)

grid("go-packages",
     [("api", "api: HTTP, SSE", ACCENT, 2, 0), ("ui", "ui: embedded Vue", "", 3, 0), ("auth", "auth: OIDC verifiers", "", 1, 0),
      ("rollout", "rollout: state machine, queue", "", 2, 1),
      ("compose", "compose: Rust binary", "", 0, 2), ("registry", "registry: oras-go", "", 1, 2),
      ("signer", "signer: Vault", "", 2, 2), ("cluster", "cluster: client-go", "", 3, 2), ("github", "github: App", "", 4, 2),
      ("store", "store: Postgres", DATA, 0, 1)],
     [("api", "auth", ""), ("api", "ui", ""), ("api", "rollout", ""), ("rollout", "compose", ""), ("rollout", "registry", ""),
      ("rollout", "signer", ""), ("rollout", "cluster", ""), ("rollout", "github", ""), ("rollout", "store", "")],
     cw=240, rh=130, w=200, h=56)

cls("go-rollout", [
    ("ev", "Event", None, ["RolloutID, Seq", "Type, At, Payload"], 0, 0),
    ("ro", "Rollout", None, ["ID, Project, Fragment", "State", "Apply(Event) Rollout"], 1, 0),
    ("es", "EventStore", "interface", ["Append(Event)", "Since(RolloutID, Seq)"], 2, 0),
    ("q", "Queue", None, ["Submit(Trigger) CompositionID", "single-flight, coalescing"], 1, 1),
    ("comp", "Composer", "interface", ["Compose(ctx, Inputs) Result"], 0, 2),
    ("reg", "Registry", "interface", ["FindRender(RenderKey)", "PushRender, MoveTag"], 1, 2),
    ("sig", "Signer", "interface", ["Sign(Digest) Signature"], 2, 2),
    ("cl", "Cluster", "interface", ["DryRun(objects) []Diagnostic", "WatchRelease(Project)"], 3, 2)],
    [("ro", "ev", "folds", "assoc"), ("ro", "es", "persists", "dep"), ("q", "ro", "starts", "assoc", "exitX=0.5;exitY=0;entryX=0.5;entryY=1;"),
     ("q", "comp", "", "dep", "exitX=0;exitY=0.5;entryX=0.5;entryY=0;"), ("q", "reg", "", "dep", "exitX=0.5;exitY=1;entryX=0.5;entryY=0;"),
     ("q", "sig", "", "dep", "exitX=0.8;exitY=1;entryX=0.5;entryY=0;"), ("q", "cl", "", "dep", "exitX=1;exitY=0.4;entryX=0.5;entryY=0;")],
    cw=380, rh=200)
grid("alignment",
     [("yaml", "Authored YAML", DATA, 1, 0),
      ("rust", "Rust serde types", "", 0, 1), ("schemas", "Committed JSON Schemas", ACCENT, 1, 1), ("go", "Go types (generated)", "", 2, 1),
      ("corpus", "Shared corpus: valid and invalid YAML", DATA, 1, 2),
      ("result", "compose-result schema", ACCENT, 1, 3)],
     [("yaml", "schemas", "validated by"), ("rust", "schemas", "drift test", "dashed=1;"), ("schemas", "go", "generates"),
      ("corpus", "rust", "runs through", "exitX=0;exitY=0.5;entryX=0.75;entryY=1;"),
      ("corpus", "go", "runs through", "exitX=1;exitY=0.5;entryX=0.25;entryY=1;"),
      ("rust", "result", "writes", "exitX=0.25;exitY=1;entryX=0;entryY=0.5;"),
      ("result", "go", "generates", "exitX=1;exitY=0.5;entryX=0.75;entryY=1;")],
     cw=400, rh=130, w=250, h=60)

# Hosts.
seq("seq-host-rollout",
    [("CI", "CI"), ("C", "binary cache"), ("S", "Service"), ("O", "ghcr"), ("A", "host applier"), ("K", "API server")],
    [("CI", "C", "push signed closures", False), ("CI", "CI", "VM test per node class", False),
     ("CI", "S", "host rollout (OIDC)", False), ("S", "O", "move host/&lt;node&gt;:prod", False),
     ("A", "O", "poll pointer, verify", False), ("A", "C", "fetch closure", False),
     ("A", "K", "take Lease, evict pods", False), ("A", "A", "switch; reboot only in window", False),
     ("A", "K", "uncordon, release Lease", False)])
grid("state-host-applier",
     [("idle", "Current", "", 1, 0), ("fetch", "Fetched", "", 1, 1), ("wait", "Waiting for Lease", "", 1, 2),
      ("drain", "Draining", "", 1, 3), ("switch", "Switching", "", 1, 4), ("reboot", "Awaiting window", WARN, 2, 4),
      ("check", "Health check", "", 1, 5), ("done", "Current (new)", GOOD, 1, 6), ("back", "Rolled back", BAD, 0, 5)],
     [("idle", "fetch", "new pointer"), ("fetch", "wait", "closure verified"), ("wait", "drain", "Lease held"),
      ("drain", "switch", "pods evicted"), ("switch", "check", "no reboot needed"), ("switch", "reboot", "kernel changed"),
      ("reboot", "check", "window opens", "exitX=0.5;exitY=1;entryX=1;entryY=0.5;"), ("check", "done", "healthy"),
      ("check", "back", "unhealthy")],
     cw=300, rh=110, w=200, h=56)
grid("inputs-host",
     [("ii", "Infrastructure Intent", DATA, 0, 0), ("pi", "Platform Intent", DATA, 0, 1), ("ver", "k3s and NixOS versions", DATA, 0, 2),
      ("comp", "compile: host data", ACCENT, 1, 1), ("mods", "hand-written NixOS modules", DATA, 2, 0),
      ("build", "CI: build closures, VM tests", ACCENT, 2, 1), ("cache", "signed binary cache", DATA, 2, 2),
      ("svc", "service: move host tags", ACCENT, 3, 1), ("agent", "host applier", ACCENT, 3, 2)],
     [("ii", "comp", "", "exitX=1;exitY=0.5;entryX=0.5;entryY=0;"), ("pi", "comp", ""),
      ("ver", "comp", "", "exitX=1;exitY=0.5;entryX=0.5;entryY=1;"),
      ("comp", "build", "host data"), ("mods", "build", ""), ("build", "cache", "pushes"), ("build", "svc", "passed"),
      ("svc", "agent", "host tag"), ("cache", "agent", "closure")],
     cw=320, rh=120, w=230, h=56)
seq("seq-mailbox",
    [("S", "Service"), ("F", "Flux"), ("K", "API server"), ("M", "mail provisioner"), ("ST", "Stalwart"), ("V", "Vault")],
    [("S", "F", "Project render with Mailbox objects", False), ("F", "K", "apply Mailbox", False),
     ("M", "K", "watch Mailboxes by label", False), ("M", "V", "read generated password", False),
     ("M", "ST", "create or update account", False), ("M", "K", "write status", False)])

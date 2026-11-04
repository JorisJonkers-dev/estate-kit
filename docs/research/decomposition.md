# Splitting estate-kit: use cases, domains and candidate services

> **Superseded in part, 2026-11-04.** A multi-model architecture evaluation
> reviewed this note. The maintainer then chose against three of its
> leanings:
>
> - **Flux stays the one applier**, observed closely, and an estate-kit Applier
>   (option B below) is built only if a measured review trigger fires.
> - **One repository at one version** stays, not three.
> - **The serverless host coordinator is dropped.** Each node runs its own host
>   applier.
>
> The service is now called Delivery, not the Conductor. The records that
> follow from the evaluation are rows 85 to 113 of
> [the register](../decisions/register.md). Read this note as the question,
> and the records as the answer.

Research note, 2026-11-03. It is not normative: where it disagrees with a
record, the record holds until a new record is written and accepted. The
questions came from the maintainer:

1. Does estate-kit become a god-project that does everything?
2. Should Flux stay, given that a deploy should be a two-way conversation that
   ends only when the rollout has fully ended?
3. Should Flagger stay, be watched more closely, or be replaced by our own
   switchover?
4. How do we watch a switchover live, in a terminal and in the deploy run?
5. How do we depend less on GitHub, with Tangled or a self-hosted forge behind
   the VPN as the likely destination?

The papers behind this note are in the private `papers/` submodule, sorted by
theme (see [Research](README.md#papers)). The themes that answer each question
below are listed under "Start from a question" in `papers/INDEX.md`. The course material it
draws on (Design of Software Architectures, Model-Driven Engineering, Modeling
and Analysis of Concurrent Systems, Service-Oriented Architecture) is in the
private coursework repository.

## Short answers

- **God-project.** The risk is real, but it sits in the repository and the
  version, not in the process. The design already runs seven kinds of process
  ([record 50](../decisions/0050-six-bounded-contexts-in-five-layers.md)); what it does not
  have is any contract between them that could outlive one repository. The
  remedy is a few products with published contracts, not many microservices.
  One maintainer gets none of the team-autonomy benefit that drives
  microservices, and pays all of their operating cost.
- **Flux.** The design already streams a rollout until the last Flagger
  promotion. It does so by watching Flux's status from outside, so the service
  learns late, by inference, and cannot say why Flux has not acted. Replacing
  Flux with an estate-kit applier gives the two-way conversation the
  maintainer asks for. It must stay a separate process with its own credential,
  or the security split of [record 17](../decisions/0017-delivery-runs-in-the-cluster-in-rust.md)
  is lost.
- **Flagger.** Keep it for now and watch it far more closely: its Canary
  status, its events and the metrics it reads. Write our own switchover only
  once the applier exists, and only for the parts Flagger cannot express, such
  as a whole Release Unit switching at once.
- **Live view.** One event stream with three readers: a terminal UI in
  `estate-kit watch`, plain grouped lines in CI logs, and the web UI. A CI log
  is not a terminal, so a full-screen TUI cannot run inside a GitHub or
  Forgejo job.
- **Host updates.** Build closures on own hardware with a warm Nix store, and
  run the coordinator as a scale-to-zero container at Scaleway, outside the
  cluster. It then survives the control-plane node's own update, no node can
  deploy another, and it costs about nothing inside the free tier.
- **Scale to zero.** Add Knative or KEDA to the existing k3s cluster rather
  than renting a functions service. Cold starts decide which Applications may
  idle, and spreading the control plane across providers is still unmeasured;
  see [A scale-to-zero layer on the cluster](#a-scale-to-zero-layer-on-the-cluster).
- **Forge.** About 195 lines of the design pages name GitHub or ghcr. Put the
  forge behind one port with an adapter per forge, and move renders off ghcr
  to a self-hosted registry. That also removes the classic-token problem the
  design review found.

## Three meanings of "split"

"Should this be microservices?" mixes three questions. Each has its own
criteria, and estate-kit answers them differently.

| Axis | Unit | What the design does today | What decides it |
| --- | --- | --- | --- |
| Code | Crate | About 70 crates in six contexts and five layers, held by `check-layers` ([record 50](../decisions/0050-six-bounded-contexts-in-five-layers.md)) | Information hiding (Parnas 1972); compile and mutation cost |
| Process | Binary and Deployment | CLI, service, Observation, host applier, six component binaries | Credential and trust boundary, failure isolation, where it must run |
| Repository | Repository and version | One repository at one version ([record 34](../decisions/0034-every-part-of-estate-kit-lives-in-this-repository-at-one-version.md)) | Rate of change, who consumes it, whether a contract can be kept |

The code axis is already well split. The process axis is split along the right
line, credentials. The repository axis is where the god-project grows: one
version means every part moves when any part moves, and nothing outside the
repository can depend on a stable piece of it.

### What the evidence says about microservices for one maintainer

- Conway's law and the mirroring hypothesis (MacCormack et al. 2012): a
  system's structure follows its organisation. With one maintainer, a split
  gains nothing on that side.
- Fritzsch et al. 2019 and the migration studies: teams split to scale
  development and deployment. The cost is distributed failure, network
  contracts and operations.
- The modular-monolith literature (Su and Li 2024) recommends strong modules
  in one deployable first, and splitting a module out only when a concrete
  force requires it.
- DDD's evidence base (Zhong et al. 2024, Özkan et al. 2025) supports bounded
  contexts as module boundaries far more than as process boundaries.

So the forces that justify a separate process here are not team forces. They
are: a different credential, a different place to run (a node, not the
cluster), a different availability need (serving must not depend on
deploying), and a contract that other code consumes.

## Actors and use cases

The catalogue below joins the use cases of [Releasing](../design/releasing.md),
[Hosts](../design/hosts.md), [Tenancy](../design/tenancy.md),
[Mail and components](../design/mail-and-components.md) and
[Operating](../design/operating.md), and adds the ones the maintainer's
questions raise (marked *new*).

| Actor | Use case | Context that owns it |
| --- | --- | --- |
| Application author | Validate a change: errors on YAML lines, render diff | Compiler |
| Application author | Dry-run a release against the live API server | Service |
| Application author | Deploy a release and see it end Serving, Held or Refused | Service |
| Application author | Watch a rollout live: phase, member, canary weight, gate answer | Service, read by every client |
| Application author | *new* Watch it in a terminal UI, locally or attached to a run | CLI |
| Application author | Generate App Roles in the Application's language | Compiler |
| Operator | Pause, resume and roll back a Project | Service |
| Operator | Act on a host's rollout: hold, skip, resume a node | Hosts |
| Operator | Read units, pods, logs, alerts; create and expire Silences | Observation |
| Operator | *new* See why the applier has not acted on a moved tag | Applier (today Flux, opaque) |
| Operator | Break glass when Vault is gone: sign with the Recovery key | Service, Hosts |
| Admin | Admit a Project; change Platform Intent | Service, Compiler |
| Admin | Change Infrastructure Intent: sites, nodes, maintenance windows | Compiler, Hosts |
| Admin | Create, lock, suspend, move, restore or purge a Tenant | Tenancy |
| Admin | *new* Move every Project to another forge without changing the model | Forge port |
| CI | Prove its identity and register the digests it built | Service |
| CI | Build host closures, run NixOS VM tests, push to the cache | Hosts (in CI) |
| Node | Pull its signed generation, take the Lease, cordon, drain, switch, decide a reboot, uncordon | Hosts (on the node) |
| Component | Reconcile secret grants, catalogs, backups, Mailboxes, migration runs | Components |
| Clock | Detect drift between the live tag and the latest release | Service |
| Clock | Run backups, mirrors and migration waves | Components, Tenancy |

## Subdomains

DDD's strategic split (Evans; the Context Mapper papers by Kapferer and
Zimmermann) sorts subdomains by how much they set estate-kit apart. Effort and
care go to the core; generic subdomains should be bought or kept thin.

| Subdomain | Kind | Changes when | Runs where | Credential it needs |
| --- | --- | --- | --- | --- |
| The model: Intent, linking, invariants, resolution | Core | The estate's vocabulary changes | Anywhere, offline | None |
| Kubernetes rendering | Supporting | A target object or adapter changes | Anywhere, offline | None |
| Nix host data rendering | Supporting | A host module changes | Anywhere, offline | None |
| Rollout orchestration and switchover | Core | The release procedure changes | In the cluster | Sign renders, move tags, dry-run |
| Applying objects | Generic (today Flux) | Rarely | In the cluster | Write to namespaces |
| Progressive delivery: canary and gate | Generic (today Flagger), with a core gate | The release procedure changes | In the cluster | Read metrics; route traffic |
| Host rollout: order, Lease, drain, reboot | Supporting | The node set or NixOS changes | Coordination in the cluster, act on each node | Sign host tags; cordon and evict |
| Platform components | Supporting | A platform system's API changes | In the cluster, one per system | Vault admin, Postgres admin, Garage, Stalwart |
| Tenancy | Supporting | Tenant operations change | In the cluster | Write Tenant resources |
| Observation | Supporting | A panel changes | In the cluster | Read only, plus Silences |
| Forge integration: identity, status, releases | Generic | The forge changes | In the cluster and in CI | Forge tokens |
| Signing and the registry | Generic | Rarely | In the cluster | Vault Transit, registry push |

Two subdomains are core, and they are the only two that should grow:
the model, and rollout orchestration. Everything else should stay thin and
replaceable. Today the forge and the registry are not thin: they reach into
records, design pages and five adapters.

## Criteria for a cut

Each candidate below is scored against the same criteria, taken from Parnas
(hide a decision likely to change), Service Cutter's coupling criteria
(Gysel et al. 2016: identity and lifecycle, consistency, security, volatility,
availability) and the quality scenarios of the
[design review](review/scenarios.md).

1. **Trust.** Does it hold a credential no other part should share an address
   space with?
2. **Place.** Must it run somewhere the others do not (a node, CI, offline)?
3. **Availability.** Must it keep working while another part is down?
4. **Volatility.** Does it change at a different rate, for a different reason?
5. **Contract.** Can its interface be written down and kept stable, so that a
   separate version is safe?
6. **Consumers.** Does anything outside estate-kit want it on its own?

A cut that meets only criterion 4 is a crate, not a process. A cut that meets
5 and 6 can be a repository.

## Candidate products

Ten products, grouped by the repository they would live in. The names are
working names for this note; a product that is adopted gets its term in
[`CONTEXT.md`](../../CONTEXT.md) first.

| # | Product | Owns | Kind | Trust | Place | Avail. | Contract | Repository |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | **Model** (`estate-model`) | Read, check, lower, compose, resolve: Intent to Resolved Deployment, with diagnostics | Library and CLI | – | Offline | – | The schemas and the Resolved Deployment | Own repository |
| 2 | **Kubernetes back end** | The eight renderers and the serializer: Resolved Deployment to a Deliverable Set | Library | – | Offline | – | Deliverable Set and canonical YAML | With the model at first |
| 3 | **Nix back end** | Host data from Infrastructure Intent and the Resolved Deployment | Library | – | Offline | – | Host data attribute set | With the model at first |
| 4 | **Conductor** | Rollouts, compositions, admission, Pause and Rollback, the Release Gate, the event stream | Service | Signing, tags, dry-run | Cluster | Deploy path | OpenAPI and the event schema | estate-kit |
| 5 | **Applier** | Pull a signed render, verify, server-side apply, prune, report per object | Controller | Write to namespaces | Cluster | Serving path | A desired-render resource and its status | estate-kit |
| 6 | **Switchover** | Canary steps, traffic weights, analysis; today Flagger plus the Gate | Controller | Traffic routes | Cluster | Deploy path | Canary status | Flagger now; estate-kit later, if ever |
| 7 | **Host builder, conductor and agent** | Build and test closures; decide node order and windows; on each node, cordon, drain, switch, reboot | Three deployables: a builder on own hardware, a conductor off the cluster, an agent on each node | Closure key; Host signing key; the node's own cordon and eviction | Outside the cluster, and on each node | Must work while the cluster's one control-plane node updates | Signed host tag and host data schema | Own repository, beside nix-config |
| 8 | **Components** | Six reconcilers over rendered resources | Controllers | One system's admin each | Cluster | Independent | Custom-resource schemas | estate-kit, or one repository for all six |
| 9 | **Observation** | Read views and Silences | Service | Read only | Cluster | Independent | Service API, read | estate-kit |
| 10 | **Forge bridge** | Identity of CI calls, deployment status, releases, checks, per forge | Adapters behind one port | Forge tokens | Cluster and CI | – | The port | estate-kit |

Tenancy stays inside the Conductor's binary as
[record 80](../decisions/0080-a-tenant-is-a-custom-resource-in-a-sixth-bounded-context-tenancy.md)
decides; nothing in the criteria argues for moving it.

### What changes, and what stays

- **The Model leaves first.** It meets every repository criterion: no
  credential, runs offline, has a written contract (the schemas, oracles and
  corpus) and has consumers outside the service: every Project's CI, editors
  through a language server later, and the shadow comparison. Splitting it
  out also stops the service's needs from leaking into the model. It would
  reverse [record 34](../decisions/0034-every-part-of-estate-kit-lives-in-this-repository-at-one-version.md)
  for one seam only, and the price is the compatibility matrix that record
  avoided: the Conductor must say which model versions it accepts. The render
  key already carries the compiler version, so provenance survives.
- **The two back ends stay with the Model** until a third target appears. They
  are where the MDE course's model-to-text lessons apply, and they share the
  Resolved Deployment.
- **The host side leaves second.** It must work when the cluster and the
  compiler are down, it runs on NixOS, and it is consumed by nix-config. Its
  contract is the signed host tag and the host data schema. It splits into
  three deployables in three places; see
  [Host updates outside the cluster](#host-updates-outside-the-cluster).
- **The Conductor and the Applier stay together in estate-kit**, as two
  processes. They change together, because the rollout protocol between them
  is the core of the product.
- **The components stay** for now. Six reconcilers over a shared `reconcile`
  step is a family, not six products. Revisit if one of them gains a consumer
  outside the estate.

The result is three repositories instead of one: `estate-model` (with both
back ends), `estate-kit` (Conductor, Applier, components, Observation, forge
bridge, CLI, UI) and the host agent. Each keeps the crate and layer rules it
has today.

## The deploy path without Flux

### What the maintainer wants

A deploy run opens a conversation with the Conductor and keeps it open until
the rollout has ended: every object applied, every member switched, the old
version scaled down, or the rollout Held or Refused, with the reason. The run
fails only for a real failure and never ends early.

### What the design does today

The deploy job already holds an SSE stream until the last Flagger promotion
([Releasing](../design/releasing.md)). The service moves the tag and then
watches Kustomization, OCIRepository and Canary status to infer what Flux and
Flagger did ([Inside the service](../design/inside-delivery.md#what-it-reads-from-the-cluster)).
That has four costs:

1. **Latency.** Flux sees a moved tag on its interval or on a Receiver call,
   not when the tag moves.
2. **Opacity.** A Kustomization reports one condition for a whole render. Why
   one object failed, or why nothing has happened yet, is in Flux's logs, not
   in the rollout's events.
3. **Two state machines.** Flux, Flagger and the rollout each have their own
   states. The rollout's state is an inference from the other two.
4. **Ordering.** Migration Jobs, Release Units and Tenant waves need steps in
   a defined order. Flux's `dependsOn` and health checks express some of it,
   and the Release Gate and the suspended migration Job work around the rest.

### Options

| Option | How the conversation works | Cost | Keeps |
| --- | --- | --- | --- |
| A. Keep Flux, drive and watch it closer | The Conductor calls a generic Receiver right after the tag move, then streams Kustomization inventory and per-object health, and Canary status | Opacity and two state machines remain | [Record 2](../decisions/0002-kubernetes-is-the-substrate-and-flux-is-the-one-applier.md) as it is |
| B. An estate-kit Applier, in its own process | The Conductor writes a desired-render resource; the Applier pulls and verifies the signed render, applies in steps, and writes per-object status and events the Conductor folds into the rollout | A second program to write: pruning, drift, inventory, field ownership | One applier, signed pull, the credential split |
| C. The Conductor applies | One process does everything | The signing and tag credentials share an address space with a write-everything credential | Nothing of the security split |
| D. CI pushes | The deploy job applies | A deploy credential outside the cluster | Nothing of [record 58](../decisions/0058-flux-is-locked-down-per-project-and-delivery-dry-runs-as-an-identity-that-cannot-write.md) |

C and D are what [record 2](../decisions/0002-kubernetes-is-the-substrate-and-flux-is-the-one-applier.md)
already rejects, and the reasons still hold. B is the option the record left
open: "The signed artifact is the seam, so a later record could replace Flux
without touching the compiler."

### Option B in more detail

- **Push to trigger, pull to verify.** The Conductor never sends objects. It
  writes a small resource naming the Project, environment and render digest.
  The Applier pulls that digest from the registry, verifies its signature
  against the Render signing key and the Recovery key, and only then applies.
  So the Applier keeps Flux's property that only signed renders cross into
  the cluster.
- **One applier still.** The Applier replaces Flux; it does not sit beside it.
  It runs with Flux's per-Project identities of
  [record 58](../decisions/0058-flux-is-locked-down-per-project-and-delivery-dry-runs-as-an-identity-that-cannot-write.md),
  and the Conductor keeps its dry-run-only identity.
- **Steps, not one apply.** The render already says what must happen in
  order: CRDs and namespaces, then secrets and grants, then migration Jobs,
  then workloads, then routes. The Applier applies step by step and reports
  each step, so the Release Gate's migration unsuspend becomes an ordinary
  step instead of a named write.
- **Events the Conductor can fold.** Each apply, prune, health change and
  failure is a status entry with a sequence number. The Conductor turns them
  into Rollout events, so the rollout's state is the fold of what the Applier
  saw, not a guess.
- **Libraries, not a rewrite.** `kube-rs` has server-side apply. Pruning by an
  inventory in the resource's status is how Flux does it (`fluxcd/pkg/ssa`)
  and is well described; it is the hardest part, and the shadow composition
  can compare the Applier's inventory with Flux's before the cutover.
- **What it costs.** Drift correction, pruning, health checks for every kind
  and the lockdown are now our code, our tests and our bugs. The kube
  controller testing papers already in `papers/` (Sieve, Acto, Anvil) describe
  how such controllers fail, and the
  [end-to-end test record](../decisions/0069-the-deploy-path-is-tested-end-to-end.md)
  would have to cover it.

### Flagger

Flagger is a second state machine the rollout must infer. Three ways forward:

1. **Keep it and watch it closely** (now). Stream Canary status, the analysis
   metrics it reads, its events and the Gate's answers as Rollout events. The
   design review found its confirm-promotion hook retries rather than fails
   ([delivery and GitOps](review/delivery-and-gitops.md)), so it is safe to
   keep.
2. **Drive it from the Applier** (with option B). The Applier treats a Canary
   as one step and waits for it to end.
3. **Our own switchover** (later, only if needed). Flagger switches one
   workload. A Release Unit switches several members together, which the
   Release Gate approximates by holding each member until all are ready. A
   switchover step in the Applier, using Traefik's weighted routes directly,
   could do that natively. The decider pattern the design already uses makes
   the canary's steps a pure function, testable like the rollout itself.

Recommendation: 1 now, 2 with the Applier, and 3 only when a Release Unit
scenario fails under Flagger.

### Proving the protocol

The conversation between CI, Conductor, Applier and switchover is a
concurrent protocol, and the design's claim that "a rollout ends in exactly
one of Serving, Held or Refused" is a liveness property. The Modeling and
Analysis of Concurrent Systems course gives the tools: write the protocol as
timed automata in UPPAAL, with crashes, a dropped stream and a lost Lease as
environment moves, and check `A[] not deadlock` and that every rollout
eventually reaches an end state. That model would sit beside the decider's
tests, the way the oracles sit beside the compiler.

## Host updates outside the cluster

The maintainer asked whether host updates could run in a serverless service
at Scaleway or OVHcloud, managed from the provider's web console, so that the
coordinator never moves between nodes and no node holds the right to deploy
to the others. Cost decides it: host updates are rare, Rust idles low, and
the expensive part is the periodic Nix build.

### Why move the coordinator off the cluster

- **The one control plane.** The cluster has one control-plane host
  ([record 1](../decisions/0001-one-maintainer-one-cluster-one-estate.md)).
  While that node switches or reboots, anything that runs in the cluster,
  including the service that moves host tags today, is down. A coordinator
  outside the cluster keeps its view of the rollout through that window.
- **No node deploys another.** Each node's agent pulls only its own signed
  host tag and cordons and drains only itself. The right to move a host tag
  sits in one place, outside every node.
- **Nothing to move.** A coordinator that scales to zero has no node to be
  evicted from.

### Three parts in three places

| Part | Where | What it holds | When it runs |
| --- | --- | --- | --- |
| Builder | Own hardware: a VPS or a home server with KVM | The closure signing key; the binary cache's write key | When nix-config or host data changes, and on a schedule for nixpkgs updates |
| Conductor | Scaleway Serverless Containers or Jobs | The Host signing key, or the right to use it; the host-tag credential | On a webhook from the builder, and on a cron inside each Maintenance window |
| Agent | Each node | Its own node's cordon and eviction rights | Polls its host tag; reports progress to the Conductor |

The Conductor does not call the Kubernetes API. Each agent cordons and drains
its own node with a credential limited to that node, and reports each step to
the Conductor. The Conductor decides node order, one node at a time, from
those reports and from Infrastructure Intent, and moves the next tag. Host
tags and closures must then live outside the cluster too, in a registry and a
binary cache the control-plane node does not serve; otherwise updating that
node takes down its own source.

### Where the builds run

Builds stay on own hardware. A NixOS closure with its build inputs is larger
than the 10 GB of ephemeral disk a Scaleway Serverless Job gets, a job has no
`/nix/store` that survives between runs, so every build starts by downloading
its inputs again, and NixOS VM tests need KVM, which a serverless job does
not offer. A VPS or home server with a warm store builds incrementally in
minutes, and the hardware is already paid for. It pushes signed closures to
the binary cache (Attic, or a plain store on object storage), and the agents
pull from there, as [record 31](../decisions/0031-host-closures-are-built-in-ci-and-cached-outside-the-cluster.md)
already plans for CI.

### Cost

Scaleway's documentation gives Serverless Jobs and Containers a free tier of
200,000 vCPU-seconds and 400,000 GB-seconds per account per month, with jobs
of up to 6 vCPU, 16 GB of memory, 10 GB of ephemeral disk and 24 hours, and
cron triggers. Paid rates differ between its own pages (around €1.00 per
100,000 vCPU-seconds), so check the console before relying on them.

| Item | Estimate | Monthly cost |
| --- | --- | --- |
| Conductor, scale to zero | 0.5 vCPU, 512 MB, about 10 minutes per host update, a few updates a month | Inside the free tier: about €0 |
| Conductor kept warm instead | 0.25 vCPU and 512 MB always on: about 650,000 vCPU-seconds and 1,300,000 GB-seconds | About €5 to €9 above the free tier, depending on which memory rate applies, so do not keep it warm |
| Builds in Serverless Jobs instead of own hardware | 6 vCPU for one hour is 21,600 vCPU-seconds | Nine such hours fit the free tier, but the 10 GB disk and the missing KVM rule it out |
| Builder on own hardware | Already running | No new cost |
| Registry and binary cache outside the cluster | A few GB of closures and tags | Object storage at cents per GB per month; check current rates |

OVHcloud has no serverless functions or containers offer that this search
found, and it announced price rises of about 9 to 11% on new public-cloud
deployments for 2026 to 2028. On OVHcloud the Conductor would be a small VPS,
a few euros a month, and one more host to patch. Scaleway is the better fit,
and both its Serverless Containers and Jobs are managed from its web console.

### What it changes

- The Hosts context becomes its own product with three deployables, which
  strengthens the case for its own repository.
- The Host signing key moves out of the in-cluster Vault, or the Conductor
  needs a route to it. That reopens
  [record 21](../decisions/0021-renders-and-host-tags-are-signed-by-separate-keys-with-an-offline-recovery-key.md)
  and [record 30](../decisions/0030-a-host-applier-on-each-node-pulls-its-signed-host-tag.md),
  both still Proposed. One option keeps the key in Scaleway's key manager,
  used only by the Conductor; the agents trust that key and the Recovery key.
- The cluster's Lease no longer orders the nodes; the Conductor does. A lost
  Conductor stops new host updates and leaves every node on its current
  generation, which is safe.

### A scale-to-zero layer on the cluster

The serverless half of the question has a cheaper answer than a provider's
functions service: add a scale-to-zero layer to the k3s cluster the estate
already runs. Knative Serving (with Kourier) or KEDA (with its HTTP add-on)
installs beside the existing workloads. For an Application that declares it
may idle, the compiler would emit a Knative Service, or a KEDA scaler beside
its Deployment, instead of a plain Deployment. A practitioner recipe for this
set-up was checked against the literature on 2026-11-03
(`papers/notes/k3s-serverless-recipe-evidence.md`): of its 28 claims, 10 are
supported, 11 qualified, 7 untested and none contradicted. What matters for
estate-kit:

- **The layer itself is sound.** Request-driven autoscaling and scale to zero
  on self-hosted Kubernetes are well studied, and k3s is a fit for small nodes.
- **Cold starts decide which Applications may go to zero.** The JVM is the
  worst case among common runtimes. GraalVM native images start in
  milliseconds, but builds are slow and reflection is limited. CRaC and CRIU
  snapshots help most when taken after warm-up. Keeping one replica gives up
  the saving. A shared pre-warmed pool is a middle way. A Kotlin service
  therefore needs a native build or a snapshot before it may idle.
- **Image pulls dominate cold start.** Small images, and a registry or
  pull-through cache inside the estate, cut it. This argues again for the
  self-hosted registry in [The registry](#the-registry).
- **Spreading across providers is the least proven part.** A Raft quorum pays
  the round trip between providers on every write, and no peer-reviewed study
  measures etcd or kine over such links. kube-vip and MetalLB move a virtual IP
  only inside one provider's network. DNS works across providers but resolvers
  can hold stale records. Replicated block storage across providers pays the
  round trip on every write. Measure on the estate before putting the control
  plane or storage across providers. Until then, keep the control plane and
  replicated storage inside one provider, and let only stateless work cross.

## Watching a switchover live

| Reader | Where | Shape |
| --- | --- | --- |
| `estate-kit watch <rollout>` | A terminal | Full-screen view: members, step, canary weight, metric against threshold, Gate answer, last events |
| The same command, without a terminal | A CI job | One line per event, grouped per step (`::group::` on GitHub, the equivalent on Forgejo), and a summary at the end |
| The web UI | A browser | The same view as the terminal one |

All three read one event stream from the Conductor's API, resumed by sequence
number, which the design already has. The terminal view is a `ratatui` front
end on that stream. It switches to line mode when standard output is not a
terminal, so the deploy job runs the same command. A full-screen interface
cannot render in a CI log: the log is not a terminal and does not support
cursor movement. A run can link to the live UI page instead.

## Depending less on GitHub

### Where GitHub is in the design today

| Coupling | Where |
| --- | --- |
| CI identity: GitHub's OIDC token and its claim policy (`repository_id`, `job_workflow_ref`, environment) | `adapter-github-oidc`, [record 8](../decisions/0008-an-image-digest-is-sealed-into-the-fragment-and-registered-by-its-build.md) |
| Rollout visibility: GitHub Deployments in `production`, check runs | `adapter-github`, [Releasing](../design/releasing.md) |
| Approval: the production environment's required reviewers | GitHub environments |
| Release trigger: release-please pull requests and releases | Every Project's workflows |
| Registry: renders and host tags on ghcr, moved with a classic token | `adapter-ghcr`, [record 9](../decisions/0009-the-live-render-is-a-signed-registry-tag-per-project-and-environment.md) |
| Reusable workflows | The pinned estate-kit workflows |
| Admission: Projects named by `repository_id` | Platform Intent |

### The port

One port, `Forge`, with the operations the Conductor needs, and one adapter
per forge:

- **Verify a CI caller**: an OIDC token, or a signed request, mapped to a
  Project and an environment.
- **Report a rollout**: create, update and end a deployment record, or a
  commit status where the forge has no deployments.
- **Read a release**: the latest release of a Project, for the drift check.
- **Name a repository**: a stable id that survives renames and moves.

The design's names already hint at this: Admitted Project is "a Project whose
repository, named by its `repository_id`…". A forge-neutral repository id is
the one model change.

### The forges

| Forge | Fit | To check before choosing |
| --- | --- | --- |
| GitHub | Today's adapter | – |
| Forgejo, self-hosted behind the VPN | Actions are close to GitHub's; commit statuses; releases; can sit behind Traefik with forward-auth to auth-api | Whether its Actions issue OIDC tokens with the claims the claim policy needs; it has no Deployments API, so the rollout is reported as a commit status and a UI link |
| Tangled | Git hosting on AT Protocol: repositories live on knots (which can be self-hosted), CI on spindles | Private repositories are not yet supported; CI identity and status reporting have to be designed with it |

### The registry

Moving renders and host tags from ghcr to a self-hosted OCI registry (for
example Zot or Harbor) behind the edge removes three problems at once: the
classic machine token that cannot be scoped
([delivery and GitOps](review/delivery-and-gitops.md)), mutable tags with no
compare-and-swap, and ghcr as an outage dependency for rollback. Images built
by Projects can stay on whichever registry their forge offers. The registry
then becomes a dependency of the estate it serves, so its storage and restore
belong with the datastore backup of
[record 59](../decisions/0059-vault-unseal-and-datastore-backup-are-assumed-from-fleet-infra.md).

## What the course material adds

- **Design of Software Architectures.** The DataForge architecture
  description used arc42 with ISO 25010 quality-attribute scenarios, a utility
  tree and decision records. The design review of 2026-10-22 already follows
  that method. This note's cut criteria are the same quality attributes
  (Barbacci et al. 1995; Bass, Clements and Kazman 2021), applied to the
  question of where a boundary goes. Kruchten's 4+1 views (1995) map onto the
  three axes above: the development view is the crate and repository axes, the
  process and physical views are the process axis. Execution viewpoints
  (Callo Arias et al. 2009) are how the deploy path across the cluster, the
  nodes and Scaleway should be drawn.
- **Model-Driven Engineering.** Context Mapper (Kapferer and Zimmermann 2021)
  models bounded contexts and their relations in a DSL and suggests
  decompositions through architectural refactorings; Service Cutter scores
  them. The 2026 guest lecture (Nguyen, from her UT thesis) turned domain and
  behaviour models into microservice code. Both support the shape above: the
  model is the core and the code around it is generated or thin.
  The model as its own product is also the lesson of the MDE project behind
  [Transformations without a DSL](../design/transformations.md): a metamodel
  held by oracles outlived both implementations written against it.
- **Modeling and Analysis of Concurrent Systems.** The rollout protocol is a
  concurrent system with timing, so it can be modelled in UPPAAL and its end
  states checked, as above.
- **Service-Oriented Architecture.** Two of the course's exam papers speak
  to this note directly. Vučković (2020), "You Are Not Netflix", argues that a
  small organisation copying large-company microservices pays their cost
  without their benefit: the one-maintainer argument above. Megargel et al.
  (2021) give a decision framework for orchestration, where a conductor drives
  each step, against choreography, where services react to each other's
  events. Flux and Flagger reacting to a moved tag is choreography; the
  Applier of option B with the Conductor is orchestration, which the framework
  favours when one process must know the state of the whole flow and decide on
  failure. Knoche and Hasselbring (2018) and Balalaie et al. (2016) describe
  incremental migrations, the way deploy-kit hands over to estate-kit, and
  Neri et al. (2020) list the smells to test each proposed boundary against,
  such as shared persistence. The SOA project's own lesson was a live
  telemetry view over WebSocket through a gateway, beside asynchronous work
  over a queue: the same split as the event stream here.

## Records this note would need

None of this binds until a record is written and accepted. In reading order:

1. The Model is its own repository and version, and the Conductor names the
   model versions it accepts (amends
   [record 34](../decisions/0034-every-part-of-estate-kit-lives-in-this-repository-at-one-version.md)).
2. An estate-kit Applier replaces Flux, in its own process, pulling and
   verifying signed renders (supersedes
   [record 2](../decisions/0002-kubernetes-is-the-substrate-and-flux-is-the-one-applier.md)
   and amends [record 17](../decisions/0017-delivery-runs-in-the-cluster-in-rust.md)).
3. A rollout is reported through a Forge port, and Projects are named by a
   forge-neutral repository id (amends
   [record 8](../decisions/0008-an-image-digest-is-sealed-into-the-fragment-and-registered-by-its-build.md)).
4. Renders and host tags live on a self-hosted registry (amends
   [record 9](../decisions/0009-the-live-render-is-a-signed-registry-tag-per-project-and-environment.md)).
5. Flagger stays, and its Canary status, analysis and events are Rollout
   events.
6. The host side is its own repository, beside nix-config: a builder on own
   hardware, a scale-to-zero Conductor at Scaleway, and an agent on each node
   (amends [record 30](../decisions/0030-a-host-applier-on-each-node-pulls-its-signed-host-tag.md)
   and [record 31](../decisions/0031-host-closures-are-built-in-ci-and-cached-outside-the-cluster.md)).
7. The rollout protocol is modelled in UPPAAL, and a check runs it.

## Sources

Papers are in the private `papers/` submodule, in theme folders whose
`INDEX.md` gives the DOI of each, a summary, and whether it was downloaded. The
ones this note leans on most:

- Parnas, D. L. (1972). On the criteria to be used in decomposing systems into
  modules. *Communications of the ACM* 15(12).
- Conway, M. E. (1968). How do committees invent? *Datamation* 14(4).
- MacCormack, A., Baldwin, C., Rusnak, J. (2012). Exploring the duality
  between product and organizational architectures. *Research Policy* 41(8).
- Gysel, M., Kölbener, L., Giersche, W., Zimmermann, O. (2016). Service
  Cutter: a systematic approach to service decomposition. ESOCC 2016.
- Kapferer, S., Zimmermann, O. (2021). Domain-driven architecture modeling
  and rapid prototyping with Context Mapper. MODELSWARD 2020, CCIS 1361.
- Su, R., Li, X. (2024). Modular monolith: is this the trend in software
  architecture?
- Auer, F., Lenarduzzi, V., Felderer, M., Taibi, D. (2021). From monolithic
  systems to microservices: an assessment framework. *Information and
  Software Technology* 137.
- Schermann, G., Schöni, D., Leitner, P., Gall, H. C. (2016). Bifrost:
  supporting continuous deployment with automated enactment of multi-phase
  live testing strategies. Middleware 2016.
- Grubic, B., et al. (2023). Conveyor: one-tool-fits-all continuous software
  deployment at Meta. OSDI 2023.
- Li, Z., et al. (2020). Gandalf: an intelligent, end-to-end analytics
  service for safe deployment in cloud-scale infrastructure. NSDI 2020.
- Gu, J. T., et al. (2023). Acto: automatic end-to-end testing for operation
  correctness of cloud system management. SOSP 2023.
- Kleppmann, M., et al. (2024). Bluesky and the AT Protocol: usable
  decentralized social media.

Course readings, in the private course-material repositories:

- Kruchten, P. B. (1995). The 4+1 view model of architecture. *IEEE
  Software* 12(6).
- Barbacci, M., Klein, M. H., Longstaff, T. A., Weinstock, C. B. (1995).
  *Quality Attributes*. CMU/SEI-95-TR-021.
- Callo Arias, T. B., America, P., Avgeriou, P. (2009). Defining execution
  viewpoints for a large and complex software-intensive system. WICSA/ECSA
  2009.
- Bass, L., Clements, P., Kazman, R. (2021). *Software Architecture in
  Practice*, 4th ed. Addison-Wesley.
- Vučković, J. (2020). You are not Netflix. In *Microservices: Science and
  Engineering*, Springer.
- Megargel, A., Poskitt, C. M., Shankararaman, V. (2021). Microservices
  orchestration vs. choreography: a decision framework. EDOC 2021.
- Knoche, H., Hasselbring, W. (2018). Using microservices for legacy software
  modernization. *IEEE Software* 35(3).
- Balalaie, A., Heydarnoori, A., Jamshidi, P. (2016). Microservices
  architecture enables DevOps: migration to a cloud-native architecture.
  *IEEE Software* 33(3).
- Neri, D., Soldani, J., Zimmermann, O., Brogi, A. (2020). Design principles,
  architectural smells and refactorings for microservices: a multivocal
  review. *SICS Software-Intensive Cyber-Physical Systems* 35(1-2).

Web sources, read 2026-11-03:

- [Flagger webhooks](https://docs.flagger.app/usage/webhooks)
- [OpenGitOps principles](https://opengitops.dev/)
- [Scaleway Serverless Jobs limitations](https://www.scaleway.com/en/docs/serverless-jobs/reference-content/jobs-limitations/)
- [Scaleway Serverless Jobs FAQ](https://www.scaleway.com/en/docs/serverless-jobs/faq/)
- [Scaleway serverless pricing](https://www.scaleway.com/en/pricing/serverless/)
- [Tangled](https://tangled.org/)

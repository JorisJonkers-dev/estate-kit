# estate-kit vocabulary

The terms estate-kit adds to, or changes in,
[deploy-kit's vocabulary](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/CONTEXT.md).
deploy-kit's terms keep their meaning until this file says otherwise. They
move here when deploy-kit is imported.

## Delivery

**Admitted Project**:
A Project whose repository, named by its `repository_id`, Platform Intent lists as allowed to deploy.
_Avoid_: participant, registered project

**Prod tag**:
The signed registry tag `render/<project>:prod` that names a Project's current render. One tag per environment; `prod` is the only one.
_Avoid_: pin, live tag

**Render key**:
The digest of everything a Project's render depends on: its fragment, Platform Intent, the ClusterState snapshot, the compiler version, and the Surface declarations that Link reads from other Projects (each Surface its Applications consume or route to: its name, its port and the Project and Application that provide it). A change to a provider's Surface therefore changes the Render key of every Project that consumes it. It is kept as provenance with each published render and is never a cache key. It is not the key that signs: that is the Render signing key.
_Avoid_: cache key, input hash, signing key

**Render signing key**:
The Vault Transit key that signs `render/<project>:prod`. Flux verifies renders against it. The service's Vault policy may use it only for that path; it never signs a host tag.
_Avoid_: render key, Transit key

**Host signing key**:
The Vault Transit key that signs `host/<node>:prod`. Host appliers verify host tags against it. It never signs a render.
_Avoid_: host key, Transit key

**Recovery key**:
The hardware-held key, kept offline, that Flux and every Host applier trust beside the online signing keys. It signs only in a break-glass, when Vault is gone.
_Avoid_: backup key, root key

**Serving**:
The outcome of a Rollout whose new version has been promoted and now takes the Project's traffic. A Rollout ends in exactly one of Serving, Held or Refused.
_Avoid_: live, deployed

**Held**:
The state of an Application whose release failed: its old version keeps serving while the Project's Prod tag names the new render, until a later render lands. The Rollout ends Held.
_Avoid_: stuck, failed

**Pause**:
The state of a Project whose Prod tag the service does not move. Composition still checks it and Flux still applies the render the tag names. It is recorded in the Project's ProjectControl; a missing or unreadable ProjectControl reads as Paused. An Operator resumes it, and a Rollback leaves the Project Paused.
_Avoid_: freeze, suspend

**ProjectControl**:
The custom resource, one per admitted Project in its own namespace, that records whether the Project is Paused and the render it is held at after a Rollback. Only the service writes it.
_Avoid_: control file, pause object

**Rollout**:
One Project's release, from the moment the service moves its Prod tag until it ends Serving, Held or Refused. The service records it as an append-only log of Rollout events and reports it as a GitHub Deployment in the environment `production`. Not a Kubernetes `Deployment`.
_Avoid_: deployment, release run

**Release Gate**:
The service's answer to Flagger, from cluster state, for each member of a switchover: may this member's new version start, and may it be promoted. It fails closed. Its answer reads cluster state; its only writes are the Application's record and the unsuspend of a migration Job, made by the service under the Writer Lease. Not the Kubernetes readiness gate.
_Avoid_: gate controller, promotion check

**Writer Lease**:
The coordination Lease in the API server that the one service pod takes immediately before it signs a render or moves a tag, and checks it still holds before the move. The move is read, verify, write: the tag is read again after the write, and a different value is a lost race, because ghcr has no compare-and-swap. It has a time-to-live.
_Avoid_: leader election, lock

**Machine account**:
The dedicated GitHub account whose classic token, kept in Vault, moves the `render/` and `host/` tags on ghcr. It has write access only on the render and host packages.
_Avoid_: bot, service token

**Composition**:
The service's estate-wide step that unions every admitted Project's fragment and renders them. It names no workflow, job or check.
_Avoid_: compose job, deploy

**Plan**:
A composition that signs nothing and contacts no cluster, returning errors and the render diff.
_Avoid_: preview

**Dry-run**:
A composition followed by a server-side apply with `dryRun=All` against the live API server, persisting nothing.
_Avoid_: test deploy, rehearsal

**Rollout event**:
One entry in a rollout's append-only log; a rollout's state is the fold of its events.
_Avoid_: status update, log line

**Reconstructed event**:
A Rollout event that reconciliation appended after a crash, marked as reconstructed and naming the observation it was inferred from. The service did not see it happen.
_Avoid_: backfill, replayed event

**Observation**:
The context that shows what runs and how it is doing: units, pods, containers, alerts and silences, logs, health and checks. It reads, except that it creates and expires Alertmanager silences with a credential for that API alone. It holds no credential that can deploy, pause or roll back.
_Avoid_: dashboard backend, monitoring

**Viewer**:
A signed-in person who may read. Roles come from auth-api groups.
_Avoid_: guest, user

**Operator**:
A signed-in person who may also pause, resume and roll back a Project, and act on a host's rollout.
_Avoid_: deployer, SRE

**Admin**:
A signed-in person who may also change what the estate admits: Platform Intent and Infrastructure Intent.
_Avoid_: owner, superuser

## Diagnostics and traceability

**Model path**:
The RFC 6901 pointer to a node of an authored document, by position (`/applications/0/processes/1/image`). It exists to find a line at a commit.
_Avoid_: path, location

**Element reference**:
The identity of a model element and field, keyed by names (Project, Application, Process, then the field). It survives reordering, and names an element outside the run that found it.
_Avoid_: id path, source id

**Location**:
Where a diagnostic points: an authored location (Project, document, model path), a Platform Intent location, or a ClusterState fact. A diagnostic has one primary location and any number of related ones.
_Avoid_: position, span

**Provenance**:
For one rendered field, the set of element references that caused its value. Deferred ([record 72](docs/decisions/0072-per-field-provenance-and-explain-are-deferred.md)).
_Avoid_: origin, lineage

## Hosts

**Infrastructure Intent**:
The authored document that declares the estate's sites and nodes: what each node has, what it needs, and its maintenance window.
_Avoid_: inventory, fleet file

**Host data**:
The typed Nix attribute set the compiler renders for one node, which hand-written NixOS modules consume.
_Avoid_: generated config, node template

**Host applier**:
The agent on each NixOS node that pulls its signed generation and switches to it, one node at a time.
_Avoid_: deployer, updater

**Host tag**:
The signed registry tag `host/<node>:prod` that names the generation a node should run. The service moves it once the closures are built and the VM tests pass.
_Avoid_: host pin, target generation

**Node class**:
A set of nodes that share one NixOS VM test: control plane, worker, GPU or utility.
_Avoid_: node type, profile

**Maintenance window**:
The hours in which a node may reboot. Declared per site, and a node may override it.
_Avoid_: reboot schedule, downtime window

## Applications

**Mailbox**:
An email address an Application declares by its local part. The same local part declared twice within one Project names one shared Mailbox; across Projects it is refused.
_Avoid_: email account, mail user

## Rewrite and parity

**Characterization fixture**:
A recorded exchange of a Go or Python program, taken from the program itself before it is rewritten and kept in `oracles/characterization/<program>/`. It shows what the program did, not what it should do.
_Avoid_: golden file, snapshot

**Expected-differences ledger**:
The committed list (`shadow/expected-differences.yaml`) of the differences allowed between a shadow render and the production render, each naming its cause. A difference not on it stops the switch for that Project.
_Avoid_: allowlist, diff exceptions

## Code

**Port**:
A trait in an application crate that names one thing the core needs from an outside system, such as `Registry` or `Signer`. A port has one adapter crate, one hand-written fake and one contract suite. The `Ports` wiring bundle, whose associated types are ports, is not a port.
_Avoid_: interface, service, driver

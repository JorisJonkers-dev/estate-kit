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
The digest of everything a Project's render depends on: its fragment, Platform Intent, the ClusterState snapshot and the compiler version.
_Avoid_: cache key, input hash

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

## Diagnostics and traceability

**Model path**:
The RFC 6901 pointer to a node of an authored document, by position (`/applications/0/processes/1/image`). It exists to find a line at a commit.
_Avoid_: path, location

**Element reference**:
The identity of a model element and field, keyed by names (Project, Application, Process, then the field). It survives reordering, and is what the trace, provenance and live objects use.
_Avoid_: id path, source id

**Location**:
Where a diagnostic points: an authored location (Project, document, model path), a Platform Intent location, or a ClusterState fact. A diagnostic has one primary location and any number of related ones.
_Avoid_: position, span

**Provenance**:
For one rendered field, the element reference that caused its value.
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

## Code

**Port**:
A trait in an application crate that names one thing the core needs from an outside system, such as `Registry` or `Signer`. A port has one adapter crate, one hand-written fake and one contract suite. The `Ports` wiring bundle, whose associated types are ports, is not a port.
_Avoid_: interface, service, driver

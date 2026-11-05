# estate-kit vocabulary

The terms estate-kit adds to, or changes in,
[deploy-kit's vocabulary](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/CONTEXT.md).
deploy-kit's terms keep their meaning until this file says otherwise. They
move here when deploy-kit is imported.

## Delivery

**Delivery**:
The bounded context, and its one process in the cluster (`estate-kit-delivery`), that admits Projects, composes, dry-runs, signs and publishes renders, observes what Flux and Flagger do with them, records each Rollout and serves the API and the event stream. It never applies: Flux does. Capitalised, it is this context; it is not the old `delivery` repository it replaces.
_Avoid_: the service, Conductor, deployer

**Admitted Project**:
A Project whose repository, named by its `repository_id`, Platform Intent lists as allowed to deploy.
_Avoid_: participant, registered project

**Prod tag**:
The signed registry tag `render/<project>:prod` that names a Project's current render in production.
_Avoid_: pin, live tag

**Environment tag**:
The signed registry tag `render/<project>:<env>` that names a Project's current render in one Environment. There is one per Project per Environment. The Prod tag is production's Environment tag.
_Avoid_: pin, live tag

**Render key**:
The digest of everything a Project's render depends on, and of nothing else: its fragment, Platform Intent, the ClusterState snapshot, Provider facts (after the cutover), the compiler version, and the Surface declarations that Link reads from other Projects (each Surface its Applications consume or route to: its name, its port and the Project and Application that provide it). A change to a provider's Surface therefore changes the Render key of every Project that consumes it. It is kept as provenance with each published render and is never a cache key. It is not the key that signs: that is the Render signing key.
_Avoid_: cache key, input hash, signing key

**ClusterState snapshot**:
The one route by which live facts reach a render: Delivery captures them, digests them, and the digest becomes a render input. It holds exactly four things: the kinds the cluster serves, the installed CRDs with their versions, the namespace names, and the Kubernetes version. Nothing else of the live cluster enters it.
_Avoid_: cluster facts, live state, cluster inventory

**Render signing key**:
The Vault Transit key that signs `render/<project>:prod`. Flux verifies renders against it. Delivery's Vault policy may use it only for that path; it never signs a host tag.
_Avoid_: render key, Transit key

**Host signing key**:
The Vault Transit key that signs each of a node's numbered host tags (`host/<node>:<number>`). Host appliers verify host tags against it. It never signs a render.
_Avoid_: host key, Transit key

**Recovery key**:
The hardware-held key, kept offline, that Flux and every Host applier trust beside the online signing keys. It signs only in a break-glass, when Vault is gone.
_Avoid_: backup key, root key

**Recovery-key successor**:
The named person who holds a sealed copy of the recovery key, so a break-glass survives the maintainer's absence. Not yet named: an open item with a date.
_Avoid_: backup maintainer, escrow agent, deputy

**Serving**:
The outcome of a Rollout whose new version has been promoted and now takes the Project's traffic. A Rollout ends in exactly one of Serving, Held, Refused, Replaced or Observation lost.
_Avoid_: live, deployed

**Held**:
The state of an Application whose release failed: its old version keeps serving while the Project's Prod tag names the new render, until a later render lands. The Rollout ends Held and records why: a failed analysis verdict, or an inconclusive one on a Project too quiet to gather a sample. A Held Rollout has a deadline, 24 hours unless the Project states another: at the deadline the tag keeps naming the held render, nothing is promoted by itself, and an Operator promotes or rolls back. A later render starts a new Rollout and cancels the deadline.
_Avoid_: stuck, failed

**Pause**:
The state of a Project, in one Environment, whose Prod tag Delivery does not move there. Composition still checks it and Flux still applies the render the tag names. It is recorded in that Environment's ProjectControl; a missing or unreadable ProjectControl reads as Paused. An Operator resumes it, and a Rollback leaves the Project Paused.
_Avoid_: freeze, suspend

**ProjectControl**:
The custom resource, one per admitted Project and Environment, in the Project's namespace and named by the Environment, that records whether the Project is Paused there, the render it is held at after a Rollback, and its monotone `lastServing`. Every read and write names the Environment. Only Delivery writes it.
_Avoid_: control file, pause object

**Rollout**:
One Project's release, from the moment Delivery moves its Prod tag until it ends Serving, Held, Refused, Replaced or Observation lost. Delivery records it as an append-only log of Rollout events and reports it as a GitHub Deployment in the environment `production`. Not a Kubernetes `Deployment`.
_Avoid_: deployment, release run

**Release Gate**:
Delivery's answer to Flagger, from cluster state, for each member of a switchover: may this member's new version start, and may it be promoted. It fails closed. Its answer reads cluster state; its only writes are the Application's record and the unsuspend of a migration Job, made by Delivery under the Writer Lease. Not the Kubernetes readiness gate.
_Avoid_: gate controller, promotion check

**Writer Lease**:
The coordination Lease in the API server that the one Delivery pod takes immediately before it signs a render or moves a tag, and checks it still holds before the move. The move is read, verify, write: the tag is read again after the write, and a different value is a lost race, because ghcr has no compare-and-swap. It has a time-to-live.
_Avoid_: leader election, lock

**Machine account**:
The dedicated GitHub account whose classic token, synced from Vault into a Kubernetes Secret Delivery mounts, moves the `render/` and `host/` tags on ghcr. It has write access only on the render and host packages. The maintainer's CLI uses the same token to move the Environment tag of Delivery's own render.
_Avoid_: bot, service token

**Composition**:
Delivery's estate-wide step that unions every admitted Project's fragment and renders them. It names no workflow, job or check.
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
A Rollout event that reconciliation appended after a crash, marked as reconstructed and naming the observation it was inferred from. Delivery did not see it happen.
_Avoid_: backfill, replayed event

**Predecessor digest**:
The digest each Rollout event row carries of the stored content of the row before it in the same Rollout — its rollout id, sequence, type, version, time and payload; the first event of a Rollout carries the empty digest. An append is refused when it does not name the last row the writer read, so a gap or a reorder in the log is detected. It is written into the event schema before the schema is committed.
_Avoid_: parent hash, chain hash, event hash

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

**Operation**:
One deploy of one Project to one Environment, from the request to the end of its Rollout, identified by its Operation id. Delivery returns the Operation id and the URL of its event stream to the caller. Losing the caller does not end the Operation.
_Avoid_: job, run, deploy request

**Operation id**:
The identifier of an Operation, unique within its Project and Environment. Each Rollout event of the Operation carries it, and the Rollout's source revision and render digest are bound to it.
_Avoid_: run id, request id, correlation id

**Apply group**:
A set of a Project's rendered objects that Flux applies as one Kustomization, after the groups it depends on are healthy. The compiler derives the groups and their order, for example grants and secrets, then the migration Job, then workloads, then routes. A Project's render holds namespaced kinds only; its namespaces and every cluster-scoped kind are objects of the platform render, so no group of its chain is cluster-scoped.
_Avoid_: wave, stage, phase, reconcile unit

**Superseded**:
The end of an Operation that a newer Operation for the same Project and Environment replaced before its Rollout ended. A Rollout that had begun ends Replaced. Superseded is never a Rollout end.
_Avoid_: cancelled, aborted

**Replaced**:
The end of a Rollout that a newer Operation for the same Project and Environment closed before it reached Serving, Held or Refused. The Operation ends Superseded.
_Avoid_: superseded (for a Rollout), cancelled, aborted

**Observation lost**:
The end of an Operation's stream when Delivery can no longer see what Flux or Flagger did, so it cannot say how the Rollout ended. It is not a failure of the Rollout, which may still reach Serving.
_Avoid_: timeout, unknown, disconnected

**Publication point**:
The step after which a render is visible to Flux: the moment its tag is created in the registry. Before it, an interrupted Operation has changed nothing the cluster can read; after it, the render may be applied.
_Avoid_: commit, push, release point

**Sequence tag**:
An immutable registry tag that names one published render of one Project in one Environment, numbered so that a later publication has a higher version. Flux follows the highest; the registry refuses to change a tag once created. A Rollback creates a new Sequence tag that names an older, already-signed digest. A Host tag is numbered the same way.
_Avoid_: pin, live tag, moving tag

**Bootstrap step**:
The step that applies Delivery's own Deployment, the one rendered object Flux never applies: run from the maintainer's CLI with the offline admin credential, it reads the Environment tag that names Delivery's current render, verifies the signature on every manifest, and refuses an unverified render before it applies. Its rollback is a move of that Environment tag, which only the maintainer's CLI makes.
_Avoid_: self-upgrade, Delivery applier, apply job

**Roll-forward**:
Recovering from a failed Rollout by publishing a new render that fixes it, when rolling back would run a migration backwards.
_Avoid_: fix forward, hotfix

**Retire**:
The lifecycle step that removes an object a Project no longer declares, from the outside systems that hold it, after a Retirement tombstone has been recorded. A kind that is prune-protected is never removed by a render change alone.
_Avoid_: delete, prune, drop

**Retirement tombstone**:
The durable record that an object was declared and is now retired: what it was, where its data went and when it may be removed for good. A component keeps it so that a rename or a lost render never deletes data.
_Avoid_: soft delete, deletion marker

**Analysis verdict**:
The answer of the pure analysis function for one check of a Rollout: pass, fail or inconclusive. An inconclusive verdict holds the Rollout; it never promotes.
_Avoid_: score, result, health

**Forge port**:
One of the three narrow ports through which Delivery reaches a forge: CI identity (who is calling), Rollout projection (where a Rollout is shown) and release source (where a Project's releases come from). GitHub is the first adapter of each.
_Avoid_: forge adapter, git provider, SCM

## Model and contracts

**Model layer**:
One of the four layers of the metamodel, each depending only on the ones before it: the core, which knows no target or provider; profiles and component kinds; provider facts; and the estate instance.
_Avoid_: tier, level, module

**Profile**:
The part of the metamodel for one target, such as Kubernetes or NixOS. It refines core concepts for that target and knows no provider.
_Avoid_: target model, backend

**Component kind**:
A kind of platform component a Project may declare, such as a Database or a Mailbox, defined from the capabilities of the core and the profiles.
_Avoid_: resource type, plugin, CRD

**Provider facts**:
Pinned data about one provider's behaviour, such as an idle timeout or a token model, read by the compiler as input. Never compiler code or schema meaning.
_Avoid_: provider config, quirks

**Estate instance**:
The estate's own data: Platform Intent, Infrastructure Intent and the Projects' fragments. Every fact about this estate lives here or in Provider facts.
_Avoid_: estate config, deployment data

**Contract major**:
The major version of one persisted or externally read contract, such as the Rollout event schema or host data, with its own identifier and supported range, apart from estate-kit's own version.
_Avoid_: schema version, API version

**Unverifiable by construction**:
A rendered object the dry-run cannot check because its kind, or the namespace it needs, does not exist in the cluster yet. Such objects are published in a first stage before the objects that depend on them.
_Avoid_: unknown kind, skipped object

**Recovery class**:
A group of stored data with one stated recovery time and recovery point, such as the datastore, the registry, Project databases or the event log. Not deploy-kit's Durability Class, which says what a volume's data is worth.
_Avoid_: durability class, tier, backup level

**Critical set**:
The small set of items whose loss takes the estate's keys to everything else: the Vault snapshot, the signing and repository credentials, and the datastore snapshot. It is the only set with a second copy.
_Avoid_: critical items, key set, escape kit

**Second copy**:
The one copy of the Critical set held at a second EU provider, other than the provider of each first copy, written with it and held to the age its row in the recovery table states. Nothing else is copied twice.
_Avoid_: mirror, backup of the backup, off-site copy

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

**Causation id**:
The id of the first request or job that set off a chain of work, carried unchanged by every request, job and message it causes, across Projects. Each step keeps its own trace; the Causation id ties the traces together.
_Avoid_: correlation id, trace id, request id

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
The signed registry tag `host/<node>:<number>` that names the generation a node should run. Host tags are numbered and immutable, with the semantics of a Sequence tag: the Host applier takes the highest, and a rollback publishes a new, higher number that names an older generation. Delivery publishes one once the closures are built and the VM tests pass.
_Avoid_: host pin, target generation

**Node class**:
A set of nodes that share one NixOS VM test: control plane, worker, GPU or utility.
_Avoid_: node type, profile

**Maintenance window**:
The hours in which a node may reboot. Declared per site, and a node may override it.
_Avoid_: reboot schedule, downtime window

## Applications

**Environment**:
One of development, staging and production, lettered `d`, `s` and `p`. All three run in the one cluster, each with its own identity, its own Tenants and its own data. Not a GitHub environment, though the `production` GitHub environment guards production deploys.
_Avoid_: stage, tier, deployment kind

**Tenant**:
An organisation whose people and data the estate's Applications serve, within one environment, kept apart from every other Tenant's. The same organisation in staging and in production is two Tenants. Not an operator of the estate: the estate has one maintainer, whatever the number of Tenants. Not deploy-kit's "tenant project", which is any Project other than the platform's.
_Avoid_: customer, organisation, realm, client, tenant project

**Tenant key**:
The short, immutable name that identifies a Tenant everywhere inside the estate, and shows which environment it belongs to. It is never shown to the Tenant's people and never reused.
_Avoid_: tenant id, slug, tenant name

**Tenant handle**:
The name a Tenant's people see in its URLs. It is unique within an environment and may change; a former handle redirects for a grace period of 90 days, then is free again.
_Avoid_: subdomain, slug, vanity name

**Product domain**:
The domain a multi-tenant Application names, under which every Tenant host is derived. Platform Intent admits it for the Project; two Projects may not claim one.
_Avoid_: base domain, root domain, vanity domain

**Tenant host**:
The host at which a Tenant's people reach an Application, derived as the Tenant handle, the environment suffix (none in production) and the Product domain. The environment suffix is its own DNS label, so each Environment has its own wildcard certificate, one per Product domain and Environment suffix, issued by fleet-infra, whose expiry estate-kit's alert names. A host finds its Tenant through a lookup, never by parsing.
_Avoid_: tenant url, subdomain, vanity host

**Estate name**:
The estate's one stable DNS-style name, at most 32 characters, held in Platform Intent. It is the seam for a later second cluster or estate.
_Avoid_: cluster name, estate id

**Tenant export**:
One Tenant's rows exported from one Project database in one snapshot transaction, with that database's migration revision. A Tenant is restored from its exports Project by Project.
_Avoid_: dump, tenant backup, tenant snapshot

**Backup generation**:
The set of one Tenant's Tenant exports, one per Project database that holds its rows, taken on that Tenant's schedule and kept in the central catalogue. The exports share no point in time. A single-tenant Project's generation covers that Project's datastores instead.
_Avoid_: snapshot, dump, backup run

**Mirror**:
A staging or development Tenant's link to the production Tenant whose latest Tenant exports replace its rows on a schedule. Production masks the exports where the Mirror requires it and pushes them to the target Environment, which never holds production's credentials. A development Mirror is always masked; a staging Mirror is masked only if it says so.
_Avoid_: sync, clone, refresh

**Membership**:
A User's belonging to one Tenant. One User signs in once per environment and may hold Memberships in many Tenants.
_Avoid_: tenant user, seat, account

**Canary Tenant**:
A Tenant its Tenant resource marks as a targeting group for feature flags inside Applications: a flag is on for the Canary Tenants first, then for everyone. Migrations and deploys do not use it; a migration reaches every Tenant at once, and deploy canaries are weight-based.
_Avoid_: pilot, early adopter, test tenant

**Tenant lock**:
The brief state in which the platform stops a Tenant's traffic and work around a restore or a Mirror load: its people see a standard maintenance page, and no request or message for it is processed. Not a Locked record.
_Avoid_: maintenance mode, freeze, locked tenant

**Tenant hook**:
A call the tenancy context makes to a multi-tenant Application for one Tenant at one lifecycle step (after-create, lock, unlock, prepare-restore, after-restore, export), so the Application can do what the platform cannot see. An Application implements only the hooks it declares.
_Avoid_: webhook, callback, lifecycle event

**Tenant Admin**:
A User whose Membership lets them manage their Tenant's Memberships and App Roles, for every Project the Tenant uses. Not estate-kit's Admin, and not identity's Admin.
_Avoid_: tenant owner, customer admin, superuser

**Gate**:
The part of identity that resolves a request's host to a Tenant, checks the User's Membership and signs the Principal. Not the Release Gate.
_Avoid_: forward-auth, proxy, middleware

**Principal**:
Who is calling an Application, as identity signs it: the User or Machine Identity, its App Roles, and for a multi-tenant Application the Tenant key and that Tenant's App Roles. An Application takes its Tenant only from it.
_Avoid_: identity, user context, claims

**Tenant header**:
The broker-neutral header a producer sets on every message to name its one Tenant. A consumer sends a message without one to its dead-letter queue.
_Avoid_: tenant id header, routing key

**Suspended**:
The state of a Tenant whose people cannot sign in and whose traffic is refused, while all its data is kept. A Suspended Tenant is purged when its grace period of 30 days ends, unless it is resumed.
_Avoid_: disabled, deactivated, frozen

**Purge**:
The end of a Tenant: its rows in every Project database, its Tenant exports, its Mirror targets' data, cache keys, stored objects, Tenant secrets, mail domain and Memberships are removed everywhere. Whole-database backups that still hold its rows expire under their retention, and the Purge states the date the last copy expires.
_Avoid_: delete, destroy, offboard

**Tenant operation**:
One lifecycle action on a Tenant: create, add a Project, remove a Project, lock, unlock, suspend, resume, purge, restore or export. The tenancy context runs it across every system that holds the Tenant's data, and records each step with its full error output in one operation log.
_Avoid_: job, task, workflow

**Purge marker**:
The record of one Purged Tenant in its Environment's locked repository: the Tenant catalogue's entry for it, its key and its erasure date, named by an opaque UUID. A Purge writes and verifies it before it deletes anything; platform-postgres only caches it, so a restore does not un-purge a Tenant.
_Avoid_: deletion marker, tombstone

**Mailbox**:
An email address an Application declares by its local part. The same local part declared twice within one Project names one shared Mailbox; across Projects it is refused.
_Avoid_: email account, mail user

**Verified domain**:
A domain of a Tenant's own that a Tenant Admin has proven control of, by publishing the DKIM, SPF and DMARC records the platform names and passing its check. It becomes the Tenant's own mail domain, with its own DKIM key. Until then a Tenant sends as its Product domain.
_Avoid_: custom domain, tenant domain, vanity domain

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

## Records and checks

### Locked record

A record whose front-matter status is `locked`: Accepted, and its Confirmation names a check that fails when the decision is broken. Only the maintainer changes it. A pull request that changes a Locked record, including one that unlocks it, needs the `contract-change` label, which is the maintainer's approval. The Contract gate detects it by the changed path and the status on the base.
_Avoid_: frozen record, protected record

### Locked contract path

A path that is Locked by default: anything under `contracts/` (the committed schemas, the OpenAPI files, the error catalogue, the CLI's `--json` output schema, the schema corpus) or `oracles/`, and the shadow's expected-differences ledger (`shadow/expected-differences.yaml`). A pull request that changes one needs the `contract-change` label, which is the maintainer's approval. The Contract gate detects it by the changed path alone.
_Avoid_: frozen path, protected file

**Revised line**:
The line `Revised: YYYY-MM-DD: <what changed>` that sits under the title of an Accepted record whose wording was fixed in place. A change of rule is never a Revised line: it needs an amending record.
_Avoid_: edit note, changelog line

**Enforcement status**:
Whether the checks a record's Confirmation names hold it, as one of four values: planned (a check is a row of the table of checks, with the issue that builds it, and no code yet), implemented (every named check runs, but at least one runs outside `Pipeline Complete` or has no negative fixture shown to fail it), verified (every named check runs inside `Pipeline Complete` and its negative fixture fails it) or review (the Confirmation names no check, or only retired ones, so the rule is held by review only). It is the lowest status of the live checks the record names, planned < implemented < verified. The table of checks gives each check its own status: planned, implemented, verified, or retired, for a check a later record replaced or removed, kept as a row for history. Derived from the table of checks, never written by hand.
_Avoid_: check status, lock status

**Generality test**:
A CI test that proves the core is free of estate facts: a new Component kind built from existing capabilities, the NixOS profile, and a second estate's fixture all pass without a change to the core or the compiler.
_Avoid_: portability test

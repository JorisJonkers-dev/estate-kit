# Operating the estate

Operators act through the UI or the CLI ([record 113](../decisions/0113-every-ui-action-is-a-cli-command-with-the-same-identifier.md)). Every rollout they start still shows up as a deploy run and a Deployment in the Project's own repository.

## Low-attention defaults

The estate states its defaults for a low-attention week, and every default fails safe ([record 86](../decisions/0086-the-estate-states-its-defaults-for-a-low-attention-week.md)). During a week when the maintainer's attention varies — a holiday, an illness or a busy week elsewhere — Projects still release, nightly jobs still run, and Flux, Flagger and the components keep acting. What happens then is decided by defaults, not by anyone watching.

Every situation the estate can reach without the maintainer has a stated default, and every default fails safe: it blocks, holds or keeps the last good state, and it alerts. A default never widens what changes, never retries a move of traffic or a destructive step on its own, and never warns and carries on. An unattended step that destroys data proceeds only where a recovery copy outlives it. A low-attention week costs throughput, not correctness.

The defaults are this table. A new situation gets its row, and its default, in the record that creates it. The rows for Sequence tags wait for [record 98](../decisions/0098-the-live-pointer-is-an-immutable-sequence-tag-that-flux-selects-by-version.md), which is Proposed.

| Situation | Default |
| --- | --- |
| A dry-run fails, or an object is unverifiable for a reason other than construction | Block the move; never warn and continue |
| Objects are Unverifiable by construction | Publish the objects they depend on first; dry-run the rest after |
| An Analysis verdict is inconclusive | Hold; never promote; alert when the Held deadline passes |
| A Rollout ends Held | The old version keeps serving; nothing retries on its own |
| ProjectControl is missing or unreadable | Read as Paused |
| A step's outcome is unknown after a crash | Rebuild from observed state; never replay a write on the log's word |
| A composition input moved during the run | Publish nothing; compose again |
| The applied revision trails the latest published one for 1 hour | Alert; running workloads keep serving |
| A credential is expired or cannot be verified | Fail closed |
| Vault is sealed | Nothing is signed; a Rollback still works |
| Delivery is down | Nothing new deploys; Flux keeps serving the last renders |
| A migration fails and its Project database is marked failed | No release of that Project in that Environment until an Operator retries the migration or requests a Roll-forward |
| A lock or prepare-restore Tenant hook fails | The Tenant operation stops before any data changes |
| A Suspended Tenant reaches the end of its grace period | The Purge proceeds; its Tenant exports go at once, and whole-database backups that hold its rows remain until their retention ends |
| A Retire grace period ends | Delete only after a verified recovery copy exists |
| A backup reconciler is down | Alert; nothing else changes |
| A node class has no rehearsed fallback | No automatic host rollout for that class |
| Observation of an Operation is lost | The CI job exits with its own code; the Operation continues |

## Rollouts no Project run started

A Platform Intent change, the nightly recompose or a Rollback from the UI: Delivery dispatches the Project's `deploy` workflow in watch mode, with a run
name that says why (for example "Deploy notes: Platform Intent changed").
Missed triggers heal on a timer that scans the registry for fragments newer
than the last composition.

## UC-5 Pause or resume a Project

An Operator pauses a Project in the UI. Delivery records it in the Project's
cluster object and stops moving its tag until the Operator resumes. Outcome:
Flux keeps serving the current render.

![UC-5 Pause or resume a Project](../diagrams/png/uc5-pause.png)

## UC-6 Roll back a Project

An Operator rolls a Project back. The fast path signs nothing and composes
nothing ([review](../research/review/README.md) D7): Delivery dry-runs the last Serving render against today's
cluster, moves `render/<p>:prod` back to it by read, verify, write under the writer Lease, and sets the
Project to Paused, so no new release moves the tag until the Operator resumes.
Only if that dry-run fails does Delivery re-compose at the earlier fragment
and dispatch the deploy run in watch mode. Signatures are kept exactly as long
as their renders, so every render that ever served can serve again. Outcome:
the previous render serves within five minutes, even with Vault down.

![UC-6 Roll back a Project](../diagrams/png/uc6-rollback.png)

![Sequence: roll back a Project](../diagrams/png/seq-rollback.png)

## UC-7 Admit a Project

An Admin merges a Platform Intent change that admits a Project's
`repository_id`. Delivery derives the Project's Flux source into the
platform render. Outcome: the Project's CI may deploy from then on.

![UC-7 Admit a Project](../diagrams/png/uc7-admit.png)

## UC-8 Pull and apply a render

Flux sees `render/<p>:prod` point at a new digest, verifies the signature, then
applies and prunes. Outcome: the cluster holds the new render; the traffic
switch is UC-9.

![UC-8 Pull and apply a render](../diagrams/png/uc8-apply.png)

## UC-9 Gate a traffic switch

Flagger asks the Release Gate whether to promote. Delivery answers from
cluster state alone, yes only when every member of the Release Unit is
healthy. Flagger cannot authenticate the call, so the gate reads and never
writes. Outcome: traffic switches
together, or the release is Held.

![UC-9 Gate a traffic switch](../diagrams/png/uc9-gate.png)

## States of a Project

A Project's state decides whether Delivery may move its tag. A Project
with no cluster object at all is treated as Paused, so a lost object fails
safe.

![States of a Project](../diagrams/png/state-project.png)

## When something underneath fails

| What fails | What keeps working | How it comes back |
| --- | --- | --- |
| Delivery pod | Flux serves the last tags | Recreate starts one pod; it reconciles unfinished rollouts from ghcr and Flux status (D9) |
| Vault | Serving, and rollback | Auto-unseal through a cloud KMS; a VaultSealed alert (D6); the offline recovery key for break-glass (D10) |
| ghcr or GitHub | Serving, until a pod moves to a node without the image | Deploys fail loudly and resume when it returns |
| The control-plane node | Workloads keep running | Rebuild with nixos-anywhere, restore the k3s datastore from its off-provider backup, restore Vault from its snapshot (D5) |
| Delivery, Vault and GitHub together | Serving | The break-glass runbook: `flux suspend`, or an OCIRepository pinned to a digest, by hand ([#39](https://github.com/JorisJonkers-dev/estate-kit/issues/39)) |

Every row is answered in the [review](../research/review/README.md), decisions D5 to D10.

## Restore order and drill cadence

The control plane is restored in a dependency order that is tested, drilled and timed ([record 106](../decisions/0106-the-control-plane-is-restored-in-a-dependency-order-that-is-tested-drilled-and-timed.md)). After total loss of the control-plane node, the estate is restored in this order:

1. A new host from nixos-anywhere, with its first generation from the cache, and the offline credentials (Recovery key, admin credential, backup decryption keys) from the maintainer's offline store.
2. The k3s datastore from its off-provider copy. Every Flux Kustomization of a Project that holds data stays suspended until step 5.
3. Vault from its raft snapshot, unsealed as fleet-infra provides.
4. The registry and the binary cache, checked reachable; neither depends on the cluster, and neither may run on the control-plane node.
5. The contents of local-path volumes and platform-postgres, from their off-cluster backups. The backup times are compared and any gap is recorded.
6. Flux, bootstrapped from the bootstrap render with the CLI.
7. Projects resumed in dependency order. Components apply their Retirement tombstones first ([record 105](../decisions/0105-removal-is-a-retire-lifecycle-with-durable-retirement-tombstones-and-declared-moves-and-prune-protected-kinds-never-prune.md)) and hold destructive actions until their stores are confirmed restored.
8. Delivery reconciles its Rollouts from observed state, marking reconstructed events.
9. The time taken and the data lost are recorded against the targets.

The restore order is rehearsed in CI on every release, on a throwaway cluster. Once a year the procedure is drilled on the real estate and timed against the recovery time and point of each Recovery class ([record 87](../decisions/0087-recovery-time-and-recovery-point-are-stated-per-recovery-class.md)).

## Weekly restore rehearsal

The backup component restores the latest snapshot of each store into throwaway containers once a week and checks what it reads back ([record 115](../decisions/0115-backups-are-kopia-snapshots-in-one-locked-repository-per-environment-on-an-eu-object-store-with-wal-archived-beside-them.md)). Each result is an active check result of [record 108](../decisions/0108-active-checks-run-in-the-owning-components-observation-reads-their-results-and-one-heartbeat-lives-outside-the-cluster.md): Observation reads it, and a pass also reaches the external heartbeat, so a rehearsal that stops running raises an alert from outside the cluster.

## External heartbeat

One heartbeat lives outside the cluster ([record 108](../decisions/0108-active-checks-run-in-the-owning-components-observation-reads-their-results-and-one-heartbeat-lives-outside-the-cluster.md)). It is Alertmanager's Watchdog alert, which always fires while the alerting pipeline works. Alertmanager sends it on a schedule to a hosted dead-man's switch from an EU-based provider, such as healthchecks.io, and when it stops arriving, that service raises the alert from outside. The service shares no machine with the control plane. The heartbeat holds no estate data, so the rule that a store of estate data runs on an EU-controlled provider or on owned hardware does not bind it; an EU-based service is still preferred.

## CLI command behind each UI action

Every action the UI offers, a read or a write, calls one operation of a committed OpenAPI document, and the CLI has a command that calls the same operation ([record 113](../decisions/0113-every-ui-action-is-a-cli-command-with-the-same-identifier.md)). The operation's `operationId` is the one identifier of the action: the UI action carries it, the CLI command's words joined by hyphens spell it (`estate-kit tenant suspend` is `tenant-suspend`), and its row in the authorization matrix is keyed by it. An `operationId` is not an Operation id, which names one deploy. Operators act through the UI or the CLI.

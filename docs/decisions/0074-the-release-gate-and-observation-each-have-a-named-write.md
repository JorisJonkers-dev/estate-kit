---
status: accepted  # proposed | accepted | locked
date: 2026-10-29
rests-on: [50, 63, 58]
lessons: [DO-1]
---

# The Release Gate and Observation each have named writes, with their own credentials

Amended by [record 92](0092-capacity-is-in-the-resolved-deployment-cost-is-estimated-outside-the-render-key-and-recorded-from-bills.md): Observation appends cost-ledger rows to its own schema, with a role for that schema only and no Lease, and it also holds read-only billing credentials.

Amended by [record 93](0093-the-rollout-plan-is-compiled-with-checks-bound-to-cohorts-a-failsafe-and-a-held-deadline.md): the Release Gate answers from the compiled rollout plan, the Analysis verdicts and cluster state.

Amended by [record 102](0102-analysis-is-a-pure-verdict-function-and-an-inconclusive-verdict-holds.md): the gate's answer stays a read, and an inconclusive verdict holds.

## Context

The redesign said the Release Gate never writes and that Observation is read
only. Both statements are false of the programs being replaced:

- delivery's Release Gate (`internal/gate/kube.go`) creates and updates one
  ConfigMap per Application as its record, and patches a migration Job to
  unsuspend it.
- estate-dashboard writes Alertmanager silences and mirrors them in its own
  Postgres table: "its one write".

The review of 2026-10-29 settled the placement. This record names each write
so the pages that say "read only" can name the exception and nothing more.

## Decision

There are four writes. Nothing else in either context writes.

| Write | Context | Credential | Lease |
| --- | --- | --- | --- |
| Unsuspend a migration Job (patch `spec.suspend`) | Delivery, in the Release Gate | A service account of its own, limited by RBAC to `patch` on Jobs in admitted Projects' namespaces | The writer Lease: taken before the write, checked still held |
| Create or update the Application's gate record (one ConfigMap per Application) | Delivery, in the Release Gate | The same service account, limited to ConfigMaps of that name | The writer Lease |
| Create or expire a Silence in Alertmanager | Observation | A credential for the Alertmanager silences API only, held by Observation's own binary | None: a Silence changes no rollout and no tag |
| Append cost-ledger rows to its own schema | Observation | A role for that schema only | None |

The Release Gate's webhook answer stays a read (of the compiled rollout plan,
the Analysis verdicts and cluster state,
[record 93](0093-the-rollout-plan-is-compiled-with-checks-bound-to-cohorts-a-failsafe-and-a-held-deadline.md)),
and an inconclusive Analysis verdict holds
([record 102](0102-analysis-is-a-pure-verdict-function-and-an-inconclusive-verdict-holds.md));
it takes no
credential from Flagger. The Job unsuspend and the record are made by Delivery's reconcile under the Lease, never inside the answer to an
unauthenticated request. Delivery's dry-run identity stays unable to write
([record 58](0058-flux-is-locked-down-per-project-and-delivery-dry-runs-as-an-identity-that-cannot-write.md)).
Observation still holds no Vault, ghcr or signing credential, and none that can
deploy, pause or roll back ([record 50](0050-six-bounded-contexts-in-five-layers.md)); the
only credentials it holds outside the cluster are read-only billing
credentials ([record 92](0092-capacity-is-in-the-resolved-deployment-cost-is-estimated-outside-the-render-key-and-recorded-from-bills.md)).
Its
mirror of Silences lives in its own Postgres schema and nothing else reads it.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Say the gate never writes and drop the unsuspend | Migration Jobs never start, or something else must start them | The behaviour is characterized and the rollout depends on it ([record 55](0055-every-go-and-python-program-is-characterized-before-it-is-rewritten.md)) |
| Move the Job unsuspend into the Components context | A second writer of Jobs beside the gate's decision | The unsuspend follows the gate's answer; one writer holds the Lease |
| Drop silences from the Rust Observation | The dashboard loses a feature it has today | Operators silence alerts from it |
| Silences through Delivery's credential | The rollout core holds an Alertmanager write | The read side would then sit beside a deploy credential |

## Consequences

- Easier: every "read only" has one named exception to point at, and each
  write has a credential that can be revoked alone.
- Harder: Observation needs a secret for the silences API, and the Release
  Gate needs a service account distinct from the dry-run identity.
- Forbidden: a write by either context that is not in the table above.

## Confirmation

Not yet Lockable. A check is proposed: the **RBAC fixtures**, one per context, fail
when a credential grants a verb or resource outside the table, and run in the
end-to-end suite ([record 69](0069-the-deploy-path-is-tested-end-to-end.md)),
and the **Characterization fixtures** for the gate's writes and the dashboard's
silences ([record 55](0055-every-go-and-python-program-is-characterized-before-it-is-rewritten.md)).

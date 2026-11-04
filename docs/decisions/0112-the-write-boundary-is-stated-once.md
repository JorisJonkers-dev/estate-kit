---
status: proposed  # proposed | accepted | locked
date: 2026-11-04
rests-on: [2, 9, 17, 21, 23, 28, 30, 50, 58, 63, 74, 80]
lessons: [DR-3, DO-1]
---

# The write boundary is stated once, in one table of every writer

## Context

Who may write to the cluster is told four ways, and the tellings disagree. The
architecture evaluation of 2026-11-04 (section 3.22) found three sets of
exceptions; reading the records again finds a fourth.

- [Record 2](0002-kubernetes-is-the-substrate-and-flux-is-the-one-applier.md)
  says nothing but Flux creates or changes an object in the cluster, and leaves
  Delivery's exceptions to "its own record". It does not mention Flagger, the
  host applier or any other controller, all of which write.
- [Record 17](0017-delivery-runs-in-the-cluster-in-rust.md) and
  [record 58](0058-flux-is-locked-down-per-project-and-delivery-dry-runs-as-an-identity-that-cannot-write.md)
  let Delivery's identity write without `dryRun` only its writer Lease and
  ProjectControl objects.
- [Record 74](0074-the-release-gate-and-observation-each-have-a-named-write.md)
  says "there are three writes" in Delivery and Observation (the Job
  unsuspend, the gate record, Silences) and "nothing else in either context
  writes", which leaves out the Lease, ProjectControl, the tags and the event
  log.
- [Record 80](0080-a-tenant-is-a-custom-resource-in-a-sixth-bounded-context-tenancy.md)
  makes Delivery the one writer of Tenant resources, but the admission table
  of [record 58](0058-flux-is-locked-down-per-project-and-delivery-dry-runs-as-an-identity-that-cannot-write.md) has no row for them, and the participants that release finalizers on a
  Tenant also write to it.

[Record 28](0028-pause-and-rollback-are-a-cluster-object-per-project.md),
[record 50](0050-six-bounded-contexts-in-five-layers.md) and
[Inside Delivery](../design/inside-delivery.md) each repeat part of one of
these sets. No record names the credential under which Flux applies the
platform render.

## Decision

The table below is the write boundary: every writer, what it writes, and
under which credential. A writer writes nothing outside its row, and each row
is one credential that can be revoked alone. A new write is a new row here
first, in its own pull request. When this record is accepted, the records it
rests on that list writers ([2](0002-kubernetes-is-the-substrate-and-flux-is-the-one-applier.md), [17](0017-delivery-runs-in-the-cluster-in-rust.md), [28](0028-pause-and-rollback-are-a-cluster-object-per-project.md), [50](0050-six-bounded-contexts-in-five-layers.md), [58](0058-flux-is-locked-down-per-project-and-delivery-dry-runs-as-an-identity-that-cannot-write.md), [74](0074-the-release-gate-and-observation-each-have-a-named-write.md) and [80](0080-a-tenant-is-a-custom-resource-in-a-sixth-bounded-context-tenancy.md))
and Inside Delivery are corrected to cite this table instead of listing
exceptions; their checks stay. Until then those records bind as written.

**Into the API server.** "Flux is the one applier"
([record 2](0002-kubernetes-is-the-substrate-and-flux-is-the-one-applier.md))
means only Flux applies the objects a render declares. Controllers the
platform render installs write what they derive, as listed.

| Writer | What it writes | Credential |
| --- | --- | --- |
| Flux, per Project | The objects of that Project's render, in its target namespaces | The Project's own service account, named by its Kustomization; Flux's default account has no rights |
| Flux, for the platform | The platform render: namespaces, per-Project service accounts, Flux sources, CRDs and admission policies | The platform Kustomization's service account, the only one with cluster-scoped rights |
| Delivery | Every change with `dryRun`; without it, only the Lease `estate-kit-writer` and ProjectControl objects | Delivery's service account, held there by the ValidatingAdmissionPolicy |
| Delivery's Release Gate | `spec.suspend` of a migration Job; one gate ConfigMap per Application | A service account of its own, limited by RBAC to those, under the writer Lease |
| Delivery's tenancy context | The spec of Tenant resources | A service account of its own, limited to Tenant resources, under the writer Lease, as the Release Gate's is under [record 74](0074-the-release-gate-and-observation-each-have-a-named-write.md) |
| A Tenant's participants | Each its own finalizer and status condition on a Tenant, and the status of the objects it reconciles | Each component's own service account |
| Flagger | Canary status, and the workloads, Services and routes it derives from a Canary | Flagger's service account |
| Other controllers the platform installs | What they derive and their status; the Vault Secrets Operator writes the Secrets it syncs, the machine account's among them | Each its own service account |
| The host applier on a node | Cordon of its own node, eviction of its own node's pods, the host rollout Lease | A credential per node; an admission policy limits it to its own node |
| A person | Nothing, outside a break-glass | The offline admin credential |

Observation and a Project's CI write nothing into the API server.

**Outside the API server.**

| Writer | What it writes | Credential |
| --- | --- | --- |
| Delivery | Renders, their signatures, and the `render/` and `host/` tags | The machine account's token, from a mounted Secret, with write only on the render and host packages |
| Delivery | Signatures over renders and host tags | Vault Transit through Delivery's service account; each key only on its own path |
| Delivery | Rollout events, registered digests, the job table and the Tenant operation log | Its database role: insert and select on the logs, and its own rows of the job table |
| The retention job | Deletion of expired Rollout events | Its own database role, delete only |
| Delivery | GitHub Deployment statuses and check runs | The GitHub App's installation token |
| Observation | Silences in Alertmanager, its mirror of them and the cost ledger's rows in its own schema ([record 92](0092-capacity-is-in-the-resolved-deployment-cost-is-estimated-outside-the-render-key-and-recorded-from-bills.md)) | A credential for the silences API only, and a database role for its own schema only |
| A Project's CI | Its images and its Intent Fragment in its own packages; digest registrations through Delivery's API | The job's own token; the GitHub OIDC token for Delivery |
| estate-kit's CI on `main` | Signed host closures in the binary cache | The environment-scoped cache signing key, after a reviewer approves |
| A component | Its one outside system: Vault policies, Postgres roles, Garage buckets, Stalwart accounts or backup copies | A credential for that system alone |
| The maintainer, in a break-glass | A signature over a render or a host tag | The offline Recovery key |

Delivery writes Tenant resources under a service account of its own, the
pattern [record 74](0074-the-release-gate-and-observation-each-have-a-named-write.md)
set for the Release Gate, not under a third exemption in the policy of
[record 58](0058-flux-is-locked-down-per-project-and-delivery-dry-runs-as-an-identity-that-cannot-write.md)
for Delivery's identity. Flux applies the platform render under the platform
Kustomization's service account, which this record names because no other
does. The participants' row reads the **Tenant one writer** check as covering a
Tenant's spec only.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Correct each record in place and keep the lists apart | Four lists drift again on the next write | One table, cited, cannot disagree with itself |
| Tenant writes as a third exemption for Delivery's identity | The dry-run identity's policy widens with each new write | A write gets its own credential, as in [record 74](0074-the-release-gate-and-observation-each-have-a-named-write.md) |
| The platform render applied under Flux's default account | Flux's default account gains cluster-scoped rights that every Project's Kustomization could fall back to | Flux's default account has no rights; the platform has its own |
| Say only Flux writes, and leave controllers unstated | Flagger and the other controllers write without a row, so no check covers them | A boundary that omits writers is not a boundary |
| List only the writes into the API server | The registry, signing keys and logs are where a stray write does the most harm | The tags and signatures decide what runs |

## Consequences

- Easier: one place answers "who can change this"; a review of a new write
  has one table to amend; each credential can be revoked alone.
- Harder: the table must be kept complete as components and controllers are
  added, and the cited records must be corrected on acceptance.
- Forbidden: a write by any identity outside its row; a new writer without a
  row; a record or page that lists its own exceptions instead of citing this
  table, once this record is accepted.

## Confirmation

The **Write table check** fails when a Role, ClusterRole or binding in the
platform render grants a write verb to an identity with no row, or wider than
its row (a grant to Delivery's own identity on Tenant resources among them), or
when the platform Kustomization names a service account other than its own. The
rows keep their own checks: the **Dry-run admission fixtures**, the
**ProjectControl admission fixtures**, the **RBAC fixtures**, the **Tenant one
writer**, the **Eviction fixture**, the **Token grant check**, the **Event-log
tests** and the **Operation log append-only** check.

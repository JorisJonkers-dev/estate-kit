# Identity and access

Every caller that can change something proves who it is with an OIDC token.
One long-lived secret remains: the PAT that moves ghcr tags, because ghcr
refuses GitHub App tokens ([review](../research/review/README.md) D3). It lives in Vault.

## Who calls, with what

| Caller | Token | What the service checks |
| --- | --- | --- |
| Project CI | GitHub Actions OIDC token, audience `estate-kit`, re-requested while a deploy job waits | The [claim policy](#the-claim-policy), with pass and fail fixtures (D8) ([record 8](../decisions/0008-an-image-digest-is-sealed-into-the-fragment-and-registered-by-its-build.md)) |
| People in the UI | auth-api; estate-kit is a declared Client | Group claims map to viewer, operator or admin in Platform Intent. Operators pause, resume and roll back; admins change admissions. "Signed in means operator" was rejected: one identity system maps groups to roles |
| Flagger's Release Gate webhook | None: Flagger cannot send a projected service-account token | The answer only reads cluster state and changes nothing, so an unauthenticated call can learn health and nothing more (D9). The gate's own writes are made by the service under the Lease, not by this call ([record 74](../decisions/0074-the-release-gate-and-observation-each-have-a-named-write.md)) |
| Flux | None: the service watches Flux's status instead of taking its events | Nothing to check (D9) |
| Service to Vault | Vault Kubernetes auth | The service's own service account |
| Service to GitHub | GitHub App installation token | Not OIDC: GitHub issues it per installation |
| Service to ghcr | A machine account's classic PAT, synced by the Vault Secrets Operator into a Kubernetes Secret the service mounts, so a tag move never reads Vault | Write only on the render and host packages; a check fails on any other grant; rotated on a schedule (D3) |
| Service to the API server | Its own service account | Dry-run only: a ValidatingAdmissionPolicy refuses a write by the service's identity without `dryRun` other than to its writer Lease, by its name, and to ProjectControl objects (D4) |
| Release Gate to the API server | A service account of its own | Patch migration Jobs and write one record ConfigMap per Application, under the writer Lease ([record 74](../decisions/0074-the-release-gate-and-observation-each-have-a-named-write.md)) |
| Observation to Alertmanager | A credential for the silences API only | Create and expire silences, nothing else ([record 74](../decisions/0074-the-release-gate-and-observation-each-have-a-named-write.md)) |
| Host applier to the API server | A credential per node | Cordon, evict and the rollout Lease, limited by policy to its own node (D2) |

## The claim policy

A Project's CI call passes only if every rule holds
([record 8](../decisions/0008-an-image-digest-is-sealed-into-the-fragment-and-registered-by-its-build.md)):

| Claim | Rule |
| --- | --- |
| `aud` | `estate-kit` |
| `repository_id` and `repository_owner_id` | Match the Project's admission |
| `job_workflow_sha` | The pinned estate-kit reusable workflow |
| `event_name` | On an allowlist; a pull request may only plan or dry-run |
| `ref_type` | `tag` for a deploy |
| Runner | GitHub-hosted, for a deploy |
| Environment | `production`, for a deploy |
| `sub` | Never used |

## Authenticating a deploy job

A GitHub OIDC token is short-lived, but a rollout can run longer. The
service-minted rollout token that would bridge the gap is deferred until spike
#11 shows whether a deploy job can request a fresh GitHub OIDC token while it
waits. Meanwhile the job requests a new GitHub token whenever it needs one and
presents it to the stream.

The service restarts under `Recreate`
([record 63](../decisions/0063-the-service-has-one-writer-and-reconciles-from-observed-state.md)),
and the stream drops. A waiting job re-requests a GitHub OIDC token, reconnects,
and resumes the stream by sequence
([record 23](../decisions/0023-a-rollout-is-an-append-only-event-log-on-the-shared-postgres.md)).
The service holds no token state, so an upgrade mid-rollout loses nothing.

The diagram below still shows the exchange; it follows once spike #11 settles.

![Sequence: authenticating a deploy job](../diagrams/png/seq-auth.png)

## Why repository_id and not the name

A renamed or recreated repository keeps its name but not its id. Binding
admission to `repository_id` means a new repository with an old name cannot
take a Project over.

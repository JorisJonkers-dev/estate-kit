# Identity and access

Every caller of the service proves who it is with an OIDC token. Nothing holds
a long-lived secret for the service.

## Who calls, with what

| Caller | Token | What the service checks |
| --- | --- | --- |
| Project CI | GitHub Actions OIDC token, audience `estate-kit` | `repository_id` matches the Project's admission in Platform Intent. `job_workflow_ref` is the estate-kit reusable workflow at a pinned ref. Deploy needs environment `production`; a PR ref may only plan or dry-run |
| CI after the exchange | Service-issued token | Scoped to one Project and one rollout, read-only on the stream |
| People in the UI | auth-api; estate-kit is a declared Client | Group claims map to viewer, operator or admin in Platform Intent. Operators pause, resume and roll back; admins change admissions |
| In-cluster callers (Flagger webhooks, Flux events) | Projected service-account token, audience `estate-kit` | Verified locally against the cluster's OIDC keys; the service account maps to the caller's declared API access |
| Service to Vault | Vault Kubernetes auth | The service's own service account |
| Service to GitHub and ghcr | GitHub App installation token | Not OIDC: GitHub issues it per installation |

## Authenticating a deploy job

A GitHub OIDC token is short-lived, but a rollout can run longer. The job
exchanges its token once for a rollout token, and reconnects with that.

![Sequence: authenticating a deploy job](../diagrams/png/seq-auth.png)

## Why repository_id and not the name

A renamed or recreated repository keeps its name but not its id. Binding
admission to `repository_id` means a new repository with an old name cannot
take a Project over.

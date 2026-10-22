# Review: delivery and gitops

Part of the [design review](README.md). Each finding was checked by a second
reviewer that tried to refute it; its verdict and corrections follow the finding.

## Verdict

The delivery path already follows OpenGitOps where it matters most. Flux pulls signed artifacts named by digest and is the only thing that applies them, and images are built once and promoted, so what dry-ran is what deploys. Its weak points sit around that core. The service's dry-run needs the same write permissions as a real apply, and ghcr does not accept GitHub App tokens, so the trust model on the security page does not hold as written. The desired-state pointer is a mutable tag whose history lives in a service-owned Postgres. Rollback depends on every moving part being healthy at the moment it is needed most. The service is also more than this delivery path needs: an edge-triggered request/stream orchestrator with a queue, an event store, resume semantics and a timer for missed triggers. A level-triggered composer plus mature Flux features (multi-tenancy lockdown, suspend, an OIDC Receiver, pkg/ssa, the Flux Operator Web UI) would remove much of that bespoke code without giving up S1. The service cannot be removed entirely: the pre-tag dry-run and Vault signing must happen inside the cluster. But it can shrink to a small reconciler.

## What the design gets right

- Only signed, digest-named artifacts cross into the cluster, and Flux stays the single applier that pulls them. This meets OpenGitOps principles 1, 3 and 4 and avoids a push-based applier (where-state-lives.md, 'Where each part runs').
- Images are built on the release PR and promoted by digest on release, with a dry-run on the release PR and again just before each tag move. This closes the gap between what was checked and what deploys, and the estate can change between merge and deploy without being missed (releasing.md, 'The three runs').
- CI identity is bound to repository_id, a pinned job_workflow_ref and the production environment, rather than the repository name. This is stronger than most GitOps setups (identity-and-access.md).
- Cancelling a deploy job only detaches it, and stopping is an explicit Pause or Rollback. Deploy calls are idempotent on the natural key (project, fragment digest) with compare-and-swap tag moves, and streams resume by sequence number. These are the right semantics for at-least-once delivery.
- The shadow writes unsigned shadow/ tags that admission refuses, and the switch is staged per Project, a strangler pattern with a revert at each step (overview.md, 'Order of work').
- There is no central pin repository, and the nightly drift check reports differences instead of repairing them silently. This follows prior-art takeaway 6, 'no mutable central store of desired state'.
- Errors land on YAML lines through a model path that the caller resolves. The check run gets around GitHub's annotation caps, which is a better developer experience than any off-the-shelf GitOps tool gives (errors-in-ci.md).

## Findings

### delivery-1: The service's dry-run needs the same RBAC as a real apply, which makes the service a second, estate-wide writer

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| risk | high | S10, S11, S1, S6 | weakened | high |

**Concerns:** releasing.md 'What a dry-run is'; security.md 'Threats per boundary' (Service to Vault, Service to ghcr); where-state-lives.md 'Per-Project Flux sources'; overview.md 'Hosting'

Kubernetes authorises a dryRun=All request exactly like the real request: 'to make a dry-run request, you must be authorized to make the non-dry-run request.' To dry-run every changed object of every Project under Flux's field manager, the service therefore needs write permission on everything Flux applies, which in practice is cluster-admin. That one pod would then hold three powers: write access to the API server, the Vault Transit signer and the right to move tags. The 'Hosting' choice ('the deploy credential stays inside the cluster') and 'Flux alone applies' both assume the service cannot write to the cluster, and that is false here. The design also never says Flux runs per tenant. By default kustomize-controller applies as cluster-admin, so a render substituted into another Project's tag (both are signed with the same key) would be applied anywhere. Separately, admission webhooks that do not declare sideEffects None or NoneOnDryRun make every dry-run fail.

**Recommendation.** Adopt Flux's multi-tenancy lockdown. Give each admitted Project a namespace-scoped ServiceAccount, set spec.serviceAccountName on its Kustomization, and run kustomize-controller with --default-service-account and --no-cross-namespace-refs. Have the service dry-run by impersonating that same per-Project ServiceAccount, with RBAC granting only 'impersonate' on those named accounts and nothing else. Then the dry-run sees exactly the permissions Flux will have, and a compromised service can only do what the Projects' own accounts can do. Use one Vault Transit key per Project, with the matching public key in that Project's OCIRepository verify secret, so that a render signed for Project B fails verification on Project A's tag. Add a check that fails when any ValidatingWebhookConfiguration or MutatingWebhookConfiguration in the cluster lacks sideEffects None or NoneOnDryRun. Record these as additions to the trust-boundary table.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| Flux multi-tenancy lockdown (kustomize-controller flags plus per-tenant ServiceAccount) | Documented, supported Flux configuration. Flux v2.9.6 released 2026-10-01; CNCF graduated. | One ServiceAccount and Role per Project, generated by the compiler into the platform render. No new code. |
| Per-Project Vault Transit keys | Vault Transit plus cosign's hashivault:// KMS provider, documented in the Sigstore docs. cosign v3.1.4 released 2026-10-20. | N keys to rotate instead of one. Admitting a Project must also create its key. |

**Verification (weakened).** The core claim holds and matters. The Kubernetes docs say 'Authorization for dry-run and non-dry-run requests is identical'. releasing.md 'What a dry-run is' sends every changed object with dryRun=All. No design page mentions RBAC for the service, per-Project ServiceAccounts, spec.serviceAccountName or tenancy (grep finds none). So the service needs write permission on everything Flux applies, and kustomize-controller applies as cluster-admin by default. Four parts are overstated. (1) The sideEffects check is close to pointless. The v1 API reference makes sideEffects required with acceptable values 'None, NoneOnDryRun (webhooks created via v1beta1 may also specify Some or Unknown)', and v1beta1 was removed in Kubernetes 1.22, so only legacy objects could carry Some or Unknown. (2) 'Flux alone applies' describes behaviour; it is not an assumption about RBAC. The finding is right that the design never states the service's write power, but it is wrong that the design 'assumes' the service has none. (3) Impersonation narrows the power but does not remove it. The 'impersonate' verb lets a compromised service make real writes as every Project account. The platform Project (the estate repo, which carries the per-Project Flux objects and cluster-scoped objects) still needs a near-cluster-admin account to dry-run against, so the service stays an estate-wide writer through that one. (4) Per-Project Transit keys mean N keys to create and rotate for one maintainer. With spec.serviceAccountName plus targetNamespace, a render substituted from another Project can only damage the victim's own namespace, and the attacker also needs the tag-move credential, so per-Project keys are optional defence in depth, not required. Also, --no-cross-namespace-refs breaks the setup if the per-Project OCIRepository and Kustomization live in flux-system and point at Project namespaces; the finding does not address where these objects live.

**Corrections.** Drop or downgrade the sideEffects check: in admissionregistration.k8s.io/v1 only None and NoneOnDryRun are accepted, so only webhooks created via v1beta1 could carry Some or Unknown. With impersonation, a compromised service can still act as the platform Project's account, which is cluster-wide, so the claim that it can only do 'what the Projects' own accounts can do' understates its reach. Per-Project keys are optional defence in depth, because a per-Project ServiceAccount with targetNamespace already confines a cross-Project substitution to the victim's namespace.

Sources:

- <https://kubernetes.io/docs/reference/using-api/api-concepts/#dry-run-authorization>
- <https://fluxcd.io/flux/installation/configuration/multitenancy/>
- <https://fluxcd.io/flux/components/kustomize/kustomizations/>
- <https://fluxcd.io/flux/components/source/ocirepositories/>
- <https://docs.sigstore.dev/cosign/key_management/overview/>
- <https://github.com/fluxcd/flux2/releases>
- <https://kubernetes.io/docs/reference/kubernetes-api/extend-resources/validating-webhook-configuration-v1/>
- <https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/>

### delivery-2: ghcr does not take GitHub App tokens, so moving tags from the cluster needs a long-lived classic PAT

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| risk | high | S10, S7, S4 | confirmed | medium |

**Concerns:** identity-and-access.md 'Who calls, with what' (row 'Service to GitHub and ghcr'); security.md 'Service to ghcr: the App token is scoped to render/ and host/'; inside-the-service.md 'registry' package

GitHub's packages documentation says 'GitHub Packages only supports authentication using a personal access token (classic)'. The one other path is the GITHUB_TOKEN of a workflow, for packages linked to that workflow's repository. Nothing documents GitHub App installation tokens for ghcr, and community reports of 'installation not allowed to Write organization package' match that. A classic PAT cannot be scoped to the render/ and host/ prefixes. write:packages covers every package the account can write, and the token is long-lived and tied to a person's account. That breaks three statements in the design: 'Nothing holds a long-lived secret for the service', 'App token scoped to render/ and host/', and the S10 blast radius. Flux's pull credential for private renders has the same problem.

**Recommendation.** Spike this before writing the registry adapter: try an App installation token push to an org package. If it fails as documented, pick one of three options and record it as a Proposed record. (a) The service signs in-cluster and returns the signature. A single estate-kit 'promote' workflow then moves the tag with its GITHUB_TOKEN; through per-package 'Manage Actions access', only that workflow's repository gets Write on render/* and host/*. Vault still holds the key, so a compromised workflow cannot produce a valid signature. (b) A registry with scoped robot accounts or workload identity. (c) Accept the classic PAT with a bot account, put it in Vault, rotate it on a check, and say so in the threat table. Option (a) keeps the design's 'no long-lived secret' property.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| GITHUB_TOKEN plus per-package Actions access | Documented GitHub Packages feature; per-package Read/Write/Admin roles. | Tag moves pass through GitHub Actions, so a GitHub outage blocks deploys. It already does today, through the deploy run. |
| Registry with scoped robot accounts (e.g. Quay, Harbor) | Mature products. | One more external system, or the in-cluster registry the design rejected under 'Render store'. |

**Verification (confirmed).** GitHub's packages permissions page still says 'GitHub Packages only supports authentication using a personal access token (classic)' and offers GITHUB_TOKEN for packages tied to the workflow's repository. It does not mention App installation tokens. Community discussion #171423 says GHCR rejects App installation tokens even with packages:read. It drew unanswered 2026 follow-ups through 2026-09-08, and I found no changelog entry announcing a fix. A dangerzone.rocks post from May 2026 also says GHCR only accepts PATs. App installation tokens are scoped by repository and permission, never by package-name prefix, so security.md's 'App token is scoped to render/ and host/' could not hold even if ghcr accepted App tokens. The recommendation to spike this first is proportionate.

**Corrections.** The statement 'Nothing holds a long-lived secret for the service' in identity-and-access.md is about callers of the service, and the design already gives the service a long-lived secret, the GitHub App private key. So the classic PAT adds a broader long-lived secret rather than breaking a no-long-lived-secret property. Option (a) puts GitHub Actions on every tag move, including rollback and host-tag moves. That adds runner start-up latency against S12 and S3, and makes GitHub an outage dependency for rollback, which conflicts with delivery-3's fast path. Flux's pull credential is only needed if the render packages are private, and the design does not say whether they are.

Sources:

- <https://docs.github.com/en/packages/learn-github-packages/about-permissions-for-github-packages>
- <https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry>
- <https://github.com/orgs/community/discussions/171423>
- <https://dangerzone.rocks/news/2026-05-26-ghcr-signer/>

### delivery-3: Rollback and Pause depend on the whole service chain and duplicate Flux's own suspend and digest pin

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| weakness | high | S3, S7, S8, S6 | weakened | high |

**Concerns:** operating.md 'UC-5 Pause or resume a Project' and 'UC-6 Roll back a Project'; diagrams specs.py seq-rollback; choices.md 'Pause and rollback state' and 'Pin' (rejected 'the service patching OCIRepository'); overview.md 'Open: name and kind of the per-Project object'

A rollback re-composes at the old fragment, dry-runs, signs through Vault, moves the tag and dispatches a GitHub workflow. Every part must be healthy during the incident that called for the rollback: the queue (one composition at a time), the compiler, the API server, Vault, ghcr and GitHub. A re-composition can also be refused if Platform Intent or ClusterState has changed since. That fails S3 ('previous signed render serves again within 5 minutes') and S7 exactly when they matter. Pause is a bespoke cluster object whose meaning ('stop moving the tag') overlaps Flux's spec.suspend. Flux already defines the operator interface for both: spec.suspend on the Kustomization, and spec.ref.digest on the OCIRepository, which 'takes precedence over all other fields'. The Flux Operator Web UI (OIDC SSO, RBAC-guarded reconcile, suspend and resume) and the flux CLI write those fields anyway. So the reason given for rejecting 'the service patching OCIRepository' ('no second writer of Flux objects') cannot hold during break-glass.

**Recommendation.** Make the fast path a compare-and-swap tag move back to the Project's last known good render digest. That render is already signed, so the path needs no Vault and no composition, only a dry-run of the old render against today's cluster. Fall back to a re-composition only when that dry-run fails. Write a break-glass runbook that works with the service, Vault and GitHub all down: 'flux suspend kustomization `<p>'` or set spec.ref.digest on the OCIRepository to a retained signed digest. Retention already keeps the last 20 renders. Decide the open Pause object question in favour of the Kustomization's spec.suspend, or a field the platform render maps onto it, rather than a new CRD. Test that rollback meets S3 with Vault scaled to zero.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| Flux Kustomization spec.suspend plus OCIRepository spec.ref.digest | Stable v1 APIs in Flux v2.9.6 (2026-10-01). | The service must reconcile its view from Flux objects instead of owning the state. |
| Flux Operator Web UI | Ships inside Flux Operator, which is active (v0.61.0, 2026-10-01). OIDC SSO plus Kubernetes RBAC; reconcile, suspend and resume actions. | No rollback-to-release action and no Release Unit view. Could replace part of the Vue UI for operators. |
| Flagger automatic rollback | Flagger v1.45.0 (2026-09-01), active. | Covers only a failed analysis (S2), not a rollback the operator starts after promotion. |

**Verification (weakened).** The core point is right. operating.md 'UC-6' says the service 're-composes at that fragment'. The ClusterState snapshot is digested into the render key, so a cache hit is unlikely and the re-composed render must be signed through Vault. That conflicts with S3's 'previous signed render serves again' and with S7. A fast path that moves the tag back to a retained signed digest after a dry-run is sound and needs no new tool. Three parts are overstated. (1) seq-rollback in specs.py shows only dispatch and watch, not compose, sign or tag, so the claim that GitHub dispatch blocks the tag move is inferred, not stated; the design is ambiguous there. (2) Mapping Pause onto Kustomization spec.suspend changes its meaning. The design's Pause means 'stop moving the tag, Flux keeps serving'. spec.suspend stops all reconciliation of the Project, including drift correction and pruning, and it would make the service a writer of Flux objects, which the 'Pin' choice rejected. (3) The argument that the 'no second writer' reason 'cannot hold during break-glass' does not follow. A human running flux suspend in an emergency is a documented exception, not the service writing Flux objects on the normal path. A break-glass runbook is still worth writing. Flux Operator v0.61.0 (2026-10-01) is current, and its Web UI offers OIDC SSO plus RBAC-guarded reconcile, suspend and resume (listed for the Helm release dashboard), but it has no rollback.

**Corrections.** The rollback sequence in specs.py does not show compose, sign or tag-move steps, so dependence on GitHub is inferred. Kustomization spec.suspend stops all reconciliation, not just tag movement, so it is not equivalent to the design's Pause. The Web UI's suspend and resume are documented for the Helm release dashboard, and it has no rollback action. Keep the break-glass runbook, but do not use break-glass as an argument against the normal-path single-writer rule.

Sources:

- <https://fluxcd.io/flux/components/kustomize/kustomizations/>
- <https://fluxcd.io/flux/components/source/ocirepositories/>
- <https://fluxoperator.dev/web-ui.md>
- <https://github.com/controlplaneio-fluxcd/flux-operator/releases>
- <https://github.com/fluxcd/flagger/releases>

### delivery-4: The service is an edge-triggered request/stream orchestrator where a small level-triggered reconciler would do

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| alternative | high | S4, S5, S6, S13, S15 | weakened | medium |

**Concerns:** inside-the-service.md 'The rollout core', 'The event log', 'One replica'; releasing.md 'Failure paths'; operating.md 'Rollouts no Project run started' ('Missed triggers heal on a timer'); identity-and-access.md 'Authenticating a deploy job'; choices.md 'Rollout log' and 'Concurrency'

The service puts a lot of bespoke machinery on the deploy path: a deploy API, natural-key idempotency, a coalescing queue, a rollout state machine, an append-only Postgres log with versioned events, upcasters and 400-day retention, an SSE stream with resume by sequence number, a rollout-token exchange, workflow dispatch, and a timer that heals missed triggers. The timer is the giveaway: the design is edge-triggered. The research's own takeaway 7 recommends many small level-triggered controllers coordinating through API objects, and so do the Borg/Omega/Kubernetes papers. Is the service needed at all? Partly. CI plus Flux alone cannot meet S1 without cluster credentials in CI, because Flux has no dry-run-only mode, and Vault signing should stay in-cluster. So something must dry-run and sign inside the cluster. It does not need to be a request-driven server with its own database. Flux now provides several of these pieces. A generic-oidc Receiver verifies GitHub Actions OIDC tokens with CEL on their claims (for example repository_id and job_workflow_ref) and can filter which resources reconcile by those claims. Kustomization status, CEL health checks and notification providers (commit status, PR comment) report progress. ResourceSet in Flux Operator templates per-tenant OCIRepository and Kustomization objects from inputs.

**Recommendation.** Write a Proposed record to reshape the service into a level-triggered composer. Desired state is 'the latest signed fragment tag of each admitted Project plus Platform Intent'. The composer reconciles toward it on change and on an interval, and writes progress as Kubernetes conditions plus GitHub Deployment statuses. Publishing the fragment becomes the deploy request. The CI job watches by polling the Deployment status or the Kustomization and Canary status through the service's read API. That removes the deploy POST semantics, the rollout token exchange, SSE resume and the missed-trigger timer, since level triggering is idempotent and self-healing by construction. Demote Postgres to a disposable cache, or drop it in favour of GitHub Deployments plus Tempo/Loki plus signed promotion records (see delivery-5); S15 is already answered by those. Keep the one-composition-at-a-time rule; a single-replica reconciler gives it for free. Use Flux Operator's ResourceSet, or the compiler, for the per-Project Flux objects. Do not adopt Kargo or Argo CD for this estate (see alternatives).

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| Kargo | Active; v1.13.0 in release candidate (rc.4, 2026-10-21). Built by Akuity, not a CNCF project. | A promotion engine with freight history, verification and a UI. Its step catalogue centres on git-*, kustomize-*, helm-* and argocd-update, and it 'complements Argo CD'. It writes desired state to Git, which the design rejected ('Git holds no digests'), and adds an API server, controller and UI on Raspberry Pi workers. It only pays off with several environments, which the design does not have. |
| Argo CD Source Hydrator plus Argo Rollouts | Argo CD v3.5.6 stable, v3.6.0-rc4 (2026-10-22). Source Hydrator beta since v3.5 and Git-only output. Argo Rollouts v1.10.1 (2026-10-12). | The rendered-manifests pattern done well, but in Git branches, not signed OCI. Replacing Flux and Flagger would be a second port for no gain on the priorities. |
| Flux image automation | image-automation-controller v1.2.5 (2026-08-31), v1 API. | Writes image references into Git, which contradicts the sealed-fragment choice. Not a fit. |
| kro | kubernetes-sigs subproject; ResourceGraphDefinition is v1alpha1; v0.9.4 with v0.10.0-rc.0 (2026-09-22). | Composes custom APIs inside the cluster. It does not do promotion, signing or estate-wide checks, and it is alpha. Not for this path. |
| Flux generic-oidc Receiver | Documented in the Flux v2.9 notification docs; validates GitHub OIDC tokens with CEL. | Can replace the service's trigger endpoint and auth for 'reconcile now', but not the dry-run or signing. |
| Flux Operator ResourceSet | fluxcd.controlplane.io/v1; Flux Operator v0.61.0 (2026-10-01). | Generates per-Project Flux objects from inputs; another operator to run. |

**Verification (weakened).** The observation about how much bespoke machinery sits on the deploy path is fair for a one-maintainer budget. Flux's generic-oidc Receiver does exist, with CEL validations over OIDC claims and claims available in resourceFilter. The proposed reshaping does not follow cleanly. (1) It drops two settled choices without new facts: 'Rollout visibility', where every rollout is a run with environment approval gates, and the rejection of service-created Deployments. If publishing a fragment is the deploy request, the production-environment approval check on the OIDC token disappears unless the composer verifies the fragment's keyless signature identity (job_workflow_ref plus environment), which the finding never designs. (2) The design's 'timer that heals missed triggers' is already the level-triggered safety net the finding asks for, so this is a difference of degree. (3) Dry-run, signing, the one-composition-at-a-time queue and per-Project status all remain, and so does the deploy job's progress view, now done by polling. The saving is mainly the SSE stream, the token exchange and the event log, which the 'Rollout log' and 'Delivery semantics' choices already weighed. (4) Takeaway 7 in prior-art.md concerns separate controllers for workloads and hosts coordinating through API objects; it is not a verdict on the service's request API. Kargo's current release is v1.12.4 (2026-10-12); the claimed v1.13.0-rc.4 is not on the first releases page. The recommendation against Kargo and Argo stands.

**Corrections.** The design already heals on a timer, so it is a hybrid, not purely edge-triggered. A fragment-publish trigger would need its own authentication design, verifying signer identity and environment, to keep the production approval gate. Takeaway 7 is about host versus workload controllers. Kargo's latest stable is v1.12.4 (2026-10-12).

Sources:

- <https://fluxcd.io/flux/components/notification/receivers/>
- <https://fluxoperator.dev/docs/crd/resourceset/>
- <https://fluxcd.io/blog/2026/02/flux-v2.8.0/>
- <https://github.com/akuity/kargo/releases>
- <https://kargo.io/llms.txt>
- <https://argo-cd.readthedocs.io/en/latest/user-guide/source-hydrator/>
- <https://github.com/argoproj/argo-cd/releases>
- <https://github.com/argoproj/argo-rollouts/releases>
- <https://github.com/fluxcd/image-automation-controller/releases>
- <https://kro.run/docs/overview>
- <https://github.com/kubernetes-sigs/kro/releases>

### delivery-5: The prod tag is mutable, its history lives in a service-owned database, and the signature binds no Project, environment or order

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| best-practice-gap | medium | S11, S15, S10, S3 | weakened | medium |

**Concerns:** where-state-lives.md 'Every fact' (Current render, Release history); overview.md 'Risks: No PR-reviewable pin'; choices.md 'Pin' and 'Retention'; security.md 'Service to ghcr'

OpenGitOps principle 2 asks that desired state be 'stored in a way that enforces immutability, versioning and retains a complete version history'. Here desired state is a mutable OCI tag. The history of where it pointed lives only in the Postgres event log, a mutable store owned by the service, and in GitHub Deployments. Renders are garbage-collected after 20 or 90 days. A cosign signature covers a digest only, and Flux's key-based verify checks the signature, not claims. So anyone who can move tags can roll a Project back to any older signed render, freeze it, or, with one shared key, point it at another Project's render. These are TUF's rollback, freeze and mix-and-match attacks. The nightly drift check would notice only within 24 hours.

**Recommendation.** Make every promotion an immutable, signed record in the registry itself. Push the render under a never-moved tag such as `render/<p>:prod-<seq>`, or as a semver tag like `0.<seq>.0`, and attach a signed in-toto statement (project, environment, seq, previous digest, render key, rollout id, approver). Then either let Flux follow ref.semver so the newest record wins and tags never move, or keep prod as a convenience alias that the drift check verifies against the newest record. A rollback becomes a new, higher record pointing at old content, so the pointer's full history lives in the registry, the event log can be rebuilt, and retention keeps every render a record names. Pair this with the per-Project keys from delivery-1. Add a check that fails if retention would delete a render that a record within 400 days points at.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| OCIRepository ref.semver over immutable promotion tags | Stable Flux v1 API (source-controller v1.9.6, 2026-10-01). | The registry's tag list becomes the ledger; the tag namespace grows (bounded by retention). |
| Signed in-toto promotion statements (cosign attest) | cosign v3.1.4 (2026-10-20); Flux 2.8 added cosign v3 verification. | Flux verifies the signature but not the predicate, so ordering is enforced by tag immutability and checked by the drift check, not by Flux. |

**Verification (weakened).** The facts are right. OpenGitOps principle 2 reads as quoted. Flux's key-based verify checks only the signature, and matchOIDCIdentity applies only to keyless signatures. One shared key allows rollback, freeze and mix-and-match by anyone who can move tags. The remedy does not work on ghcr. ghcr has no tag immutability: community discussion #181783 is an open request, and GitLab, ECR and Docker Hub have the feature but GitHub does not. So 'never-moved tags' are convention only. With ref.semver, an attacker who can write tags pushes a higher version, such as 0.99999.0, pointing at an old signed render. That is still a rollback attack, and it freezes the Project permanently, because legitimate sequence numbers must then exceed it. The finding concedes Flux does not check the predicate, so ordering is enforced by nothing at admission time. Detection stays with the nightly drift check, which the design already has ('latest release on GitHub' compared with the prod tag). The 400-day retention check is the useful part. The severity depends on how far the tag-write credential reaches, which is delivery-2's issue.

**Corrections.** ghcr does not offer tag immutability, so 'immutable promotion tags' cannot be enforced there. ref.semver makes the freeze attack worse, not better. The existing drift check already compares the prod tag against the latest GitHub release. The effective mitigations are a narrow tag-write credential (delivery-2) and per-Project keys, not semver tags.

Sources:

- <https://opengitops.dev/>
- <https://fluxcd.io/flux/components/source/ocirepositories/>
- <https://theupdateframework.github.io/specification/latest/>
- <https://fluxcd.io/blog/2026/02/flux-v2.8.0/>
- <https://github.com/sigstore/cosign/releases>
- <https://github.com/orgs/community/discussions/181783>

### delivery-6: The hand-rolled dry-run misjudges new namespaces and CRDs and drifts from Flux's apply; reuse fluxcd/pkg/ssa

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| weakness | medium | S1, S4, S12 | weakened | medium |

**Concerns:** releasing.md 'What a dry-run is'; inside-the-service.md 'cluster' package ('Server-side dry-run, through client-go'); CONTEXT.md 'Dry-run'

A dry-run does not persist anything. So when a render introduces a namespace, or a CRD together with a CR of that kind, the dependent objects fail dry-run with 'namespace not found' or 'no matches for kind'. That gives false refusals for exactly the first release of a Project and for any component that adds a CRD. Flux solves this with staging. Its fluxcd/pkg/ssa ResourceManager applies cluster-scoped and class definitions first, waits for them, then applies the rest (ApplyAllStaged). It also offers a server-side dry-run Diff and Secret masking. A client-go reimplementation will diverge from Flux's apply semantics over time: field managers, immutable-field force, and the SSA ignore rules added in Flux 2.9. The dry-run would then pass things Flux rejects, or the reverse. The design does not say what the dry-run does in these cases.

**Recommendation.** Build the cluster adapter on fluxcd/pkg/ssa, the same library and field-manager settings kustomize-controller uses (v0.80.0 published 2026-10-14), impersonating the Project's ServiceAccount (delivery-1). Define, in a record with a fixture, a distinct dry-run outcome: 'unverifiable: depends on a CRD or namespace this render introduces'. Dry-run the definitions, then validate the dependent objects offline against the CRD's openAPIV3Schema, and let Flux's own pre-apply dry-run in ApplyAll be the last line of defence. Add fixtures for a first release and for a CRD-plus-CR render so S1 is tested both ways.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| fluxcd/pkg/ssa | v0.80.0 published 2026-10-14; the apply engine of kustomize-controller v1.9.6. | Ties the service to Flux's library release cadence, which is the point: the dry-run tracks the applier. |
| flux diff kustomization / flux build | Flux CLI v2.9.6. | Same engine, but as a CLI with cluster credentials; suits a break-glass check, not the service. |

**Verification (weakened).** The core claim is right. A dry-run persists nothing, so objects in a namespace the same render introduces, or custom resources of a CRD it introduces, fail dry-run, and releasing.md 'What a dry-run is' says nothing about these cases. The remedy is mis-sold, though. In fluxcd/pkg/ssa, ApplyAllStaged stages by really applying CRDs and namespaces first, then waiting. The dry-run path, ResourceManager.Diff in manager_diff.go, returns NewDryRunErr on any dry-run failure except a forced re-create, and the flux CLI's diff (internal/build/diff.go) only aggregates errors. Neither special-cases missing namespaces or kinds, so adopting the library does not remove the false refusals. The part of the recommendation that does fix it is the 'unverifiable' outcome with offline validation against the CRD's openAPIV3Schema. Reusing pkg/ssa (v0.80.0 published 2026-10-14) is still worthwhile for parity with Flux's field-manager, force and ignore-rule behaviour, at the cost of following its frequent 0.x API changes, which counts against S4. Project namespaces may be created by the platform render at admission (UC-7), which would remove the first-release namespace case; the design does not say.

**Corrections.** fluxcd/pkg/ssa does not solve dry-run of objects that depend on a CRD or namespace introduced in the same render. Staging needs real applies, and Diff propagates the dry-run error. The fix is the explicit 'unverifiable' outcome plus offline schema validation. pkg/ssa is a pre-1.0 library, so adopting it adds upgrade churn against S4.

Sources:

- <https://pkg.go.dev/github.com/fluxcd/pkg/ssa>
- <https://kubernetes.io/docs/reference/using-api/api-concepts/#dry-run-authorization>
- <https://fluxcd.io/flux/components/kustomize/kustomizations/>
- <https://github.com/fluxcd/kustomize-controller/releases>
- <https://github.com/fluxcd/pkg/blob/main/ssa/manager_diff.go>
- <https://github.com/fluxcd/flux2/blob/main/internal/build/diff.go>

### delivery-7: The service sits on the traffic-switch path, and the 10-minute deploy budget is not split into its stages

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| risk | medium | S12, S7, S2, S6 | weakened | medium |

**Concerns:** operating.md 'UC-9 Gate a traffic switch'; releasing.md 'UC-3 Deploy a release' step 3; overview.md 'Service levels' (deploy p95 under 10 min, 99% availability); inside-the-service.md 'One replica'

Flagger's confirm-promotion hook pauses promotion until it returns HTTP 200, and a non-2xx or timeout halts advancement. With the Release Gate inside a single-replica service at a 99% target (about 7 hours a month), every canary in the estate stalls whenever the service restarts or Postgres is down. S7 (deploys fail loudly, serving unaffected) is met, but rollouts stuck mid-canary are not 'Serving'. On speed, a one-line change crosses many stages: the release-please PR, the release, the deploy job, a queue shared by the whole estate, compose, dry-run, sign and push. Flux then notices the tag only on the OCIRepository interval or a reconcile request; there is no ghcr Receiver type. Flagger then runs interval × iterations of analysis, and the Release Gate waits for every member. Nothing assigns a budget per stage, so S12's p95 cannot be checked during the shadow phase.

**Recommendation.** Write a per-stage budget into the service-levels record and measure each stage during the shadow phase. After a tag move, trigger reconciliation at once, either by setting the reconcile.fluxcd.io/requestedAt annotation or through a generic-oidc Receiver, and keep the OCIRepository interval as the fallback. Make the Release Gate's decision depend only on cluster state (Canary and workload conditions of the Release Unit members) so it can be answered by a tiny stateless endpoint, or by a Flagger confirm-promotion hook in a separate deployment with two replicas. That way a service or Postgres restart never blocks a promotion. Keep Flagger: it is active (v1.45.0, 2026-09-01) and maintained by the Flux project. Argo Rollouts (v1.10.1) only pays off with Argo CD.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| Flagger confirm-promotion with a stateless gate | Flagger v1.45.0 (2026-09-01); webhook semantics documented. | Splits one small handler out of the service. |
| Argo Rollouts AnalysisTemplates | v1.10.1 (2026-10-12), active. | Replaces Deployments with Rollout objects; a second ecosystem beside Flux. |

**Verification (weakened).** The source contradicts the impact claim. In Flagger's pkg/controller/scheduler_hooks.go, runConfirmPromotionHooks on error only sets the phase to WaitingPromotion, emits an event and returns false. It increments no failed checks and does not roll back, and it is retried on the next interval. So a restart of the service or Postgres delays promotion by about the downtime plus one interval; it does not stall or fail canaries. A 99% availability target is a floor, not 7 hours of expected monthly downtime, and with one replica a pod restart takes seconds to minutes. The Release Gate's answer, 'every member of the Release Unit is healthy', is cluster state, so the claim that Postgres is on the gate path is an assumption. Splitting the gate into a separate two-replica deployment adds a component for little gain. The per-stage budget and an immediate reconcile after a tag move are good, cheap ideas. Use a generic or generic-oidc Receiver rather than the requestedAt annotation, because the annotation makes the service a writer of Flux objects, which the 'Pin' choice rejected. There is no ghcr Receiver type; the closest is 'github'.

**Corrections.** A failing confirm-promotion hook pauses promotion in WaitingPromotion and retries; it does not count failed checks or roll back. The service being down delays promotion; it does not leave rollouts stuck. Prefer a Receiver over the requestedAt annotation to keep a single writer of Flux objects.

Sources:

- <https://docs.flagger.app/usage/webhooks>
- <https://github.com/fluxcd/flagger/releases>
- <https://fluxcd.io/flux/components/source/ocirepositories/>
- <https://fluxcd.io/flux/components/notification/receivers/>
- <https://github.com/argoproj/argo-rollouts/releases>
- <https://github.com/fluxcd/flagger/blob/main/pkg/controller/scheduler_hooks.go>

### delivery-8: The service signs whatever image digests a fragment names; no build provenance is checked

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| missing | medium | S10, S11 | weakened | medium |

**Concerns:** releasing.md 'The three runs' (candidate images built on the release PR, promoted on release); security.md 'Runner to edge: Tampering'; choices.md 'Image lock' and 'Release PR images'

S10 requires that a compromised Project 'cannot sign anything not built from its own sources'. The design seals digests into the fragment and signs the render, but nothing checks where those images came from. A compromised Project workflow can name an attacker-built image, or another Project's image, and the service will sign a render that runs it. The Vault signature then vouches for something nobody verified. GitHub artifact attestations reach SLSA v1.0 Build Level 2 on their own and Build Level 3 when the build runs in a shared, isolated reusable workflow. That is exactly the pinned estate-kit reusable workflow the design already requires through job_workflow_ref. Private repositories use GitHub's own Sigstore instance without a transparency log; whether the account's plan allows attestations on private repositories was not confirmed.

**Recommendation.** Build and attest images in the pinned estate-kit reusable workflow (actions/attest with push-to-registry). Before composing, have the service verify that every digest in the fragment has provenance whose source repository_id matches the Project's admission and whose signer workflow is the pinned estate-kit workflow. Refuse otherwise, with a diagnostic code and fixture. Enforce the same rule at admission for defence in depth, with Kyverno verifyImages (v1.19.2, 2026-10-21). Prefer Kyverno over sigstore policy-controller, whose last release, v0.15.1, was on 2026-03-26. Confirm attestation availability for private repositories on the current plan first.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| GitHub artifact attestations (actions/attest) | GA; SLSA v1.0 Build L2, L3 with an isolated reusable workflow. | Private repositories rely on GitHub's Sigstore instance (no public log); plan availability to be confirmed. |
| Kyverno verifyImages | v1.19.2 (2026-10-21), CNCF, very active. | Another admission webhook, which must declare sideEffects None for the dry-run (delivery-1). |
| sigstore policy-controller | v0.15.1 (2026-03-26); slower cadence. | Narrower scope; less active than Kyverno. |

**Verification (weakened).** The gap is real. No design page mentions provenance, attestation or SLSA, yet S10 requires that a compromised Project 'cannot sign anything not built from its own sources'. The candidate digests built on the release PR and promoted at release are a handoff an attacker with push rights could interfere with. The recommended mechanism has a plan problem the finding left open. GitHub's documentation (per the search summary) limits artifact attestations to public repositories on Free, Pro and Team plans, with private and internal repositories requiring Enterprise Cloud. If the Project repositories are private on a non-Enterprise plan, actions/attest is not available, and the alternative, cosign keyless signing on the public Sigstore instance, publishes repository names to the public Rekor log. The rule 'every digest has provenance from the Project's repository' would also refuse legitimate third-party images, such as upstream databases, unless there is an allowlist, which the finding omits. Kyverno v1.19.2 (2026-10-20/21) and policy-controller v0.15.1 (2026-03-26) are as stated. An admission webhook adds load and must answer dry-runs, though in admissionregistration v1 only None and NoneOnDryRun are allowed (see delivery-1).

**Corrections.** Artifact attestations on private repositories need GitHub Enterprise Cloud; on Free, Pro or Team plans they work only on public repositories. The provenance rule needs an allowlist for third-party images. Kyverno v1.19.2 was tagged late on 2026-10-20.

Sources:

- <https://docs.github.com/en/actions/concepts/security/artifact-attestations>
- <https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations>
- <https://github.com/kyverno/kyverno/releases>
- <https://github.com/sigstore/policy-controller/releases>
- <https://docs.github.com/actions/security-guides/using-artifact-attestations-to-establish-provenance-for-builds>

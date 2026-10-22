# Review: supply chain and security

Part of the [design review](README.md). Each finding was checked by a second
reviewer that tried to refute it; its verdict and corrections follow the finding.

## Verdict

The basic design is sound: the service signs only after a dry-run succeeds, the key is a non-exportable Vault Transit key, only digest-named artifacts are admitted, identity is bound to repository_id, and the STRIDE table and matrix are checked by tests. S10 still fails today. Three gaps cause it. Nothing proves that the image digests a Project seals into its fragment were built from that Project's sources, so the service will sign whatever a fragment names. The OIDC check ignores event_name and job_workflow_sha. Nothing in the cluster limits what a signed render may touch: there is no Flux tenant lockdown, and the service's dry-run RBAC equals write access. S11 holds against tampered bytes but not against replay: an older or cross-copied signed render still verifies. One key signs both renders and host tags, and that key lives in an in-cluster Vault with no recovery key. Two identity claims in the design do not hold. GHCR does not accept GitHub App installation tokens, so the service has no scoped way to push renders. Flagger and Flux cannot send projected service-account tokens, so in-cluster callers cannot be identified the way the design says. Nearly every fix uses built-in mechanisms (GitHub artifact attestations or a service-side build register, ValidatingAdmissionPolicy, Pod Security Admission, Flux lockdown flags, a second Transit key). None of them needs a new admission engine.

## What the design gets right

- Admission binds to repository_id rather than the repository name. GitHub has moved the same way: since 15 July 2026, new and renamed repositories get an OIDC sub claim that includes owner and repository IDs.
- The service signs nothing until the API server accepts a dryRun=All, and a test proves it (security.md, 'Service to Vault'). Release images are built on the PR and promoted by digest, so what dry-ran is what deploys.
- The signing key is a non-exportable Vault Transit key used through cosign's hashivault:// provider (also openbao://). A Transit key cannot be marked non-exportable again once export is enabled, so this choice is cheap to keep and costly to undo.
- Only signed, digest-named artifacts cross into the cluster (where-state-lives.md). Image digests are sealed into the fragment, so a tampered image byte stream fails on digest. S11 for images then reduces to 'every image reference is a digest'.
- The only allowed caller is the pinned reusable workflow. GitHub's docs say this pattern gives the isolation SLSA Build L3 requires.
- Flux verifies OCIRepository signatures and retries with backoff when verification fails, so a tampered render never replaces a good one (S7 and S11). The Secret can hold several .pub keys, which allows rotation without downtime.
- There is a STRIDE table per boundary and an authorization matrix, and a test fails on any route without a row. Most designs at this size have neither.
- Host trust has two layers: a Vault-signed host tag plus a Nix narinfo signature. Appliers pull, so no node holds credentials to another node.
- Shadow tags are unsigned and refused by admission, so the shadow phase cannot leak into serving.

## Findings

### supply-1: Nothing proves an image or fragment was built from its Project's own sources, so the service signs any digest a fragment names

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| missing | high | S10, S11, S15 | weakened | high |

**Concerns:** security.md, STRIDE row 'Runner to edge / Tampering: Fragments are signed and named by digest'; releasing.md, 'The three runs'; where-state-lives.md, 'Image digests'

S10 requires that a compromised Project cannot get anything signed that was not built from its own sources. The design seals image digests into the Intent Fragment, and the service signs the composed render. Nothing checks where those digests came from. A Project fragment can name an image built by another Project, a digest from any public registry, or an image pushed by hand, and the Vault key signs it all the same. The STRIDE row says fragments are signed, but no page names a signer or a verifier: the deploy sequence has the CI job publish the fragment to ghcr and the service pull it by digest. The reusable workflow also builds images, running the Project's own build scripts and Dockerfile, in the same run that requests the estate-kit OIDC token. Any build step that can reach ACTIONS_ID_TOKEN_REQUEST_TOKEN can mint a deploy token. SLSA v1.2 (current since November 2025) calls this a Build L3 failure: signing material must be isolated from the build.

**Recommendation.** Add a provenance gate before signing, and record it as a Proposed decision with a failing-check fixture. (1) Split the reusable workflow into a build job with no id-token permission and an attest-and-deploy job that receives only digests as outputs. (2) Have the attest job run actions/attest (currently v4; attest-build-provenance v4 is a wrapper over it) on every image and on the fragment. Have the service verify the bundles with sigstore-go (v1.3.0, July 2026) before composing. The certificate's repository_id and job_workflow_sha must match the deploy token, and the attested source ref must be the release tag or the release-please PR head. (3) GitHub artifact attestations work in private repositories only on GitHub Enterprise Cloud. If Project repositories are private on Free or Team, use a cheaper equivalent instead: the attest job calls a service route ('register build') with its OIDC token and the digests it pushed, and the service refuses any fragment that names a digest not registered under the same repository_id. The event log then becomes the provenance record, which also answers S15. (4) Allow third-party images (postgres and the like) only by digest from an allowlist in Platform Intent. (5) State in the design that the Project is always derived from the token's repository_id and never from the request body, and add a matrix test that tries to deploy another Project's fragment digest.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| GitHub artifact attestations (actions/attest v4) | GA since June 2024. Public repositories use the Sigstore public-good instance; private repositories use GitHub's own Sigstore instance (no transparency log) and need Enterprise Cloud | Standard SLSA provenance that gh attestation verify and sigstore-go can check. Free for public repos, gated by plan for private repos. Verification needs the Sigstore trusted root, which is a TUF fetch that can be cached. |
| Service-side build register (OIDC-authenticated digest registration) | Bespoke; about one route and one table in the existing Postgres | Works on any GitHub plan and adds no Sigstore dependency. It is not portable SLSA provenance, and the service becomes the record. |
| cosign keyless signing in CI (Fulcio public good) | cosign v3.1.4, 20 Oct 2026 | Works on any plan. For private repos it publishes repository names and workflow refs to the public Rekor log. |

**Verification (weakened).** The gap is real. security.md's STRIDE row says 'Fragments are signed and named by digest', but no page names who signs a fragment or who verifies it, and nothing checks where an image digest came from. The threat is overstated against S10, though. The S10 attacker controls the Project repository, so a provenance check that the image was 'built in this repo's CI' still passes for whatever malicious code that attacker pushes. The gate only blocks digests from outside the repository: another Project's image, a public image or a hand-pushed one. Without supply-4's Flux lockdown, such an image runs in the attacker's own namespace. The token-minting argument also misreads releasing.md. The release run builds nothing; it 'promotes the candidate digests'. Candidate images are built on the release-please PR, and a PR token can only plan or dry-run. Steps inside a Docker build do not see the runner's ACTIONS_ID_TOKEN_REQUEST_TOKEN unless it is passed in. Splitting the build job from the token job is still cheap and right. Verifying Sigstore bundles in the service puts a TUF trusted-root fetch on the deploy path, which S7 has to absorb. The service-side 'register build' route (option 3) is the cheaper fit for one maintainer.

**Corrections.** Most Project repositories in JorisJonkers-dev are public: deploy-kit, delivery, estate-dashboard, auth-api, immich, jellyfin and others. The private ones are estate, nix-config, fleet-infra and workspace. GitHub artifact attestations are therefore free for nearly every Project, using the Sigstore public-good instance, so the Enterprise Cloud caveat mostly does not apply. actions/attest-build-provenance v4 is a wrapper on actions/attest, which is checked. sigstore-go v1.3.0 (30 July), cosign v3.1.4 (20 October 2026) and SLSA v1.2 (24 November 2025) are checked. Lower severity to medium. Without Flux lockdown and an image allowlist, provenance alone does not bound the harm.

Sources:

- <https://docs.github.com/en/actions/concepts/security/artifact-attestations>
- <https://github.com/actions/attest-build-provenance>
- <https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations>
- <https://slsa.dev/spec/v1.2/build-track-basics>
- <https://slsa.dev/blog/2025/11/announce-slsa-v1.2>
- <https://github.com/sigstore/sigstore-go/releases>
- <https://github.com/sigstore/cosign/releases>
- <https://github.com/orgs/JorisJonkers-dev/repositories>
- <https://docs.github.com/en/enterprise-cloud@latest/actions/concepts/security/artifact-attestations>

### supply-2: The OIDC check ignores event_name and pins the workflow by ref, so pull_request_target runs pass as releases

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| weakness | high | S10, S1 | weakened | high |

**Concerns:** identity-and-access.md, 'Who calls, with what', Project CI row; choices.md, 'CI identity'; security.md, matrix columns 'Project CI (release)' and 'Project CI (PR)'

The check reads repository_id, job_workflow_ref at a pinned ref, and environment production, and 'a PR ref may only plan or dry-run'. A GitHub change effective 8 December 2025 breaks the ref-based part. pull_request_target now always runs the default branch's workflow with GITHUB_REF set to the default branch, and environment branch rules are evaluated against that ref. A Project workflow on pull_request_target that calls the estate-kit reusable workflow and checks out the PR head therefore receives a token with ref=refs/heads/main and environment=production. That token cannot be told apart from a real release on the claims the design checks, while it runs attacker code from a fork. Three more gaps: (a) job_workflow_ref names a tag or branch, which can move, whereas job_workflow_sha is immutable. (b) The environment claim proves only that the job named an environment. Its required reviewers are configured by the Project's own admins, so it is not an approval the service can rely on. (c) runner_environment and repository_owner_id are not checked, so a self-hosted runner or a transferred repository is not recognised.

**Recommendation.** Write the claim policy as a table in the identity page and in a contract test with one passing and one failing token fixture per row. Deploy requires event_name in {release, workflow_dispatch}. Accept workflow_dispatch only for a run the service itself dispatched, matched by run_id from the event log. Plan and dry-run require event_name=pull_request. Refuse pull_request_target, workflow_run, issue_comment and dynamic outright. Pin job_workflow_sha to the estate-kit release SHAs listed in Platform Intent, not to a ref. Require repository_owner_id to be the organisation, runner_environment=github-hosted, and ref_type=tag for deploys. Never read sub, because its format is customisable per repository and changed on 15 July 2026. Treat environment as an audit field, not as authorisation.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| Custom properties as claims (repo_property_*) | Documented in GitHub's OIDC reference, 2026 | An org-level property such as `estate_project=<p>` can be added to the token. It is useful as a cross-check but is set by org admins, so it complements repository_id rather than replacing it. |

**Verification (weakened).** The facts are verified. From 8 December 2025, pull_request_target takes its workflow from the default branch, sets GITHUB_REF to the default branch, and checks environment rules against that branch. The OIDC claims job_workflow_sha, event_name, ref_type, runner_environment, repository_owner_id and repo_property_* exist. Repositories created after 15 July 2026 use an immutable sub format. The attack is overstated. UC-3 in releasing.md has the production environment's approver allow every deploy, so a pull_request_target job that names production gets no token until the maintainer approves it. A write-only attacker (S10) cannot change environment protection rules, which needs admin, and in this estate the only admin is the maintainer. Calling environment 'not an approval the service can rely on' ignores that. The 'runs attacker code from a fork' step needs the estate-kit reusable workflow, which is our own code, to check out the PR head. Under the new rules the default checkout is the default branch. The cheap hardening still stands and costs one contract test: an event_name allowlist, job_workflow_sha instead of a moving ref, ref_type=tag for deploys, and runner_environment=github-hosted.

**Corrections.** Severity is medium, not high. The 'indistinguishable from a release' token exists only after the environment's required reviewer approves. Keep the environment claim as one input alongside event_name; do not reduce it to audit-only. The rest of the recommendation follows.

Sources:

- <https://github.blog/changelog/2025-11-07-actions-pull_request_target-and-environment-branch-protections-changes/>
- <https://docs.github.com/en/actions/reference/security/oidc>

### supply-3: GHCR does not accept GitHub App installation tokens, so the scoped token that guards tag moves does not exist

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| risk | high | S10, S11, S7 | confirmed | medium |

**Concerns:** identity-and-access.md, 'Service to GitHub and ghcr: GitHub App installation token'; security.md, STRIDE row 'Service to ghcr / Tampering: the App token is scoped to render/ and host/'

GitHub's Container registry documentation says GitHub Packages 'only supports authentication using a personal access token (classic)', or GITHUB_TOKEN for packages linked to the workflow's own repository. It does not mention GitHub Apps. Community bug #171423, open since August 2025 with reports through September 2026, shows App installation tokens are denied by ghcr even for pulls. Package permissions are granted per package, not by name prefix. The mitigation 'App token scoped to render/ and host/' therefore cannot be built as written. In practice the service would hold a classic PAT, a long-lived secret (contradicting 'Nothing holds a long-lived secret') that can write every package its user can reach, including every Project's fragments. Whoever holds it can move any prod or host tag to any older signed render (see supply-5).

**Recommendation.** Before the decision is accepted, run a drill as the estate's own lessons require: try to push a tag to ghcr with an App installation token. If it fails, pick and record one of these. (a) A dedicated machine account whose only package access is write on the render and host packages, its classic PAT stored in Vault and rotated on a timer, with a check that lists the account's package grants and fails on any extra one. (b) Move tag writes into a GitHub Actions job in estate-kit that the service dispatches, using GITHUB_TOKEN with per-package repository access. This adds GitHub to the deploy path, a minute of latency and a dependency for S12. (c) Reopen 'Render store' with this new fact. An in-cluster registry was rejected only because a rebuilt cluster could not pull renders, which a nightly mirror to ghcr would also fix. Option (a) is the least work.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| Machine account plus classic PAT in Vault | Supported by GitHub today | Long-lived but bounded by package grants. Needs a rotation check. |
| zot (CNCF sandbox) in-cluster with mirroring to ghcr | Not re-checked in this review | Accepts OIDC and bearer authentication, so the service could push with its own identity. Adds a component, which works against one-maintainer load. |

**Verification (confirmed).** GitHub's Container registry page and its package-permissions page both still say GitHub Packages 'only supports authentication using a personal access token (classic)', plus GITHUB_TOKEN inside workflows. Neither mentions GitHub Apps or fine-grained tokens. Community discussion #171423 was opened 28 August 2025: App installation tokens get 'denied' on docker pull from ghcr. Its last replies are 4 to 8 September 2026, with no fix and no staff reply. Package permissions are granted per package, not by name prefix. So security.md's mitigation 'the App token is scoped to render/ and host/' cannot be built as written, and identity-and-access.md's 'Service to GitHub and ghcr: GitHub App installation token' does not work for ghcr. A drill before accepting the decision matches the estate's own lesson DR-1.

**Corrections.** Minor overstatement: 'Nothing holds a long-lived secret' in identity-and-access.md is about callers of the service. The GitHub App's private key is already a long-lived secret, so a PAT adds a second one rather than breaking a rule that holds today. Whether the PAT can write 'every Project's fragments' depends on the machine account's grants, which option (a) bounds. The zot alternative was not re-checked and adds a component; option (a) remains the least work.

Sources:

- <https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry>
- <https://docs.github.com/en/packages/learn-github-packages/about-permissions-for-github-packages>
- <https://github.com/orgs/community/discussions/171423>
- <https://github.com/JorisJonkers-dev/estate-kit/blob/main/docs/lesson-candidates.md>

### supply-4: Nothing in the cluster limits what a signed render can change, and the service's dry-run RBAC is write access

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| missing | high | S10, S11, S2 | weakened | high |

**Concerns:** releasing.md, 'What a dry-run is' (dryRun=All under Flux's field manager); operating.md, UC-8; security.md (no row for Flux applying a Project render); where-state-lives.md, 'Per-Project Flux sources'

Isolation between Projects rests entirely on the compiler being correct. No page says which identity Flux applies a Project render with. Without Flux's multi-tenancy lockdown, kustomize-controller applies every render as cluster-admin. A compiler bug, a replayed render, or one Project's render copied under another Project's tag can therefore write into any namespace or create cluster-scoped objects. Separately, a server-side dry-run needs the same RBAC verbs as the real write, so the service's service account must be able to write everything Flux writes. Kubernetes RBAC has no dry-run-only verb. A bug or compromise in the service can apply for real.

**Recommendation.** Use only built-in mechanisms. (1) Turn on Flux lockdown: --no-cross-namespace-refs, --no-remote-bases and --default-service-account. Have the platform render give each Project's Kustomization a serviceAccountName bound to a Role in that Project's namespace. (2) Run the service's dry-run by impersonating that same per-Project service account, so the dry-run also proves the RBAC and the service needs only impersonate rights on those accounts. (3) Add a ValidatingAdmissionPolicy (GA since Kubernetes 1.30) that denies any write from the service's own identity when request.dryRun is false. AdmissionRequest.dryRun is exposed to CEL as request.dryRun. (4) Label each Project namespace for Pod Security Admission 'restricted' in enforce mode, matching the existing offline lint from lesson #530. (5) Add a second ValidatingAdmissionPolicy that refuses any container image without @sha256 in Project namespaces, so S11 holds for images even outside Flux. Give each policy a failing fixture, as Locked records require.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| Kyverno | CNCF graduated 24 March 2026; v1.19.2 released 20 Oct 2026; CEL-based ValidatingPolicy and ImageValidatingPolicy | Can also verify image signatures and attestations at admission. Runs several controllers that are heavy on Raspberry Pi workers, and adds its own upgrade cadence (S4). Its webhook joins the deploy path. |
| sigstore policy-controller | v0.15.1, 26 March 2026; cosign v3 and Sigstore bundle support | Verifies signatures on every pod admission. A ghcr or TUF outage can block pod restarts unless set to fail open, which conflicts with S7. Releases are slower than Kyverno's. |
| Built-in ValidatingAdmissionPolicy plus Pod Security Admission | GA in Kubernetes 1.30+, shipped with k3s | No extra component and no runtime dependency. Cannot verify signatures; it relies on digests in the signed render. |

**Verification (weakened).** The core claim holds. No page names the identity Flux applies a Project render with (a grep of the docs finds no serviceAccountName, tenant or lockdown). Flux's multi-tenancy page confirms that without lockdown kustomize-controller applies as cluster-admin. The lockdown flags are --no-cross-namespace-refs, --no-remote-bases and --default-service-account. RBAC has no dry-run-only verb. The recommendation does not hold together, though. Step (2) runs the service's dry-run by impersonating each Project's service account. Step (3) denies non-dry-run writes from 'the service's own identity'. Under impersonation, an admission request's userInfo is the impersonated account, so step (3) cannot see the writes step (2) makes. A policy keyed on the per-Project account would also block Flux, which applies as that same account. Impersonate rights on accounts that can write are, in effect, write rights. Step (4), enforcing Pod Security Admission 'restricted', may break Projects that need devices or privileges; this needs a drill and exemptions in Platform Intent.

**Corrections.** Choose one of (2) and (3): either the service keeps its own identity and a ValidatingAdmissionPolicy denies its non-dry-run writes, or it impersonates and accepts write-equivalent rights. request.dryRun is reachable as an AdmissionRequest attribute, but the Kubernetes VAP page does not list it explicitly; confirm it with a fixture. Versions checked: Kyverno graduated from the CNCF on 24 March 2026 and v1.19.2 shipped on 20 October 2026; policy-controller v0.15.1 shipped on 26 March 2026, with no release in 7 months. Built-in ValidatingAdmissionPolicy plus Pod Security Admission remains the right choice for one maintainer.

Sources:

- <https://fluxcd.io/flux/installation/configuration/multitenancy/>
- <https://kubernetes.io/docs/reference/access-authn-authz/validating-admission-policy/>
- <https://kubernetes.io/docs/reference/config-api/apiserver-admission.v1/>
- <https://www.cncf.io/announcements/2026/03/24/cloud-native-computing-foundation-announces-kyvernos-graduation/>
- <https://github.com/kyverno/kyverno/releases>
- <https://github.com/sigstore/policy-controller/releases>
- <https://github.com/kyverno/kyverno/releases/tag/v1.19.2>

### supply-5: Signatures do not stop replay, one key controls both Projects and hosts, and losing Vault means losing it

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| weakness | high | S11, S8, S10, S4 | weakened | medium |

**Concerns:** security.md, STRIDE rows 'Service to ghcr' and 'Service to Vault / Disclosure'; hosts.md, 'Signed pointer' and 'When the cluster is down'; choices.md, 'Signing' and 'Host pointer'

A cosign signature binds a manifest digest to the key. It does not bind the Project, the environment or freshness. Whoever can write a tag (see supply-3) can move `render/<p>:prod` back to an older, validly signed render with a known vulnerability, and Flux accepts it. The nightly drift check finds this up to a day later. Copying another Project's signed render and its signature probably verifies too; this should be confirmed in a drill. One Transit key signs both render/ and host/ tags, so leaking its use rights means root on all seven nodes as well as every Project. Vault runs inside the cluster and the key is non-exportable, so losing the cluster's storage loses the key. Every host trusts only that key, so recovery would need break-glass on every node. Separately, the signature format is not fixed. Flux 2.7.x could not verify cosign v3 signatures (support came in Flux 2.8, February 2026). Flux's v3 bundle path has been reported to require matchOIDCIdentity. cosign signs in the bundle format by default since v3. Key-based cosign signing also uploads to public Rekor by default unless told not to, which would publish render repository names and deploy times.

**Recommendation.** (1) Use separate Transit keys for render and host, and per environment once a second one exists. Flux trusts only the render key; appliers trust only the host key. (2) Sign Project, environment and a monotonic rollout sequence as annotations (cosign -a). The host applier, which is our code, refuses any sequence lower than the one it last applied. For Flux, the service compares each Project's applied artifact digest with the event log on every Flux event rather than nightly, and Holds the Project on mismatch. (3) Trust two keys everywhere: the Transit key and an offline recovery key kept off-cluster on a hardware token. Flux accepts several .pub files. Ship Vault Raft snapshots off-cluster and run a key-loss drill. (4) Fix the format in a Proposed record (legacy .sig tag or bundle referrer, and tlog upload off), and add a contract test that signs with the service's signer against a Vault dev server and verifies with the pinned Flux source-controller in kind and with the host applier's verifier. Have Renovate upgrade cosign, sigstore-go and Flux as one group, so S4's 'one sitting' covers them together.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| Notation (Notary Project) | v1.3.2 stable, v2.0.0-alpha.1 pre-release; Flux supports provider: notation | X.509 trust policy with no transparency log. No first-party Vault Transit plugin was found. It offers nothing that cosign with a Vault key lacks for this estate, so keep cosign. |
| OpenBao instead of Vault | 2.6.x in October 2026, MPL-licensed fork; cosign supports openbao:// | Same Transit API with an open licence. Changes nothing above but removes the dependency on Vault's BSL licence. |

**Verification (weakened).** Several points hold and are cheap to fix. security.md says the appliers and Flux verify against 'Vault's public key', singular, so separate keys for render and host are worth having. A cosign signature binds the digest, not the Project, the environment or freshness. Flux accepts several .pub keys. Flux 2.7.x could not verify cosign v3 signatures, its release notes advised staying on cosign v2.6 until 2.8, and Flux 2.8 added cosign v3 support. cosign 2.x and later upload key-based signatures to Rekor by default. Overstated parts: (1) Replay needs ghcr tag-write first, so it is supply-3's problem, not a separate high-severity one. (2) 'Losing the cluster's storage loses the key' ignores Vault Raft snapshots. Non-exportable Transit keys are still in those snapshots, and Vault is existing estate infrastructure outside estate-kit's design. The real gap is that no page names a recovery key or a Vault restore path. (3) 'Flux's v3 bundle path requires matchOIDCIdentity' is unverified: Flux's OCIRepository docs tie matchOIDCIdentity only to keyless verification. (4) The monotonic sequence annotation cannot be enforced by Flux, so for Projects the fix falls back to a service-side comparison.

**Corrections.** OpenBao's latest release is v2.7.1 (1 October 2026; 2.6.4 is a patch on the older line), not '2.6.x'. Flux's current release is v2.9.6 (1 October 2026); pin the contract test to it. The latest Notation release is v1.3.2 from April 2025, 18 months without a release, which strengthens 'keep cosign'. The matchOIDCIdentity claim is unverified. Severity is medium.

Sources:

- <https://fluxcd.io/flux/components/source/ocirepositories/>
- <https://fluxcd.io/blog/2026/02/flux-v2.8.0/>
- <https://github.com/fluxcd/flux2/releases>
- <https://github.com/sigstore/cosign/releases>
- <https://docs.sigstore.dev/cosign/key_management/overview/>
- <https://developer.hashicorp.com/vault/api-docs/secret/transit>
- <https://github.com/notaryproject/notation/releases>
- <https://src.opensuse.org/pool/flux2-cli/raw/branch/factory/flux2-cli.changes>
- <https://blog.sigstore.dev/cosign-2-0-released/>
- <https://github.com/openbao/openbao/releases>

### supply-6: The Nix signing key lives in CI, so one workflow secret can sign root-level code for every host

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| risk | high | S10, S11, S9 | weakened | medium |

**Concerns:** hosts.md, 'A host rollout' ('CI builds and signs every node's closure into an off-cluster binary cache'); choices.md, 'Host closures'; security.md, row 'Applier to cache'

The Nix narinfo signature is what the appliers trust for each store path, and the design has CI produce it. The key is therefore a GitHub Actions secret, readable by any workflow in that repository, including a branch workflow pushed by someone with write access. The Vault-signed host tag only says which toplevel path to switch to. A malicious closure signed with the CI key and named by a host tag the service moves still switches every node. The service moves host tags after a 'host rollout (GitHub OIDC token)' call, and the authorization matrix has no row for that call, so neither the caller identity nor a review requirement is specified for the most powerful action in the estate.

**Recommendation.** Take the key out of CI. Use a cache that signs on the server, so pushers never hold it, and push with GitHub OIDC. niks3 is S3-backed, signs on the server, takes OIDC uploads, and is at release 1.5 and active. Attic also signs on the server but calls itself an early prototype. Add a matrix row 'Start a host rollout': estate CI only, event_name=push on main or a release tag, an environment with required reviewers, and job_workflow_sha pinned. Put the toplevel store path and its narHash in the Vault-signed host tag, and have the applier compare them with the narHash it fetched before switching. List two trusted-public-keys so the cache key can be rotated without break-glass.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| niks3 | 1.5 release in 2026, active (Mic92) | Needs S3 plus Postgres off-cluster. Garbage collection is built in. |
| Attic | Self-described early prototype; many open issues | Server-side signing, but maturity risk for a single maintainer. |
| Cachix | Commercial, active | Managed, and the signing key can stay with Cachix. A paid SaaS dependency on host recovery. |

**Verification (weakened).** Confirmed parts: hosts.md 'A host rollout' has CI build and sign the closures, and the authorization matrix in security.md has no row for the 'host rollout (GitHub OIDC token)' call that appears in the host-rollout sequence in specs.py. Overstated parts: the CI key belongs to the estate or nix-config repository, both private and written only by the maintainer, not to any Project repository, so S10's attacker cannot reach it. 'Readable by any workflow, including a branch workflow' ignores a free fix the finding omits: a GitHub environment secret limited to main with a required reviewer. Recommendation flaws: (1) A toplevel narHash in the host tag covers only the toplevel NAR, not the content of its dependencies, so it does not stop a swapped dependency under a CI-signed narinfo. It needs a signed closure manifest (every path with its narHash). (2) niks3 runs off-cluster with S3 and Postgres, a new service to operate. (3) niks3's OpenBao/Vault Transit sign-program would tie the off-cluster cache to the in-cluster Vault, against choices.md 'Host closures: hosts can be fixed while the cluster is down'.

**Corrections.** niks3 is at v1.15.0 (12 October 2026; last push 20 October 2026), not '1.5'. 1.5 was a May 2026 release. Server-side signing is confirmed in its source (server/signing/), and it includes an example sign-program for OpenBao/Vault Transit and PKCS#11. Attic still calls itself 'an early prototype'. Cheaper first step: an environment-scoped signing secret with branch rules and a reviewer, plus the missing matrix row and two trusted-public-keys.

Sources:

- <https://github.com/Mic92/niks3>
- <https://discourse.nixos.org/t/niks3-1-5-release/77539>
- <https://github.com/zhaofengli/attic>
- <https://docs.cachix.org/deploy/>
- <https://github.com/Mic92/niks3/releases>
- <https://github.com/Mic92/niks3/blob/main/cmd/niks3-openbao-signer/main.go>
- <https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment>

### supply-7: Flagger and Flux cannot send projected service-account tokens, so the in-cluster identity scheme does not work

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| weakness | medium | S2, S10 | confirmed | high |

**Concerns:** identity-and-access.md, row 'In-cluster callers (Flagger webhooks, Flux events): Projected service-account token'; choices.md, 'In-cluster identity' (rejected TokenReview and network policy); security.md matrix column 'Flagger'

Flagger's webhook spec has name, type, url, timeout, retries, metadata, disableTLS and muteAlert, and nothing for authentication. Flux notification-controller's generic provider can send static headers from a Secret, and generic-hmac signs the body with an X-Signature header. Neither attaches a projected service-account token. Both callers named in the design therefore arrive unauthenticated, or carry a static shared secret. If Flux events drive rollout state, a pod that can reach the service can forge 'applied' or 'failed' and mark a rollout Serving or Refused.

**Recommendation.** Reopen 'In-cluster identity' with this fact. Receive Flux events through generic-hmac, keep the secret in Vault and verify X-Signature. Treat every event only as a hint to re-read the Flux object's status from the API server, so a forged event changes nothing. Keep the Release Gate free of side effects and serve it on a separate internal-only port behind a NetworkPolicy, since a forged gate query learns only what the gate already answers. Change the matrix's Flagger column to match, and keep projected tokens only for in-cluster callers whose clients can actually send them.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| Service mesh mTLS (e.g. Linkerd) for caller identity | Not re-checked in this review | Gives real workload identity for every in-cluster caller, but adds a mesh. Too much for one maintainer to run for two callers. |

**Verification (confirmed).** Flagger's webhook spec has name, type, url, timeout, retries, metadata, disableTLS and muteAlert, and no authentication field. Flux notification-controller's generic provider sends static headers from a Secret, generic-hmac adds X-Signature, and certSecretRef supports a client certificate. Provider workload identity (serviceAccountName) exists only for cloud providers such as Azure, not to send a projected service-account token to an arbitrary URL. The identity-and-access.md row 'In-cluster callers (Flagger webhooks, Flux events): Projected service-account token' therefore cannot work as written.

**Corrections.** The finding misses two simpler options. (1) inside-the-service.md already gives the `cluster` package 'release status' through client-go, so the service can drop Flux event ingestion and watch Kustomization and Canary status, which removes one unauthenticated caller with no new secret. (2) The mesh is not an extra component to dismiss: deploy-kit's Proposed [deploy-kit ADR 0112](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/model/0112-east-west-traffic-is-mutually-authenticated-by-an-ambient-mesh.md) (20 October 2026) already sets the estate towards Istio ambient mTLS with ServiceAccount SPIFFE identities, which would authenticate Flagger to the service if enrolled. Also, Flux's generic provider supports client certificates (certSecretRef) as well as HMAC.

Sources:

- <https://docs.flagger.app/usage/webhooks>
- <https://fluxcd.io/flux/components/notification/providers/>
- <https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/model/0112-east-west-traffic-is-mutually-authenticated-by-an-ambient-mesh.md>

### supply-8: The STRIDE table and authorization matrix miss disclosure, denial of service, the App key, UI admissions and node scoping

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| missing | medium | S10, S12, S15 | confirmed | medium |

**Concerns:** security.md, 'Threats per boundary' and 'Authorization matrix'; identity-and-access.md, UI row ('admins change admissions'); choices.md, 'Membership'

Six gaps: (a) Disclosure. Plan and dry-run results go to Project CI, including API-server errors and cross-Project errors and diffs. In a public Project repository those logs can be read by anyone. (b) Denial of service. Compositions run one at a time, so a Project that loops plan or dry-run calls stalls every other deploy, against S12's 10-minute target. (c) The GitHub App private key is a long-lived secret, not listed as one. The App can dispatch workflows in every Project repository, so a leaked key starts deploy runs everywhere. (d) The matrix gives Admin 'Change admissions: yes' and the identity page says admins change admissions. A UI route that admits Projects bypasses the reviewed Platform Intent, which the 'Membership' choice exists to protect. (e) The STRIDE row 'RBAC limits each node to its own pods' cannot be enforced. RBAC has no field conditions, so it cannot restrict pod evictions to one node. Only the Node authorizer with NodeRestriction scopes the kubelet's own identity, and no page says how the host applier authenticates to the API server. (f) Several routes have no row: host rollout, rollout-token exchange, Flux event ingestion, break-glass and service-dispatched watch runs.

**Recommendation.** Add these rows, each with a test: filter plan and dry-run output to the caller's own Project; limit plan and dry-run calls per repository_id and keep them out of the deploy queue; import the App key into Vault Transit, which supports BYOK import and RSA PKCS#1 v1.5 signing, and sign the App JWT through Transit so the key never sits on disk; set 'Change admissions' to no for every UI role, leaving the estate repo PR as the only path; give each node applier a per-node identity with resourceNames limited to its own Node object and the Lease, and have an in-cluster component do the eviction, as the prior-art research already recommends; add the missing routes to the matrix so the existing coverage test fails until they have rows.

**Verification (confirmed).** Each sub-claim matches the pages. (a) releasing.md says the plan returns 'cross-Project errors and the render diff' to CI, and most Project repositories are public, so the logs are public. (b) choices.md runs one composition at a time with no rate limit named. (c) The service dispatches deploy workflows in watch mode (operating.md) through the GitHub App, whose private key is long-lived and not listed as a secret. Vault Transit supports BYOK import of RSA keys and signing with pkcs1v15 and sha2-256, which is what an RS256 App JWT needs. (d) The security.md matrix gives Admin 'Change admissions: yes' with no 'through Platform Intent' qualifier, against the 'Membership' choice and UC-7. (e) RBAC cannot limit evictions to pods on one node. The Node authorizer and NodeRestriction cover kubelet writes to its own Node and its own pods, but not pods/eviction, and hosts.md never says how the applier authenticates to the API server. prior-art.md item 3 already recommends that a cluster-side controller drains. (f) The matrix has no rows for host rollout, rollout-token exchange, Flux events or break-glass.

**Corrections.** (a) has low impact: secrets are referenced from Vault, never inlined, so the exposure is errors and diffs. (e)'s fix adds an in-cluster drainer. Reusing kured (CNCF sandbox, v1.23.0, June 2026) or system-upgrade-controller is cheaper than writing one. Pod evictions by a per-node identity cannot be scoped by node without a ValidatingAdmissionPolicy that checks the pod's spec.nodeName against the caller. Severity stays medium.

Sources:

- <https://developer.hashicorp.com/vault/docs/secrets/transit>
- <https://kubernetes.io/docs/reference/access-authn-authz/node/>
- <https://docs.github.com/en/actions/reference/security/oidc>
- <https://developer.hashicorp.com/vault/api-docs/secret/transit>
- <https://github.com/kubereboot/kured>

# The register, as planned

The records to be written, in reading order, with their current status. Each title becomes a file `NNNN-<slug>.md` here when written, from [the template](template.md). Records 42 onwards are placed into reading order when the register is written; the model's own records follow after the cutover.

The [design review](../research/review/README.md) of 2026-10-22 changed or added the rows marked Proposed; they stay Proposed until their records are written and accepted ([#20](https://github.com/JorisJonkers-dev/estate-kit/issues/20)). The move to an all-Rust workspace on 2026-10-29 changed rows 13 to 18, 48, 50 and 55 and added 65 to 71; the records already written are linked. The maintainer accepted 13 to 18 (except 16, already accepted and now merged into 15), 48, 50, 55, 63 and 65 to 71 the same day.

| # | Record | Status |
| --- | --- | --- |
| 1 | [One maintainer, one cluster, one estate](0001-one-maintainer-one-cluster-one-estate.md) | Accepted |
| 2 | [Kubernetes is the substrate, and Flux is the one applier](0002-kubernetes-is-the-substrate-and-flux-is-the-one-applier.md) | Accepted |
| 3 | [Three models: Intent, Resolved Deployment, Deliverable Set](0003-three-models-intent-resolved-deployment-deliverable-set.md) | Accepted |
| 4 | [Contention decides authority](0004-contention-decides-authority.md) | Accepted |
| 5 | [Derivation is total](0005-derivation-is-total.md) | Accepted |
| 6 | [Every render is a function of pinned inputs](0006-every-render-is-a-function-of-pinned-inputs.md) | Accepted |
| 7 | [A Project's state lives with the Project](0007-a-project-s-state-lives-with-the-project.md) | Accepted |
| 8 | [A Project's CI proves itself with a pinned-workflow OIDC token, and the service deploys only images its own build registered](0008-an-image-digest-is-sealed-into-the-fragment-and-registered-by-its-build.md) | Proposed |
| 9 | [The live render is a signed registry tag per Project and environment](0009-the-live-render-is-a-signed-registry-tag-per-project-and-environment.md) | Accepted |
| 10 | [Platform Intent admits the Projects, and it is pushed like any Project; the service's copies are a cache](0010-platform-intent-admits-the-projects-and-is-pushed-like-any-project.md) | Accepted |
| 11 | Platform Intent is pushed like any Project; the service's copies are a cache | Merged into 10 |
| 12 | [Infrastructure Intent declares sites, nodes and maintenance windows](0012-infrastructure-intent-declares-sites-nodes-and-maintenance-windows.md) | Accepted |
| 13 | [Every program in estate-kit is Rust, in one Cargo workspace; only the UI is Vue](0013-every-program-is-rust.md) | Accepted |
| 14 | [The compiler is a chain of plain-Rust typed steps through one trace, one crate per step, with no DSL](0014-the-compiler-is-a-chain-of-typed-models-one-crate-per-step.md) | Accepted |
| 15 | [The Rust types agree with the committed schemas on their corpus](0015-the-rust-types-agree-with-the-committed-schemas-on-their-corpus.md) | Accepted |
| 16 | The committed JSON Schemas are the contract | Merged into 15 |
| 17 | [The service runs in the cluster, in Rust: it composes, and Flux applies](0017-the-service-runs-in-the-cluster-in-rust.md) | Accepted |
| 18 | [The service links the compiler's crates; the CLI's JSON output is for CI only](0018-the-service-links-the-compiler.md) | Accepted |
| 19 | One composition runs at a time | Merged into 63 |
| 20 | [No render cache: an unchanged render is not published again](0020-no-render-cache-an-unchanged-render-is-not-published-again.md) | Proposed |
| 21 | [Signing keys: renders and host tags by separate Transit keys, closures by an environment-scoped key, and an offline recovery key](0021-renders-and-host-tags-are-signed-by-separate-keys-with-an-offline-recovery-key.md) | Proposed |
| 22 | Every caller authenticates with an OIDC token checked against a claim policy | Merged into 8 |
| 23 | [A rollout is an append-only event log on the shared Postgres](0023-a-rollout-is-an-append-only-event-log-on-the-shared-postgres.md) | Accepted |
| 24 | A rollout is an append-only event log on the shared Postgres | Merged into 23 |
| 25 | [A dry-run must pass before anything is applied, and images are built once and promoted, so what dry-ran is what deploys](0025-a-dry-run-must-pass-before-anything-is-applied-and-what-dry-ran-is-what-deploys.md) | Accepted |
| 26 | Images are built once and promoted, so what dry-ran is what deploys | Merged into 25 |
| 27 | A diagnostic names a model path, and the caller resolves the line | Merged into 71 |
| 28 | [Pause and Rollback are a cluster object per Project; a missing object reads as Paused](0028-pause-and-rollback-are-a-cluster-object-per-project.md) | Proposed |
| 29 | The compiler renders host data; hand-written modules consume it | Merged into 31 |
| 30 | [A host applier on each node pulls its signed host tag, and decides a reboot before the Lease](0030-a-host-applier-on-each-node-pulls-its-signed-host-tag.md) | Proposed |
| 31 | [Host data is rendered by the compiler for hand-written modules, and host closures are built in CI and cached outside the cluster](0031-host-closures-are-built-in-ci-and-cached-outside-the-cluster.md) | Proposed |
| 32 | Node order is derived from the change and the version skew rule | Merged into 30 |
| 33 | [A Mailbox is declared by its local part and owned by one Project](0033-a-mailbox-is-declared-by-its-local-part-and-owned-by-one-project.md) | Accepted |
| 34 | [Every part of estate-kit, the components included, lives in this repository at one version](0034-every-part-of-estate-kit-lives-in-this-repository-at-one-version.md) | Accepted |
| 35 | A further implementation, if one is ever written, meets the first at the language-neutral oracles | Merged into 67 |
| 36 | One concept per module, one fake per port, oracles only at the seams | Merged into 68 |
| 37 | [Every gate has a speed budget; coverage and mutation are ratchets](0037-every-gate-has-a-speed-budget-coverage-and-mutation-are-ratchets.md) | Accepted |
| 38 | One version for every part | Merged into 34 |
| 39 | Decisions live as Markdown in docs/, and a Pages site is built from it | Moved to [decision records](README.md#how-records-are-kept) |
| 40 | Records are read in order and cite their lessons | Moved to [decision records](README.md#how-records-are-kept) |
| 41 | A record has a status; a locked record needs a failing check | Moved to [decision records](README.md#how-records-are-kept) |
| 42 | The shadow composition is inert | Merged into 67 |
| 43 | [The service API is an OpenAPI 3.1 contract](0043-the-service-api-is-an-openapi-3-1-contract.md) | Accepted |
| 44 | Errors are RFC 9457 problems drawn from one catalogue | Merged into 71 |
| 45 | Deploy calls are idempotent on project and fragment digest; streams resume by sequence | Merged into 23 |
| 46 | IDs are UUIDv7, times RFC 3339 in UTC, and absent means unset | Moved to [conventions](../design/conventions.md#primitives) |
| 47 | Schemas evolve additively within a major version, checked in CI | Merged into 48 |
| 48 | [Every committed schema evolves additively within a major version, checked in CI, and the CLI's JSON output has one that the reusable workflows read](0048-the-cli-s-json-output-has-a-committed-schema.md) | Accepted |
| 49 | Events are versioned and upcast on read, and hold no personal data | Merged into 23 |
| 50 | [The workspace is five bounded contexts in five layers, and a check holds the crate graph to both](0050-five-bounded-contexts.md) | Accepted |
| 51 | History is kept 400 days; renders are kept by count, age and tag | Moved to [conventions](../design/conventions.md#retention) |
| 52 | Three service levels: deploy p95, availability, drift detection | Moved to [conventions](../design/conventions.md#service-levels) |
| 53 | Traces go to Tempo and logs to Loki, keyed by rollout id | Moved to [conventions](../design/conventions.md#telemetry) |
| 54 | [Every trust boundary has a threat table, and every route an authorization row](0054-every-trust-boundary-has-a-threat-table-and-every-route-an-authorization-row.md) | Accepted |
| 55 | [Every Go and Python program is characterized before it is rewritten in Rust](0055-every-go-and-python-program-is-characterized-before-it-is-rewritten.md) | Accepted |
| 56 | Agent files are short, and what must always hold is a check | Moved to [conventions](../design/conventions.md#agent-files) |
| 57 | Configuration is flags, then environment, then file; secrets only by reference | Moved to [conventions](../design/conventions.md#configuration) |
| 58 | [Flux is locked down per Project, and the service dry-runs as an identity that cannot write](0058-flux-is-locked-down-per-project-and-the-service-dry-runs-as-an-identity-that-cannot-write.md) | Proposed |
| 59 | [Vault unseal and the API server's datastore backup are decided in fleet-infra; estate-kit assumes them](0059-vault-unseal-and-datastore-backup-are-assumed-from-fleet-infra.md) | Proposed |
| 60 | The API server's datastore is backed up off the provider, and its restore is drilled | Merged into 59 |
| 61 | A rollback moves the tag back to the last Serving render without composing | Merged into 28 |
| 62 | ghcr tags move with a machine account's token kept in Vault | Merged into 9 |
| 63 | [The service has one writer and reconciles from observed state](0063-the-service-has-one-writer-and-reconciles-from-observed-state.md) | Accepted |
| 64 | [Renders use a canonical YAML style specified on one page](0064-renders-use-a-canonical-yaml-style-specified-on-one-page.md) | Proposed |
| 65 | The workspace is layered by crate, and a check holds the crate graph to the layer table | Merged into 50 |
| 66 | Transformations are plain Rust: typed steps, one trace, an invariant table, and no DSL | Merged into 14 |
| 67 | [The Rust compiler implements the 1.0 specification, and the shadow compares structure](0067-the-compiler-is-written-to-the-1-0-contract.md) | Accepted |
| 68 | [One concept per module, one fake per port that passes its contract suite, oracles only at the seams](0068-every-fake-passes-its-port-s-contract-suite.md) | Accepted |
| 69 | [The deploy path is tested end to end on a throwaway k3s cluster, nightly and before every release](0069-the-deploy-path-is-tested-end-to-end.md) | Accepted |
| 70 | Shared Rust code moves to rust-commons on its third consumer; the sign-in kit is the first | Moved to [conventions](../design/conventions.md#shared-rust-code) |
| 71 | [A diagnostic is a coded problem with typed, plural locations, and the caller resolves the lines](0071-a-diagnostic-is-a-coded-problem-with-typed-locations.md) | Accepted |
| 72 | [Per-field provenance and `estate-kit explain` are deferred until a scenario needs them](0072-per-field-provenance-and-explain-are-deferred.md) | Proposed |
| 73 | [The composition queue is a row in a Postgres job table on the shared platform-postgres](0073-the-composition-queue-is-a-row-in-a-postgres-job-table.md) | Proposed |
| 74 | [The Release Gate and Observation each have named writes, with their own credentials](0074-the-release-gate-and-observation-each-have-a-named-write.md) | Proposed |

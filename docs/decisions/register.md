# The register, as planned

The records to be written, in reading order, with their current status. Each title becomes a file `NNNN-<slug>.md` here when written, from [the template](template.md). Records 42 onwards are placed into reading order when the register is written; the model's own records follow after the cutover.

The [design review](../research/review/README.md) of 2026-10-22 changed or added the rows marked Proposed; they stay Proposed until their records are written and accepted ([#20](https://github.com/JorisJonkers-dev/estate-kit/issues/20)). The move to an all-Rust workspace on 2026-10-29 changed rows 13 to 18, 48, 50 and 55 and added 65 to 71; the records already written are linked. The maintainer accepted 13 to 18 (except 16, already accepted and now merged into 15), 48, 50, 55, 63 and 65 to 71 the same day.

| # | Record | Status |
| --- | --- | --- |
| 1 | One maintainer, one cluster, one estate | Accepted |
| 2 | Kubernetes is the substrate, and Flux is the one applier | Accepted |
| 3 | Three models: Intent, Resolved Deployment, Deliverable Set | Accepted |
| 4 | Contention decides authority | Accepted |
| 5 | Derivation is total | Accepted |
| 6 | Every render is a function of pinned inputs | Accepted |
| 7 | A Project's state lives with the Project | Accepted |
| 8 | [An image's digest is sealed into the Intent Fragment, and its build registered it](0008-an-image-digest-is-sealed-into-the-fragment-and-registered-by-its-build.md) | Proposed |
| 9 | The live render is a signed registry tag per Project and environment | Accepted |
| 10 | Platform Intent admits the Projects | Accepted |
| 11 | Platform Intent is pushed like any Project; the service's copies are a cache | Accepted |
| 12 | Infrastructure Intent declares sites, nodes and maintenance windows | Accepted |
| 13 | [Every program in estate-kit is Rust, in one Cargo workspace; only the UI is Vue](0013-every-program-is-rust.md) | Accepted |
| 14 | [The compiler is a chain of plain-Rust typed steps through one trace, one crate per step, with no DSL](0014-the-compiler-is-a-chain-of-typed-models-one-crate-per-step.md) | Accepted |
| 15 | [The Rust types agree with the committed schemas on their corpus](0015-the-rust-types-agree-with-the-committed-schemas-on-their-corpus.md) | Accepted |
| 16 | The committed JSON Schemas are the contract | Merged into 15 |
| 17 | [The service runs in the cluster, in Rust: it composes, and Flux applies](0017-the-service-runs-in-the-cluster-in-rust.md) | Accepted |
| 18 | [The service links the compiler's crates; the CLI's JSON output is for CI only](0018-the-service-links-the-compiler.md) | Accepted |
| 19 | One composition runs at a time | Accepted |
| 20 | [No render cache: an unchanged render is not published again](0020-no-render-cache-an-unchanged-render-is-not-published-again.md) | Proposed |
| 21 | [Renders and host tags are signed by separate Transit keys, with an offline recovery key](0021-renders-and-host-tags-are-signed-by-separate-keys-with-an-offline-recovery-key.md) | Proposed |
| 22 | [Every caller authenticates with an OIDC token checked against a claim policy](0022-every-caller-authenticates-with-an-oidc-token-checked-against-a-claim-policy.md) | Proposed |
| 23 | A rollout is a deploy run that streams the service's work | Accepted |
| 24 | [A rollout is an append-only event log on the shared Postgres](0024-a-rollout-is-an-append-only-event-log-on-the-shared-postgres.md) | Proposed |
| 25 | A dry-run must pass before anything is applied | Accepted |
| 26 | Images are built once and promoted, so what dry-ran is what deploys | Accepted |
| 27 | A diagnostic names a model path, and the caller resolves the line | Merged into 71 |
| 28 | [Pause and Rollback are a cluster object per Project; a missing object reads as Paused](0028-pause-and-rollback-are-a-cluster-object-per-project.md) | Proposed |
| 29 | The compiler renders host data; hand-written modules consume it | Accepted |
| 30 | [A host applier on each node pulls its signed host tag, and decides a reboot before the Lease](0030-a-host-applier-on-each-node-pulls-its-signed-host-tag.md) | Proposed |
| 31 | [Host closures are built in CI and cached outside the cluster, signed by an environment-scoped key](0031-host-closures-are-built-in-ci-and-cached-outside-the-cluster.md) | Proposed |
| 32 | Node order is derived from the change and the version skew rule | Accepted |
| 33 | A Mailbox is declared by its local part and owned by one Project | Accepted |
| 34 | Components live in this repository at one version | Accepted |
| 35 | [A further implementation, if one is ever written, meets the first at the language-neutral oracles](0035-a-further-implementation-meets-the-first-at-the-language-neutral-oracles.md) | Proposed |
| 36 | One concept per module, one fake per port, oracles only at the seams | Accepted |
| 37 | Every gate has a speed budget; coverage and mutation are ratchets | Accepted |
| 38 | One version for every part | Accepted |
| 39 | Decisions live as Markdown in docs/, and a Pages site is built from it | Accepted |
| 40 | Records are read in order and cite their lessons | Accepted |
| 41 | A record has a status; a locked record needs a failing check | Accepted |
| 42 | The shadow composition is inert | Accepted |
| 43 | The service API is an OpenAPI 3.1 contract | Accepted |
| 44 | Errors are RFC 9457 problems drawn from one catalogue | Merged into 71 |
| 45 | Deploy calls are idempotent on project and fragment digest; streams resume by sequence | Accepted |
| 46 | IDs are UUIDv7, times RFC 3339 in UTC, and absent means unset | Accepted |
| 47 | Schemas evolve additively within a major version, checked in CI | Accepted |
| 48 | [The CLI's JSON output has a committed schema that the reusable workflows read](0048-the-cli-s-json-output-has-a-committed-schema.md) | Accepted |
| 49 | Events are versioned and upcast on read, and hold no personal data | Accepted |
| 50 | [Five bounded contexts, each boundary its own record: compiler, service, observation, hosts, components](0050-five-bounded-contexts.md) | Accepted |
| 51 | History is kept 400 days; renders are kept by count, age and tag | Accepted |
| 52 | Three service levels: deploy p95, availability, drift detection | Accepted |
| 53 | Traces go to Tempo and logs to Loki, keyed by rollout id | Accepted |
| 54 | Every trust boundary has a threat table, and every route an authorization row | Accepted |
| 55 | [Every Go and Python program is characterized before it is rewritten in Rust](0055-every-go-and-python-program-is-characterized-before-it-is-rewritten.md) | Accepted |
| 56 | Agent files are short, and what must always hold is a check | Accepted |
| 57 | Configuration is flags, then environment, then file; secrets only by reference | Accepted |
| 58 | [Flux is locked down per Project, and the service dry-runs as an identity that cannot write](0058-flux-is-locked-down-per-project-and-the-service-dry-runs-as-an-identity-that-cannot-write.md) | Proposed |
| 59 | [Vault unseals itself through a cloud KMS](0059-vault-unseals-itself-through-a-cloud-kms.md) | Proposed |
| 60 | [The API server's datastore is backed up off the provider, and its restore is drilled](0060-the-api-server-datastore-is-backed-up-off-the-provider-and-its-restore-is-drilled.md) | Proposed |
| 61 | [A rollback moves the tag back to the last Serving render without composing](0061-a-rollback-moves-the-tag-back-to-the-last-serving-render-without-composing.md) | Proposed |
| 62 | [ghcr tags move with a machine account's token kept in Vault](0062-ghcr-tags-move-with-a-machine-account-token-kept-in-vault.md) | Proposed |
| 63 | [The service has one writer and reconciles from observed state](0063-the-service-has-one-writer-and-reconciles-from-observed-state.md) | Accepted |
| 64 | [Renders use a canonical YAML style specified on one page](0064-renders-use-a-canonical-yaml-style-specified-on-one-page.md) | Proposed |
| 65 | [The workspace is layered by crate, and a check holds the crate graph to the layer table](0065-the-workspace-is-layered-and-the-crate-graph-is-checked.md) | Accepted |
| 66 | Transformations are plain Rust: typed steps, one trace, an invariant table, and no DSL | Merged into 14 |
| 67 | [The Rust compiler implements the 1.0 specification, and the shadow compares structure](0067-the-compiler-is-written-to-the-1-0-contract.md) | Accepted |
| 68 | [Every port has one fake, and the fake passes the same contract suite as its adapter](0068-every-fake-passes-its-port-s-contract-suite.md) | Accepted |
| 69 | [The deploy path is tested end to end on a throwaway k3s cluster, nightly and before every release](0069-the-deploy-path-is-tested-end-to-end.md) | Accepted |
| 70 | [Shared Rust code moves to rust-commons on its third consumer; the sign-in kit is the first](0070-shared-rust-code-moves-to-rust-commons-on-its-third-consumer.md) | Accepted |
| 71 | [A diagnostic is a coded problem with typed, plural locations, and the caller resolves the lines](0071-a-diagnostic-is-a-coded-problem-with-typed-locations.md) | Accepted |
| 72 | [Per-field provenance and `estate-kit explain` are deferred until a scenario needs them](0072-per-field-provenance-and-explain-are-deferred.md) | Proposed |

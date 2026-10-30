# Testing and speed

How the Rust workspace is tested, what each kind of test is for, which gates
hold it, and how they stay inside their time budgets. It applies the estate's
testing standard
([workspace ADR-0022, "Tests specify behaviour"](https://github.com/JorisJonkers-dev/workspace/blob/main/docs/decisions/ADR-0022-tests-specify-behaviour.md))
to the layers of [The Rust workspace](rust-workspace.md), with deploy-kit's
lessons on oracles and mutation.

## Rules for code

- **One concept, one module.** Each model concept has one module in the step
  that handles it; each port has one trait, one fake and one adapter crate.
- **One public type per file**, and a file-length cap, gated with a failing
  fixture each.
- **Fakes, not mocks.** Each port has exactly one hand-written fake beside it,
  and the fake passes the port's contract suite
  ([record 68](../decisions/0068-every-fake-passes-its-port-s-contract-suite.md)).
  No `mockall`.
- **Duplication before the wrong abstraction.** Code is shared within the
  workspace when a second caller needs the same behaviour, and moves to
  rust-commons on its third Rust consumer ([workspace ADR-0017](https://github.com/JorisJonkers-dev/workspace/blob/main/docs/decisions/ADR-0017-go-commons-extracts-on-third-use.md)). A helper used
  once stays where it is used.
- **Readable over clever.** No macro where a function will do; no generic
  parameter that only ever takes one type; no trait with one implementation
  unless it is a port.
- **Generated code stays apart**, in its own module, never edited by hand, and
  outside coverage and churn metrics.

## The kinds of test

| Kind | What it proves | Lives in | Runs |
| --- | --- | --- | --- |
| Unit | One behaviour of one function, named as a sentence in `CONTEXT.md` words | `#[cfg(test)]` in each crate | Every `cargo test`, no Docker, no network |
| Property | Totality, determinism, locality, round trips (the canonical emitter, upcasters) | The crate that owns the property | Every run, with a fixed case count; a nightly run with more |
| Fixture and oracle | The compiler's four seams: use cases, the adapter port, the rendered tree, the CLI. Refusal fixtures assert a code and a path | `oracles/`, read-only to tests | Every run |
| Contract | The JSON Schema corpus; the OpenAPI document against the routes; the error catalogue against the fixtures; identity's Principal vectors | `contracts/` and the crate that implements each | Every run |
| Port contract | A fake and its adapter behave alike | Application crate (fake), adapter crate (real) | Fake: every run. Adapter: the integration job |
| Integration | Real HTTP in process; real Postgres, Vault, an OCI registry and k3s in containers | `tests/` behind the `integration` feature | The integration job, on every pull request |
| Characterization | A Go or Python service's recorded answers, before it is replaced ([record 55](../decisions/register.md)) | `oracles/characterization/` | Every run, until the old service is archived |
| End to end | A whole deploy, on a throwaway cluster | `e2e/` | Nightly, and required before a release |
| Host VM | A node class boots its generation; the applier switches, holds the Lease, rolls back | `hosts/vm-tests/`, NixOS tests | On a host change, and nightly |
| UI | Vue components and stores; Playwright journeys against a stubbed API, each stub validated against the OpenAPI document | `ui/` | When `ui/` changes |
| Fuzz | The YAML reader and the schema validator against hostile input | `fuzz/` (cargo-fuzz) | Nightly, time-boxed |

A test that only exercises excluded code is deleted. Retries stay at zero; a
flaky test is quarantined with
`#[ignore = "quarantine: <issue url> until YYYY-MM-DD"]`, at most 14 days out,
which the estate's quarantine check must learn to read (a follow-up in
github-workflows).

## End to end

The e2e suite runs the deploy path the way production does, with nothing
faked except GitHub:

- a k3s cluster in CI with Flux, Flagger and the ValidatingAdmissionPolicies;
- an OCI registry (zot) standing in for ghcr, Vault in dev mode with the two
  Transit keys, Postgres, and the service image built from the pull request;
- a fixture Project repository whose `deploy` job is replayed by the test
  runner with a minted OIDC token.

Its scenarios are the use cases: validate and plan; dry-run; deploy to
Serving; a refused deploy; Pause and Resume; Rollback with Vault scaled to
zero; a service restart mid-rollout that resumes from observed state; a service
upgraded mid-rollout, after which the waiting deploy job re-requests a GitHub
OIDC token and resumes by sequence; an
unchanged render that publishes nothing. Each scenario asserts what a
consumer sees (the tag, the object in the cluster, the Deployment status),
never only a Ready condition (DO-4).

## Gates

| Gate | Threshold | Scope |
| --- | --- | --- |
| Unit coverage | 100% of lines, functions and regions | Domain, application and step crates. Branch coverage needs nightly `cargo llvm-cov --branch`, and is added when it is stable |
| Integration coverage | 100% of functions | Adapter and binary crates |
| Mutation | 100% break score | Domain, application and step crates; adapters report-only, then a ratchet |
| Coverage and mutation ratchet | The measured value, only rising | Every crate ([record 37](../decisions/0037-every-gate-has-a-speed-budget-coverage-and-mutation-are-ratchets.md)) |
| Lints | `clippy::pedantic`, `-D warnings`; `unsafe_code = "forbid"`; `unreachable_pub`; `missing_docs` on public items | Every crate |
| Layers | `cargo xtask check-layers` | The crate graph ([record 50](../decisions/0050-five-bounded-contexts.md)) |
| Ports | A grep-level script: each port trait has a `Fake<Port>` and a `<port>_contract` suite, found by name | The application crates ([record 68](../decisions/0068-every-fake-passes-its-port-s-contract-suite.md)) |
| Supply chain | `cargo-deny` (advisories, licences, banned crates, one version of each), `cargo-machete`, gitleaks | The lockfile and the manifests |

Unit and integration coverage are separate gates, so a unit suite that starts
needing Docker cannot pass on the integration run ([identity ADR 0011](https://github.com/JorisJonkers-dev/identity/blob/main/docs/adr/0011-unit-tests-reach-every-statement-branch-condition-and-function.md)).

## The checks

Every check a record's Confirmation names has one name, here. A Confirmation
writes the name in bold, exactly as the first column spells it, and the Records
check fails on a bold name that is not a row. A check that runs today says so;
every other has the workstream issue that builds it, and that issue lists the
check under its name in its acceptance criteria. A rule that no check can hold,
such as a review rule, is written without a bold name.

| Check | Fails when | Records | Runs in | Status |
| --- | --- | --- | --- | --- |
| Records | A record's status, rests-on, lessons or Confirmation breaks the register's rules, or a Confirmation names a check that is not in this table | every record | CI job Records (`scripts/check_records.py`) | runs today |
| Links | A relative link or anchor does not resolve | [59](../decisions/0059-vault-unseal-and-datastore-backup-are-assumed-from-fleet-infra.md) | CI job Links | runs today |
| `cargo xtask check-layers` | A crate edge the layers file does not allow, a member that is not Rust, or a compiler crate that depends on a cluster client, a clock or an adapter; one failing fixture workspace per rule | [6](../decisions/0006-every-render-is-a-function-of-pinned-inputs.md), [13](../decisions/0013-every-program-is-rust.md), [14](../decisions/0014-the-compiler-is-a-chain-of-typed-models-one-crate-per-step.md), [18](../decisions/0018-the-service-links-the-compiler.md), [50](../decisions/0050-five-bounded-contexts.md) | xtask, Lint job | [#60](https://github.com/JorisJonkers-dev/estate-kit/issues/60) |
| Workspace version check | A member sets its own `version` instead of inheriting the workspace's | [34](../decisions/0034-every-part-of-estate-kit-lives-in-this-repository-at-one-version.md) | xtask, Lint job | [#60](https://github.com/JorisJonkers-dev/estate-kit/issues/60) |
| Port contract script | A port trait has no `Fake<Port>` or no `<port>_contract`, or the suite is not called from both the fake's tests and an adapter's integration tests; one failing fixture per rule | [68](../decisions/0068-every-fake-passes-its-port-s-contract-suite.md) | Lint job | [#60](https://github.com/JorisJonkers-dev/estate-kit/issues/60) |
| Compiler dependency bans | A compiler crate depends on `tokio`, `reqwest` or an adapter crate (cargo-deny bans), or uses `std::env`, `std::fs` or `SystemTime::now` (clippy `disallowed-methods`) | [18](../decisions/0018-the-service-links-the-compiler.md) | Lint job | [#60](https://github.com/JorisJonkers-dev/estate-kit/issues/60) |
| Release profile check | The release profile lacks `panic = "unwind"` | [18](../decisions/0018-the-service-links-the-compiler.md) | Lint job | [#60](https://github.com/JorisJonkers-dev/estate-kit/issues/60) |
| Mutation trigger lint | The mutation workflow has a trigger other than `push` to main and `schedule` | [37](../decisions/0037-every-gate-has-a-speed-budget-coverage-and-mutation-are-ratchets.md) | Actionlint job | [#60](https://github.com/JorisJonkers-dev/estate-kit/issues/60) |
| Ratchet step | A crate's coverage or mutation score is below the committed baseline; a negative fixture lowers a baseline and expects the failure | [37](../decisions/0037-every-gate-has-a-speed-budget-coverage-and-mutation-are-ratchets.md) | CI, on main | [#60](https://github.com/JorisJonkers-dev/estate-kit/issues/60) |
| Mutation exclusion count | `.cargo/mutants.toml` holds any exclusion | [37](../decisions/0037-every-gate-has-a-speed-budget-coverage-and-mutation-are-ratchets.md) | Ratchet step | [#60](https://github.com/JorisJonkers-dev/estate-kit/issues/60) |
| Schema evolution check | A change to a committed schema, classified against the last release, disagrees with the version bump | [48](../decisions/0048-the-cli-s-json-output-has-a-committed-schema.md) | CI | [#60](https://github.com/JorisJonkers-dev/estate-kit/issues/60) |
| Rewritten-components check | A Go module, Node runtime or Python program remains in an image estate-kit ships or in a reusable workflow for a component the committed list marks rewritten, or the old image of a rewritten component is still built | [13](../decisions/0013-every-program-is-rust.md) | CI job, reads one committed list | [#60](https://github.com/JorisJonkers-dev/estate-kit/issues/60) |
| Pin scan | A file in this repository or the estate repository names a deployed digest or pin | [7](../decisions/0007-a-project-s-state-lives-with-the-project.md) | CI job in each repository | [#60](https://github.com/JorisJonkers-dev/estate-kit/issues/60) |
| Mechanism-field lint | A committed schema has a field that names a target mechanism without an Intent requirement behind it | [5](../decisions/0005-derivation-is-total.md) | CI, over `contracts/` | [#61](https://github.com/JorisJonkers-dev/estate-kit/issues/61) |
| Corpus-agreement test | The schema refuses a corpus document the typed conversion accepts, or a document's diagnostics, as a whole set with model paths, differ from the set recorded beside it. The corpus holds the window fixtures of Infrastructure Intent | [3](../decisions/0003-three-models-intent-resolved-deployment-deliverable-set.md), [12](../decisions/0012-infrastructure-intent-declares-sites-nodes-and-maintenance-windows.md), [15](../decisions/0015-the-rust-types-agree-with-the-committed-schemas-on-their-corpus.md) | Test crate, every run | [#61](https://github.com/JorisJonkers-dev/estate-kit/issues/61) |
| Typestate compile-fail tests | The next phase builds without the producing step's token, or a renderer builds while reading Intent | [3](../decisions/0003-three-models-intent-resolved-deployment-deliverable-set.md), [14](../decisions/0014-the-compiler-is-a-chain-of-typed-models-one-crate-per-step.md) | Each step crate | [#61](https://github.com/JorisJonkers-dev/estate-kit/issues/61) |
| Invariant table test | A catalogue code has no invariant or no negative fixture | [14](../decisions/0014-the-compiler-is-a-chain-of-typed-models-one-crate-per-step.md) | Test crate, every run | [#61](https://github.com/JorisJonkers-dev/estate-kit/issues/61) |
| Single-cluster fixture | The compiler accepts a cluster name other than the estate's one | [1](../decisions/0001-one-maintainer-one-cluster-one-estate.md) | Compiler test, every run | [#61](https://github.com/JorisJonkers-dev/estate-kit/issues/61) |
| Diagnostic fixtures | A cross-Project code lacks primary and related locations, a code lacks its negative fixture, or a path is wrong | [71](../decisions/0071-a-diagnostic-is-a-coded-problem-with-typed-locations.md) | Compiler tests, `oracles/` | [#61](https://github.com/JorisJonkers-dev/estate-kit/issues/61) |
| Location resolution test | A model path does not resolve to a line at a pinned commit, or a fragment carries a position | [71](../decisions/0071-a-diagnostic-is-a-coded-problem-with-typed-locations.md) | Compiler test | [#61](https://github.com/JorisJonkers-dev/estate-kit/issues/61) |
| Oracle parity | A refusal's code or path differs, an expected model differs as JSON, or a rendered object differs in structure | [67](../decisions/0067-the-compiler-is-written-to-the-1-0-contract.md) | `oracles/parity`, every run | [#61](https://github.com/JorisJonkers-dev/estate-kit/issues/61) |
| Contention fixtures | A contended value lacks a negative fixture that fires its contention diagnostic | [4](../decisions/0004-contention-decides-authority.md) | Compiler test, every run | [#62](https://github.com/JorisJonkers-dev/estate-kit/issues/62) |
| Platform Intent admission test | A Project absent from Platform Intent is composed | [10](../decisions/0010-platform-intent-admits-the-projects-and-is-pushed-like-any-project.md) | Compiler and service tests | [#62](https://github.com/JorisJonkers-dev/estate-kit/issues/62) |
| Double-render test | Two renders of identical pinned inputs, at different times, differ byte for byte | [6](../decisions/0006-every-render-is-a-function-of-pinned-inputs.md) | Compiler test, every run | [#63](https://github.com/JorisJonkers-dev/estate-kit/issues/63) |
| Render digest property test | Rendering the same inputs twice gives different digests | [20](../decisions/0020-no-render-cache-an-unchanged-render-is-not-published-again.md) | Property test, every run | [#63](https://github.com/JorisJonkers-dev/estate-kit/issues/63) |
| Trace-completeness test | A Deliverable has no source, or an authored element produced nothing | [14](../decisions/0014-the-compiler-is-a-chain-of-typed-models-one-crate-per-step.md) | Compiler test, every run | [#63](https://github.com/JorisJonkers-dev/estate-kit/issues/63) |
| Canonical YAML tests | A generated string or object does not round-trip, or a rendered oracle differs from the specification's examples | [64](../decisions/0064-renders-use-a-canonical-yaml-style-specified-on-one-page.md) | `canonical` crate, every run | [#54](https://github.com/JorisJonkers-dev/estate-kit/issues/54) |
| Mailbox fixtures | One local part in two Projects gives no contention diagnostic with both locations, or twice in one Project does not give one Mailbox, or the Mailbox custom resource is not pinned whole | [33](../decisions/0033-a-mailbox-is-declared-by-its-local-part-and-owned-by-one-project.md) | Compiler and render tests | [#66](https://github.com/JorisJonkers-dev/estate-kit/issues/66) |
| Host-data window test | Host data is rendered for a node whose site has no window | [12](../decisions/0012-infrastructure-intent-declares-sites-nodes-and-maintenance-windows.md) | Compiler test | [#43](https://github.com/JorisJonkers-dev/estate-kit/issues/43) |
| Host-data regeneration check | A committed host-data file differs from the compiler's output | [31](../decisions/0031-host-closures-are-built-in-ci-and-cached-outside-the-cluster.md) | CI | [#43](https://github.com/JorisJonkers-dev/estate-kit/issues/43) |
| Dry-run admission fixtures | A row of the admission table in [record 58](../decisions/0058-flux-is-locked-down-per-project-and-the-service-dry-runs-as-an-identity-that-cannot-write.md) gives a different verdict, so a widened exemption fails | [2](../decisions/0002-kubernetes-is-the-substrate-and-flux-is-the-one-applier.md), [17](../decisions/0017-the-service-runs-in-the-cluster-in-rust.md), [58](../decisions/0058-flux-is-locked-down-per-project-and-the-service-dry-runs-as-an-identity-that-cannot-write.md) | Fixtures on the ValidatingAdmissionPolicy | [#31](https://github.com/JorisJonkers-dev/estate-kit/issues/31) |
| Pause refusal test | Deleting the ProjectControl object leaves the next deploy accepted instead of refused as Paused | [28](../decisions/0028-pause-and-rollback-are-a-cluster-object-per-project.md) | Service test | [#38](https://github.com/JorisJonkers-dev/estate-kit/issues/38) |
| ProjectControl admission fixtures | A write to the ProjectControl object from any other identity is admitted | [28](../decisions/0028-pause-and-rollback-are-a-cluster-object-per-project.md) | Fixtures on the admission policy | [#38](https://github.com/JorisJonkers-dev/estate-kit/issues/38) |
| Deploy dry-run | The `estate-kit / deploy (dry-run)` check on a release pull request fails | [25](../decisions/0025-a-dry-run-must-pass-before-anything-is-applied-and-what-dry-ran-is-what-deploys.md) | Required check in each Project | [#32](https://github.com/JorisJonkers-dev/estate-kit/issues/32) |
| Sign-precondition test | The service signs a render whose dry-run did not pass in the same deploy | [25](../decisions/0025-a-dry-run-must-pass-before-anything-is-applied-and-what-dry-ran-is-what-deploys.md) | Service test | [#35](https://github.com/JorisJonkers-dev/estate-kit/issues/35) |
| Digest registration test | A fragment with an unregistered digest, or a digest registered by another Project's build, is composed, or the refusal lacks its location | [8](../decisions/0008-an-image-digest-is-sealed-into-the-fragment-and-registered-by-its-build.md), [25](../decisions/0025-a-dry-run-must-pass-before-anything-is-applied-and-what-dry-ran-is-what-deploys.md) | Service test | [#36](https://github.com/JorisJonkers-dev/estate-kit/issues/36) |
| Claim-policy fixtures | A claim-policy rule has no pass and no fail token fixture | [8](../decisions/0008-an-image-digest-is-sealed-into-the-fragment-and-registered-by-its-build.md) | Service test | [#30](https://github.com/JorisJonkers-dev/estate-kit/issues/30) |
| Platform Intent drift check | The service's cached Platform Intent differs from the registry's copy | [10](../decisions/0010-platform-intent-admits-the-projects-and-is-pushed-like-any-project.md) | Nightly job | [#64](https://github.com/JorisJonkers-dev/estate-kit/issues/64) |
| Token grant check | The machine-account token grants a package beyond the ones its record lists | [9](../decisions/0009-the-live-render-is-a-signed-registry-tag-per-project-and-environment.md) | CI | [#34](https://github.com/JorisJonkers-dev/estate-kit/issues/34) |
| Token rotation alert | The token is older than its rotation schedule | [9](../decisions/0009-the-live-render-is-a-signed-registry-tag-per-project-and-environment.md) | Scheduled job, alerting | [#34](https://github.com/JorisJonkers-dev/estate-kit/issues/34) |
| Signature contract test | A key's signature fails to verify with its verifier, or a verifier accepts the other key's signature | [21](../decisions/0021-renders-and-host-tags-are-signed-by-separate-keys-with-an-offline-recovery-key.md) | Test crate | [#33](https://github.com/JorisJonkers-dev/estate-kit/issues/33) |
| Signing environment check | The signing workflow runs without its environment | [21](../decisions/0021-renders-and-host-tags-are-signed-by-separate-keys-with-an-offline-recovery-key.md) | Workflow test | [#42](https://github.com/JorisJonkers-dev/estate-kit/issues/42) |
| Closure signature test | A node accepts a closure signed by any other key | [21](../decisions/0021-renders-and-host-tags-are-signed-by-separate-keys-with-an-offline-recovery-key.md) | Host applier test | [#46](https://github.com/JorisJonkers-dev/estate-kit/issues/46) |
| Event-log tests | A duplicate (rollout id, sequence) is appended, the service's role can UPDATE or DELETE events, the retention role holds any other grant, a repeated deploy gives another rollout, a resumed stream repeats events, or a reconstructed event is not marked | [23](../decisions/0023-a-rollout-is-an-append-only-event-log-on-the-shared-postgres.md) | Tests against a real Postgres | [#27](https://github.com/JorisJonkers-dev/estate-kit/issues/27) |
| Event payload lint | An event has no version, or a payload field names a person | [23](../decisions/0023-a-rollout-is-an-append-only-event-log-on-the-shared-postgres.md) | Lint, every run | [#27](https://github.com/JorisJonkers-dev/estate-kit/issues/27) |
| Single-writer tests | The service's Deployment strategy is not `Recreate`, a non-holder signs or moves a tag, a tag change between write and re-read is retried on the old decision, or two queued triggers give more than one composition | [63](../decisions/0063-the-service-has-one-writer-and-reconciles-from-observed-state.md) | Deployment and service tests | [#28](https://github.com/JorisJonkers-dev/estate-kit/issues/28) |
| Composition budget tests | A looping input, an oversized input or a panicking transformation fails the next Composition, or the refusal code, location or problem class is wrong | [18](../decisions/0018-the-service-links-the-compiler.md) | Service tests | [#26](https://github.com/JorisJonkers-dev/estate-kit/issues/26) |
| Job queue tests | Two triggers during one composition produce more than one queued row | [73](../decisions/0073-the-composition-queue-is-a-row-in-a-postgres-job-table.md) | Service test with the `JobStore` fake; adapter contract suite on a real Postgres | [#64](https://github.com/JorisJonkers-dev/estate-kit/issues/64) |
| OpenAPI route contract test | A route or its request or response type is not in the committed document | [43](../decisions/0043-the-service-api-is-an-openapi-3-1-contract.md) | Contract test | [#26](https://github.com/JorisJonkers-dev/estate-kit/issues/26) |
| OpenAPI lint | The committed document breaks the lint rules, including cursor pagination | [43](../decisions/0043-the-service-api-is-an-openapi-3-1-contract.md) | CI | [#26](https://github.com/JorisJonkers-dev/estate-kit/issues/26) |
| Error catalogue test | A catalogue code has no entry or no fixture | [43](../decisions/0043-the-service-api-is-an-openapi-3-1-contract.md) | Contract test | [#26](https://github.com/JorisJonkers-dev/estate-kit/issues/26) |
| UI stub validation | A UI stub does not validate against the OpenAPI document | [43](../decisions/0043-the-service-api-is-an-openapi-3-1-contract.md) | UI tests | [#52](https://github.com/JorisJonkers-dev/estate-kit/issues/52) |
| Authorization matrix test | A route has no matrix row, a row has no route, or a denied row is not refused | [54](../decisions/0054-every-trust-boundary-has-a-threat-table-and-every-route-an-authorization-row.md) | Service test | [#26](https://github.com/JorisJonkers-dev/estate-kit/issues/26) |
| CLI schema fixtures | The CLI's JSON output for an example or refusal fixture does not validate against the committed schema | [48](../decisions/0048-the-cli-s-json-output-has-a-committed-schema.md) | CI | [#23](https://github.com/JorisJonkers-dev/estate-kit/issues/23) |
| Characterization fixtures | A Go or Python program's recorded answers change, or the gate's writes and the dashboard's silences are not covered | [55](../decisions/0055-every-go-and-python-program-is-characterized-before-it-is-rewritten.md), [74](../decisions/0074-the-release-gate-and-observation-each-have-a-named-write.md) | Each component's and the service's CI | [#25](https://github.com/JorisJonkers-dev/estate-kit/issues/25) |
| Archive checklist | A program is archived with a failing fixture or an unlisted change, or its fixtures are deleted before the owning crate's docs hold its behaviour summary | [55](../decisions/0055-every-go-and-python-program-is-characterized-before-it-is-rewritten.md) | Checklist in the archive pull request | [#53](https://github.com/JorisJonkers-dev/estate-kit/issues/53) |
| Host VM tests | A node class does not survive a live change and a reboot change through the applier | [30](../decisions/0030-a-host-applier-on-each-node-pulls-its-signed-host-tag.md) | NixOS VM test per node class | [#45](https://github.com/JorisJonkers-dev/estate-kit/issues/45) |
| Node-order check | A target breaks the version skew policy | [30](../decisions/0030-a-host-applier-on-each-node-pulls-its-signed-host-tag.md) | Host applier test | [#49](https://github.com/JorisJonkers-dev/estate-kit/issues/49) |
| Eviction fixture | The eviction policy admits another node's pods | [30](../decisions/0030-a-host-applier-on-each-node-pulls-its-signed-host-tag.md) | Admission fixture | [#47](https://github.com/JorisJonkers-dev/estate-kit/issues/47) |
| Shadow comparison | A difference is missing from `shadow/expected-differences.yaml`, a ledger entry is unused, or an entry's cause is outside the closed set | [67](../decisions/0067-the-compiler-is-written-to-the-1-0-contract.md) | Comparison job | [#50](https://github.com/JorisJonkers-dev/estate-kit/issues/50) |
| Shadow admission check | Any Flux object has a shadow-prefixed source | [67](../decisions/0067-the-compiler-is-written-to-the-1-0-contract.md) | Admission check | [#50](https://github.com/JorisJonkers-dev/estate-kit/issues/50) |
| Derivation coverage | A live value of the estate is reached by no field; each is listed as a counterexample | [5](../decisions/0005-derivation-is-total.md) | Renders the live estate and diffs it against what runs | [#50](https://github.com/JorisJonkers-dev/estate-kit/issues/50) |
| Oracle change check | An oracle file changes in the same pull request as the code it tests, unless the pull request is labelled as an oracle review | [67](../decisions/0067-the-compiler-is-written-to-the-1-0-contract.md) | CI | [#22](https://github.com/JorisJonkers-dev/estate-kit/issues/22) |
| E2E scenarios | A scenario of [record 69](../decisions/0069-the-deploy-path-is-tested-end-to-end.md) fails: a deploy leaves the tag, the object or the Deployment status other than a consumer should see | [2](../decisions/0002-kubernetes-is-the-substrate-and-flux-is-the-one-applier.md), [7](../decisions/0007-a-project-s-state-lives-with-the-project.md), [8](../decisions/0008-an-image-digest-is-sealed-into-the-fragment-and-registered-by-its-build.md), [9](../decisions/0009-the-live-render-is-a-signed-registry-tag-per-project-and-environment.md), [10](../decisions/0010-platform-intent-admits-the-projects-and-is-pushed-like-any-project.md), [17](../decisions/0017-the-service-runs-in-the-cluster-in-rust.md), [20](../decisions/0020-no-render-cache-an-unchanged-render-is-not-published-again.md), [25](../decisions/0025-a-dry-run-must-pass-before-anything-is-applied-and-what-dry-ran-is-what-deploys.md), [28](../decisions/0028-pause-and-rollback-are-a-cluster-object-per-project.md), [58](../decisions/0058-flux-is-locked-down-per-project-and-the-service-dry-runs-as-an-identity-that-cannot-write.md), [63](../decisions/0063-the-service-has-one-writer-and-reconciles-from-observed-state.md), [73](../decisions/0073-the-composition-queue-is-a-row-in-a-postgres-job-table.md) | `e2e/`, nightly and before a release | [#72](https://github.com/JorisJonkers-dev/estate-kit/issues/72) |
| Release e2e requirement | The release workflow runs without the e2e job's success on the release commit | [69](../decisions/0069-the-deploy-path-is-tested-end-to-end.md) | Release workflow | [#72](https://github.com/JorisJonkers-dev/estate-kit/issues/72) |
| Scenario-list test | A use case in the scenario list has no scenario | [69](../decisions/0069-the-deploy-path-is-tested-end-to-end.md) | `e2e/` suite | [#72](https://github.com/JorisJonkers-dev/estate-kit/issues/72) |
| RBAC fixtures | A credential grants a verb or resource outside the context's table | [74](../decisions/0074-the-release-gate-and-observation-each-have-a-named-write.md) | E2E suite | [#72](https://github.com/JorisJonkers-dev/estate-kit/issues/72) |
| Provenance tests | A rendered field has no element reference, reordering id-keyed lists changes an annotation or digest, or a refused field's diagnostic lacks its line | [72](../decisions/0072-per-field-provenance-and-explain-are-deferred.md) | Test crate | deferred until [record 72](../decisions/0072-per-field-provenance-and-explain-are-deferred.md) is Accepted |

## Mutation testing

cargo-mutants changes one expression at a time, rebuilds, and runs the tests.
A mutant rebuilds its own crate and every crate and test binary that depends
on it, so the crate graph decides the cost:

- **Small domain and step crates** keep each rebuild short, and their unit
  tests live in the same crate, so `cargo mutants --package <crate>` runs only
  that crate's tests.
- **No heavy dependency in a mutated crate.** Domain crates do not compile
  `kube` or `sqlx`.
- **On main, never on a pull request.** deploy-kit moved its mutation run to
  every push to main on 2026-10-29: per pull request it took 80% of CI minutes,
  and its spurious failures sat in files the pull request had not changed
  ([deploy-kit ADR 0063](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/architecture/0063-coverage-and-mutation-are-ratchets.md)). estate-kit starts there: each push to main mutates
  the lines changed since the last green report (`--in-diff`), sharded; a
  weekly full run, sharded across 8 to 32 runners, opens an issue per
  survivor.
- **Turned on per crate.** A crate joins the 100% gate when its tests are in;
  until then it reports ([process-5](../research/review/process-and-plan.md)).
- **An equivalent mutant is a design smell.** It is rewritten, not excluded.
  An exclusion in `.cargo/mutants.toml` needs a reason and an issue, and the
  number of exclusions is held at zero by the ratchet.

## Speed budgets

| Gate | Budget | How |
| --- | --- | --- |
| Lint, unit, property, fixture and contract tests on a pull request | Under 2 minutes | Only crates the diff reaches and their dependents; `cargo nextest`; `rust-cache` |
| Integration on a pull request | Under 5 minutes | Containers started once per test binary; a template database per test ([workspace ADR-0021](https://github.com/JorisJonkers-dev/workspace/blob/main/docs/decisions/ADR-0021-liquibase-runner-is-the-one-migration-path.md)) |
| Mutation on main | Under 10 minutes | `--in-diff`, sharded, crates in the graph's leaves |
| Full mutation | Weekly | 8 to 32 shards |
| End to end | Under 15 minutes | Nightly and before a release |

The path-to-crate mapping follows the estate's path buckets: a changed path
runs the crates that own it and their dependents, and a path no crate claims
runs everything.

## Compile time

A change should rebuild only what depends on it. The rules that make that
true are in [Keeping builds fast](rust-workspace.md#keeping-builds-fast): heavy
dependencies only at the edge, no `k8s-openapi`, few proc macros, one feature
set, per-crate test runs.

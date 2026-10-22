# The register, as planned

The records to be written, in reading order, with their current status. Each title becomes a file `NNNN-<slug>.md` here when written, from [the template](template.md). Records 42 onwards are placed into reading order when the register is written; the model's own records follow after the cutover.

The [design review](../research/review/README.md) of 2026-10-22 changed or added the rows marked Proposed; they stay Proposed until their records are written and accepted ([#20](https://github.com/JorisJonkers-dev/estate-kit/issues/20)).

| # | Record | Status |
| --- | --- | --- |
| 1 | One maintainer, one cluster, one estate | Accepted |
| 2 | Kubernetes is the substrate, and Flux is the one applier | Accepted |
| 3 | Three models: Intent, Resolved Deployment, Deliverable Set | Accepted |
| 4 | Contention decides authority | Accepted |
| 5 | Derivation is total | Accepted |
| 6 | Every render is a function of pinned inputs | Accepted |
| 7 | A Project's state lives with the Project | Accepted |
| 8 | An image's digest is sealed into the Intent Fragment, and its build registered it | Proposed |
| 9 | The live render is a signed registry tag per Project and environment | Accepted |
| 10 | Platform Intent admits the Projects | Accepted |
| 11 | Platform Intent is pushed like any Project; the service's copies are a cache | Accepted |
| 12 | Infrastructure Intent declares sites, nodes and maintenance windows | Accepted |
| 13 | The compiler stays TypeScript until model 1.0, shipped as one binary | Proposed |
| 14 | The compiler is a chain of steps, one module per step | Proposed |
| 15 | Types are held to the committed schemas by a drift test | Proposed |
| 16 | The committed JSON Schemas are the contract | Accepted |
| 17 | The service runs in the cluster, in Go: it composes, and Flux applies | Accepted |
| 18 | The service runs the compiler as a subprocess over a directory and a result file | Accepted |
| 19 | One composition runs at a time | Accepted |
| 20 | No render cache: an unchanged render is not published again | Proposed |
| 21 | Renders and host tags are signed by separate Transit keys, with an offline recovery key | Proposed |
| 22 | Every caller authenticates with an OIDC token checked against a claim policy | Proposed |
| 23 | A rollout is a deploy run that streams the service's work | Accepted |
| 24 | A rollout is an append-only event log on the shared Postgres | Proposed |
| 25 | A dry-run must pass before anything is applied | Accepted |
| 26 | Images are built once and promoted, so what dry-ran is what deploys | Accepted |
| 27 | A diagnostic names a model path, and the caller resolves the line | Accepted |
| 28 | Pause and Rollback are a cluster object per Project; a missing object reads as Paused | Proposed |
| 29 | The compiler renders host data; hand-written modules consume it | Accepted |
| 30 | A host applier on each node pulls its signed host tag, and decides a reboot before the Lease | Proposed |
| 31 | Host closures are built in CI and cached outside the cluster, signed by an environment-scoped key | Proposed |
| 32 | Node order is derived from the change and the version skew rule | Accepted |
| 33 | A Mailbox is declared by its local part and owned by one Project | Accepted |
| 34 | Components live in this repository at one version | Accepted |
| 35 | A second implementation, if one is ever written, meets the first at the oracle files | Proposed |
| 36 | One concept per module, one fake per port, oracles only at the seams | Accepted |
| 37 | Every gate has a speed budget; coverage and mutation are ratchets | Accepted |
| 38 | One version for every part | Accepted |
| 39 | Decisions live as Markdown in docs/, and a Pages site is built from it | Accepted |
| 40 | Records are read in order and cite their lessons | Accepted |
| 41 | A record has a status; a locked record needs a failing check | Accepted |
| 42 | The shadow composition is inert | Accepted |
| 43 | The service API is an OpenAPI 3.1 contract | Accepted |
| 44 | Errors are RFC 9457 problems drawn from one catalogue | Accepted |
| 45 | Deploy calls are idempotent on project and fragment digest; streams resume by sequence | Accepted |
| 46 | IDs are UUIDv7, times RFC 3339 in UTC, and absent means unset | Accepted |
| 47 | Schemas evolve additively within a major version, checked in CI | Accepted |
| 48 | The fields the service reads from result.json are committed fixtures that Rust CI verifies | Accepted |
| 49 | Events are versioned and upcast on read, and hold no personal data | Accepted |
| 50 | Four bounded contexts, each boundary its own record | Accepted |
| 51 | History is kept 400 days; renders are kept by count, age and tag | Accepted |
| 52 | Three service levels: deploy p95, availability, drift detection | Accepted |
| 53 | Traces go to Tempo and logs to Loki, keyed by rollout id | Accepted |
| 54 | Every trust boundary has a threat table, and every route an authorization row | Accepted |
| 55 | Go services are characterized before they are ported | Accepted |
| 56 | Agent files are short, and what must always hold is a check | Accepted |
| 57 | Configuration is flags, then environment, then file; secrets only by reference | Accepted |
| 58 | Flux is locked down per Project, and the service dry-runs as an identity that cannot write | Proposed |
| 59 | Vault unseals itself through a cloud KMS | Proposed |
| 60 | The API server's datastore is backed up off the provider, and its restore is drilled | Proposed |
| 61 | A rollback moves the tag back to the last Serving render without composing | Proposed |
| 62 | ghcr tags move with a machine account's token kept in Vault | Proposed |
| 63 | The service has one writer and reconciles from observed state | Proposed |
| 64 | Renders use a canonical YAML style specified on one page | Proposed |

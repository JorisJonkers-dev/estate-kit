# Redesign practices

Practices for redesigning and re-implementing deploy-kit, delivery and
estate-dashboard as estate-kit. The note checks a set of guidance from another
agent against primary sources, then measures the current design against it.
It ends with a proposed first decision set.

As of 2026-10-22. Sources were opened on that date. Practitioner blogs are
marked as such, because they carry less weight than a standard, an RFC or a
tool's own documentation.

The note has three parts:

1. [Practices](#1-practices): one section per topic. Each practice ends with a
   line that says what it means for estate-kit.
2. [Gap analysis](#2-gap-analysis): every item of the guidance, marked covered,
   partly covered or missing in the current design.
3. [A first decision set](#3-a-first-decision-set): records numbered in
   reading order. Each is marked as settled by the design or open for the
   maintainer.

The current design was read from these sources:

- [`README.md`](../../README.md), [`CONTEXT.md`](../../CONTEXT.md),
  [`docs/design/README.md`](../design/README.md),
  [`prior-art.md`](prior-art.md) and the diagram declarations in
  [`docs/diagrams/specs.py`](../diagrams/specs.py);
- the design document's tabs Choices made, Decision records, Identity and
  access, Errors in CI, Inside the service, Code shape and speed, and
  Operating the estate (outline only).

## 1. Practices

### 1.1 Re-implementation strategy

**The big rewrite usually fails, for known reasons.** Spolsky argues that a
from-scratch rewrite is the worst strategic mistake a software company can
make. Old code that looks messy holds years of bug fixes found in the field.
Netscape stopped shipping for about three years while it rewrote, and lost the
market
([Spolsky, 2000](https://www.joelonsoftware.com/2000/04/06/things-you-should-never-do-part-i/)).
Caudill's six case studies push back on the absolute claim. Some rewrites
won, and in the cases that won, the new system was built beside the old one
rather than in its place (Herb Caudill, 2019, practitioner
essay; summary at
[simonwillison.net](https://simonwillison.net/2019/Feb/19/lessons-6-software-rewrite-stories)).
- *For estate-kit:* the risk is not the rewrite itself, but losing the
  knowledge held in the old code. deploy-kit's oracle files carry that
  knowledge for the compiler. delivery and estate-dashboard have no oracles,
  so their behaviour is the part most at risk.

**Strangler fig: grow the new system beside the old one.** Replace behaviour
piece by piece behind seams, and accept transitional code that exists only
while both systems run. Fowler reports that the simple-replacement plan has
mostly gone down in flames. Small replaced parts deliver value early and teach
the team how to do the rest
([Fowler, Strangler Fig](https://martinfowler.com/bliki/StranglerFigApplication.html);
[Patterns of Legacy Displacement](https://martinfowler.com/articles/patterns-legacy-displacement/)).
- *For estate-kit:* the staged switch is a strangler at the level of the
  Project. Each Project's tag can move to the new service on its own, so the
  switch needs no estate-wide flag day.

**Branch by abstraction: keep the trunk shippable during the swap.** Put an
abstraction over the old supplier, build the new one behind it, move clients
across, then delete the old one
([Fowler, Branch By Abstraction](https://martinfowler.com/bliki/BranchByAbstraction.html),
a name Paul Hammant coined).
- *For estate-kit:* the composition seam is the abstraction. The old delivery
  path and the new service both turn the same fragments into a render. Which
  of them moves a Project's tag is one setting per Project.

**Characterization tests: pin what the code does, not what it should do.**
Run the code, capture its actual output, and make that output the expected
value. The aim is to detect any change in behaviour during a rewrite you do
not fully understand
([Feathers, Characterization Testing](https://michaelfeathers.silvrback.com/characterization-testing)).
Approval and golden tests are the tooling form of the same idea
([ApprovalTests](https://approvaltests.com/); [insta](https://insta.rs/) for
Rust).
- *For estate-kit:* write characterization tests for delivery and
  estate-dashboard before porting them, at their HTTP and event-stream
  boundaries. Commit them as oracle files beside deploy-kit's, so all three
  ports meet the same kind of proof.

**Parallel run and shadow traffic: compare live, but never act twice.**
GitHub's Scientist runs the old code (the control) and the new code (the
candidate) on the same input. The caller gets the control's result, and every
mismatch is published. GitHub used it to replace its permissions code, and
warns that it must not wrap code with side effects
([GitHub, Scientist, 2016](https://github.blog/2016-02-03-scientist/)).
- *For estate-kit:* shadow composition must be inert. It must not move a
  `prod` tag, must not sign with the production key, and must not write the
  production event log. Compare render digests and diagnostics, and publish
  the mismatches. A shadow that also deploys is a second applier.

**Hyrum's law: every observable behaviour becomes a contract.** With enough
users, someone depends on any behaviour a system shows, whether the contract
promised it or not ([hyrumslaw.com](https://www.hyrumslaw.com/)).
- *For estate-kit:* byte-identical parity is the right cutover proof, because
  Flux, Kubernetes and the people reading diffs consume the exact bytes. It
  also means a cosmetic change in the old stack during the port must land in
  the oracles the same day.

### 1.2 Decision records

**Nygard's ADR is short, numbered and never deleted.** A record has a title,
its context, the decision, a status and its consequences. It runs to one or
two pages, numbers are never reused, and a reversed decision is marked
superseded rather than removed. Statuses are proposed, accepted, deprecated
and superseded
([Nygard, 2011](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)).
- *For estate-kit:* the register already keeps numbers in reading order and
  never reuses one.

**MADR adds options, drivers and a Confirmation section.** MADR 4.0.0
(2024-09-17) adds the considered options, the decision drivers, and a
Confirmation section that says how compliance is checked, for example by a
review or an ArchUnit-style test. Status, date, decision-makers, consulted and
informed live in YAML front matter. The listed statuses are proposed,
rejected, accepted, deprecated and superseded ([MADR](https://adr.github.io/madr/)).
- *For estate-kit:* Confirmation is the field that answers "locked, and
  backed by which failing check". Make it required for an accepted record.

**Y-statements compress a decision into one sentence.** The shape is: in the
context of X, facing Y, we decided for Z and against W, to achieve Q,
accepting the downside D. It comes from Zdun and others, "Sustainable
Architectural Design Decisions", IEEE Software, 2013
([adr.github.io](https://adr.github.io/)). The original Medium post refused
the fetch, so this is cited from the ADR organisation's index.
- *For estate-kit:* open each record with one Y-statement. Agents and people
  can scan the register at that level, and the Choices made table already
  holds the chosen and rejected halves.

**Decision records for agents (practitioner evidence).** Agents have no memory
of yesterday, so a record in the repository tells them why the code has its
shape. Davidson reports two failure modes. Agents apply an outdated decision
too rigidly, and they bloat a record with amendment logs when they edit it.
His advice is that a record should state only the decision in force, leave
the history to git, and give agents explicit permission to flag a decision
that no longer fits
([Davidson, 2026](https://duncandavidson.com/agents-love-decisions);
[Swan, 2025](https://blog.thestateofme.com/2025/07/10/using-architecture-decision-records-adrs-with-ai-coding-assistants/)).
- *For estate-kit:* this supports deploy-kit's rule of rewriting a record in
  place rather than superseding it. It conflicts with Nygard's superseded
  status, and the conflict is deliberate. Say so once, in the record about
  records.

**Status values, mapped to "locked" and "proposed".** Proposed and Accepted
are the standard words. "Locked" is not a standard status. In practice it
means accepted and confirmed by a check.
- *For estate-kit:* use two statuses: `proposed` (open, may change without
  ceremony) and `accepted` (requires a Confirmation that names a check, or
  says "review only" with a reason). Drop deprecated and superseded, because a
  changed decision is rewritten.

**arc42 gives a checklist of what an architecture document covers.** It has
twelve sections: goals, constraints, context, solution strategy, building
blocks, runtime, deployment, cross-cutting concepts, decisions, quality
requirements, risks and glossary ([arc42](https://arc42.org/overview)).
- *For estate-kit:* sections 8 (cross-cutting concepts) and 10 (quality
  requirements) are the two the design has least of. Use the list as a
  completeness check, not as a document layout.

**C4: context and container diagrams are enough for most teams.** C4 has four
levels (system context, container, component, code) and three supporting
diagrams (landscape, dynamic, deployment). The site says the first two levels
suffice for most teams, and that the lower levels are drawn only where they
add value ([c4model.com](https://c4model.com/diagrams)). Structurizr defines
one C4 model as text and renders many views from it, alongside Markdown
documentation and ADRs ([Structurizr DSL](https://docs.structurizr.com/dsl)).
- *For estate-kit:* `docs/diagrams/specs.py` already plays the
  diagrams-as-code role. The `context` diagram should show every outside
  system (GitHub, Vault, auth-api, Postgres, people). The `components`
  diagram should name its containers and their protocols.

**Docs as code and living documentation.** Documentation lives in git as
plain text, goes through the same review, and is tested by the same pipeline
([Write the Docs](https://www.writethedocs.org/guide/docs-as-code/)). Living
documentation is meant to be reliable, low-effort, collaborative and
insightful. It is derived from the code and its tests wherever possible,
rather than written separately (Martraire,
[*Living Documentation*, 2019](https://www.informit.com/store/living-documentation-continuous-knowledge-sharing-by-9780134689326)).
Diátaxis splits documentation into tutorials, how-to guides, reference and
explanation ([diataxis.fr](https://diataxis.fr/)).
- *For estate-kit:* the error-code catalogue, the rule ledger and the schema
  reference should be generated or checked from the code, never kept by hand.
  The ADRs are the explanation, and `spec/` is the reference.

### 1.3 Fitness functions and architecture tests

**A fitness function makes "fit" executable.** Ford, Parsons and Kua define
evolutionary architecture as one that changes incrementally and keeps itself
fit by checks that are automated wherever possible
([evolutionaryarchitecture.com](https://evolutionaryarchitecture.com/)).
Thoughtworks describes them as automated gates in the pipeline that measure
how close the architecture is to an aim, and gives examples: coverage above a
floor, an error rate during deploys, no plaintext secrets, no PII in logs,
trace ids present
([Thoughtworks](https://www.thoughtworks.com/insights/articles/fitness-function-driven-development)).
- *For estate-kit:* each accepted record's Confirmation is a fitness function.
  deploy-kit already has the discipline (a rule id, a ledger row and a
  failing fixture, per
  [deploy-kit 0066](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/architecture/0066-every-enforced-rule-has-an-id-a-row-and-a-fixture.md)).
  Carry it over unchanged.

**ArchUnit-style rules test the dependency graph as a unit test.** ArchUnit
checks package and class dependencies, layers and cycles from inside an
ordinary test run ([archunit.org](https://www.archunit.org/)).

**Rust: Cargo's crate graph is the strongest boundary there is.** A crate
cannot use another crate it does not declare, so one crate per step makes the
layer rule a compile error. cargo-deny lints the dependency graph for
advisories, licences, sources and bans. A ban entry can carry `wrappers`: only
the listed crates may depend directly on the banned one. The same check also
flags duplicate and unused `[workspace.dependencies]`
([cargo-deny](https://embarkstudios.github.io/cargo-deny/);
[bans config](https://embarkstudios.github.io/cargo-deny/checks/bans/cfg.html)).
- *For estate-kit:* use `wrappers` to pin each adapter crate to its one
  caller, for example the OCI client only inside the registry adapter. Add a
  small test that reads `cargo metadata` and asserts the allowed edges between
  workspace crates, because cargo-deny bans third-party crates, not internal
  edges.

**Go: packages are not enforced by the compiler beyond `internal/`.** The
`internal/` directory blocks imports from other modules, and nothing more.
go-arch-lint maps packages to named components and fails on any import that
a component's `mayDependOn` list does not allow
([go-arch-lint](https://github.com/fe3dback/go-arch-lint)). depguard, run
through golangci-lint, allows or denies import paths per file glob
([depguard](https://github.com/OpenPeeDeeP/depguard)).
- *For estate-kit:* go-arch-lint for the service's internal layering (the
  rollout core imports no adapter). depguard for third-party bans, for
  example no mocking library and no second logging library.

### 1.4 Repositories that agents can read

**AGENTS.md is the open, tool-neutral agent file.** It is plain Markdown with
no required fields: overview, build and test commands, code style, testing,
security, and PR conventions. In a monorepo the nearest file wins, and the
user's prompt overrides it. It is stewarded by the Agentic AI Foundation under
the Linux Foundation ([agents.md](https://agents.md/)).
- *For estate-kit:* the repository has no AGENTS.md yet. Add one with a
  `CLAUDE.md` that imports it, and one nested file per toolchain root
  (`compiler/`, `service/`), since Rust and Go commands differ.

**Claude Code: short instruction files, deterministic checks for
must-always rules.** Anthropic's guidance:
- A CLAUDE.md holds only what Claude cannot infer from the code: commands,
  non-default style, test runners, repository etiquette, project-specific
  architectural decisions, and gotchas.
- Aim for fewer than 200 lines per file. Move partial-scope rules into
  path-scoped `.claude/rules/` files, and procedures into skills.
- Instructions are advisory. Hooks are deterministic, so a rule that must
  hold every time belongs in a hook or a check.
- The most valuable thing to give an agent is a check it can run, which
  returns pass or fail.
- Specs work best when they are self-contained: they name files and
  interfaces, state what is out of scope, and end with an end-to-end
  verification step.

Sources: [best practices](https://code.claude.com/docs/en/best-practices),
[memory](https://code.claude.com/docs/en/memory).
- *For estate-kit:* this is the strongest primary support for the guidance's
  "lock what an agent cannot infer". Lock it in a short file, and back every
  must-always rule with a check rather than a sentence.

**Spec-driven development (GitHub Spec Kit).** The specification is the
primary artifact, and code is its expression. A project constitution states
principles once: test-first, a small number of components, framework
features used directly rather than wrapped, and integration tests against real
services. Templates make the model mark unknowns with `[NEEDS CLARIFICATION]`
rather than guess
([spec-kit](https://github.com/github/spec-kit);
[spec-driven.md](https://github.com/github/spec-kit/blob/main/spec-driven.md)).
- *For estate-kit:* `spec/` plus the accepted records already serve as the
  constitution. Borrow one habit: an open question stays visible in the
  document as a marker, and is never filled with a plausible default.

**Locked versus free, as the sources agree.**
- Lock what is expensive to change, and what cannot be read from the code:
  boundaries, the schemas, stored data and its identifiers, invariants, and
  conventions that cut across modules.
- Leave free what a test already pins down, and what a later agent can change
  locally: a function's body, a private type, the order of private helpers.
- Locked without a check is advisory, and the agent's context window decides
  whether it holds.
- *For estate-kit:* every accepted record names its check. A record that
  cannot have a check (for example "one maintainer") says so.

### 1.5 Contracts and errors

**RFC 9457 is the one HTTP error shape.** A problem details object has `type`
(a URI and the primary identifier), `status`, `title`, `detail` and
`instance`, served as `application/problem+json`. Extension members are
allowed, and clients ignore those they do not know. It is not a debugging
channel, so stack traces and internals stay out. When several problems occur,
the response carries the most relevant one, and a problem type can define an
extension that lists the rest. Published July 2023, it obsoletes RFC 7807
([RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html)).
- *For estate-kit:* the service's API returns problem details, with `type`
  built from the catalogue code (for example
  `https://estate-kit.dev/errors/E_GRANT_UNKNOWN_TARGET`; the domain is a
  placeholder). A diagnostics extension carries the list of model-path
  diagnostics from a composition.

**An error-code catalogue is reference documentation generated from code.**
deploy-kit already keeps every spec `E_` code exercised by a fixture or
marked pending (its `lint:codes` gate).
- *For estate-kit:* one catalogue file is the source for the Rust compiler,
  the Go service, the problem `type` URIs and the documentation page. A gate
  checks that every code has a firing fixture and a page.

**Compatibility rules for the schemas.** Google's AIP-180 separates source,
wire and semantic compatibility. Adding an optional field is compatible.
Adding a required field, removing or renaming a field, changing a type or a
default, or changing validation bounds is breaking
([AIP-180](https://google.aip.dev/180)). Confluent defines BACKWARD (new
readers read old data, so upgrade readers first), FORWARD (old readers read
new data, so upgrade writers first) and FULL, each with a transitive variant
([Confluent](https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html)).
JSON Schema 2020-12 is the dialect to declare with `$schema`
([json-schema.org](https://json-schema.org/understanding-json-schema/reference/schema)).
- *For estate-kit:* authored intent is read by a compiler that is newer than
  the YAML, so the intent schemas must be BACKWARD_TRANSITIVE within a major
  version. `result.json` and the event schemas are read by the service, which
  ships in lockstep with the compiler, so they need no promise beyond "same
  version". Put the rule in a check that diffs each schema against its last
  release.

**Golden examples written as Given, When, Then.** Oracle files are golden
tests. The practice the guidance adds is to name each oracle by its scenario:
given these inputs, when this command runs, then these bytes come out.
- *For estate-kit:* lay out each oracle directory as `given/`, a `when` file
  (the command line) and `then/`. Agents can then find the example that
  matches a change, and the four-seam rule stays intact.

### 1.6 Cross-cutting semantics and data primitives

**Idempotency.** The IETF `Idempotency-Key` header draft makes POST and PATCH
safe to retry. Draft 07 has expired and is not an RFC
([draft-ietf-httpapi-idempotency-key-header](https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/)).
- *For estate-kit:* prefer natural keys over a header. A deploy is
  identified by (Project, fragment digest), so a retried deploy job joins the
  existing rollout instead of starting a second one. A tag move is a
  compare-and-swap from the expected old digest.

**Pagination from day one.** AIP-158 uses `page_size`, an opaque
`page_token` and `next_page_token`. Adding pagination to an existing list is a
breaking change, so a list endpoint is paginated from its first version
([AIP-158](https://google.aip.dev/158)).
- *For estate-kit:* rollout history and Project lists are paginated, with
  cursors that clients cannot parse. The event stream needs no pages, because
  it resumes from a sequence number.

**Ordering, delivery and concurrency.** Kubernetes gives optimistic
concurrency through `resourceVersion`, and Leases for mutual exclusion
([API concepts](https://kubernetes.io/docs/reference/using-api/api-concepts/)).
- *For estate-kit:*
  - Events are totally ordered within one rollout and carry no order across
    rollouts.
  - Delivery to a stream reader is at least once, and the reader deduplicates
    by sequence number.
  - The Project object is written with `resourceVersion` preconditions.
  - Host switches hold the Lease.
  - Write these four sentences down once, as one record.

**Identifiers and timestamps.** UUIDv7 puts a millisecond Unix timestamp in
its high bits, so new keys stay local in a B-tree index. RFC 9562 recommends
it over v1 and v6, and advises treating UUIDs as opaque
([RFC 9562](https://www.rfc-editor.org/rfc/rfc9562.html)).
- *For estate-kit:* rollout ids are UUIDv7, and every other id is a content
  digest or a Kubernetes name. Timestamps are RFC 3339 in UTC, with
  sub-second precision on events. In the schemas, absent and `null` never
  both appear: optional fields are omitted, never null.

### 1.7 Observability

**Use OpenTelemetry's semantic conventions, not house names.** The
conventions give fixed attribute names and values across traces, metrics,
logs, events and resources
([semconv](https://opentelemetry.io/docs/specs/semconv/)). The HTTP span
conventions are stable, and include `http.request.method`, `http.route`,
`http.response.status_code` and `error.type`. Instrumentations switch to the
stable names through `OTEL_SEMCONV_STABILITY_OPT_IN=http`
([HTTP spans](https://opentelemetry.io/docs/specs/semconv/http/http-spans/)).
A log record carries `TraceId`, `SpanId` and `TraceFlags`, so logs join their
trace ([logs data model](https://opentelemetry.io/docs/specs/otel/logs/data-model/)).
W3C Trace Context's `traceparent` header carries the trace across processes
([W3C Recommendation, 2021](https://www.w3.org/TR/trace-context/)).
- *For estate-kit:*
  - One correlation chain runs from the GitHub run id through the rollout id
    and the trace id to the composition and the compiler subprocess. The
    service passes `traceparent` to the subprocess in an environment
    variable.
  - Logs are structured. Each has the OTel fields plus three house
    attributes: `estate.project`, `estate.rollout_id` and
    `estate.render_key`.
  - Name the house attributes once, in a record, and check them with a test
    that parses a log line.

**SLOs as numbers, few of them.** Choose a small set of SLIs that users feel.
Use percentiles, not averages. Keep internal targets tighter than published
ones, and spend an error budget
([Google SRE book](https://sre.google/sre-book/service-level-objectives/)).
- *For estate-kit:* candidate SLIs are the time from a deploy request to the
  moved tag at p95, the rate of failed compositions that are not the author's
  fault, and the time a host rollout takes per node. The gate speed budgets
  in Code shape and speed are already numeric NFRs for CI.

### 1.8 Security design

**Threat modeling answers four questions.** What are we building? What could
go wrong? What will we do about it? Was the effort good enough? It should be
done early, often and in small scopes, and judged by design fixes rather than
by paperwork ([Threat Modeling Manifesto](https://www.threatmodelingmanifesto.org/)).
STRIDE lists the threat types to look for: Spoofing, Tampering, Repudiation,
Information disclosure, Denial of service and Elevation of privilege
([Microsoft](https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats)).
- *For estate-kit:* draw one trust-boundary diagram (GitHub and CI, the
  service, Vault, ghcr, the API server, the nodes, the off-cluster cache).
  Walk STRIDE across each edge that crosses a boundary. Keep the result as a
  table in the security record, and revisit it in any PR that adds an edge.

**An authorization matrix, denied by default and tested per row.** OWASP
asks for least privilege, deny by default, a check on every request, and
tests that the designed permissions are what the code enforces
([OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)).
- *For estate-kit:* turn the Identity and access table into a matrix of
  caller by action (plan, dry-run, deploy, watch, pause, roll back, admit,
  push Platform Intent, gate webhook, move a host tag). One table-driven test
  asserts each cell, including the refusals.

### 1.9 Rust and Go conventions

**Rust workspace layout.** Matklad's advice for large workspaces:
- a virtual manifest at the root;
- a flat `crates/*`, with each crate named exactly after its folder;
- internal crates at version `0.0.0`;
- automation in Rust through `cargo xtask`.

([matklad, 2021](https://matklad.github.io/2021/08/22/large-rust-workspaces.html)).
- *For estate-kit:* this fits one crate per step. Lockstep versioning applies
  to the shipped binary, not to internal crate versions.

**thiserror in the library crates, anyhow only at the edge.** anyhow's README
recommends anyhow when the caller does not care about the error type
(application code), and thiserror when the caller should receive exactly the
failure you designed (library code) ([anyhow](https://github.com/dtolnay/anyhow)).
- *For estate-kit:* every step crate returns a `thiserror` enum, because its
  variants are diagnostics with codes. Only `main` and `xtask` may use anyhow.
  A cargo-deny `wrappers` entry enforces it.

**Go layout: the official guide, not "project-layout".** The Go team's guide
puts server code in `internal/` and entry points in `cmd/<name>/`
([go.dev, module layout](https://go.dev/doc/modules/layout)). Russ Cox stated
that `golang-standards/project-layout` is not a Go standard, and that most Go
code does not use `pkg/`
([issue 117](https://github.com/golang-standards/project-layout/issues/117)).
- *For estate-kit:* use `service/cmd/estate-kit-service` and
  `service/internal/{api,auth,rollout,compose,registry,signer,cluster,github,store,ui}`,
  with no `pkg/`. The components use the same shape.

**Go error wrapping makes the wrapped error part of the API.** Use `%w` with
`errors.Is` and `errors.As` when callers should inspect the cause. Use `%v`
to hide an implementation detail
([Go 1.13 errors](https://go.dev/blog/go1.13-errors)).
- *For estate-kit:* adapters translate outside errors into a few sentinel
  errors of their port (`ErrNotFound`, `ErrConflict`, `ErrUnavailable`). They
  wrap the cause with `%v`, so no client-go or oras type leaks into the
  rollout core.

### 1.10 Wiki or docs in the repository

**A GitHub wiki is a separate git repository, outside review.** A wiki clones
from `<repo>.wiki.git`, and only pushes to its default branch go live
([GitHub Docs, editing wiki pages](https://docs.github.com/en/communities/documenting-your-project-with-wikis/adding-or-editing-wiki-pages)).
Search engines index a wiki only once the repository has 500 stars and
public editing is closed. Above about 5,000 files, GitHub points to Pages
instead ([About wikis](https://docs.github.com/en/communities/documenting-your-project-with-wikis/about-wikis)).
GitHub's documentation does not mention a pull request flow for wikis. In
practice, wiki edits are not reviewed and CI cannot check them.

**A docs directory plus a generated site keeps documentation under the same
gates as code.** mdBook builds a searchable book from Markdown, is written in
Rust, and can test Rust code samples
([mdBook](https://rust-lang.github.io/mdBook/)). MkDocs is the Python
equivalent.
- *For estate-kit:* keep everything in `docs/` and check it with the link
  gate deploy-kit already has. If a site is wanted, mdBook adds no new
  toolchain to a Rust repository. Agents read the Markdown directly, so the
  site is for people only.

## 2. Gap analysis

The status is judged against the files listed at the top and the settled
choices. "Covered" means a settled choice or an existing artifact meets the
item. "Partly" means part of it is met, and the column says what is missing.

| # | Guidance item | Status | Evidence, and what is missing |
|---|---|---|---|
| 1 | Lock what is expensive to change and not inferable: boundaries, contracts, data, invariants, conventions | Partly | Boundaries (one crate per step, ports), contracts (committed JSON Schemas, `result.json`) and where data lives are settled. Cross-cutting conventions are not written down. |
| 2 | C4 levels 1 and 2 | Partly | The `context` and `components` diagrams exist. `context` omits GitHub, Vault, auth-api, Postgres and the people. `components` labels no protocols. |
| 3 | Domain model and glossary | Covered | `CONTEXT.md` with "Avoid" terms, and the `mm-*` metamodel diagrams. |
| 4 | State machines | Covered | `state-project`, `state-rollout`, `state-host-applier`, `state-mailbox`. |
| 5 | Sequences that include failure paths | Partly | Eleven sequences, but only `seq-deploy-2-dryrun` has an `alt` frame (rejected). Missing: an OIDC refusal, an expired rollout token, Vault or ghcr unavailable, a service restart mid-rollout, a host switch that fails health. |
| 6 | Data flow and trust boundaries | Partly | The `inputs-*` diagrams show data flow. There is no trust-boundary diagram and no threat model. |
| 7 | Deployment | Covered | `deploy-placement`, `deploy-in-cluster`, `deploy-hosts`. |
| 8 | Contracts as executable sources of truth | Partly | Covered for the compiler (schemas plus a drift test). The service's HTTP and SSE API has no committed contract. |
| 9 | Golden examples in Given, When, Then | Partly | Oracle files at the four seams are golden examples. They are not laid out as scenarios, and delivery and the dashboard have none. |
| 10 | One error model (RFC 9457) and an error-code catalogue | Partly | The compiler's diagnostic model (code, file, model path) and the "a code only for real harm, with a fixture" rule are settled. No error model for the service's HTTP API, and no single catalogue shared by Rust and Go. |
| 11a | Idempotency | Missing | Coalescing triggers and the render key give some of it. A retried deploy or tag move has no stated semantics. |
| 11b | Pagination | Missing | No list endpoints are specified. |
| 11c | Concurrency | Covered | One composition at a time, one service replica, a Lease for hosts. Optimistic writes to the Project object are implied, not stated. |
| 11d | Ordering | Partly | Per-rollout sequence numbers and the derived host order are settled. Cross-rollout ordering is not stated. |
| 11e | Delivery | Partly | The stream resumes from a sequence number. At-least-once delivery and reader deduplication are not stated. |
| 12 | Data primitives: ids, timestamps, nullability | Missing | The event table names its columns, but no id format, time format or null policy. |
| 13 | Authorization matrix | Partly | Identity and access lists callers, tokens and three UI roles. Missing: a full caller-by-action matrix and a test per cell. |
| 14 | Data lifecycle and migration policy | Missing | Not stated: event-log retention, garbage collection of renders and fragments in ghcr, Postgres schema migrations, and migrating authored YAML across schema majors. |
| 15 | NFRs as numbers | Partly | Gate budgets are numeric (under 2 minutes, mutation under 5 minutes). No runtime SLOs for the service, the compiler or host rollouts. |
| 16 | Observability conventions | Missing | No tracing, log fields, metrics or correlation chain. |
| 17 | Configuration conventions | Partly | Platform Intent versus toolchain configuration is settled. Not stated: the service's own sources, precedence, validation at start-up, and secret handling. |
| 18 | ADRs settled first, across shape, data, communication, security, quality, operations and agent workflow | Partly | The 31 founding titles cover shape, data, communication, security (OIDC, signing) and quality (gates, oracles, fakes). Operations is thin (pause and rollback only), and agent workflow has no record. The records are titles, not yet written. |
| 19 | Locked versus Proposed status, each locked decision backed by a failing check | Partly | "Every rule has a ledger row and a failing fixture" carries over from deploy-kit, and Code shape and speed applies it. The register has no status field and no Confirmation link. |
| 20 | Agent-legible repository (AGENTS.md and the agent files) | Missing | estate-kit has no AGENTS.md, CLAUDE.md, skills or settings yet. |
| 21 | Re-implementation safety (characterization, an inert shadow) | Partly | Parity, shadow and staged switch are settled. Not stated: characterization oracles for the Go services, and the rule that the shadow has no side effects. |

**What is missing, in short:**

- **Cross-cutting semantics:** idempotency, pagination and the data
  primitives.
- **Data lifecycle and migrations.**
- **Observability conventions.**
- **Agent files** for the repository.
- **Security:** a threat model on a trust-boundary diagram, and an
  authorization matrix with tests.
- **Service API contract:** a contract for the HTTP API, and an RFC 9457
  error model tied to one shared catalogue.
- **Runtime NFRs.**
- **Failure-path sequences.**
- **ADR status rule:** a status field whose "accepted" requires a
  Confirmation.

## 3. A first decision set

The design's 31 founding records stay as titled, in their order. The new
records are slotted in where they belong in reading order, so that each rests
only on earlier numbers. "Settled" means the design or the settled choices
already decide it; "Open" means the maintainer has yet to decide. A record
marked "Settled, extended" is settled, but this note proposes adding the
named clause.

### Frame

| # | Record | Status |
|---|---|---|
| 1 | One maintainer, one cluster, one estate | Settled |
| 2 | Records are read in order, cite their lessons, and state only the decision in force | Settled, extended: statuses are `proposed` and `accepted`, and `accepted` needs a Confirmation |
| 3 | The repository is the documentation: `docs/` under review and gates, no wiki, diagrams generated from their declarations | Open (the design doc moves in tab by tab, but the end state is not recorded) |
| 4 | The agent contract: AGENTS.md as the one agent file, CONTEXT.md as the naming authority, what an agent may change freely and what needs a record | Open |
| 5 | Port at byte-identical parity, shadow-compose, staged switch, then rewrite | Settled, extended: the shadow is inert, and the Go services get characterization oracles first |

### Shape

| # | Record | Status |
|---|---|---|
| 6 | Kubernetes is the substrate, and Flux is the one applier | Settled |
| 7 | Three models: Intent, Resolved Deployment, Deliverable Set | Settled |
| 8 | Contention decides authority | Settled |
| 9 | Derivation is total | Settled |
| 10 | Every render is a function of pinned inputs | Settled |
| 11 | A Project's state lives with the Project | Settled |
| 12 | The compiler is one static Rust binary | Settled |
| 13 | The compiler is a chain of crates, one per step | Settled, extended: cargo-deny `wrappers` and a `cargo metadata` edge test enforce it |
| 14 | The service runs in the cluster, in Go: it composes, and Flux applies | Settled |
| 15 | The service is a rollout core behind ports, laid out as `cmd/` and `internal/` | Settled (Inside the service), extended: go-arch-lint enforces it |
| 16 | One model renders hosts too; a host applier per node pulls and switches under a Lease | Settled (Hosts; not yet among the founding titles) |
| 17 | Components live in the repository, and every part shares one version | Settled |

### Contracts and data

| # | Record | Status |
|---|---|---|
| 18 | The committed JSON Schemas are the contract | Settled, extended: authored-intent schemas are BACKWARD_TRANSITIVE within a major, and a gate diffs each schema against its last release |
| 19 | Rust types are hand-written and held to the committed schemas | Settled |
| 20 | The service runs the compiler as a subprocess over a directory and a result file | Settled |
| 21 | The service's HTTP and event API has a committed contract | Open: OpenAPI 3.1, or JSON Schemas per payload |
| 22 | Data primitives: ids, digests, timestamps, optional fields | Open (proposed: UUIDv7 rollout ids, RFC 3339 UTC, omitted rather than null) |
| 23 | An image's digest is sealed into the Intent Fragment | Settled |
| 24 | The live render is a signed registry tag per Project and environment | Settled |
| 25 | Platform Intent admits the Projects | Settled |
| 26 | The registry is the render cache | Settled |
| 27 | A rollout is an append-only event log | Settled, extended: event types are versioned, and old events are read through upcasters, never rewritten |
| 28 | Data lifecycle: event retention, garbage collection in ghcr, forward-only Postgres migrations, migrating authored YAML | Open |

### Communication semantics

| # | Record | Status |
|---|---|---|
| 29 | One composition runs at a time | Settled |
| 30 | Idempotency, ordering and delivery: deploys keyed by Project and fragment digest, compare-and-swap tag moves, at-least-once streams with deduplication by sequence | Open (the parts follow from settled choices; the rule itself is unwritten) |
| 31 | List endpoints are paginated from their first version, with opaque cursors | Open |
| 32 | A rollout is a deploy run that streams the service's work | Settled |

### Errors

| # | Record | Status |
|---|---|---|
| 33 | A diagnostic names a model path, and the caller resolves the line | Settled |
| 34 | One error-code catalogue for Rust and Go; a code only for harmful authored input, each with a firing fixture | Partly settled (the rule is settled; one shared file is open) |
| 35 | The service answers errors as RFC 9457 problem details, whose `type` is the catalogue code | Open |

### Security

| # | Record | Status |
|---|---|---|
| 36 | Every caller authenticates with an OIDC token | Settled |
| 37 | Authorization is a caller-by-action matrix, denied by default, with a test per cell | Open (the roles are settled; the matrix and its test are not) |
| 38 | Renders are signed through Vault Transit | Settled |
| 39 | A threat model: STRIDE over the trust-boundary diagram, revisited when an edge is added | Open |

### Quality

| # | Record | Status |
|---|---|---|
| 40 | A dry-run must pass before anything is applied | Settled |
| 41 | Images are built once and promoted, so what dry-ran is what deploys | Settled |
| 42 | Two implementations meet at the oracle files, laid out as given, when, then | Settled, extended by the layout |
| 43 | One concept per module, one fake per port, oracles only at the seams | Settled |
| 44 | Every enforced rule has an id, a ledger row and a failing fixture | Settled in deploy-kit ([0066](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/architecture/0066-every-enforced-rule-has-an-id-a-row-and-a-fixture.md)); needs restating here |
| 45 | Every gate has a speed budget; coverage and mutation are ratchets | Settled |
| 46 | Runtime NFRs: a few SLOs with numbers | Open |

### Operations

| # | Record | Status |
|---|---|---|
| 47 | Pause and Rollback are a cluster object per Project | Settled |
| 48 | The service runs as one replica and recovers from its log | Settled (Inside the service; not yet among the founding titles) |
| 49 | Observability: OTel semantic conventions, one correlation chain from the GitHub run to the trace, structured logs with three house attributes | Open |
| 50 | Configuration: the service's sources, precedence, validation at start-up, secrets only from Vault | Open |

### Open questions for the maintainer

1. **Status rule (2).** Is "accepted needs a Confirmation" acceptable? Two
   statuses only, with `deprecated` and `superseded` dropped?
2. **Agent contract (4).** One root AGENTS.md plus nested files under
   `compiler/` and `service/`? Which skills move over from deploy-kit (`adr`,
   `spec-change`, `gate-triage`, `new-rule`)?
3. **Shadow (5).** Should the shadow compose write to a separate tag prefix
   (for example `shadow/<p>`), or only compare digests in memory?
4. **API contract (21).** OpenAPI 3.1 for the service, or keep to JSON Schemas
   alone? The UI's TypeScript client would be generated from either.
5. **Data lifecycle (28).** How long are rollout events kept? Which renders
   and fragments may ghcr garbage-collect, given that a rollback needs old
   ones?
6. **RFC 9457 (35).** Is the service's API worth a formal error model, given
   that its only clients are the deploy job and the UI?
7. **SLOs (46).** Which two or three numbers would the maintainer act on? For
   example, deploy to moved tag at p95, and host rollout time per node.
8. **Observability (49).** Is there a trace backend in the cluster today
   (Tempo, Jaeger)? Without one, the record covers logs and metrics only.

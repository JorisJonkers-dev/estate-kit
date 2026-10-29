# Lesson candidates

Candidate lessons drawn from deploy-kit, its course reports and presentations, its research notes and its delivery incidents. The maintainer curates them; only Keep and Merge rows become `lessons.md`, which the decision records cite. The curation state below mirrors the lessons document as of 2026-10-22.

## Curation

| ID | Lesson | Decision |
| --- | --- | --- |
| MS-1 | One concept, one chapter, one module | Keep |
| MS-2 | The spec describes only built behaviour and grows only with code | Keep |
| MS-3 | A refusal code guards a real hazard at this scale, and something always exercises it | Keep |
| MS-4 | Authors state requirements, the compiler derives mechanism, and there is no override hatch | Keep |
| MS-5 | Measure model coverage against the live estate from the first month | Keep |
| MS-6 | Use closed enumerations for any finite set, never free strings | Keep |
| MS-7 | Hold every artefact to the scale premise, and park a second cluster behind a seam that costs nothing | Keep |
| MS-8 | The release unit and the ordering graph are different relations | Keep |
| MS-9 | Check a derived network policy at both ends of each edge | Keep |
| MS-10 | Placement sums requests per node instead of checking each Process alone | Keep |
| DR-1 | A claim a decision rests on is checked against a primary source or a drill first | Keep |
| DR-2 | An open claim gets a settling test with an owner and a date, or the decision is not accepted | Keep |
| DR-3 | Register hygiene: rewrite in place, fold records that change together, never reuse a number, allocate numbers at merge | Keep |
| DR-4 | The ADR justifies and the spec is normative, so records carry no field lists | Keep |
| CS-1 | The resolved model records every decision, including each file's path, and renderers only serialise | Keep |
| CS-2 | No abstraction without two implementations, the architecture doc checked against the module graph, one typed input per stage | Keep |
| CS-3 | Abort, never default; check authored input before the transformation; report every error with its location | Keep |
| CS-4 | Lower shared declarations in a step of their own, before resolution | Keep |
| CS-5 | Determinism: only pinned, digested inputs, and a double render compared byte for byte | Keep |
| CS-6 | Each command validates every input it carries | Keep |
| TM-1 | Oracles are written before the run, reviewed by hand, never written by a test or CI, and labelled as independent or regression | Keep |
| TM-2 | Diff the parsed structure before comparing bytes or digests | Keep |
| TM-3 | Four seams carry the suite, and no fifth is added | Keep |
| TM-4 | Every gate has a negative fixture, and a new gate needs a real incident behind it | Keep |
| TM-5 | Mutation testing at a 100 break score, run on the changed code on main and on everything weekly | Keep |
| TM-6 | Hold rendered output to the target's own schemas and policies in-process, then dry-run against a real API server | Keep |
| DO-1 | A Project owns every object it delivers, with nothing shared at estate scope unless it cannot be avoided | Keep |
| DO-2 | Every object kind the compiler emits has a stated lifecycle on the substrate | Keep |
| DO-3 | Only required edges create apply order | Keep |
| DO-4 | A handover is proved by a value a consumer reads, after a one-off diff, and finished in one change | Keep |
| DO-5 | Prove the old applier can be removed without deleting what the new one takes over | Keep |
| DO-6 | One composition run covers all inputs and refuses to publish if an input moved during the run | Keep |
| DO-7 | When a platform dependency fails, the service degrades rather than wedges | Drop |
| PR-1 | Durable state lives in the tracker and the repository, never in transcripts or untracked files | Keep |
| PR-2 | Shorten the propagation chain: a model change should not cross five repositories | Keep |
| PR-3 | Map the decisions before the rewrite, then follow one ordered plan with move-only steps first and one contract release | Keep |
| PR-4 | Parallel agent sessions need explicit ownership and a list of what not to touch | Keep |
| PR-5 | Flag operator-only steps up front | Drop |
| MD-1 | Two implementations held to shared oracles found spec gaps, at twice the cost | Keep |
| MD-2 | Define the typed model first and derive the syntax from it | Keep |
| MD-3 | Keep a trace from every output back to the authored element that caused it | Keep |
| MD-4 | Pick an implementation language whose test tooling reaches the transformation code | Keep |
| MD-5 | Run the whole toolchain headless before modelling (a walking skeleton) | Keep |
| MD-6 | Keep an external deadline's work off the production critical path | Drop |
| MD-7 | Track leverage as a headline metric | Drop |

## The candidates in full

These are raw candidates for the maintainer to curate. Nothing here is decided.
They were drafted on 2026-10-22 from read-only sources. Paths are relative to
`~/IDEAProjects/JorisJonkers-dev/` unless they start with `#`, which means an
issue or PR in JorisJonkers-dev/deploy-kit, or name another repository.

Abbreviations used in the Evidence lines:

- **#373**: the rewrite plan, JorisJonkers-dev/deploy-kit#373, and its Problem
  Statement.
- **UC**: `deploy-kit/docs/research/unsupported-claims.md`, whose claims are
  numbered C1 to C49.
- **CS**: `deploy-kit/CONTINUATION-SPEC.md`.
- **EOW**: `deploy-kit/ESTATE-OWNERSHIP-WORKFLOW.md`.
- **WS**: `workspace/SPEC-remaining-work.md`.
- **T0, T1, T2**: the Task 0, 1 and 2 reports, under `deploy-kit/docs/mde/task-*/Sections/`.
- **P2**: `mde-presentation-2/slides.md`.

There are 45 candidates. Where two said the same thing they have already been
merged, and the evidence of both is kept. A few are proposed for dropping and
are left in so the maintainer can see why.

---

## Top 10, ranked

1. **DR-1**: Verify every claim a decision rests on, about a third-party tool or the live estate, against a primary source or a drill before the decision is accepted.
2. **MS-2**: The spec describes only built behaviour. A chapter lands together with its code, examples, oracles and schemas.
3. **MS-1**: One concept, one chapter, one compiler module.
4. **MS-3**: A refusal code exists only for a real hazard in authored input, and only once a negative fixture fires it.
5. **DO-1**: A Project renders, publishes and applies every object it delivers from its own unit. Nothing is shared at estate scope unless it cannot be avoided.
6. **CS-1**: The resolved model records every decision, including file paths. Renderers only print.
7. **TM-1**: Oracles are written before the first run, reviewed by hand, never written by a test or CI, and labelled as independent or regression.
8. **DR-2**: An open claim gets a settling test with an owner and a date. Otherwise the decision is not accepted.
9. **DO-2**: Every object kind the compiler emits has a stated lifecycle on the substrate: how it is replaced, when it is healthy, and how it retries.
10. **MD-1**: Two implementations held to shared oracles found real spec gaps. Get that independent second reading cheaply, not by building a second implementation.

Close runners-up: **MS-5** (render the live estate and diff it from the start),
**PR-2** (a model change crossed five repositories on its way to production) and
**CS-3** (abort, never default, and report every error with its location).

---

## Model and spec

### MS-1. One concept, one chapter, one module
- **Lesson**: Each model concept lives in one spec chapter, covering its authored fields, its Platform fields, its derivation, its render and its refusals. In the compiler, each stage gives it exactly one module.
- **Evidence**: #373 Problem Statement: "One concept is spread over four chapters and over 7 to 21 compiler modules, so every change touches all of them." #373 Step 4: "the six modules that carry five or six concepts are split". #373 Step 2 sets out the new layout: a pipeline frame plus 7 concept chapters.
- **Applies to estate-kit as**: the spec is laid out as frame chapters plus concept chapters from the start, and the compiler gives each concept one module per stage. A chapter PR edits one chapter and at most one module per stage (#373 story 7).
- **Proposed**: keep. This is the structural root of the cost #373 measured.

### MS-2. The spec describes only built behaviour and grows only with code
- **Lesson**: A spec chapter lands in the same PR as its code, its worked examples, its oracle files and its schemas. Behaviour that is not built gets no normative text, only a pending code that names a ticket.
- **Evidence**: #373 Problem Statement: the spec "grew one decision at a time, to 10,489 lines over 11 chapters"; "a quarter of the sections are linked from nowhere"; "several chapters describe behaviour no code has". `spec/v1` is 11,958 lines today (`wc -l deploy-kit/spec/v1/*.md`). #373 Step 6 makes "never describes unbuilt behaviour" the rule for every chapter PR.
- **Applies to estate-kit as**: spec and process. A gate checks that every normative section is cited by at least one test or example, and fails on a section nothing links to.
- **Proposed**: keep.

### MS-3. A refusal code guards a real hazard at this scale, and something always exercises it
- **Lesson**: A diagnostic code exists only for authored input that would do real harm on this estate, and it ships with a negative fixture that fires it. The compiler's own invariants are tests or internal assertions, not user-facing codes.
- **Evidence**: #373: "42 of 108 refusal codes were never exercised"; "four refusals fire on shapes that run fine today". #373 Step 7 turns seven compiler self-invariants into tests and folds two duplicate codes. UC C33 (line 118): `E_PRIVILEGED_PORT_UNDER_NONROOT` guards against a hazard that does not exist on k3s (`enable_unprivileged_ports`), yet the decision would have had four Applications rebuild their images.
- **Applies to estate-kit as**: compiler. The Rust error type splits authored-input diagnostics (stable codes, each listed with a fixture) from internal bugs (`panic!` or `unreachable!`, covered by a test). A `lint:codes` equivalent exists from the first commit.
- **Proposed**: keep.

### MS-4. Authors state requirements, the compiler derives mechanism, and there is no override hatch
- **Lesson**: Authors state what only they can know: a startup budget, whether an upgrade may interrupt service, writable paths, what a volume's data is worth. They never write a target mechanism. No derived value can be overridden per object. Target field names appear only in the adapter that emits them, and an authored concept never shares a name with its rendered form.
- **Evidence**:
  - T1 `03-modelling-decisions.tex`, §"Derived Values Cannot Be Overridden" and §"Requirements Instead of Target Fields". T1 `04-alternatives.tex`, table rows "An override mechanism" ("Per-process exceptions would conceal an incorrect general rule") and "Annotate the target files" ("authored and resolved forms the same name. Errors could not identify which form was wrong").
  - `deploy-kit/docs/adr/model/0005-derivation-is-total.md` §Why: four live Deployments carried an identical hand-tuned rollout block, the same derivation done by hand four times. Its Consequences add that a wrong rule now mis-tunes every Application at once.
  - EOW §3 decision 9: "the maintainer rejects authored mechanism".
- **Applies to estate-kit as**: the spec vocabulary, a review checklist item for every new field, and type naming in the compiler and `CONTEXT.md`.
- **Proposed**: keep.

### MS-5. Measure model coverage against the live estate from the first month
- **Lesson**: Render the whole live estate and diff it against what runs, early and on a schedule. Only that diff settles the premise that derivation covers the estate. Argument does not.
- **Evidence**: `deploy-kit/docs/adr/model/0005-derivation-is-total.md` premise: "Settled by: rendering the whole estate and diffing against the live manifests". The record also says the premise is "currently false as built", and its claim is still `open`. #373: deploy-kit "renders three things on the estate path"; "ten needs of live Applications have no model concept"; "every live object is still hand-written in fleet-infra".
- **Applies to estate-kit as**: process and testing. An early deliverable is a coverage report listing live objects that no concept produces, ready before most of the spec is written.
- **Proposed**: keep. It is close to DR-2 but concrete enough to stand on its own.

### MS-6. Use closed enumerations for any finite set, never free strings
- **Lesson**: Every value from a fixed set is an enumeration, so a constraint can cover every literal.
- **Evidence**: T1 `04-alternatives.tex`, row "Free-form strings instead of enumerations": "The existing free-form field was wrong in every application."
- **Applies to estate-kit as**: compiler. Rust enums with `deny_unknown_fields`, plus closed registries for adapters and Node Agents (#373, chapters 14 and 30).
- **Proposed**: keep. The evidence is cheap and strong.

### MS-7. Hold every artefact to the scale premise, and park a second cluster behind a seam that costs nothing
- **Lesson**: A concept, check or ledger stays only if it catches a maintainer mistake on the real estate: one maintainer, one cluster, about 30 Applications. A job done once is handled by a one-off tool, not by a permanent model rule. Do not design for a second cluster or tenant. Make the single cluster explicit instead, so an input that names another cluster is refused and a later extension stays possible.
- **Evidence**:
  - #373 "What stays fixed": "an artefact that catches no maintainer mistake on the estate path goes" (`deploy-kit/docs/adr/model/0001-estate-scale-and-ownership.md`).
  - #373 Step 7 cuts the reconciliation ledgers, `alertClass`, the soft placement preferences, the per-cluster env overlay and the term Cluster Target. Story 18 replaces the ledgers with "a one-off diff at each handover".
  - `deploy-kit/docs/adr/deferred/0097-multi-cluster-and-multi-tenancy-are-parked.md`. #373 chapter 15: "The Cluster is one named instance". T2 `01-purpose.tex`, §"More Than One Cluster".
- **Applies to estate-kit as**: spec and ADR process. The ADR for a new concept names the maintainer mistake that concept prevents.
- **Proposed**: keep.

### MS-8. The release unit and the ordering graph are different relations
- **Lesson**: What is released together (the Application) is a separate relation from what must be applied first (the dependency graph). Deriving one from the other merges everything into one unit.
- **Evidence**: T1 `03-modelling-decisions.tex`, lines 58 to 62: "Using that graph for release grouping joined all applications into one unit through transitive dependencies." `deploy-kit/docs/adr/model/0052-an-application-is-the-release-unit.md`.
- **Applies to estate-kit as**: spec, and the ordering logic in the Go service.
- **Proposed**: keep. DO-3 could be folded into it.

### MS-9. Check a derived network policy at both ends of each edge
- **Lesson**: A compiler invariant checks that every egress the policy allows has a matching ingress allow. A policy that is rendered but never enforced hides gaps.
- **Evidence**: T2 `04-evaluation.tex`, §"Gaps in the Evidence": the Secret Store's policy allowed no inbound traffic while its consumers were allowed to send to it. It was found only when the `secrets` output was reviewed (#440). Because of `deploy-kit/docs/adr/model/0035-network-policy-is-default-deny-and-render-only.md`, the live cluster never exposed the gap.
- **Applies to estate-kit as**: a compiler invariant test. A render-only stage still runs the same checks.
- **Proposed**: keep, or merge into TM-4 as an example of an internal invariant.

### MS-10. Placement sums requests per node instead of checking each Process alone
- **Lesson**: If eligibility is checked one Process at a time, the check accepts placements whose combined requests exceed the node.
- **Evidence**: T1 `03-modelling-decisions.tex`, §"Shared Values Are Set by the Platform" ("cannot detect aggregate overcommit"). T2 `04-evaluation.tex`, §Limitations. P2, Appendix F ("Per-Process placement").
- **Applies to estate-kit as**: compiler, in the placement derivation.
- **Proposed**: keep if estate-kit keeps derived placement. Otherwise drop it as a known limit of the model.

---

## Decision records

### DR-1. A claim a decision rests on is checked against a primary source or a drill first
- **Lesson**: Before an ADR is accepted, every claim in its `rests-on` about a third-party tool or the live estate cites a primary source: the documentation or source at the version that runs, or the live object. Where no source can settle a claim (rotation under a connected client, a rollout under anti-affinity, a failover gap), a drill in a throwaway namespace settles it before the chapter that depends on it is written. Each claim records a verdict: holds, holds with a condition, fails, or unverified.
- **Evidence**:
  - UC checked 49 claims behind the map's settled decisions. Six failed: C4 (line 64, the wildcard has a second consumer), C8 (line 73, no live RabbitMQ dynamic credential exists), C17 (line 87, MetalLB cannot serve the Frankfurt node), C28 (line 108, Alloy is not host-privileged), C33 (line 118, low ports on k3s) and C43 (line 133, a dashboard without a `uid`). About 18 more hold only under a condition the decision never stated, for example C2 (Traefik ACME allows one replica) and C21 (`across: node` stalls a rollout that surges).
  - #373: "six of the claims the newest decisions rested on turned out to be false". #366 had to decide what each settled decision does about its failed claim.
  - For the drills: the #373 section "Conditions that gate a step" (#369, #371, #372), and story 64. UC's "Settle by drill" table. UC notes C7 to C9 (lines 210 to 242): the RabbitMQ dynamic credential had already been dropped live after Vault revoked the user under a running pod, yet a decision adopted it again. The mesh direction ([deploy-kit 0112](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/model/0112-east-west-traffic-is-mutually-authenticated-by-an-ambient-mesh.md)) ran lab drills in stage 1 before any cluster change (CS stories 42 to 55).
- **Applies to estate-kit as**: ADR process. The ADR lint requires every premise claim to carry a source link or a drill ticket. A `drill` issue template exists. `docs/research/` stays evidence, never decision.
- **Proposed**: keep.

### DR-2. An open claim gets a settling test with an owner and a date, or the decision is not accepted
- **Lesson**: The "False if / Settled by" format only pays off if the settling test is scheduled. A premise left open indefinitely is a foundation nobody has tested.
- **Evidence**: of the frontmatter `claim:` values in `deploy-kit/docs/adr/**`, 58 read `open` and 39 read `settled`. Examples:
  - 0002: "Settled by: two observations, both still to be run".
  - 0042: "a test … to be written".
  - 0056: "Settled by: the first rewrite slice rendering `minimal` end to end", still open.
  - 0005 calls its own premise "currently false as built".
- **Applies to estate-kit as**: ADR process. `lint:adrs` refuses `claim: open` without a linked issue, and a periodic report lists open claims by age.
- **Proposed**: keep.

### DR-3. Register hygiene: rewrite in place, fold records that change together, never reuse a number, allocate numbers at merge
- **Lesson**: A changed decision is rewritten in its one record. Two records that would always change together are one record. A retired number is listed once and never reused. With parallel work, the number is fixed when the PR merges, not when the branch is cut.
- **Evidence**:
  - `deploy-kit/docs/adr/README.md`, lines 9 to 12: the register was rebuilt on 2026-09-29 by merging 141 records, "many of them reversed by dated notes", into 82.
  - #373 Step 3 adds a Retired-numbers table and three folds (0041 into 0092, 0029 into 0028, 0051 and 0083 into 0047). Step 7 adds another (0044 into 0032).
  - CS line 202: [deploy-kit 0114](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/model/0114-every-images-lock-entry-records-its-version.md) "was 0113 until #539 took that number". WS P3, "ADR numbers".
- **Applies to estate-kit as**: ADR process and lint. A retired-numbers table, a gap check, and a number taken at merge (or a reservation file). A soft budget on how many records exist.
- **Proposed**: keep.

### DR-4. The ADR justifies and the spec is normative, so records carry no field lists
- **Lesson**: An ADR carries the why, the alternatives and the premises. Field lists, error codes and YAML live only in the chapter its `normative:` pointer names. Where the two disagree, the spec wins.
- **Evidence**: `deploy-kit/AGENTS.md`, §"What this repository is". `deploy-kit/docs/adr/README.md`, lines 14 to 21. It held up: it is why the move-only spec PR (#373 Step 2) could be proved by the link and ADR gates alone.
- **Applies to estate-kit as**: the founding rule of the new ADR set.
- **Proposed**: keep, as a positive lesson. It is not novel, but it is cheap to state.

---

## Compiler structure

### CS-1. The resolved model records every decision, including each file's path, and renderers only serialise
- **Lesson**: Every derived value exists in a typed intermediate model you can inspect before any text is generated, and that includes the path of each output file and the Project that owns it. A renderer makes no decisions. A check verifies who owns each directory, not only that paths are unique.
- **Evidence**:
  - T1 `03-modelling-decisions.tex`, §"What Each Stage May Contain": "An earlier two-stage design let the generator compute values internally. It produced three incompatible documents with one version identifier."
  - T2 `01-purpose.tex`: "template tests cannot pass while a template makes an unchecked deployment decision". P2 line 650: "Templates stayed simple: every template fix came from a model change".
  - T2 `04-evaluation.tex`, §"Defects Found": estate-wide route files were planned under `apps/edge/`, inside one Project's directory, and duplicate-path checks could not see it. `deploy-kit/docs/adr/model/0036-path-authority-is-layer-2.md`.
- **Applies to estate-kit as**: the compiler's core pipeline (read, lower, resolve, render through adapters), plus a test that every Deliverable's directory belongs to its owner.
- **Proposed**: keep.

### CS-2. No abstraction without two implementations, the architecture doc checked against the module graph, one typed input per stage
- **Lesson**:
  - Do not declare a port, trait or registry slot that nothing implements.
  - Check the architecture document mechanically against the real dependency graph.
  - Give each stage one typed input. Never dispatch on an untyped value or reach for a global instance search.
- **Evidence**:
  - #373 Step 4: "the four ports it names and nothing declares leave it, and no port is added until a second implementation exists". Story 62: "so that the two cannot disagree again".
  - `deploy-kit/docs/adr/model/0037-six-registered-adapters-satisfy-one-port.md`, lines 43 to 48: the old registry typed render as `(input: never)`, four adapters carried `@ts-nocheck`, and two "working renderers that were never registered turned out to consume a different model".
  - T2 `02-alternatives.tex`, §"Typed Extents": an unqualified `allInstances()` returned both the authored and the flattened Processes.
- **Applies to estate-kit as**: a Rust workspace whose crate graph is enforced, with the Layers table in the doc checked against it. Functions take `&Estate` and similar explicitly.
- **Proposed**: keep.

### CS-3. Abort, never default; check authored input before the transformation; report every error with its location
- **Lesson**: A value the compiler cannot derive fails the run. It never gets a default, whether written in code or implied by deserialisation. Authored input is validated before resolution, and all errors are reported at once, each with a code, a file and an object path.
- **Evidence**:
  - T2 `02-alternatives.tex`, §"Rejecting Unresolvable Inputs": a default "would give a file that looks valid and deploys the wrong configuration".
  - T2 `04-evaluation.tex`, §Limitations: checks moved into OCL because errors "had previously reached QVTo aborts", and the remaining aborts "stop at the first problem without a source location". P2 line 662 lists clearer error messages as a future improvement.
  - T1 `07-syntax-and-constraints.tex`, lines 25 to 27: each invariant is named by its code, and its context is the object to fix. Lines 62 to 64: EMF read an unset enumeration as its first literal and needed an `absent` literal. That is EMF trivia, but it is the same no-implicit-default trap.
- **Applies to estate-kit as**: compiler diagnostics. Errors are collected with source spans (for example a `miette`-style report), validation is kept separate from resolution, and model types whose absence matters get no `Default`.
- **Proposed**: keep.

### CS-4. Lower shared declarations in a step of their own, before resolution
- **Lesson**: One lowering step settles declaration precedence (Project, then Application, then Process). The resolution rules then read one effective value and never walk up through ancestors.
- **Evidence**: T2 `02-alternatives.tex`, §"Flattening Before the Resolution". The reflection in T2 `04-evaluation.tex`: "Flattening made resolution rules simpler … This separation makes the extra model worthwhile." `deploy-kit/docs/adr/model/0012-shared-intent-descends-and-is-lowered.md`. The cost was an extra model and its own tests.
- **Applies to estate-kit as**: the compiler's `lower` stage.
- **Proposed**: keep, as a positive lesson that held.

### CS-5. Determinism: only pinned, digested inputs, and a double render compared byte for byte
- **Lesson**: The compiler reads only a closed set of pinned inputs. It never reads the live cluster or secret values, and the same inputs give byte-identical output.
- **Evidence**: T0 `02-solution.tex`. `deploy-kit/docs/adr/model/0006-pinned-inputs.md`. #373 Testing Decisions: "double render and schema validation beside it". The ClusterState snapshot is the one route by which live facts get in (T2 `01-purpose.tex`, §Assumptions).
- **Applies to estate-kit as**: the compiler is pure. The Go service captures snapshots and publishes them as pinned inputs.
- **Proposed**: keep. It is foundational and it held.

### CS-6. Each command validates every input it carries
- **Lesson**: Every CLI subcommand (validate, publish, compose) validates every document it reads or packs, not only the one it is about.
- **Evidence**: WS line 72: "neither `deploy-kit validate` nor `publish` reads the platform's images lock. Both accepted a renamed field and a numeric `version` … Only composition would notice." WS line 100: overleaf 1.1.0's publish failed late, with `"version" is not a field of the model`.
- **Applies to estate-kit as**: the compiler CLI.
- **Proposed**: keep. It is concrete and cheap.

---

## Testing and mutation

### TM-1. Oracles are written before the run, reviewed by hand, never written by a test or CI, and labelled as independent or regression
- **Lesson**: An expected output written by looking at the tool's own output is a regression snapshot, not evidence. Write expected results before the first run and say which oracles are independent. Make it physically impossible for test code to overwrite an oracle.
- **Evidence**:
  - T2 `04-evaluation.tex`, §Reflection: "Evidence should have been planned alongside the examples … Those runs established execution, not correctness." The `secrets` model is "a regression check, not an independent one" (P2, Appendix F).
  - P2 line 655: "Some expected example files had errors of their own, which were not found in time."
  - CS lines 209 to 211: a test overwrote `minimal`'s rendered `workload.yaml` and `canary.yaml` twice during a run that was writing oracle candidates.
  - #373 story 60. `deploy-kit/docs/adr/architecture/0088-the-committed-schemas-and-their-corpus-are-the-contract.md`.
- **Applies to estate-kit as**: testing. Oracle directories are read-only to `cargo test`, updates go through a separate explicit tool, and each oracle file records its provenance.
- **Proposed**: keep.

### TM-2. Diff the parsed structure before comparing bytes or digests
- **Lesson**: A failed comparison names the value that differs. Compare the canonical structure first, then the bytes, and only then any digest over them.
- **Evidence**:
  - T2 `04-evaluation.tex`, §Reflection: rebuilding the canonical JSON for the Revision digest took "about one sixth of resolution.qvto", and "a hash mismatch could mean either a wrong deployment decision or a wrong JSON representation, with no indication of where".
  - P2 line 660 lists diffing the parsed output as a future improvement.
  - CS line 206: rebases were reviewed with a semantic JSON diff.
  - EOW §7: "byte checks should come after a parsed JSON/YAML diff".
- **Applies to estate-kit as**: the test harness, with a structural YAML/JSON diff ahead of the byte diff.
- **Proposed**: keep.

### TM-3. Four seams carry the suite, and no fifth is added
- **Lesson**: Tests sit only at published boundaries: the use-cases (pinned inputs in, result out), the adapter port, the rendered tree and the CLI. No test reaches into a derivation's internals.
- **Evidence**: #373 Testing Decisions. `deploy-kit/docs/architecture.md#testing`. Prior art listed in CS §Testing Decisions (#534, #536, #538, #530).
- **Applies to estate-kit as**: Rust integration tests at each seam, plus the Go service's own seam (the Release Gate's answer against a fake cluster, as `MayStart` is tested today).
- **Proposed**: keep.

### TM-4. Every gate has a negative fixture, and a new gate needs a real incident behind it
- **Lesson**: A gate that has only ever passed is untested. A gate is added only when a real incident or defect justifies it, so the number of gates does not grow on its own.
- **Evidence**: `deploy-kit/AGENTS.md`, §"Testing strategy". `deploy-kit/docs/architecture-rules.md` holds 75 rules, 2 of them pending. #373 story 63: "a new repository gate only with a real incident behind it".
- **Applies to estate-kit as**: testing and process. A rule ledger (id, enforcer, failing fixture) that starts small.
- **Proposed**: keep. The "incident first" half is the new part.

### TM-5. Mutation testing at a 100 break score, run on the changed code on main and on everything weekly
- **Lesson**: Mutation testing found weak tests that coverage did not. Keep the bar, but run only the changed code, on main after a merge rather than on a PR, where a full run cost 9 to 18 minutes. Pin whole rendered objects rather than single fields. Treat an equivalent mutant as a sign the code should be rewritten.
- **Evidence**:
  - WS line 121: #423's first push left 108 survivors. Then "every rendered object is now pinned whole, and Stryker kills all 204 mutants".
  - EOW progress log: #561 had 5 survivors, and #564 had 3 more.
  - CS line 385: touching a test file surfaces survivors in modules nobody edited, and #536 swapped `find` for `filter` to remove an equivalent mutant.
  - #373 story 61 and #368: a full run took 9 to 18 minutes per PR.
  - The coverage ratchet is `deploy-kit/docs/adr/architecture/0063-coverage-and-mutation-are-ratchets.md`.
- **Applies to estate-kit as**: `cargo-mutants --in-diff` on each push to main, never on a pull request, and a full weekly run, with the coverage ratchet.
- **Proposed**: keep.

### TM-6. Hold rendered output to the target's own schemas and policies in-process, then dry-run against a real API server
- **Lesson**: Every rendered object is validated in-process against pinned Kubernetes and CRD schemas and the `restricted` Pod Security profile, so the check runs everywhere. A server-side dry-run comes next. Never maintain a hand-written copy of the target schema.
- **Evidence**:
  - #530 (RULE-076): `lint:manifests` holds every pod template to `restricted`. It was added after #294 and #524 found `allowPrivilegeEscalation` missing live.
  - #259: "Resolved placement is rendered nowhere: no Deployment carries a node affinity". A derived value never reached the render.
  - P2 line 661 lists a dry-run on a real cluster as a future improvement.
  - T1 `04-alternatives.tex`, §"A Third Metamodel for the Generated Files": "a maintained copy of the target schema could drift".
- **Applies to estate-kit as**: adapters emit upstream types (for example `k8s-openapi`). One gate validates against pinned CRD schemas, and a CI job dry-runs on k3s or kind.
- **Proposed**: keep.

---

## Delivery and operations

### DO-1. A Project owns every object it delivers, with nothing shared at estate scope unless it cannot be avoided
- **Lesson**: Every object a Project needs is rendered into, published with and applied by that Project's own unit: the Vault policies and roles, the generated keys, routes, rollout events, the database catalog and network policy. Projects reference each other only by name. A change to one Project re-renders and redeploys only that Project.
- **Evidence**:
  - EOW §1, and §3 decisions 1 to 8.
  - P2 line 656: "One shared Vault Job. When it failed, every project stalled" (#454, #461, #472, #529).
  - CS lines 123 to 129: the 0.26.1 roll stalled `estate-vso-secrets`, the shared unit every Project depended on.
  - T2 §Reflection: resolving one Project at a time "did not remove the need to reason about the estate". The final pass, `estate.qvto`, coupled Projects again and was removed in #547.
  - #552: until providers admitted consumers by selector, a consumer adding a new edge moved the provider's pin.
- **Applies to estate-kit as**: delivery and compiler. Output is per Project, with no estate pass. A two-Project test proves nothing else moves (EOW decision 8, #546, #552). A provider that drops a Surface a consumer still names is isolated at composition (#559).
- **Proposed**: keep.

### DO-2. Every object kind the compiler emits has a stated lifecycle on the substrate
- **Lesson**: For each kind the compiler emits, the spec says how it is replaced when the render changes (including immutable fields), when it counts as healthy, and how it retries. Without that, a change to the compiler alone can wedge a unit.
- **Evidence**:
  - #529: one-shot Jobs got a new pod template under the same name, and a Job's template is immutable (CS lines 123 to 129; fixed with the force annotation).
  - #454: an image bump could not apply, because the Job's name ignored its image.
  - #472: an estate Job "fails for good on one slow start, and wedges every estate-path Project".
  - #461 (still open): a failed Job stays failed until its name changes.
  - #485: a fresh Project's backup claim kept its unit unhealthy until the first nightly backup.
  - estate-dashboard#81 (WS P5): finished Job pods counted as not ready.
- **Applies to estate-kit as**: a spec frame chapter on object lifecycle, with tests for each kind in both the compiler and the Go service.
- **Proposed**: keep.

### DO-3. Only required edges create apply order
- **Lesson**: An optional dependency yields a network allow but never an apply order, so two Projects with optional edges to each other cannot deadlock.
- **Evidence**: #537 and #538. CS lines 140 to 142 and 237 to 243: `apps-arr` and `apps-prowlarr` waited on each other until 0.27.1. Optional edges are now exempt from `E_DEPENDENCY_CYCLE`.
- **Applies to estate-kit as**: spec (dependencies), and the ordering logic in the compiler and the Go service.
- **Proposed**: keep, or merge into MS-8 as "ordering is a relation of its own".

### DO-4. A handover is proved by a value a consumer reads, after a one-off diff, and finished in one change
- **Lesson**: Before switching a Project over, diff its render against the hand-written objects and explain every difference. It is done only when a value a consumer reads checks out, and then one change flips the ledger and deletes the old objects. An exit code, a `Ready` condition or an accepted object is never the evidence.
- **Evidence**:
  - #373 Step 8, "Done means", and stories 52 to 54.
  - WS line 381: "Verify values, not commands". CS §Testing Decisions. WS §Traps: "A `set -e` read-back script exits on an expected NotFound; read the output, not the exit code".
  - UC C32: the priority-class rule as decided does not reproduce what runs, and only the diff would show that.
- **Applies to estate-kit as**: delivery. A `diff` command in the compiler or the service, and a handover runbook.
- **Proposed**: keep. The "verify the value" rule is already in the estate-wide contract, so `lessons.md` can link to it rather than restate it.

### DO-5. Prove the old applier can be removed without deleting what the new one takes over
- **Lesson**: Before responsibility moves from one applier to another (Helm to the render, or a shared unit to per-Project units), prove that removing the old applier leaves the objects in place.
- **Evidence**: UC C48 and C49 (lines 143 to 144, and notes at lines 458 to 481): deleting a HelmRelease uninstalls the chart. A chart that templates its CRDs then deletes them, and every object of their kind with them (MetalLB's pool included), unless the release is suspended first. #373 story 55.
- **Applies to estate-kit as**: the delivery runbook, and a check in the handover tool.
- **Proposed**: keep. It generalises beyond Helm.

### DO-6. One composition run covers all inputs and refuses to publish if an input moved during the run
- **Lesson**: One delivery run composes all of `main`, and it refuses to push its pin if its inputs changed during the run. A later run supersedes an earlier one.
- **Evidence**: CS lines 232 to 236: a run failed with "main moved under this composition". That was the guard working, and the next run composed everything. CS line 92: the cancelled deliveries were by design, since only one run per concurrency group stays pending.
- **Applies to estate-kit as**: the Go service's composition loop, using optimistic concurrency on the input set.
- **Proposed**: keep, as a positive lesson. Drop it if the service design makes it obvious.

### DO-7. When a platform dependency fails, the service degrades rather than wedges
- **Lesson**: Where estate-kit's service depends on the Secret Store or on a single node, it fails visibly and recovers without anyone deleting Jobs by hand.
- **Evidence**: CS story 6: a Frankfurt restart sealed Vault and took down every app with a database (2026-10-18). WS P3: pi-1's containerd stalled, and all four delivery Processes hung on that node.
- **Applies to estate-kit as**: placement and failure handling in the Go service.
- **Proposed**: drop. The evidence is about infrastructure (auto-unseal, node health) rather than estate-kit's design. Keep it only if the service's own high availability is in scope.

---

## Process and agents

### PR-1. Durable state lives in the tracker and the repository, never in transcripts or untracked files
- **Lesson**: Work in flight, decisions and their evidence go into issues, PRs and committed docs. An untracked continuation spec is a stopgap that goes stale within hours, and live state always beats it.
- **Evidence**:
  - CS lines 63 to 65: "The state of this work lived only in very large transcripts and short-lived scratch directories. A new session would have to rebuild it, and could act on stale claims."
  - WS Problem Statement: "fresh sessions that rebuild state from stale checkouts".
  - WS line 567: "A detached merge script dies with the session that started it."
  - Both CS and EOW are untracked by design.
- **Applies to estate-kit as**: process. A handoff is an issue comment, not a local file.
- **Proposed**: keep.

### PR-2. Shorten the propagation chain: a model change should not cross five repositories
- **Lesson**: A model change reached production only after passing through deploy-kit, the shared-workflows pin, estate, the Project's repository and fleet-infra, and any one of those hops could lag. Keep the compiler, the service and the toolkit pin together, and treat a toolkit bump as an input change that triggers a render.
- **Evidence**:
  - CS story 30: the standing order of a move.
  - WS line 100: overleaf 1.1.0's publish failed because its workflows pin lagged.
  - CS line 89: arr needed a workflows-pin bump before it could accept `vpn`.
  - CS lines 216 to 217: "A toolkit bump dispatches no delivery", so the maintainer dispatched one by hand.
- **Applies to estate-kit as**: the repository layout (compiler and service in one repository) and the delivery triggers.
- **Proposed**: keep. It is a direct argument for consolidating into estate-kit.

### PR-3. Map the decisions before the rewrite, then follow one ordered plan with move-only steps first and one contract release
- **Lesson**: When the repository cannot say what to do first, resolve the open decisions as a map of tickets, then put the work in one order:
  - restructuring PRs that change no meaning, proved by byte-identical oracles and tests nobody edited;
  - additions, released as non-breaking releases;
  - one contract release that carries every removal.

  The model and the tool share one version number.
- **Evidence**:
  - #341 (the map: 21 resolved tickets) led to #373 ("I cannot tell from the repository what to do first"): Steps 1 to 9, stories 1, 8, 9 and 13 to 16, and its Testing Decisions ("Move-only pull requests are proved by what does not change").
  - `deploy-kit/docs/adr/model/0007-schema-version-separable.md` (open) is rewritten for lockstep in #373 Step 7: "so that I reason about one number".
- **Applies to estate-kit as**: the founding plan and its release policy.
- **Proposed**: keep. The release-please mechanics (UC C47) are tooling trivia and are left out.

### PR-4. Parallel agent sessions need explicit ownership and a list of what not to touch
- **Lesson**: When several sessions share one login, each claims its ticket, works in one worktree per ticket, and publishes a list of what others must not touch. Shared counters, such as ADR numbers, are fixed at merge (see DR-3).
- **Evidence**:
  - CS lines 33 to 36: the list of tickets to keep off while epic #544 ran.
  - EOW progress log: workspace-46 paused #429 because it overlapped #548, #546, #553 and #547.
  - WS §"Who owns what".
- **Applies to estate-kit as**: process (`AGENTS.md`).
- **Proposed**: keep, trimmed.

### PR-5. Flag operator-only steps up front
- **Lesson**: Steps that need the maintainer's terminal, their credentials or a destructive live action are flagged when the work is planned, and batched together.
- **Evidence**: CS lines 188 to 191 and 248 to 249: auto mode refused `kubectl exec` and `gh pr merge`, so the maintainer ran them. WS §"Operator to-do, one sitting".
- **Applies to estate-kit as**: process. Each ticket marks whether its steps are for the agent or the operator.
- **Proposed**: drop, or merge into PR-4. It is about the agent harness, not estate-kit.

---

## Model-driven engineering takeaways

### MD-1. Two implementations held to shared oracles found spec gaps, at twice the cost
- **Lesson**: An independent second reading of the spec catches ambiguities and gaps that one implementation agreeing with itself never will. Get that reading more cheaply than with a full second implementation: hand-written expected outputs, a small reference evaluator, or property tests over invariants.
- **Evidence**:
  - P2 speaker notes under Reflection: #216 found a RollingUpdate/Recreate disagreement, and #440 found the Secret Store policy gap.
  - `deploy-kit/docs/research/modelling-languages.md`, §Positioning item 5.
  - #373: the second implementation "doubles the cost of every model change".
  - CS line 355: naming Jobs by their rendered template was rejected because the EMF side fixes names before rendering. The second implementation constrained the production design.
- **Applies to estate-kit as**: testing strategy. Rust is the only implementation, and independent oracles (TM-1) provide the second reading.
- **Proposed**: keep. It generalises, and it is the course's main finding.

### MD-2. Define the typed model first and derive the syntax from it
- **Lesson**: Define the abstract model first, then derive every concrete syntax from it: YAML for authors, JSON Schema for editors, any interchange form. The YAML shape never defines the concepts.
- **Evidence**: T1 `04-alternatives.tex`, §"Grammar First or Metamodel First": two syntaxes needed the same concepts. T0 `06-tooling.tex`: on the TypeScript side, one `zod` definition gave the static types and the JSON Schema.
- **Applies to estate-kit as**: compiler. Rust types are the source, and serde plus a schema generator (for example `schemars`) produce the published JSON Schema.
- **Proposed**: keep.

### MD-3. Keep a trace from every output back to the authored element that caused it
- **Lesson**: Each resolved object and rendered file links back to the element it came from, so a diagnostic or a diff can name the authored line.
- **Evidence**: T2 `03-design.tex`, §"The Trace and End Sections". `04-evaluation.tex` §Reflection: the QVTo trace "avoided a manual source-to-target table". `deploy-kit/docs/adr/architecture/0058-every-step-links-through-one-trace.md` (claim still open). In T2 `03-design.tex` §"The Path Plan", each Deliverable records "the model elements used to generate it".
- **Applies to estate-kit as**: compiler. Source spans travel with model nodes, and every Deliverable carries its provenance.
- **Proposed**: keep. It pairs with CS-3.

### MD-4. Pick an implementation language whose test tooling reaches the transformation code
- **Lesson**: If coverage and mutation tools cannot measure the transformation itself, the strongest gates stop at the glue code around it.
- **Evidence**: T2 `04-evaluation.tex`, lines 44 to 46: coverage and mutation required 100% "for the Java integration code. They do not measure QVTo." The course's survey reading found that dedicated transformation languages are held back by tooling and community more than by language design (`deploy-kit/docs/mde/course-material/INDEX.md`, line 1880; paraphrased, not quoted).
- **Applies to estate-kit as**: the case for Rust, where `cargo-llvm-cov` and `cargo-mutants` reach the resolution code directly.
- **Proposed**: keep, as a short note behind the stack ADR.

### MD-5. Run the whole toolchain headless before modelling (a walking skeleton)
- **Lesson**: Run every tool end to end in CI on a trivial example before writing the model.
- **Evidence**: P2 line 648: "Tools proven first: Every tool ran headless in CI before any modelling" (speaker notes: #109, 14 Sep). By contrast, `deploy-kit/docs/adr/architecture/0056-the-compiler-is-a-chain-of-typed-models.md` is still `claim: open`, waiting for "the first rewrite slice rendering `minimal` end to end".
- **Applies to estate-kit as**: the first milestone. The Rust compiler and the Go service render and deliver `minimal` in CI before the spec grows.
- **Proposed**: keep.

### MD-6. Keep an external deadline's work off the production critical path
- **Lesson**: Work owed to an outside party, such as a course or a demo, must not sit on the production repository's critical path or constrain its design.
- **Evidence**: EOW §4: "If time runs short before 2026-10-30, #547 and its blockers come first: that is what the Task 3 report and the presentation claim." #373, Out of Scope and Step 1: no rewrite step starts before Task 3 is submitted. CS line 355 records the design constraint (see MD-1).
- **Applies to estate-kit as**: process. Nothing course-related lives in estate-kit.
- **Proposed**: merge into MD-1, or drop. It is course bookkeeping unless the maintainer wants the general rule.

### MD-7. Track leverage as a headline metric
- **Lesson**: Track authored lines or files against rendered ones, as evidence that the model pays for itself.
- **Evidence**: P2 line 651: "41 hand-written files generate 325". EOW §7: the live estate renders 325 files and 13,089 lines.
- **Applies to estate-kit as**: a report in the service or the dashboard.
- **Proposed**: drop, or keep as a one-line goal metric. It is nice to have, not a lesson.

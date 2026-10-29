# Review: process, testing and the plan

Part of the [design review](README.md). Each finding was checked by a second
reviewer that tried to refute it; its verdict and corrections follow the finding.

## Verdict

The plan's parts are each sound: parity before rewrite, an inert shadow, characterization before porting, oracles only at the seams, and Locked records backed by checks. Taken together, though, it costs more than a few hours a week can pay, and it pays nothing back until the end. The compiler it ports changes fast: deploy-kit went from its first commit on 2026-09-07 to v0.31 in six weeks, with about 30 feat and fix commits to src/ between 1 and 20 October and 57 October commits under spec/v1/examples. Byte parity is measured against a third-party JavaScript YAML emitter. Three large pieces of work are not in port.md at all: the TypeScript gate tooling, the unit-test suite that the 100% mutation gate needs, and the host applier and mail provisioner. Premortem (assume it is 2027-10 and the port has stalled): the most likely causes are (1) Rust never catches a TypeScript compiler that keeps moving, (2) the budget goes on the YAML emitter, the gate tooling and the mutation gate, not on delivery, (3) two stacks run in shadow with no exit date, and (4) writing 57 records came before any code and used up the first months. The cheapest fix is to reorder the plan. Deliver first, through the Go service and the existing compiler behind the subprocess seam. Port the compiler crate by crate afterwards, if at all, and cut or postpone the host applier.

## What the design gets right

- Port at parity, cut over, then rewrite keeps a change of language apart from a change of meaning, so a renders diff points to a porting bug, not a model decision (choices.md 'Rewrite and parity').
- The subprocess seam (a directory in and out, plus result.json with its own schema and committed fixtures) is the right abstraction for a branch-by-abstraction swap: any implementation that honours it can sit behind the service.
- The shadow is inert by construction: unsigned `shadow/<p>` tags that Flux never reads, and an admission check that refuses them (conventions.md, register [record 67](../../decisions/0067-the-compiler-is-written-to-the-1-0-contract.md)). This avoids Scientist's warning about side effects.
- Characterization tests before the Go services merge ([record 55](../../decisions/register.md)) protect delivery and estate-dashboard, the parts with no oracle files.
- Oracles only at four seams, one hand-written fake per port, and no snapshot tests keep fixture churn low when output changes (code-shape-and-speed.md).
- 'Locked' is mapped onto MADR's Confirmation section, not invented as a new status, and every must-always rule is backed by a check, not a sentence. This matches primary guidance for agent-legible repositories.
- The lesson candidates are grounded in measured evidence (#373's 42 of 108 unexercised refusal codes, 10,489 spec lines). DR-1 and DR-2 make claims settle on a source or a drill.
- Quality scenarios S1 to S15 and numeric speed budgets make the design reviewable against outcomes, not taste.

## Findings

### process-1: Catch-up drift: byte parity chases a compiler that changes several times a day

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| risk | high | S4: two compilers to upgrade, fix and port forward through every dependency bump while both live, S5: returning after two months means a backlog of TypeScript changes that are not yet in Rust, S14: the rewrite can only start after the cutover, and a port that never converges means the cutover never happens | weakened | high |

**Concerns:** plan/port.md 'Order of work' (changes 'are ported forward before the shadow phase can close'); overview.md 'Risks and open questions', Catch-up drift; choices.md 'Old repos meanwhile' (Both stacks evolve; Rust catches up)

The design rejected a freeze because 'production is not held back'. The new fact is the measured rate of change. deploy-kit's history starts on 2026-09-07 and holds 225 commits. Between 1 and 20 October it took about 30 feat or fix commits to src/: VPN attachment, GPU requests, internet egress, libraries, rate limits, Vault key generation and more. 57 commits touched the oracle examples in October alone, and the tags reached v0.31.0. A 15,908-line compiler that gains more than a feature a day cannot be ported at byte parity by one person with a few hours a week. The port-forward queue grows faster than it drains, and the gate 'identical renders for an agreed number of days' is never met. This is the most likely cause of a stalled port in 2027.

**Recommendation.** Make convergence a stated rule, not a hope. Option A (preferred, see process-2): do not start the Rust port until the service has cut over on the existing compiler. Option B, if Rust stays first: freeze the model one concept at a time. A concept that is being ported takes only fixes in TypeScript, and any new feature lands in Rust first or waits. Track port-forward debt as a number in CI: TypeScript commits to src/ and spec/v1/examples since the last parity point. Set a kill criterion, for example: if the debt grows for six weeks in a row, the port stops and the plan falls back to process-2.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| Hard freeze of deploy-kit semantics during the port | Rejected in choices.md; the October churn is the new fact that reopens it | Converges, but holds production features back for the length of the port. |
| Per-concept freeze with a port-forward debt counter | Process only, no tooling needed beyond a git log count in CI | Converges concept by concept and holds back only the concept being ported, at the cost of some bookkeeping. |

**Verification (weakened).** The risk is real, and the design's only answer is 'the shadow diff is the check' (overview.md Risks, Catch-up drift). That diff detects drift but does nothing to make the port converge. The finding's history facts check out against the local deploy-kit checkout: first commit 2026-09-07, 225 commits, tags up to v0.31.0, 57 October commits touching spec/v1/examples. The headline inference is overstated, though. 38 of those 57 example commits, and 37 of the 57 feat/fix commits to src/ in October, also touched emf/. The same maintainer was already keeping a second implementation at oracle parity on every change, at that rate. Much of the churn was also pushed by the 2026-10-30 course hand-in. So 'cannot be ported at byte parity by one person' is not shown, and the throughput behind 225 commits in six weeks is clearly not 'a few hours a week'. The real cost is MD-1's 'twice the cost', not impossibility. The per-concept freeze and the debt counter are cheap and sound. The kill criterion overlaps process-7.

**Corrections.** The finding undercounts: 57 feat or fix commits touched src/ between 2026-10-01 and 2026-10-20, not 'about 30'. The weekly counts were 18, 17 and 24 for the weeks of 28 Sep, 5 Oct and 12 Oct, and only 5 in the week of 19 Oct (last commit 2026-10-20). About two thirds of October's src and oracle churn was done in lockstep with the EMF implementation, which is deleted after 2026-10-30. Lockstep parity at this rate has therefore already been sustained once. The October rate is an upper bound shaped by the course deadline, not a steady state.

Sources:

- `git log of JorisJonkers-dev/deploy-kit (local checkout, read 2026-10-22): first commit 2026-09-07, 225 commits, tags v0.29.0 to v0.31.0`
- <https://martinfowler.com/articles/patterns-legacy-displacement/transitional-architecture.html>
- `deploy-kit local checkout: git log --since=2026-10-01 -- src and -- spec/v1/examples, cross-checked against git show --stat for emf/ paths`
- `docs/lesson-candidates.md MD-1 and MD-6`

### process-2: Deliver first through the subprocess seam: Go service plus the existing compiler, Rust later or never

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| alternative | high | S4: one language fewer on the critical path until the cutover, S5: one stack in production sooner, S12: deploy speed comes from the service and registry tags, not from the compiler's language, S10, S11: signing, per-Project tags and OIDC land months earlier | weakened | medium |

**Concerns:** overview.md 'Order of work' steps 2 to 5; plan/port.md 'Problem' and 'Order of work'; choices.md 'Rust start' (in estate-kit from day one) and 'Compiler in the service' (subprocess, same binary as CI)

Every problem in port.md's Problem section except one is solved by the Go service and the registry tags: four repositories drifting apart, the central pin list, the images lock and the participants list. The exception is 'no single binary, types erased at runtime'. The plan still puts the whole Rust port (step 2) before the service merge (step 3), so none of that value arrives until a 16k-line port is done. That is the big-bang shape that redesign-practices.md section 1.1 itself warns against. It also contradicts kept lesson MD-5, which calls for a headless walking skeleton through the whole toolchain first. The subprocess seam already lets the service run any compiler that honours the directory and result.json contract. The single-binary goal can be met without a port: Node's single executable applications now have built-in generation (`node --build-sea`, added in v25.5.0, stability 1.1 'Active development', ESM supported through mainFormat 'module'). The compiler's runtime dependencies are only yaml and zod, and zod already checks types at runtime. The 230-package development tree can be hardened with pnpm's minimumReleaseAge (added in v10.16.0, default 1440 minutes since v11) and trustPolicy 'no-downgrade' (added in v10.21.0).

**Recommendation.** Reorder the plan into: (1) found the repository; (2) a walking skeleton: the Go service composes the 'minimal' example with the TypeScript compiler as a subprocess, packaged as a SEA binary or as an image, signs, and writes a shadow tag; (3) merge the Go services behind characterization tests; (4) shadow; (5) staged switch; (6) archive. Then decide the Rust port on its own merits, as a strangler behind the same seam, one compiler command or one stage at a time with oracle parity per stage. If it never pays, it never happens. Write this into the port-strategy record as the fallback path.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| Node single executable application (node --build-sea) | Built-in since Node v25.5.0; stability 1.1 Active development; VFS part 1.0 Early development | One binary without a port. Larger binary (it bundles Node) and Node startup cost. Still a Node toolchain in CI. |
| Bun or Deno compile to a single binary | Both active; bun pushed 2026-10-22 | One binary; adds a second JavaScript runtime whose behaviour may differ from Node's, so the oracles would need re-proving. |
| Rust port as planned, before the service | Current plan | Best end state for types and binary size; no delivery value until the port converges (see process-1). |

**Verification (weakened).** The direction holds. Lesson MD-5 ('Applies to estate-kit as: the first milestone. The Rust compiler and the Go service render and deliver minimal in CI') conflicts with a plan that finishes the whole port (step 2) before the service exists (step 3). The new facts check out. node --build-sea was added in v25.5.0, stability 1.1 Active development, with mainFormat 'module' supported (it cannot be combined with useSnapshot). pnpm's minimumReleaseAge was added in v10.16.0 with a 1440-minute default since v11, and trustPolicy was added in v10.21.0 with a default of off. deploy-kit's CLI already has validate, publish and compose commands that read and write directories only, which makes the subprocess seam realistic. Three things cut against the finding. First, 'big-bang' misreads redesign-practices.md 1.1. The port runs beside production and is followed by shadow and a staged switch, so the plan has a sequencing problem, not a big-bang one. Second, the finding hides work the TypeScript compiler would need: it has no result.json today, and it would need the compose-result schema, digests sealed into the fragment instead of the estate images lock, tag-based Flux pin sources instead of pin commits, and model-path diagnostics. All of that lands in TypeScript and must later be ported again. Third, 'Rust later' puts a port after the cutover, next to the #373 rewrite, which is the outcome S14 forbids. That holds unless 'never' is chosen. A SEA binary still carries Node startup, which overview.md lists as a weak point.

**Corrections.** MD-5 as written asks for a walking skeleton built with the Rust compiler and the Go service, not the TypeScript compiler. The finding reinterprets it. deploy-kit uses npm (package-lock.json), not pnpm, so the pnpm hardening first needs a package-manager migration. The TypeScript CLI does not write result.json, the contract the service is designed to read (inside-the-compiler.md 'The wire to the service'). 'Every problem except one is solved by the Go service and the registry tags' omits that the tag-based pins and sealed digests are compiler output changes.

Sources:

- <https://nodejs.org/api/single-executable-applications.html>
- <https://pnpm.io/settings/dependency-resolution>
- <https://martinfowler.com/bliki/StranglerFigApplication.html>
- <https://martinfowler.com/bliki/BranchByAbstraction.html>
- `docs/lesson-candidates.md MD-5`
- `deploy-kit/src/cli/main.ts (validate, publish, compose commands; no result.json)`
- `docs/design/inside-the-compiler.md 'The wire to the service'`
- `docs/research/redesign-practices.md 1.1`

### process-3: Byte parity is defined by a JavaScript YAML 1.1 emitter that no Rust crate reproduces

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| weakness | high | S4: a yaml major release (v3 is in prerelease) moves the parity target, S14: the bespoke emitter becomes permanent upkeep after the cutover, S1: the render the API server sees depends on emitter quoting rules | confirmed | high |

**Concerns:** overview.md 'Order of work' step 2 (Gate: byte-identical); 'Risks and open questions', Open: which Rust YAML parser keeps source positions; plan/port.md Gate 'every oracle file renders byte-identical'

deploy-kit writes every render with eemeli/yaml's stringify, using version '1.1', lineWidth 0 and aliasDuplicateObjects false (src/infrastructure/serializer.ts:46). It writes JSON with ECMAScript JSON.stringify (canonical-json.ts, json-schema.ts). Byte parity therefore means re-implementing that library's YAML 1.1 quoting and scalar-style choices (yes, no, on, off, octal-looking and timestamp-looking strings) and JavaScript's number formatting in Rust. serde_yaml is deprecated. Its successor serde-saphyr 2.0.0 (2026-10-13) has its own style options: quote-all, yaml_12, block scalars for long strings, and no documented line-width setting. The design's open question is only about a parser that keeps source positions, not about the emitter. The target itself is moving: yaml v3.0.0-2 was published on 2026-09-11 and warns that 'everything/anything' may still change.

**Recommendation.** Before porting, take one strangler step in TypeScript. Define the render bytes as a canonical form both languages produce trivially, and regenerate the oracles once in a single reviewed PR. Either emit JSON canonicalized with RFC 8785 (JSON is valid YAML, and Kubernetes and Flux read it), or emit a tiny canonical YAML subset written by a hand-written emitter of about 100 lines that the spec describes and both implementations share. Pin yaml to 2.x in deploy-kit for the life of the port. Keep TM-2 (diff parsed structure first) as the debugging aid. The byte gate then costs almost nothing.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| serde-saphyr | 2.0.0 released 2026-10-13; active; supports `Spanned<T>` locations and serialization | A good parser for diagnostics; its emitter will not match eemeli/yaml byte for byte. |
| RFC 8785 JSON Canonicalization Scheme | IETF RFC, June 2020; number serialization follows ECMAScript | Byte determinism across languages for free; renders are less pleasant for people to read in diffs. |
| Hand-written canonical YAML emitter in both languages | Bespoke, small | Readable output and full control; about 100 lines per language to maintain. |

**Verification (confirmed).** The core claim survives. deploy-kit/src/infrastructure/serializer.ts line 46 calls stringify with aliasDuplicateObjects false, lineWidth 0 and version '1.1'. JSON is written with JSON.stringify and canonical-json.ts, which sorts keys and formats numbers through JSON.stringify. The oracles really exercise YAML 1.1 quoting: quoted "on", "off", "true", "0400" and numeric-looking port strings appear across spec/v1/examples. The design's only open question (overview.md Risks; inside-the-compiler.md 'Spanned parse') is about a parser that keeps positions, never the emitter, so this gap is new. The crate facts check out on crates.io: serde_yaml is 0.9.34+deprecated (2024-03-25), and serde-saphyr 2.0.0 was released 2026-10-13. Its README documents quote-all (with wrapping off), yaml_12 and block scalars for long or multi-line strings, and names no line-width option. eemeli/yaml v3.0.0-2 is a prerelease that says 'expect everything/anything to still change'. Severity could be argued down to medium: with lineWidth 0 only scalar quoting has to match, and a Rust emitter written for that one subset would also work. The recommendation to canonicalize first also needs every oracle rewritten once. TM-1 forbids tests or CI from writing oracles, so that PR must be hand-reviewed, with TM-2's structural diff as the proof of no semantic change.

**Corrections.** deploy-kit already pins yaml exactly at 2.9.1 in package.json. The real exposure is Renovate, through the shared JorisJonkers-dev/renovate-config, proposing 3.x once it is stable, so the action is a Renovate rule, not a new pin. v2.9.1 and v3.0.0-2 were released the same day (11 Sep). A Rust-only emitter that copies the exercised YAML 1.1 subset is a third option the finding does not weigh.

Sources:

- <https://github.com/bourumir-wyngs/serde-saphyr>
- <https://github.com/eemeli/yaml/releases/tag/v3.0.0-2>
- <https://www.rfc-editor.org/rfc/rfc8785>
- `deploy-kit/src/infrastructure/serializer.ts:46 (local checkout)`
- <https://crates.io/api/v1/crates/serde-saphyr>
- <https://crates.io/api/v1/crates/serde_yaml>
- <https://github.com/eemeli/yaml/releases>
- `deploy-kit/package.json lines 76-77 (yaml 2.9.1, zod 4.6.7)`
- `deploy-kit/renovate.json`

### process-4: The plan leaves out the gate tooling, the unit-test port, the host applier and the mail provisioner

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| missing | high | S4: every bespoke gate and component is upkeep the budget must pay, S5: unplanned work found mid-port is the 'rediscovering the system' this scenario forbids, S9: a new host applier replaces a working deploy-rs path during a cutover | weakened | high |

**Concerns:** plan/port.md 'Order of work' and 'Gates'; choices.md 'UI' (npm confined to the UI build), 'Mail provisioner' (ported to Go), 'Host apply'; design/hosts.md; design/mail-and-components.md; code-shape-and-speed.md 'Enforcement'

Measured in deploy-kit: 5,123 lines of gate scripts (lint:adrs, lint:rules, lint:codes, lint:meaning, lint:boundaries, mutation-shard, mutation-merge, mutation-survivors, pr-report, rc-publish) and 10,299 lines of tests that test those gates. Because npm is confined to the UI build, all of this must be rewritten in Rust or Go, or dropped. port.md names none of it. Holding a 100% mutation score in Rust also implies porting most of the 19,232 lines of domain tests, but the only gate in the plan is oracle parity. Order of work also never schedules the host applier, which is a new bespoke agent replacing deploy-rs in nix-config, or the Python-to-Go port of the mail provisioner. The design pages specify both. Together this is plausibly more work than the compiler port.

**Recommendation.** Add a sized line for each piece to port.md, and cut. (a) Gates: carry over only gates with an incident behind them (kept lesson TM-4) and write them as cargo xtask tests. Drop the rest, and say which in a record. (b) Tests: port unit tests concept by concept with the code, or accept oracle parity alone for ported code (see process-5). (c) Hosts: mark the host applier 'after the cutover, or never'. Keep deploy-rs meanwhile, and if pull mode is wanted, try comin plus kured before writing an agent. (d) Mail provisioner: keep it in Python until it needs a change.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| comin (pull-mode NixOS GitOps) | v0.14.0 released 2026-07-19 (SSH commit-signature verification, switch inhibitors, timeouts); v0.13.0 2026-05-08; pushed 2026-10-18; about 1.1k stars | Pulls and switches per node and verifies commit signatures; no signed-closure pointer and no cross-node serialization of switches. |
| kured (Kubernetes Reboot Daemon) | CNCF Sandbox since 2022-09-14; 1.23.0 released 2026-06-30; pushed 2026-10-21 | Reboot windows (--reboot-days, --start-time, --end-time), --reboot-sentinel-command, --concurrency default 1 lock; covers the window and one-at-a-time reboot half of the host applier. |
| Keep deploy-rs push until after the cutover | In use today in nix-config scripts/deploy | Zero new code; push needs SSH credentials and does not work when the deploying machine is down. |

**Verification (weakened).** The omission is real. Neither port.md 'Order of work' nor overview.md 'Order of work' schedules the host applier (hosts.md), the Go port of the mail provisioner (mail-and-components.md), the repository gates, or the unit tests behind the 100% Rust mutation gate. nix-config uses deploy-rs today (flake.nix, scripts/deploy/deploy-host.sh), so 'keep deploy-rs until after the cutover' costs nothing and is sound. Several supporting claims are overstated. 'Must be rewritten in Rust or Go' is wrong: estate-kit's own CI already runs repository gates in Python (scripts/check_diagrams.py, scripts/check_record_citations.py, with tests), so Python is already the gate language. The comin plus kured alternative fails S9. comin has no cross-node coordination (its own releases and prior-art.md say so), so a bad generation switches every node. kured only serializes reboots. prior-art.md had already weighed both. 'Plausibly more work than the compiler port' is not shown.

**Corrections.** The 5,123 lines are all of deploy-kit/scripts (5,088 lines of .ts plus 35 of .sh), not just the ten named gates, which total 2,601. The 10,299 lines are every top-level test/*.test.ts file. Several of those test src, not gates (published-schemas, schema-corpus, canonical-json, oracles, harness, about 1,000 lines). The other two counts are right: 15,908 lines of src and 19,232 lines of nested domain tests. comin v0.14.0 (19 Jul) added SSH signature verification, switch inhibitors and timeouts. kured's --concurrency defaults to 1 and its window flags exist, as stated.

Sources:

- <https://github.com/nlewo/comin/releases>
- <https://kured.dev/docs/configuration/>
- <https://www.cncf.io/projects/kured/>
- `deploy-kit scripts/ and test/*.test.ts line counts (local checkout)`
- `estate-kit/.github/workflows/ci.yml (Diagrams and Record citations jobs run Python checks)`
- `estate-kit/scripts/check_diagrams.py`
- `nix-config/flake.nix and scripts/deploy/deploy-host.sh (deploy-rs in use)`
- `docs/research/prior-art.md (comin and kured rows, finding 1)`

### process-5: A 100% mutation gate on code being ported, and immature Go mutation tooling

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| weakness | medium | S12: 'mutation on a PR under 5 minutes' cannot hold when every line of a port PR is new, S4: an equivalent-mutant exclusion list and a possible bespoke Go runner are upkeep, S5: a red mutation gate on a half-ported crate blocks a same-day change | weakened | high |

**Concerns:** code-shape-and-speed.md 'Mutation testing' and 'Speed budgets'; plan/port.md 'Gates'; overview.md Risks 'Go mutation tooling is immature; the service may need a small runner of its own'; lesson TM-5

cargo-mutants rebuilds once per mutant. During a port every changed line is in the diff, so a diff-scoped run on a port PR is a full run of a new crate, and the 5-minute PR budget is out of reach exactly when most PRs are being made. 100% from day one also means porting the unit tests or writing new ones before parity, which doubles the port. cargo-mutants itself is healthy: v27.1.0 on 2026-06-02 and a push on 2026-10-19. On the Go side, gremlins released v0.6.0 on 2025-12-06, after v0.5.0 on 2023-12-19, and its last commit to main was on 2026-03-30. Its README says 0.x 'doesn't guarantee backward compatibility' and 'doesn't work very well on very big Go modules'. The design's hint at 'a small runner of its own' is bespoke tooling the budget cannot carry.

**Recommendation.** During the port, the gate for ported crates is oracle parity plus coverage, and mutation runs nightly as a report. Turn on the 100% gate one crate at a time once that crate is at parity and its tests are in. Keep 100% for new behaviour after the cutover. For Go, run report-only with whichever tool works (gremlins or avito go-mutesting) on the rollout core package only. Write in a record that no bespoke mutation runner will be built.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| cargo-mutants | v27.1.0, 2026-06-02; active | Mature; cost is a build per mutant, which the crate-per-step layout keeps small. |
| gremlins | v0.6.0, 2025-12-06; last commit 2026-03-30; 0.x | Has a diff-only flag; slow on large modules; sparse releases. |
| avito-tech/go-mutesting | v2.3.1, 2025-12-26; pushed 2026-10-02 | More recently maintained fork; less documentation for diff scoping. |

**Verification (weakened).** The Rust half has a fair point. port.md 'Gates' applies 'Rust holds a 100% break score' from day one. On a port PR every line is new, so a diff-scoped run covers the whole module and forces unit tests to be written before parity. The finding overstates the speed problem, though. With one crate per step, a PR that ports one module mutates only that module, so the 5-minute budget breaks only for large port PRs, not for 'most PRs'. The Go half adds little. code-shape-and-speed.md and port.md already make Go report-only and then a ratchet, and overview.md already names Go mutation tooling as immature. The new parts are the tool facts and 'write down that no bespoke runner is built'. Those facts check out. cargo-mutants 27.1.0 was released 2026-06-02. gremlins v0.6.0 is the latest release, its last commit to main was 2026-03-30, and its README carries both quoted caveats. avito-tech/go-mutesting v2.3.1 was released 26 Dec, year not shown.

**Corrections.** gremlins does have a diff-only run flag, added in v0.5.0 (#215), so diff scoping is not the gap. Its README does not document the flag, which is why it looks absent. The year of v0.5.0 (given as 2023-12-19) cannot be read from the releases page, which shows only '19 Dec'.

Sources:

- <https://github.com/sourcefrog/cargo-mutants/releases>
- <https://github.com/go-gremlins/gremlins>
- <https://github.com/go-gremlins/gremlins/releases>
- <https://github.com/avito-tech/go-mutesting>
- <https://crates.io/api/v1/crates/cargo-mutants>
- <https://github.com/go-gremlins/gremlins/releases/tag/v0.5.0>
- <https://github.com/go-gremlins/gremlins/commits/main>
- <https://github.com/avito-tech/go-mutesting/releases>
- `docs/design/code-shape-and-speed.md 'Mutation testing'`

### process-6: 57 records marked Accepted before any is written, with documentation due before code

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| weakness | medium | S5: 57 records, an 86-row choices table, 45 lessons, 15 design pages and 85 diagrams to re-read after two months, S4: every Locked record is a lint with a fixture to keep green, S13: an agent treats an Accepted record that rests on an open spike as binding | weakened | high |

**Concerns:** decisions/register.md (all 57 rows 'Accepted'); decisions/README.md 'Status' and 'Writing order'; overview.md step 1 'Write the founding records and docs/lessons.md'; lesson-candidates.md DR-2, DR-3, MS-2

decisions/README.md defines Accepted as 'Decided. Code follows it'. Yet the register marks all 57 planned records Accepted before one exists, and several rest on questions overview.md lists as open: the Rust YAML parser spike, the number of shadow days, and whether the Pause and Rollback object is a CRD or a ConfigMap. That breaks the kept lesson DR-2 ('an open claim gets a settling test... or the decision is not accepted'). Phase 1 makes writing the founding records a precondition for founding, so with a few hours a week the first months go on prose. The history repeats: deploy-kit reached 100 ADRs (9,322 lines) and a 12k-line spec in six weeks, which is the bloat #373 measured and MS-2 warns against. Docs are already drifting before any code exists: port.md line 21 says the service moves `render/<p>:live`, while line 33 of the same page and every design page say `render/<p>:prod`.

**Recommendation.** Change every unwritten register row to 'Planned' (or Proposed), and write each record just in time, in the PR of the phase that first needs it. Phase 1 needs only the frame: one maintainer, port strategy with its fallback, records and statuses, and the agent contract. Keep choices.md as the interim decision log. Set a soft cap, for example 25 records before the cutover (DR-3 already asks for a soft budget). Lock only contracts and rules whose check already exists. Finish lesson curation in one sitting: 39 of 45 are already Keep, so it should not gate founding. Add a link-and-term check that catches drift like :live versus :prod.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| Write all 57 founding records first (current plan) | Planned | One coherent story to read; weeks of budget before code, and records written ahead of the evidence that should settle them. |
| Just-in-time records, with choices.md as the log | Process change only | Records land with their code and checks; the reading-order numbering is assigned at merge (already DR-3). |

**Verification (weakened).** The status defect is real. decisions/README.md defines Accepted as 'Decided. Code follows it', yet register.md lists all 57 unwritten records as Accepted. [Record 28](../../decisions/register.md) (Pause and Rollback as a cluster object) is Accepted while overview.md still lists its kind as open, which goes against DR-2. The :live versus :prod drift is real: port.md line 21 says `render/<p>:live`, while line 33 and hosts.md say :prod. The deploy-kit figures check out: 100 ADR files, 9,322 lines, spec/v1 11,958 lines. Two parts are overstated. choices.md line 3 already says 'A choice becomes binding when its record lands in this directory', so the design partly guards against reading the register as binding. And 'the first months go on prose' is speculative: overview.md step 1's gate is only 'the imported trees build', and this maintainer produced 100 ADRs in six weeks, so the cost is bloat and reading load (S5), not calendar time. The cap of 25 records is arbitrary.

**Corrections.** Lesson curation is finished, not partial: all 45 candidates are decided, 41 Keep and 4 Drop (DO-7, PR-5, MD-6, MD-7), not '39 of 45'. estate-kit CI already has a check for relative links and anchors, and one that records are cited by link. What is missing is a term or tag-name consistency check, which is what would have caught :live versus :prod.

Sources:

- <https://adr.github.io/madr/>
- <https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions>
- `deploy-kit docs/adr (100 files, 9,322 lines) and spec/v1 (11,958 lines), local checkout`
- `docs/decisions/choices.md line 3`
- `docs/decisions/README.md 'Status'`
- `docs/plan/port.md lines 21 and 33`
- `estate-kit/.github/workflows/ci.yml (Links job)`

### process-7: No time boxes, exit dates or fallback per phase, and the shadow exit is still open

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| missing | medium | S5: two production stacks with a half-done port is the hardest state to return to, S4: double maintenance while shadowing doubles the work of every upgrade, S8, S9: two delivery paths during an incident | weakened | medium |

**Concerns:** overview.md 'Order of work' gates; 'Risks and open questions' (Open: how many days of identical shadow renders); plan/port.md checklist

Each phase has a quality gate but no cost bound and no 'stop and fall back' rule. The worst outcome in the premortem is not failure but limbo: estate-kit half-ported while deploy-kit, delivery and estate-dashboard keep serving and keep evolving, with every fix landing twice. The shadow phase has no defined exit ('an agreed number of days'), and it requires both stacks to stay current. Fowler's transitional-architecture pattern justifies temporary code only while it 'speeds delivery or reduces migration risk' and asks that it be removed when it no longer does. Nothing in the plan forces that removal.

**Recommendation.** Give every phase a budget in maintainer hours, a target date, and a named fallback: if it is missed, stop and take the fallback (for the compiler, process-2's 'keep TypeScript behind the seam'). Define the shadow exit concretely, for example 'every admitted Project has had at least one real deploy with identical shadow render, and 14 days with no mismatch'. Switch Project by Project as the design allows, so the shadow shrinks instead of running estate-wide. Keep a dated burn-up in docs/plan/port.md.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| Per-Project switch as soon as that Project's shadow matches | Already possible with per-Project tags (redesign-practices.md 1.1, Strangler fig) | Shortens double running; mixed estate for a while, which the per-Project tag design already tolerates. |

**Verification (weakened).** Correct that no phase has a time or hours budget or a fallback, and that the shadow exit is open (overview.md Risks: 'how many days of identical shadow renders are enough'). Two parts are overstated. 'Nothing in the plan forces that removal' ignores step 6 (Archive the old repositories) and port.md's archive line. The Fowler citation is a paraphrase: the page names two values (faster delivery, lower displacement risk) and says transitional architecture 'must be removed' once the target is reached. It does not say 'only while'. The recommendation largely duplicates process-1's kill criterion. One point is worth keeping: the per-Project switch the finding proposes is already what redesign-practices.md 1.1 describes ('a strangler at the level of the Project'). But port.md and overview.md sequence the switch by component (compiler, then pins, then dashboard), so the design is inconsistent with its own research. That inconsistency is the stronger finding here.

**Corrections.** The plan does schedule removal (Archive, step 6). The Fowler page does not use the 'only while' wording. The staged switch in port.md and overview.md is per component, not per Project, contrary to redesign-practices.md 1.1. The finding cites that section as if per-Project were already the plan.

Sources:

- <https://martinfowler.com/articles/patterns-legacy-displacement/transitional-architecture.html>
- <https://martinfowler.com/articles/patterns-legacy-displacement/>
- <https://github.blog/2016-02-03-scientist/>
- `docs/research/redesign-practices.md 1.1 (Strangler fig, Branch by abstraction)`
- `docs/plan/port.md 'Order of work' switch lines`

### process-8: Four toolchains and seven programs for one part-time maintainer

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| weakness | medium | S4: Rust, Go, Vue and npm, and Nix each ship breaking releases on their own clocks, S5: re-learning four build systems after two months away, S12: PR checks under 2 minutes across a Rust workspace, a Go module and a UI build | weakened | medium |

**Concerns:** overview.md 'Risks', Two toolchains; choices.md 'Languages', 'UI', 'Mail provisioner', 'Host apply', 'Nix and Kubernetes'; code-shape-and-speed.md 'Speed budgets'

After the port the repository holds a Rust compiler, a Go service, a Vue UI (npm), a Go mail provisioner, a host applier, Nix modules and a Python diagram generator. The design counts 'two toolchains', but it is really four (Rust, Go, Node for the UI, Nix) plus Python for the docs. Each language choice is justified locally, but S4's 'upgrade lands in one sitting' is weighed per toolchain per month. The fewer-languages options were rejected on fit ('Rust's sum types fit the model'), not on upkeep. The upkeep is the constraint the scenarios rank highest.

**Recommendation.** Decide explicitly which toolchains are on the critical path before the cutover, and keep it to two. Following process-2, that is TypeScript (existing compiler, unchanged) and Go (service). Rust joins only when the port proves its worth. Cut what does not need code: the host applier (deploy-rs, or comin plus kured) and the mail provisioner (stays Python until touched). Re-weigh the UI: if the dashboard's value is the rollout stream, server-rendered Go templates remove npm entirely, a choice the design rejected without an upkeep argument. Give each toolchain a Renovate group and a monthly upgrade slot, and make the S4 drill (one upgrade, one sitting) a recurring check.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| TypeScript plus Go until the cutover, Rust optional afterwards | Both toolchains in use today | No port before value; keeps the npm development tree, which pnpm's release-age and trust policies harden. |
| Go only (compiler ported to Go) | Rejected in choices.md on model fit | One toolchain; weaker sum types, and still a full port at parity. |
| Rust plus Go as planned | Current plan | Best fit per part; the most toolchains to keep current. |

**Verification (weakened).** Partly misreads the design. overview.md Risks already says 'Rust and Go, plus npm for the UI build', so it does not undercount npm. Nix is not added by estate-kit: the hosts run NixOS and nix-config's hand-written modules exist either way. The UI choice was not made 'without an upkeep argument': choices.md gives 'Keeps the dashboard; no npm at runtime', a reuse argument. Two points the finding leaves implicit do hold and are new. Python already lives in estate-kit (diagram generator and CI checks), so porting the Python mail provisioner to Go does not give 'one toolchain less', as choices.md 'Mail provisioner' claims. And because Node is already needed for the UI build, keeping the TypeScript compiler until the cutover adds no toolchain. The finding mostly restates process-2 and process-4.

**Corrections.** The design counts Rust, Go and npm, not 'two toolchains' alone. Nix and Python are not estate-kit additions: Nix is the hosts' substrate, and Python already runs estate-kit's docs and CI checks. That second fact weakens the choices.md 'One toolchain less' rationale for porting the mail provisioner, which is a stronger argument than the one the finding makes.

Sources:

- <https://pnpm.io/settings/dependency-resolution>
- <https://github.com/nlewo/comin/releases>
- <https://kured.dev/docs/configuration/>
- `docs/design/overview.md 'Risks and open questions'`
- `docs/decisions/choices.md rows 'UI' and 'Mail provisioner'`
- `estate-kit/scripts/check_diagrams.py and docs/diagrams/gen.py (Python already in the repository)`

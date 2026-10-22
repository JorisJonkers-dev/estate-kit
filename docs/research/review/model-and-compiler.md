# Review: model, language and compiler

Part of the [design review](README.md). Each finding was checked by a second
reviewer that tried to refute it; its verdict and corrections follow the finding.

## Verdict

The model and compiler design is careful about the right things: determinism, oracle files only at the four seams, a language-neutral schema contract, diagnostics that carry a model path, and a subprocess seam that is the same in CI and in the service. Its weak point is the order of work, not the model. It ports roughly 16,400 lines of source and 31,400 lines of tests to Rust at byte parity, and then rewrites the same model. The #373 plan already sets out that rewrite in TypeScript and deletes several concepts and pinned inputs, and estate-kit itself replaces others. The TypeScript CLI already offers the same seam (`compose --fragments … --out … --json`), so the language decision can be separated from the cutover. A single-binary TypeScript build (Node `--build-sea`, `bun build --compile`) and TypeScript 7's native compiler remove most of the weak points listed against TypeScript, and Rust's YAML and serde stack adds risks the design has not yet priced: fail-fast deserialization, `null` accepted as `None`, an unsettled YAML crate, and reproducing eemeli/yaml's YAML 1.1 emitter byte for byte. A bespoke model and compiler is still the right call over CUE, KCL, Pkl, Nickel, Timoni, kro or Helm, because the model's work is total derivation plus about 100 refusal codes, not templating. That rejection should be written down.

## What the design gets right

- Diagnostics carry a model path, and the binary resolves it to a line from the checkout at the fragment's source commit (errors-in-ci.md 'How an error finds its line'). That keeps source positions out of fragments and out of serde, which is the hardest part to get right in Rust.
- The subprocess seam (directory in, directory out, plus a schema-validated result.json) is language-neutral and runs the same binary in CI and in the service (inside-the-compiler.md 'The wire to the service'). It is what lets the language choice be reopened cheaply.
- The determinism rules are explicit and testable: BTreeMap only, RFC 8785 canonical JSON inside ConfigMaps (carried over from deploy-kit's serializer), a double render, and byte-compared trees.
- Hand-reviewed oracle files exist only at the four seams, CI never rewrites them, and unit tests assert properties, never snapshots (code-shape-and-speed.md 'Rules for files'). This is good practice against golden-file rot.
- Committed JSON Schemas are the language-neutral contract, with additive-only evolution checked in CI and unknown keys refused (conventions.md 'Contracts and their evolution').
- Closed enums and newtypes for the CONTEXT.md vocabulary, a parse-don't-validate boundary, and a collected diagnostic list instead of stop-at-first-error.
- Error codes exist only for authored input that does real harm here, each with a firing fixture, and compiler invariants are tests (errors-in-ci.md 'What counts as an error code'). This matches #373's cut of unexercised codes.
- Keeping its own derivation-total model instead of charts or templates is consistent with deploy-kit's 'foundation declared from images, no chart rendered' and with the scale premise.

## Findings

### model-compiler-1: Port at byte parity, then rewrite: the plan pays for the model twice, and the cutover does not need it

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| weakness | high | S14, S4, S5, S12, S1 | weakened | high |

**Concerns:** overview.md 'Order of work' steps 2 and 7; plan/port.md 'Order of work' and 'Not in scope'; choices.md rows 'Rewrite and parity' and 'Rust start'

Phase 2 ports the whole TypeScript compiler to Rust: 102 source files (about 16,400 lines on deploy-kit main at 0.31.0) and their behaviour, of which only the oracle files carry over, since the 31,400 lines of Vitest tests do not. The proof is byte identity. Phase 7 then rewrites the model. deploy-kit#373 is that rewrite, and it is planned in TypeScript ('From this point every change is TypeScript only'). Its contract pull request deletes the reconciliation ledgers, `alertClass`, the soft placement preferences, secret delivery `self`, the per-cluster env overlay and Cluster Target, seven self-invariant codes and six ledger codes, plus the intent, effective and dependencies goldens. estate-kit's own design replaces further pinned inputs that the port would carry: the participants list becomes Admitted Projects, pin annotations and pin commits become registry tags, and images.lock is sealed into the fragment. The handover ledger retires by 2027-03-31. So a large share of what the parity port reproduces byte for byte is scheduled for deletion. The cutover does not need a Rust compiler either. The design already isolates the compiler behind a subprocess with directory in, directory out and JSON, and today's TypeScript CLI already has that shape (`deploy-kit compose --fragments <dir> … --out <dir> [--json]`). The service, the pins-to-tags switch and the dashboard switch can all cut over against the TypeScript binary. Byte parity then holds trivially, because it is the same code, and the shadow phase tests only what actually changes (the service, signing and tags).

**Recommendation.** Separate the language decision from the cutover. (1) Found estate-kit, import deploy-kit, and ship the existing TypeScript compiler as the subprocess binary behind the documented CLI and result.json contract. (2) Merge the Go services, shadow and switch against that binary. (3) Do the #373 rewrite where its tests and Stryker setup already live, up to 1.0. (4) Only then, if Rust is still wanted, port the frozen 1.0 model at byte parity against the TypeScript 1.0 oracles. That is one port of the final model, which S14 asks for. Rewrite choices.md 'Rewrite and parity' and overview steps 2 and 7 to match, and keep 'byte-identical renders are the cutover proof' as the gate for step 4.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| Current plan: Rust port at parity, cutover, then rewrite in Rust | Designed; no code | One language for the rewrite. But the rewrite is done after a full port, with tests to rewrite from scratch and cargo-mutants rebuilding per mutant. Code slated for deletion gets ported, and the cutover waits on the port. |
| Rewrite during the port (rejected in choices.md) | Rejected | Loses byte parity as proof. Correctly rejected. |
| Cut over on the TypeScript binary, rewrite in TypeScript, optional Rust port of 1.0 | Possible today: deploy-kit 0.31.0 CLI already composes directory to directory with --json | Keeps the 99.5% coverage and 100% Stryker break score through the rewrite, and makes parity trivial at the cutover. The cost is that Rust's sum types arrive later or never. |

**Verification (weakened).** The core claim holds up. Checked against deploy-kit origin/main at 0.31.0: 102 src files, 16,414 lines; 31,415 test lines; dependencies are yaml 2.9.1 and zod 4.6.7. deploy-kit#373 step 7 (the contract PR) deletes the reconciliation ledgers, alertClass, the soft placement preferences, secret delivery self beyond Vault-native apps, the per-cluster env overlay and Cluster Target, seven self-invariant codes, the six ledger codes, and the intent, effective and dependencies goldens. #373 says 'From this point every change is TypeScript only'. estate/platform.intent.yml has handover.retireBy 2027-03-31. The CLI already runs `compose --fragments <dir> ... --out <dir> [--json]`. So the cutover does not need a Rust compiler, and porting code that is slated for deletion at byte parity is a real cost for one maintainer. Two parts are overstated. (1) The finding reads the plan as a strict port, then cutover, then rewrite in Rust. But choices.md also has '#373 tickets: tracked in both repositories; both stacks may do the work' and 'Old repos meanwhile: both stacks evolve; Rust catches up'. So part of the #373 deletions may land in TypeScript before or during the port. The real defect is a moving parity target plus an ambiguous home for #373 (overview step 7 says 'in Rust'; choices says either stack), not a guaranteed double payment. (2) 'Byte parity then holds trivially' holds only for the first stage of the staged switch. Moving pins to tags, sealing images.lock and replacing participants with Admitted Projects all change the compiler. deploy-kit's compose still takes --participants, --lock and --lock-commit and reports 'pins move for'. So the TypeScript binary needs model-side changes before the cutover either way (see model-compiler-4). The recommendation also inherits finding 2's open points about shipping TypeScript as one binary. Even so, it is the most valuable finding in this area.

**Corrections.** The design does not force every deletion to be ported. choices.md lets #373 work land in either stack, so the cost is catch-up drift and an unclear owner for #373, which overview step 7 contradicts. Parity is trivial only for the 'switch the compiler' stage. The tag, sealed-lock and Admitted Projects stages need TypeScript compiler changes too. The 'single binary' gap in the TypeScript path is answered only partly (see model-compiler-2).

Sources:

- <https://github.com/JorisJonkers-dev/deploy-kit/issues/373>
- `JorisJonkers-dev/estate: platform.intent.yml (handover ledger, retireBy 2027-03-31)`
- `JorisJonkers-dev/deploy-kit (origin/main 0.31.0: src 16,414 lines, test 31,415 lines; CLI usage)`
- <https://github.com/sourcefrog/cargo-mutants/releases>
- <https://github.com/stryker-mutator/stryker-js/releases>
- `JorisJonkers-dev/estate-kit: docs/decisions/choices.md (rows '#373 tickets', 'Old repos meanwhile')`
- `JorisJonkers-dev/deploy-kit src/cli/main.ts USAGE_TEXT (origin/main)`

### model-compiler-2: New facts against 'Rust compiler': TypeScript ships as one binary now, and Rust adds a third toolchain while npm stays for the UI

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| alternative | high | S4, S5, S10, S12 | weakened | medium |

**Concerns:** choices.md row 'Languages'; overview.md 'Evaluation of what is replaced' (Weak points) and 'Risks: Two toolchains'

The overview lists TypeScript's weak points as about 230 npm dev packages, types erased at runtime, Node startup, and no single binary. Each has a new answer. Node 25.5 added `node --build-sea`, which builds a single executable in one step (CommonJS entry, so bundle first). `bun build --compile` cross-compiles self-contained binaries for linux-arm64 and musl, embedding node_modules. Bun stays MIT and maintained after Anthropic's December 2025 acquisition, and it shipped v1.4.4 on 2026-10-22. Deno 2.9.8 offers `deno compile`. TypeScript 7.0, the native Go compiler, shipped in July 2026 (typescript-go v7.0.2) with 8 to 12 times faster builds, so type-checking is one native binary. Runtime types are not erased at the boundary: deploy-kit parses with zod 4.6.7 and generates its committed schemas from it. Startup is negligible: the local CLI validated three examples in 0.35 s wall time, against budgets of 2 and 10 minutes. On supply chain, the shipped binary would hold two runtime dependencies (yaml, zod). The design keeps npm for the Vue UI build anyway, so porting the compiler does not remove npm. It adds cargo and crates.io as a third registry, and crates.io had its own malicious-crate incident in September 2025. With Rust, the estate runs Rust, Go, TypeScript/Vue and Nix for one maintainer with a few hours a week. The Rust YAML stack is also churning: serde_yaml is deprecated, serde_yml carries RUSTSEC-2025-0068, and serde-saphyr reached 2.0 only on 2026-10-13. That works against S4 (upgrade in one sitting) and S5 (return after two months).

**Recommendation.** Reopen choices.md 'Languages' as a Proposed record with these facts and compare three options on S4, S5, S10 and change safety. (a) TypeScript compiler as a single binary (Node SEA, which keeps the runtime the estate already uses, or Bun or Deno), with a CI-only npm tree trimmed: oxlint or Biome in place of the ESLint stack, `npm ci --ignore-scripts`, and Renovate `minimumReleaseAge`. (b) Go for the compiler, giving one backend toolchain with the service and using sealed interfaces plus the `exhaustive` linter for closed sets. (c) Rust as designed. If Rust stays, state the reason it is chosen (sum types, learning value) and accept the third toolchain explicitly in the record.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| TypeScript + Node SEA (--build-sea) | In Node since 25.5.0 (Jan 2026); Node 24.22.1 LTS and 26.12.1 Current released 2026-10-21 | Same runtime as today. Needs a bundling step to a single CommonJS script. Binary of about 100 MB. |
| TypeScript + bun build --compile | Bun v1.4.4, 2026-10-22; owned by Anthropic since Dec 2025, MIT | One command, cross-compiles to linux-arm64 and musl, optional bytecode. A different runtime from the tests unless the tests also run on Bun. |
| TypeScript + deno compile | Deno v2.9.8, 2026-10-21 | Permissions model and built-in toolchain. Runtime differs from Node. |
| Go compiler | Go yaml: yaml/go-yaml v4.0.0-rc.6 (Jun 2026), goccy/go-yaml 1.19.2 (Jan 2026); santhosh-tekuri/jsonschema v6.0.3 (Aug 2026) | One backend toolchain. No sum types. Mutation tooling immature (gremlins v0.6.0, Dec 2025). |
| Rust compiler (current choice) | cargo-mutants v27.1.0 (Jun 2026); schemars 1.2.3 (Oct 2026) | Best types and a static binary. A third toolchain, a full port, and a slower mutation loop. |

**Verification (weakened).** The new facts are mostly real, and they do justify reopening 'Languages' as a Proposed record. Checked: Node v25.5.0 added --build-sea; Bun v1.4.4 shipped 2026-10-22; Deno v2.9.8 shipped 2026-10-21; typescript-go typescript/v7.0.2 shipped 2026-07-08; RUSTSEC-2025-0068 says serde_yml is unsound and archived; serde-saphyr 2.0.0 shipped 2026-10-13; gremlins v0.6.0 dates from 2025-12-06; Anthropic announced on 2025-12-03 that Bun stays MIT. But several claims are overstated. (a) TypeScript 7.0 'ships without a stable programmatic API' (expected in 7.1), so typescript-eslint and the Vue tooling cannot use it yet. Typed linting therefore still needs TypeScript 6 (deploy-kit pins typescript 6.0.3), and type-checking is not 'one native binary' for the toolchain. (b) Node SEA is still 'Stability 1.1 - Active development'. Today's docs support an ESM entry through mainFormat, so 'CommonJS entry, so bundle first' is out of date. Cross-platform builds must turn off useCodeCache and useSnapshot. (c) The supply-chain comparison is lopsided. The crates.io incident was two typosquats with about 8.4k downloads in total. npm in 2025 had the Shai-Hulud worm, which compromised over 500 packages (CISA alert). (d) deploy-kit's package-lock.json has about 370 package entries, so the overview's '230' undercounts, which strengthens the toolchain-weight point rather than the finding. Option (b), Go for the compiler, is also a full rewrite without sum types, and Go mutation testing is immature (gremlins v0.6.0 is the first release since 2023). That is weak on change safety. The point that porting does not remove npm is correct, because the Vue build keeps it.

**Corrections.** TypeScript 7.0 has no stable programmatic API, so typescript-eslint and Vue tooling still need TypeScript 6. Node SEA is experimental (Stability 1.1) and accepts ESM via mainFormat. The crates.io incident was minor next to npm's 2025 worm compromises. deploy-kit's lockfile has about 370 packages, not 230. The Bun acquisition was announced on 2025-12-03.

Sources:

- <https://nodejs.org/en/blog/release/v25.5.0>
- <https://bun.com/docs/bundler/executables>
- <https://www.anthropic.com/news/anthropic-acquires-bun-as-claude-code-reaches-usd1b-milestone>
- <https://github.com/oven-sh/bun/releases>
- <https://github.com/denoland/deno/releases>
- <https://github.com/microsoft/typescript-go/releases>
- <https://www.infoq.com/news/2026/08/typescript-7-released/>
- <https://blog.rust-lang.org/2025/09/24/crates.io-malicious-crates-fasterlog-and-asyncprintln/>
- <https://rustsec.org/advisories/RUSTSEC-2025-0068>
- <https://github.com/go-gremlins/gremlins/releases>
- <https://nodejs.org/api/single-executable-applications.html>
- <https://www.cisa.gov/news-events/alerts/2025/09/23/widespread-supply-chain-compromise-impacting-npm-ecosystem>
- <https://github.com/microsoft/typescript-go/releases.atom>

### model-compiler-3: serde cannot be the validating boundary: it stops at the first error, accepts null, and its schema will not equal the zod-generated one

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| risk | high | S1, S13, S4 | weakened | high |

**Concerns:** inside-the-compiler.md 'Data structures' (Spanned parse, Errors) and 'Alignment with YAML and Go'; choices.md rows 'Rust types' and 'Schemas'; conventions.md 'Empty values'; errors-in-ci.md 'How an error finds its line'

If Rust is kept, the alignment design has three gaps. (1) Fail-fast. deploy-kit's oracle `schema-refusals/every-offending-value.diagnostics.json` requires three unrelated defects in one file all reported (an unknown key, a missing field, a wrong type). zod collects issues, but serde's derived Deserialize returns one error. eserde, the crate that collects several serde errors, supports only JSON and TOML, says YAML is planned, and has not released since 0.1.7 in June 2025. (2) Null. conventions.md says `null` is never valid, but serde maps an explicit `null` to `None` for `Option<T>` unless every such field has a custom deserializer. (3) Drift test. The committed schemas are generated by zod's `z.toJSONSchema` (deploy-kit src/model/json-schema.ts). A schemars 1.x schema derived from hand-written types will not be structurally equal to them ($defs naming, enum and Option encoding), so 'generate a schema and require it to equal the committed one' fails on day one. Fixing that means editing Locked contracts. There is also a smaller inconsistency: the oracles and the TypeScript CLI use RFC 6901 JSON Pointers with indices (`#/applications/0/processes/0/image`), while errors-in-ci.md shows a dotted, id-keyed path (`applications.api.dependencies[0]`).

**Recommendation.** Make the committed JSON Schema the validator, not just the documentation. Parse YAML into a spanned tree, validate that tree against the committed Draft 2020-12 schema with the `jsonschema` crate (0.60.0, released 2026-10-22), collect every error with its instance location as a JSON Pointer, and run serde only on input that is already valid. That gives all-errors reporting, refuses null by schema, and makes Rust, Go and editors enforce the same contract. Replace the byte-equality drift test with a corpus-agreement test: every valid and invalid corpus document must get the same verdict from the schema and from serde, plus proptest cases generated from the schema (research summary row 8, currently Open). Keep RFC 6901 as the one path syntax in diagnostics, result.json and RFC 9457 problems, and fix the example in errors-in-ci.md. Render human labels (the Application id) in the message, not in the path.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| jsonschema crate (validate before serde) | 0.60.0, 2026-10-22; about 32M downloads in 90 days | Every error, with instance paths. One more dependency, and error text must be mapped to codes. |
| boon (JSON Schema validator) | 0.6.1, Jan 2025 | Good output formats. Releases are slower. |
| eserde | 0.1.7, Jun 2025; JSON and TOML only | Collects serde errors, but has no YAML support and looks stalled. |
| typify (generate Rust types from the schemas) | 0.8.0, 2026-10-14 | Removes drift by construction. Generated types are less idiomatic; choices.md rejected this for the authored model, but it may suit the result.json wire types. |

**Verification (weakened).** The individual facts check out. The oracle every-offending-value requires three paths (/applications/0/colour, /applications/0/processes/0/image, /applications/0/processes/0/provides/http). Derived serde Deserialize stops at the first error. serde-saphyr's README says `'Option<T>` continues to accept null as None'. eserde supports only JSON and TOML (0.1.7, 2025-06-24). The committed schemas come from z.toJSONSchema. errors-in-ci.md shows the dotted path `applications.api.dependencies[0]`, while the oracles use RFC 6901. The drift-test point is stronger than the finding says. deploy-kit's own [deploy-kit ADR 0088](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/architecture/0088-the-committed-schemas-and-their-corpus-are-the-contract.md) already rules that byte equality 'would tie every future implementation to zod's output' and makes the hand-written accept/refuse corpus the contract. So inside-the-compiler.md 'Alignment with YAML and Go' contradicts a record the design imports. That also means the corpus-agreement test is not a new proposal; deploy-kit already has spec/v1/schemas/corpus/*. The design does not actually say serde is the validator. It says the spanned tree goes 'then into the typed model' and that no step stops at the first error, so a hand-written conversion from the spanned tree is open. The main recommendation, making the JSON Schema the validator, does not fully follow. [deploy-kit ADR 0088](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/architecture/0088-the-committed-schemas-and-their-corpus-are-the-contract.md) notes that zod drops refinements when it generates a schema, so the schema states less than the model and cannot be the only validator. The jsonschema crate reports `required` at the parent object, but the missing-field oracle wants the path where the field would be, so the paths need mapping. Its default features pull in reqwest for remote refs, which has to be turned off for supply chain. typify 0.8.0 shipped 2026-09-09; the 2026-10-14 release is 0.10.0-alpha.3.

**Corrections.** The schema-drift fix already exists as deploy-kit [deploy-kit ADR 0088](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/architecture/0088-the-committed-schemas-and-their-corpus-are-the-contract.md) and its corpus. The design page should adopt it rather than invent it. The committed schema cannot be the only validator, because zod refinements are absent from it. jsonschema's instance paths for required and additionalProperties do not match the oracle paths without mapping. The design leaves the tree-to-model step open rather than mandating serde derive. typify's 2026-10-14 release is 0.10.0-alpha.3; stable 0.8.0 is from 2026-09-09.

Sources:

- `JorisJonkers-dev/deploy-kit spec/v1/examples/schema-refusals/every-offending-value.diagnostics.json`
- `JorisJonkers-dev/deploy-kit src/model/json-schema.ts`
- <https://github.com/mainmatter/eserde>
- <https://crates.io/crates/jsonschema>
- <https://docs.rs/schemars/latest/schemars/generate/struct.SchemaSettings.html>
- <https://crates.io/crates/typify>
- <https://www.rfc-editor.org/rfc/rfc6901>
- `JorisJonkers-dev/deploy-kit docs/adr/architecture/0088-the-committed-schemas-and-their-corpus-are-the-contract.md (origin/main)`
- `JorisJonkers-dev/deploy-kit spec/v1/examples/schema-refusals/README.md`
- <https://docs.rs/jsonschema/latest/jsonschema/>
- <https://github.com/bourumir-wyngs/serde-saphyr>
- <https://crates.io/api/v1/crates/typify>

### model-compiler-4: New model concepts have no slot in the order of work, which clashes with 'no meaning change before the cutover'

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| missing | high | S13, S14, S9 | confirmed | high |

**Concerns:** models-and-metamodels.md 'New in estate-kit' (Mailboxes, admission and UI roles, Infrastructure Intent, host data); plan/port.md 'Not in scope: Changing what the model means before the cutover'; overview.md 'Order of work'; decisions/README.md 'Writing order'

The metamodel page adds four new concepts: Mailbox, admission with UI roles, Infrastructure Intent, and host data rendered per node. The staged switch also changes pinned inputs: images.lock is sealed into the fragment, participants become Admitted Projects, and pin commits become tags. The port plan forbids meaning changes before the cutover and puts the model rewrite last, after archiving. deploy-kit on main has no Mailbox, and #373 lists 'A generator from Infrastructure Intent to NixOS host configuration' as out of scope. As written, the host applier, mail provisioning and admission can land only after the #373 chain reaches 1.0, or they quietly break the parity rule. The plan does not say which. The pinned-input changes also change rendered Flux sources, so byte parity cannot outlive the first stage of the staged switch, and the plan does not say what proves the later stages.

**Recommendation.** Add a sequencing table to plan/port.md that places each new concept and each pinned-input change in a phase. Mark each as additive (a new optional field or a new document, allowed before the cutover as a minor release) or as a change of meaning (it waits for the rewrite). State the proof for each staged-switch step after the first: reviewed oracle changes plus a shadow diff whose differences are explained. Ship Infrastructure Intent and host data as an additive, separate document so hosts do not wait for #373.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| Additive concepts before the cutover | Compatible with conventions.md's additive-within-a-major rule | Hosts and mail ship early. The parity gate must exclude the new documents. |
| All new concepts after the #373 rewrite | Implied by the current text | Simple, but the host applier and Mailboxes wait for the longest chain in the plan. |

**Verification (confirmed).** Verified. models-and-metamodels.md 'New in estate-kit' lists Mailbox, admission and UI roles, Infrastructure Intent, and host data. plan/port.md 'Not in scope' forbids changing meaning before the cutover. Neither overview.md 'Order of work' nor port.md places any of these concepts in a phase. The decision register's writing order puts model records after the cutover. deploy-kit main has no Mailbox. The staged switch (tags, sealed lock, Admitted Projects) changes rendered Flux sources with no stated proof after the first stage. The recommendation follows, and it costs one table, which suits the one-maintainer constraint.

**Corrections.** The finding understates what #373 already covers. deploy-kit spec chapter 15 already specifies Infrastructure Intent and uses it for placement. #373 user story 50 and step 4 add a step that generates the node contract, label set and host data. Only the NixOS generator is out of scope. #373 also already has the finding's rule: an addition ships first as a 0.x release, and a removal or change of meaning waits for the contract PR. estate-kit needs to adopt that rule and place its concepts against it, not invent it.

Sources:

- `JorisJonkers-dev/estate-kit: docs/design/models-and-metamodels.md`
- `JorisJonkers-dev/estate-kit: docs/plan/port.md`
- <https://github.com/JorisJonkers-dev/deploy-kit/issues/373>
- `JorisJonkers-dev/deploy-kit spec/v1/15-infrastructure-intent.md (origin/main, 'What is not built')`

### model-compiler-5: Byte parity hides a bespoke YAML 1.1 emitter and a YAML crate choice that is still open

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| risk | medium | S1, S4, S11 | confirmed | high |

**Concerns:** inside-the-compiler.md 'Data structures' (Spanned parse: 'to be settled by a spike'); overview.md 'Open: which Rust YAML parser keeps source positions'

deploy-kit renders every YAML Deliverable through eemeli/yaml `stringify(..., { lineWidth: 0, version: "1.1", aliasDuplicateObjects: false })` (src/infrastructure/serializer.ts), across 184 YAML and 24 JSON files in the example oracles. Byte parity means the Rust emitter must reproduce that library's YAML 1.1 quoting choices exactly: which plain strings get quoted ('yes', 'on', '0123', timestamps, leading indicators), and how block scalars and their chomping are chosen. No Rust emitter does this. serde-saphyr offers 'quote all strings' or block scalars and an optional yaml_12 mode, so this becomes bespoke code. On input, TypeScript reads YAML 1.2 core through a restricted subset (one document, no anchors, aliases or tags). serde-saphyr is lenient by default and reads YAML 1.1 booleans into bool fields unless `strict_booleans` is set. The candidate crates are moving: serde_yaml is 0.9.34+deprecated, serde_yml is unsound and archived (RUSTSEC-2025-0068), serde-saphyr 2.0.0 shipped 2026-10-13, and saphyr 0.2.2 shipped 2026-10-15. eemeli/yaml itself has 3.0 in prerelease (v3.0.0-2), so the TypeScript baseline may shift too.

**Recommendation.** Before any port, change the serializer in TypeScript to a fully specified canonical style that can be written down in one page, for example strings always double-quoted JSON-style except a small whitelist, and `|` block literals only for multi-line strings. Land the oracle churn once, reviewed. Then the Rust emitter, around 100 lines, implements the spec, and a differential test compares it with the TypeScript one on generated strings. Turn the spike into a Proposed record with explicit criteria: YAML 1.2 core, strict booleans, duplicate keys refused, the anchor, alias and tag refusals reproducible, positions on every node for path-to-line resolution, a budget against resource exhaustion, and no advisory in cargo-deny. Pin eemeli/yaml at 2.x until the port is done.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| saphyr (parser with markers) + own emitter | 0.2.2, 2026-10-15; about 1M downloads in 90 days | Pure Rust YAML 1.2 with positions. Young API. |
| serde-saphyr | 2.0.0, 2026-10-13; about 9M downloads in 90 days; `Spanned<T>`, budgets, duplicate-key policy | Most complete serde path. A major release just landed, and spans are lost when serde buffers (untagged and flatten enums). |
| marked-yaml | 0.8.0, May 2025 | Spanned nodes, simple. Less active. |
| serde_yaml / serde_yml | Deprecated (2024) / unsound, RUSTSEC-2025-0068 | Do not use. |

**Verification (confirmed).** Verified in deploy-kit src/infrastructure/serializer.ts. Every YAML Deliverable goes through yaml's stringify with { aliasDuplicateObjects: false, lineWidth: 0, version: "1.1" }. src/read/yaml.ts refuses multiple documents, anchors, aliases and tags. The crate states also check out on crates.io and RustSec: serde_yaml is 0.9.34+deprecated; serde_yml is unsound and archived (RUSTSEC-2025-0068); serde-saphyr 2.0.0 is from 2026-10-13; saphyr 0.2.2 is from 2026-10-15; marked-yaml 0.8.0 is from 2025-05-26. serde-saphyr reads YAML 1.1 booleans by default unless strict_booleans is set, and only offers 'quote all strings' plus a yaml_12 switch. eemeli/yaml v3.0.0-2 is a prerelease. Byte parity against eemeli's YAML 1.1 quoting is a real, unbudgeted bespoke emitter, and the design names only the parser as open. The finding is relevant only if Rust stays (see model-compiler-1 and -2).

**Corrections.** There are 198 YAML and 24 JSON oracle files under the examples' rendered and expected trees (the finding says 184 YAML). JSON in a ConfigMap is already written as RFC 8785 canonical JSON, so quoting rules affect only the other strings. deploy-kit already pins yaml exactly at 2.9.1, so the 'pin at 2.x' step is already done. Canonicalising the serializer changes every live render's bytes once, which means one Flux reapply of every Project.

Sources:

- `JorisJonkers-dev/deploy-kit src/infrastructure/serializer.ts and src/read/yaml.ts (origin/main)`
- <https://github.com/bourumir-wyngs/serde-saphyr>
- <https://github.com/saphyr-rs/saphyr/releases>
- <https://crates.io/crates/serde_yaml>
- <https://rustsec.org/advisories/RUSTSEC-2025-0068>
- <https://crates.io/crates/marked-yaml>
- <https://github.com/eemeli/yaml/releases>
- `JorisJonkers-dev/deploy-kit package.json (origin/main: yaml 2.9.1 exact)`
- <https://crates.io/api/v1/crates/serde-saphyr>
- <https://github.com/eemeli/yaml/releases.atom>

### model-compiler-6: The registry render cache adds machinery and cannot be faster than recompiling; lockstep versioning also invalidates it on every release

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| weakness | medium | S12, S4, S6, S15 | weakened | medium |

**Concerns:** inside-the-compiler.md 'Caching'; choices.md rows 'Caching' and 'Versioning'; CONTEXT.md 'Render key'

Before rendering each Project, the service asks ghcr for a render keyed by the fragment, Platform Intent and ClusterState digests and the compiler version. Rendering one Project is a pure in-memory step that takes milliseconds in Rust, and about 0.35 s for a whole TypeScript CLI run including startup. Even a cache hit costs a ghcr round trip per Project, about 20 per composition, so the cache adds latency and a failure mode (ghcr down, S7) without saving time. Because the version is lockstep, any estate-kit release, even a UI-only change, changes the compiler version in every key, so every Project misses. Whether a Project then gets a new artifact, signature and tag move depends on reproducible bytes, and that is the property that actually matters.

**Recommendation.** Drop the cache lookup. Always render in memory. Make the OCI artifact reproducible: fixed or input-derived `created` annotations and canonical layer bytes. Skip signing, pushing and moving the tag when the render digest equals the digest the prod tag already names. Keep the Render key, but as a provenance annotation on the render for S15, not as a cache key. If a key must stay, derive it from an output-format version that changes only when oracle files change, not from the lockstep release version.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| Registry lookup keyed by inputs + compiler version (current) | Designed | Avoids recompute, which is already cheap. Adds a network dependency per Project and misses on every release. |
| Recompute always + digest-equality skip | Needs only reproducible artifacts | Simpler and offline-capable. Needs reproducible artifact metadata. |

**Verification (weakened).** The lockstep point is right. inside-the-compiler.md 'Caching' and CONTEXT.md 'Render key' include the compiler version, so any release, even a UI-only one, misses the cache for every Project. Reproducible bytes plus a digest-equality skip is the property that matters. Two parts are overstated. About 20 ghcr manifest lookups cost seconds against a 10-minute p95 budget. And ghcr being down already blocks every deploy, because renders are pushed there, so the cache adds no new S7 failure mode. The recommended skip already exists in what is being ported: deploy-kit spec chapter 55 says 'An unchanged render publishes nothing' and carries the render hash as an annotation. The finding misses a stronger, correctness-level problem. The Render key hashes only the Project's own fragment, Platform Intent, ClusterState and the compiler version. But deploy-kit's ResolvedDeployment pins 'Intent Fragments of every other project', and chapter 55 says a Project's artifact stops depending on other fragments only after #548, #482, #546 and #545 move the catalogs, policy job and routes out of _estate. Until then a cache hit can serve a stale render. A per-Project cache also does not fit 'one composition at a time', since estate-wide checks require composing everything anyway.

**Corrections.** Latency cost is negligible and ghcr is already on the deploy path, so the latency and S7 arguments are weak. The digest-equality skip already exists in deploy-kit spec 55. Missing from the finding: the Render key leaves out other Projects' fragments, which is safe only after deploy-kit's per-Project artifact independence work ([deploy-kit ADR 0116](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/model/0116-a-project-owns-every-object-it-delivers.md), #548, #482, #546, #545) lands.

Sources:

- `JorisJonkers-dev/estate-kit: docs/design/inside-the-compiler.md`
- <https://github.com/opencontainers/image-spec/blob/main/annotations.md>
- `JorisJonkers-dev/deploy-kit spec/v1/55-delivery.md (origin/main, 'An unchanged render publishes nothing'; 'A Project's artifact then never depends on another Project's fragment')`
- `JorisJonkers-dev/deploy-kit spec/v1/20-resolved-deployment.md (pinned inputs diagram: 'Intent Fragments of every other project')`
- `JorisJonkers-dev/estate-kit: docs/diagrams/specs.py (seq-cache)`

### model-compiler-7: The metamodel diagrams are generated from Ecore files that are deleted on 2026-10-30

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| risk | medium | S5, S14, S13 | weakened | high |

**Concerns:** models-and-metamodels.md (intro: 'generated from deploy-kit's emf/bundles/metamodel/model/*.ecore by ../diagrams/metamodels.py'); overview.md 'Order of work' step 1

docs/diagrams/metamodels.py reads `<deploy-kit>/emf/bundles/metamodel/model/*.ecore`. Step 1 of the plan, and #373's sunset, delete `emf/` after the hand-in. From then on, the 30-odd class diagrams that document the model have no source and no check. They will drift from the zod or Rust types and from the committed schemas with the first model change. That breaks AGENTS.md's rule to keep a design page and its diagram in step, and it is the documentation a returning maintainer (S5) or an agent would read first.

**Recommendation.** Before `emf/` goes, repoint metamodels.py at the committed JSON Schemas, which are the language-neutral contract and survive any language choice. Generate one class diagram per concept from the schemas' $defs, keep the colour marks as a separate change list, and add a CI check that regenerates the diagrams and fails on a diff. Alternatively, freeze the current images explicitly as 'deploy-kit 0.31 metamodel, historical'.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| Generate from the committed JSON Schemas | Schemas already committed (spec/v1/schemas, about 150 KB) | Stays true to the contract. Inheritance is less visible than in Ecore. |
| Generate from Rust or TypeScript types | Possible | Ties the docs to one implementation language. |
| Freeze as history | Zero cost | The diagrams stop describing the live model. |

**Verification (weakened).** Verified that docs/diagrams/metamodels.py reads `<deploy-kit>/emf/bundles/metamodel/model/*.ecore`. There are 31 mm-* diagrams. The model-diagrams page names Ecore as its source, and overview step 1 and #373 step 1 delete emf/. Three parts are overstated. (1) The source is not lost: #373 step 1 tags the Task 3 submission commit, so the Ecore files stay reachable at that tag and the script still runs against a checkout of it. (2) No check is lost. CI's Diagrams job checks diagrams.lock against raw/ and src/ only; it never regenerates mm-* from Ecore. (3) The page is a delta, 'what estate-kit changes' against deploy-kit's model, with colour marks. That is a design-time artefact, and the #373 rewrite will supersede it by intent. For one maintainer, labelling the page as a deploy-kit 0.31 snapshot now is the proportionate step. Generating diagrams from the JSON Schemas is worth doing after 1.0, when the schemas settle, not before the rewrite.

**Corrections.** The Ecore sources survive at the Task 3 submission tag. CI never checked the mm-* diagrams against Ecore, so no check is removed. The cheapest correct fix is to mark the page as a historical deploy-kit 0.31 snapshot plus a change delta. Schema-generated diagrams fit after 1.0.

Sources:

- `JorisJonkers-dev/estate-kit: docs/diagrams/metamodels.py`
- <https://github.com/JorisJonkers-dev/deploy-kit/issues/373>
- `JorisJonkers-dev/estate-kit: docs/diagrams/README.md (CI Diagrams job checks diagrams.lock)`
- <https://github.com/JorisJonkers-dev/deploy-kit/issues/373 (step 1: tag the submitted commit)>

### model-compiler-8: Configuration languages and Kubernetes packaging tools were never recorded as rejected; they do not fit the derivation, and that should be written down

| Kind | Severity | Scenarios | Verdict | Confidence |
| --- | --- | --- | --- | --- |
| missing | low | S13, S5, S4 | weakened | medium |

**Concerns:** choices.md (no row for the model language or authoring format); research/prior-art.md (no configuration-language survey)

Neither choices.md nor the research pages consider CUE, KCL, Pkl, Nickel, Jsonnet, Dhall, Timoni, Holos, kro, KubeVela, cdk8s or a Helm chart with a values schema. On the facts, the bespoke model still wins. The model's job is total derivation: grants become Vault policies, edges become network policy, Release Gate inputs, a database catalog, about 100 refusal codes and cross-Project union checks, with no escape hatch and no charts (#373 Implementation Decisions). The packaging tools template objects and leave derivation to the author. kro and KubeVela render in-cluster, which defeats the offline, signed render that Flux verifies. The general-purpose configuration languages could express the schema layer. Their derivation code, however, would lose mutation testing, typed adapters and per-path diagnostics, and several are pre-1.0 or quiet: CUE v0.18.0-rc.1, KCL v0.13.2 (CNCF Sandbox since 2023), Timoni v0.36.0 with a README warning of incompatible API changes, Holos with no release since v0.106.0 in Nov 2025, and Dhall and Jsonnet slow. The one useful idea to borrow is the one finding 3 already proposes: the schema as the validator that reports every error with its location.

**Recommendation.** Add a choices.md row and a short Accepted record: 'Authored YAML plus own compiler; rejected CUE, KCL, Pkl, Nickel (configuration languages), and Timoni, Holos, cdk8s, Helm, kro and KubeVela (packaging or in-cluster), because derivation is total and diagnostics are per path'. Name the condition that would reopen it, for example the model shrinking to templating. Keep publishing the schemas for editors (yaml-language-server `$schema`) so authors get completion without a new language.

| Alternative | Status | Trade-offs |
| --- | --- | --- |
| CUE (+ Timoni / Holos) | CUE v0.18.0-rc.1 (2026-10-15), still 0.x; Timoni v0.36.0 (2026-10-21), README warns of incompatible API changes; Holos last release v0.106.0 (2025-11-24) | Strong validation and JSON Schema import and export. Pre-1.0 Go API, derivation logic awkward, no mutation testing. |
| KCL | v0.13.2 (2026-10-19), CNCF Sandbox | Kubernetes-oriented, Rust core. Small community, and an extra language to learn. |
| Pkl | 0.32.2 (2026-10-21), Apple; Go binding 0.14.0, LSP 0.8.0, no official Rust binding | Good tooling and code generation. A JVM or native binary, and an extra language. |
| Nickel | nickel-lang 2.2.0 (Jun 2026), nickel-lang-core 0.19.0 (Sep 2026) | Contracts with blame, embeddable in Rust. A small ecosystem. |
| kro / KubeVela | kro v0.10.0-rc.0 (Sep 2026), kubernetes-sigs, pre-1.0; KubeVela v1.11.0 (Aug 2026) | Render in-cluster, which conflicts with signed offline renders and Flux as the one applier. |
| cdk8s / Helm 4 with values.schema.json | cdk8s-cli v2.207.70 (2026-10-21); Helm v4.3.1 (2026-10-15) | Templating and packaging, not derivation. Charts are ruled out by the model's own goals. |
| Jsonnet / Dhall | go-jsonnet v0.22.0 (Mar 2026); dhall-haskell 1.42.3 (Sep 2026), slow cadence | Mature but quiet. Weak typing (Jsonnet) or a small community (Dhall). |

**Verification (weakened).** It is true that estate-kit's choices.md and its docs/research pages never name CUE, KCL, Pkl, Nickel, Jsonnet, Dhall, Timoni, Holos, kro, KubeVela or cdk8s. The release facts check out: CUE v0.18.0-rc.1 (2026-10-15), KCL v0.13.2 (2026-10-19), Timoni v0.36.0 (2026-10-21), Holos v0.106.0 (2025-11-24, no release since), kro v0.10.0-rc.0 (2026-09-22), KubeVela v1.11.0 (2026-08-03), Helm v4.3.1 (2026-10-15), go-jsonnet v0.22.0 (2026-03-24). But the survey already exists. deploy-kit docs/research/modelling-languages.md (researched 2026-10-09) compares CUE and Timoni, KCL, Pkl, Jsonnet and Tanka, cdk8s, Nickel, Dhall and KubeVela/OAM against deploy-kit's derivation and cross-Project checks. It also restates the earlier rejection of templating. estate-kit imports deploy-kit with its history, so the gap is only a missing choices.md row and record that cite that page. That is an hour's work, and low severity is right.

**Corrections.** The configuration-language and packaging-tool survey already exists in deploy-kit docs/research/modelling-languages.md (2026-10-09), which is imported into estate-kit. The fix is a choices.md row and record citing it with a reopen condition, not new research.

Sources:

- <https://github.com/cue-lang/cue/releases>
- <https://cuelang.org/docs/concept/how-cue-works-with-json-schema/>
- <https://github.com/kcl-lang/kcl/releases>
- <https://www.cncf.io/projects/kcl/>
- <https://pkl-lang.org/main/current/release-notes/index.html>
- <https://crates.io/crates/nickel-lang>
- <https://github.com/stefanprodan/timoni>
- <https://github.com/holos-run/holos/releases>
- <https://github.com/kubernetes-sigs/kro/releases>
- <https://github.com/kubevela/kubevela/releases>
- <https://github.com/cdk8s-team/cdk8s-cli/releases>
- <https://github.com/helm/helm/releases>
- <https://github.com/google/go-jsonnet/releases>
- <https://github.com/dhall-lang/dhall-haskell/releases>
- <https://github.com/JorisJonkers-dev/deploy-kit/issues/373>
- `JorisJonkers-dev/deploy-kit docs/research/modelling-languages.md (origin/main)`
- <https://github.com/holos-run/holos/releases.atom>
- <https://github.com/cue-lang/cue/releases.atom>

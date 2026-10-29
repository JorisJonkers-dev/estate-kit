# Transformations without a DSL

The compiler is a model-driven chain: authored Intent, checked against its
metamodel, lowered, resolved into a Resolved Deployment, then rendered to
files. The Model-Driven Engineering course taught that chain with Ecore, OCL,
Xtext, ATL, QVT-O and Acceleo, and deploy-kit's coursework implemented it in
them. estate-kit uses none of those tools and writes no language of its own
([record 66](../decisions/0066-transformations-are-plain-rust.md)). This page
says which idea each tool contributed, what went wrong with it in practice,
and the plain-Rust mechanism that keeps the idea.

The sources are the course hand-outs (lectures 1 to 6 and the practicals, in
the private coursework repository), the maintainer's Task 1 and Task 2
reports and the two presentations, and the lessons already drawn in
[lesson candidates](../lesson-candidates.md) (cited by id).

## The chain, and the type at each arrow

| Step | Course term | Input type | Output type | Crate |
| --- | --- | --- | --- | --- |
| read | parse (Xtext phase 1) | YAML text | `Raw<Intent>` with a model path per node | `step-read` |
| link | linking and scoping (Xtext phase 3) | `Raw<Intent>` | `Linked<Intent>`: every reference is an index | `step-read` |
| check | OCL invariants (Xtext phase 4) | `Linked<Intent>`, the input set | `Checked<Intent>`, or diagnostics | `step-check` |
| lower | endogenous, out-place M2M | `Checked<Intent>` | `EffectiveIntent` | `step-lower` |
| compose | union of models | every admitted Project's `EffectiveIntent` | `ComposedSet` | `step-compose` |
| resolve | exogenous M2M, vertical refinement | `ComposedSet`, `PinnedInputSet` | `ResolvedDeployment` plus its `Trace` | `step-resolve` |
| render | M2M into the target vocabulary | `ResolvedDeployment` | `DeliverableSet` | `render-*` |
| serialize | M2T | `DeliverableSet` | bytes, in the canonical format | `serialize` |

Each step is a function of its inputs. `Checked<Intent>` has a constructor
private to `step-check`, so `step-lower` cannot be handed input that skipped
the checks; `EffectiveIntent` is its own type, so `step-resolve` cannot be
handed un-lowered input (CS-4).

## Metamodels are Rust types

Ecore is the class-diagram subset of UML. Every Ecore construct the course
used has a Rust form that the compiler checks:

| Ecore | Rust | What it prevents |
| --- | --- | --- |
| EClass | `struct` | |
| Abstract class with subclasses | `enum` with one struct per variant | QVT's `disjuncts` was not checked for completeness; `match` is |
| EEnum | Closed `enum`, no `Default` | EMF read an unset enum as its first literal and needed an `absent` literal (Task 1); here an optional value is `Option<E>` |
| EDataType (`Fqdn`, `Duration`, `Quantity`) | Newtype with `TryFrom` | Free strings that were "wrong in every app" (MS-6) |
| Multiplicity `1`, `0..1`, `0..*`, `1..*` | `T`, `Option<T>`, `Vec<T>`, `NonEmpty<T>` | |
| Name-unique collection | `BTreeMap<Name, T>` | Duplicates are a diagnostic at construction; order is deterministic |
| Containment | Ownership | EMF's single-container rule silently *moved* a shared declaration to the last Process (Task 2, "The Flattening"); values are cloned, so it cannot happen |
| Non-containment reference | `Ref<Name>` before linking, an index after | Pointers, lifetimes and cycles |
| `eOpposite`, container back-pointers | Not stored; context is passed down or a reverse index is built | Two sides that disagree |
| A field that applies only to some variants | Lives inside that variant | An illegal combination cannot be written |

**Abstract and concrete syntax.** The Rust types are the abstract syntax. The
YAML is one concrete syntax. The committed JSON Schemas and their
accept/refuse corpus are the language-neutral contract, and the types agree
with them on the corpus, one-directionally and diagnostic by diagnostic, not by
byte equality of a generated schema
([deploy-kit ADR 0088](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/architecture/0088-the-committed-schemas-and-their-corpus-are-the-contract.md)).
The Task 1 lesson stands: the model comes first and the syntaxes follow it
(MD-2), and the output gets no third metamodel that restates the target's
schema.

## Read, link, check: what Xtext taught, without Xtext

Xtext splits reading into lexing, parsing, linking and validation, and a
cross-reference is declared in the grammar but established in the linking
phase. The 2024 course project skipped that: references were plain strings,
linked by a derived OCL attribute that guessed the target by camel-casing and
singularising a name. It lost Xtext's free "unknown reference at this
position" error. The 2026 project linked properly and got `E_UNKNOWN_PROCESS`
from the linker.

estate-kit keeps the split:

1. **Read.** `yaml-source` parses YAML 1.2 with a model path and span on every
   node, under a budget, and refuses anchors, aliases, tags, duplicate keys and
   a second document. The tree is checked against the committed JSON Schema,
   collecting every error with its JSON Pointer, and only then converted to
   types. serde never sees invalid input, so it can neither stop at the first
   error nor read `null` as absent
   ([model-compiler-3](../research/review/model-and-compiler.md)).
2. **Link.** Each reference is resolved against an explicit **scope table**
   that says which names are visible from where: Processes within an
   Application, Surfaces across Projects, Tiers and Providers from Platform
   Intent, nodes from Infrastructure Intent. An unknown name is an
   `E_UNKNOWN_*` diagnostic with the nearest candidates as its help line, the
   analogue of Xtext's content assist.
3. **Check.** The invariant table runs (next section).

Diagnostics carry a model path, never a line; the caller resolves the line
([Errors in CI](errors-in-ci.md)).

## Invariants, where OCL was

OCL gave the course a declarative, side-effect-free way to narrow the set of
valid models: `inv`, `pre` and `post`, `derive`, `def`, navigation and the
collection operations. The 2026 project's OCL held 36 invariants, each named
by its diagnostic code with the rejected object's class as its context, and
that naming worked. Three things did not:

- **Cross-document rules passed silently** when a Project file was loaded
  alone, because `X.allInstances()->notEmpty() implies …` guards evaluate to
  true on an empty extent.
- **Uniqueness across every Project document could not be expressed.**
- **Checks that lived in QVT-O as aborts** stopped at the first problem, with
  no location (CS-3).

The Rust form is a table, not a language:

```rust
pub struct Invariant {
    pub code: RefusalCode,       // from the catalogue
    pub context: &'static str,   // the kind of object to fix
    pub scope: Scope,            // Object, Document or InputSet
    pub check: fn(&Linked, &mut Diagnostics),
}

pub static INVARIANTS: &[Invariant] = &[ /* one entry per code */ ];
```

- **Scope is explicit.** An `InputSet` invariant takes the whole input set
  and is only ever run with it; it cannot run on one file and pass.
- **Every invariant runs.** Diagnostics are collected, never thrown.
- **Navigation is iterators.** `select` and `reject` are `filter`, `collect`
  is `map`, `forAll` and `exists` are `all` and `any`, `iterate` is `fold`,
  and `allInstances` is an explicit typed field of the input set.
- **`derive` and `def` are pure functions**, or values computed once in the
  link step and kept in an index, like ATL's cached attribute helpers.
- **The table is checked.** A test walks `INVARIANTS` and the error catalogue
  and fails if a code has no invariant, no negative fixture, or a fixture that
  fires a different code or path ([deploy-kit ADR 0067](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/architecture/0067-every-spec-error-code-is-proved-by-a-test.md)).

## Model-to-model: what QVT-O and ATL taught

Both languages solve the same three problems: which rule makes which target,
how a rule refers to a target another rule made, and how the result is traced
back to its source.

| Problem | ATL | QVT-O | What went wrong in Task 2 | Rust |
| --- | --- | --- | --- | --- |
| One rule per target | Matched rules, one match per rule | One mapping per target type, callers filter with `->select` | Worked; guards (`when`) yield null when they fail, silently | One named function per source-to-target concept, guard first; a failed guard is a filter at the call site or a `match` arm, never a silent null |
| Referring to another rule's target | Allocate every target first, then bind; `resolveTemp` | `resolve`, `resolveone`, `late resolve` | Construction order was "ours to get right" | Two phases: *allocate* an id for every referenceable target (Process, Exposure, Application), then *populate*, looking ids up in the trace |
| Tracing | Implicit trace links | Trace records; objects made in helpers or nested `object`s get none | About one sixth of `resolution.qvto` rebuilt canonical JSON for a digest | An explicit `Trace` that every target is written through, so nothing escapes it; digests come from the canonical emitter |
| Reading the finished target | Not allowed: targets are write-only | The `end` section | Needed for the Revision hash | A separate pass over the finished, immutable value |
| Rule inheritance, disjuncts | `extends` | Inheritance, `disjuncts` | Not used | `enum` dispatch with an exhaustive `match` |
| Shared helpers | Attribute helpers, cached | Queries | Many small queries worked well | Pure functions in a `queries` module; indices built once |
| In-place passes | Refining mode | `inout` | The estate-wide in-place pass coupled every Project; its shared Vault Job stalled them all when it failed | Out-place only; every step returns a new value |
| Abort | Runtime error | `assert fatal` | First problem only, no location | A diagnostic with a code and a path |

The trace is the one generic piece, because every mapping needs the same
machinery ([deploy-kit ADR 0056](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/architecture/0056-the-compiler-is-a-chain-of-typed-models.md): "a generic appears when two mappings need the
same trace machinery, not before"). It lives in the `trace` foundation crate:

```rust
let process_id = trace.allocate::<ResolvedProcess>(&source_path);     // phase 1
let target = trace.resolve_one::<ResolvedProcess>(&route.process)?;   // phase 2, resolveone
let sources = trace.sources_of(target);                               // invresolve
```

There is no `Rule` trait and no rule engine. SiTra, the Java library the
course showed, has a three-method `Rule` and a reflective transformer, and its
own authors advise explicit invocation. One function per mapping, called
explicitly by the step, is the clearest form of that advice.

## Model-to-text: what Acceleo taught

Acceleo's take-home was that model-to-text is the last step of a chain and
that its templates should be simple. The coursework's `render.mtl` held 56
templates and 29 queries, and chose no path itself: the resolution planned
every Deliverable with its path and its source elements, so "every template
fix came from a model change". An earlier design that let each generator
compute values "produced three incompatible documents under one version
identifier" (CS-1).

| Acceleo | Rust |
| --- | --- |
| Polymorphic templates per type | An exhaustive `match` on the Deliverable's kind; a new kind without a renderer does not compile |
| Queries in templates | None; renderers read finished values only |
| `[file(path)]` blocks | `Deliverable { path, owner, kind, sources }`, planned by `step-resolve`; `serialize` checks that each path lies inside its owner's directory, not only that paths are unique |
| `[trace]` blocks | Provenance per rendered field, written to the CLI's JSON output, and shown by `estate-kit explain` (see [Traceability in both directions](#traceability-in-both-directions)) |
| `[protected]` areas | None. Generated files are never hand-edited; generated host data and hand-written Nix modules are separate files ([record 29](../decisions/register.md)) |
| Text templates | None for Kubernetes or host data. Renderers build objects of the narrow `deliverable` model, and one canonical emitter writes the bytes. `generate` (App Roles in five languages) is the one text output, and its templates take a prepared view struct with no logic |

The `deliverable` model declares only the fields the estate sets. Upstream
client types such as `k8s-openapi` were rejected for the same reason as in
deploy-kit: every field is settable, "so an adapter can invent a decision"
([deploy-kit ADR 0058](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/architecture/0058-every-step-links-through-one-trace.md)).
Conformance to the target comes from a test that validates every rendered
object against pinned Kubernetes and CRD schemas (TM-6), then from the
server-side dry-run.

## Traceability in both directions

The course treated traceability as the reason transformations keep links at
all: so that changes, and the errors they cause, can be followed from source
to target and back. Each tool offered part of it, and named its own gap.

| Tool | What it traced | The gap it names | Rust |
| --- | --- | --- | --- |
| Xtext | Each model object to the text it was parsed from; validation names an object and a feature | References linked by plain strings lose "unknown reference here" (the 2024 project) | Model path per node; the link step's scope table gives every unknown name a location |
| OCL and EMF diagnostics | The object to fix, with a computed message and severity; a diagnostic may carry several objects | A guard on `allInstances()` passes silently on one file | A primary location and labelled related locations; invariants scoped to the input set |
| QVT-O | Every mapping's inputs to its outputs; `resolve` forwards, `invresolve` backwards, `late resolve` after all mappings | Objects built in helpers or nested expressions get no trace (QVT 1.3 §8.1.11.1) | Every rendered field has provenance, because the narrow object model's setters take the element reference that caused the value |
| ATL | Matched rules, automatically; `resolveTemp` for non-default targets | Iterative target patterns break the trace | One `Trace`; no construction outside it |
| MOFM2T | `[trace]` ties text regions to model elements; file blocks have ids derived from element identifiers, so a file survives a rename | Protected areas preserved hand edits | Element references keyed by identity, not position; no hand edits |
| QVT Relations | Check-only mode: are two existing models related? | | The drift check: each difference between a live object and its render is reported on the source line |

So the trace is used in both directions on purpose
([record 71](../decisions/0071-every-diagnostic-names-its-locations-and-every-output-traces-to-its-source.md)):

- **Backwards.** A field refused by the dry-run, an admission webhook or a
  CRD schema becomes a diagnostic on the authored line that set it. A live
  object's annotation (Project and element reference) leads the UI from a pod
  or an alert to the element that configured it.
- **Forwards.** `estate-kit explain <element>` lists what an element
  produces, and `estate-kit explain <file>` what produced a file. A plan shows
  each changed object with the lines that changed it.
- **Across Projects.** A conflict's diagnostic has the other Project's
  declaration as a related location, linked at that repository's commit.

Two references keep this stable. The positional **model path** finds a line
at a commit; the id-keyed **element reference** is what the trace and the live
annotations hold, so reordering a list changes neither the annotations nor the
render.

## Testing a transformation

The course graded evidence that a transformation produces the right targets,
and the reports name what failed: oracles written after the run were only
regression snapshots, a few expected files were themselves wrong, and a digest
mismatch could not say what differed. QVT-O was invisible to coverage and
mutation tools (MD-4); Rust is not.

| Test | What it asserts | Where |
| --- | --- | --- |
| One negative fixture per code | Exactly that code at exactly that path; a model refused for the wrong reason fails | `step-check` |
| Per-rule tables | Each derivation rule against the specification's table (own value wins, lists union, nearest level wins) | The rule's own crate |
| Totality (property test) | Any schema-valid input gives a result or coded diagnostics; never a panic, never an uncoded error | `step-resolve` |
| Determinism (property test) | Rendering twice, and with the input documents permuted, gives the same bytes | `compiler` |
| Locality (property test) | Adding an unrelated Project leaves another Project's render unchanged (DO-1) | `compiler` |
| Idempotent lowering | `lower(lower(x)) == lower(x)` | `step-lower` |
| Trace completeness | Every rendered field has an element reference; every authored Process and Exposure is the source of something; nothing is dropped silently | `compiler` |
| Stable references | Reordering every list in an example changes no annotation and no render digest | `compiler` |
| Contracts over source and target | Every allowed egress has a matching ingress (MS-9); every resolved Process has an eligible node or the run failed | `step-resolve` |
| Specification coverage | Every schema type and enum variant is instantiated by some fixture | `testkit` |
| Oracles at the seams | Parsed structure first, then bytes, then digest (TM-2); oracles are read-only to tests and labelled independent or regression (TM-1) | `oracles/` |
| Mutation | Every surviving mutant in a step crate is a missing test or dead code | cargo-mutants, per crate |

[Testing and speed](code-shape-and-speed.md) sets how these run and what each
costs.

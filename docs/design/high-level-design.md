# High-level design

What estate-kit will look like as a system, from the whole picture down to
the classes inside each step, in the order a reader needs them. Each section
links to the page that holds the detail. The decisions behind it are
[record 13](../decisions/0013-every-program-is-rust.md),
[record 18](../decisions/0018-delivery-links-the-compiler.md) and
[record 50](../decisions/0050-six-bounded-contexts-in-five-layers.md) and
[records 67 to 71](../decisions/register.md), all accepted.

Flux stays the one applier, observed closely: Delivery watches every
Project's Kustomizations, OCIRepository and Canary objects, Events in
`flux-system` and the Project's namespaces, and every object in each step's
inventory. It computes each object's health itself by the kstatus rules and
folds each observation into a versioned Rollout event with a sequence number
([record 94](../decisions/0094-flux-stays-the-one-applier-observed-closely-and-an-estate-kit-applier-waits-for-a-review-trigger.md)).

Backups are Kopia snapshots in one locked repository per Environment on an EU
object store, with the WAL archive beside them ([record 115](../decisions/0115-backups-are-kopia-snapshots-in-one-locked-repository-per-environment-on-an-eu-object-store-with-wal-archived-beside-them.md)). Every store of estate data runs on an EU-controlled provider or on owned hardware, with ghcr as the named exception for renders and host tags until milestone M5 ([record 116](../decisions/0116-every-store-of-estate-data-runs-on-an-eu-controlled-provider-or-on-owned-hardware.md)).

A multi-tenant Project keeps its Tenants in shared tables, separated by
row-level security, with one database per Project per Environment
([record 114](../decisions/0114-multi-tenant-projects-keep-their-tenants-in-shared-tables-separated-by-row-level-security.md)).

## 1. The whole system

Six bounded contexts, each a set of crates, and the outside systems each one
talks to. A Project's CI runs the CLI offline and calls Delivery to deploy;
Delivery links the compiler; Flux applies what Delivery publishes; the
components and the host applier act on what the compiler renders. The tenancy
context writes Tenant resources that the components reconcile, and calls the
Tenant hooks of multi-tenant Applications
([record 80](../decisions/0080-a-tenant-is-a-custom-resource-in-a-sixth-bounded-context-tenancy.md)).

![High-level design: every bounded context and what it talks to](../diagrams/png/hld-system.png)

The same system at C4 level 2, with the protocol on each edge:

![C4 containers](../diagrams/png/c4-containers.png)

## 2. The divisions

**By layer.** Every crate is in one layer, and every dependency points down.
`cargo xtask check-layers` refuses any other edge
([record 50](../decisions/0050-six-bounded-contexts-in-five-layers.md)).

![The workspace's layers](../diagrams/png/rust-layers.png)

**By context.** How the contexts depend on each other, and what crosses each
boundary:

![Context map](../diagrams/png/context-map.png)

**By crate.** The compiler's crates, where no step crate depends on another:

![The compiler's crates](../diagrams/png/rust-crates.png)

Delivery's crates, where adapters implement the ports of `delivery-app`:

![Delivery's crates](../diagrams/png/rust-delivery-crates.png)

Every crate, with one line on what it holds, is in
[The crates](rust-workspace.md#the-crates).

## 3. The pipeline, step by step

Each step turns one typed model into the next and adds to one list of
diagnostics; none stops at the first error.

![Each step and the typed model it produces](../diagrams/png/rust-pipeline.png)

**Read, link and check.** YAML is parsed with a model path on every node,
validated against the committed schema, converted, linked through a scope
table, and checked by the invariant table. Each phase has its own type, and
`Checked` can be built only by `step-check`.

![Reading, linking and checking](../diagrams/png/rust-step-read.png)

**Resolve.** One function per source-to-target mapping, in two phases through
one `Trace`: phase 1 allocates an id for every element others refer to, phase
2 fills each target and resolves its references. Revisions are a pass over
the finished value.

![Resolving through one trace](../diagrams/png/rust-step-resolve.png)

**Render and serialize.** Eight renderers behind one trait build Deliverables
of the narrow object model; one serializer checks ownership and writes the
canonical format.

![Eight renderers and one serializer](../diagrams/png/rust-step-render.png)

The types that cross the seams between steps:

![Pipeline types and ports](../diagrams/png/rust-pipeline-types.png)

Why each step has this shape, and which MDE lesson it keeps, is
[Transformations without a DSL](transformations.md).

## 4. Control flow: one deploy

One deploy call, through every crate it touches, from the CI job's request to
the moved tag and the streamed events:

![Control flow: one deploy call through the crates](../diagrams/png/seq-compose-crates.png)

The decisions inside the composition, with every way it can end:

![The decisions inside one composition](../diagrams/png/flow-composition.png)

The rollback, host rollout and component paths are traced the same way in
[End to end, crate by crate](end-to-end.md).

## 5. Delivery's code

The use cases are generic over one bundle of ports, so `main` wires the real
adapters and tests wire the fakes. The queue runs one composition at a time,
through a runner that isolates the compiler.

![Delivery's use cases](../diagrams/png/rust-delivery-app.png)

A rollout is a pure decider: `decide` turns a command into events, `evolve`
folds them into state.

![The rollout decider and its ports](../diagrams/png/rust-rollout.png)

## 6. The drivers

The six components and the host applier share one pure decide step in
`reconcile`: what differs between desired and observed. Each context's `-app`
crate owns its own driver (observe, decide, act one step) and its own ports, with
its own desired, observed and action types.

![The reconcile loop](../diagrams/png/rust-reconcile.png)

The host applier's and the mailbox component's ports:

![The host applier](../diagrams/png/host-applier.png)

![The mailbox component](../diagrams/png/mail-provisioner.png)

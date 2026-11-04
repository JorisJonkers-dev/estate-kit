# Models and metamodels

deploy-kit's three Ecore metamodels, drawn one concept per diagram, with what
estate-kit changes. They are generated from deploy-kit's
`emf/bundles/metamodel/model/*.ecore` by
[`../diagrams/metamodels.py`](../diagrams/metamodels.py). Colour marks the
change: amber changed, red removed, green new; grey is carried over as is.

| Metamodel | Classes | Enums |
| --- | --- | --- |
| Project Intent, including Platform Intent | 86 | 28 |
| Resolved Deployment, including the Deliverable Set | 79 | 10 |
| Pinned inputs | 14 | 1 |
| Infrastructure Intent | none yet | |

## The four Model layers

The metamodel has four Model layers, and each depends only on the ones before
it. They cut across the three models above; they are not a fourth model
([record 88](../decisions/0088-the-metamodel-is-layered-core-profiles-and-component-kinds-provider-facts-estate-instance.md)).

| Model layer | Holds | Written by |
| --- | --- | --- |
| Core | Concepts any estate has: Project, Application, Process, Surface, Exposure, Environment, Volume and its Recovery class. Nothing about a target or a provider | estate-kit |
| Profiles and Component kinds | A Profile per target (Kubernetes, NixOS) with the capabilities it offers; a Component kind per platform component (database grant, bucket, backup, Mailbox, migration) with its closed authored block | estate-kit |
| Provider facts | DNS, registry, object store, secret store, forge, measured node ceilings | The Admin, pinned |
| Estate instance | Project fragments, Platform Intent, Infrastructure Intent | Authors and the Admin |

A value belongs in the core or a Component kind if it changes what is built; in
a Profile if it describes what a target can do; in Provider facts or the Estate
instance if it changes only where, or with what credential
([record 88](../decisions/0088-the-metamodel-is-layered-core-profiles-and-component-kinds-provider-facts-estate-instance.md)).
The core keeps the estate's vocabulary. Mailbox is a Component kind, and the
Tenant's types stay in the tenancy context
([record 80](../decisions/0080-a-tenant-is-a-custom-resource-in-a-sixth-bounded-context-tenancy.md)).

**The core neutrality rule.** No estate fact lives in the core, the profiles or
the compiler's code
([record 85](../decisions/0085-general-purpose-means-no-estate-fact-in-the-core-the-profiles-or-the-compiler-s-code.md)).
`core` names no target or provider and imports neither `profile` nor `kind`. A
Profile declares its capabilities, and `step-resolve` refuses an Intent that
needs one its target lacks, with a diagnostic that names the Profile and the
missing capability
([record 88](../decisions/0088-the-metamodel-is-layered-core-profiles-and-component-kinds-provider-facts-estate-instance.md)).

During the port the layers are modules of `model-intent`: `core`,
`profile::kubernetes`, `profile::nixos` and `kind`. Fields that `spec/v1` 1.0
gives provider meaning, such as `proxied` and `proxiedBy`, stay outside `core`
for parity. After parity the modules become the crates `model-core` and
`model-profile`, and `crates/layers.toml` holds their edges. After the cutover,
Provider facts become a pinned input by digest beside ClusterState, which extends
the input set of
[record 6](../decisions/0006-every-render-is-a-function-of-pinned-inputs.md). A
layer is published apart only when a consumer outside estate-kit needs it
([record 88](../decisions/0088-the-metamodel-is-layered-core-profiles-and-component-kinds-provider-facts-estate-instance.md)).

## New in estate-kit

![New: Mailboxes](../diagrams/png/mm-new-mailbox.png)

![New: admission and UI roles](../diagrams/png/mm-new-admission.png)

![New: Infrastructure Intent](../diagrams/png/mm-new-infrastructure.png)

![New: host data, rendered per node](../diagrams/png/mm-new-host-data.png)

## Project Intent

![Project, Application, Process](../diagrams/png/mm-project.png)

![Effective Intent: after lowering](../diagrams/png/mm-effective.png)

![What a Process needs](../diagrams/png/mm-process.png)

![What a Process reaches](../diagrams/png/mm-process-reach.png)

![Probes](../diagrams/png/mm-probes.png)

![Exposure and edges](../diagrams/png/mm-exposure.png)

![Migration](../diagrams/png/mm-migration.png)

![Configuration](../diagrams/png/mm-config.png)

![Grants](../diagrams/png/mm-grants.png)

## Platform Intent

![The Platform document](../diagrams/png/mm-platform.png)

![Policies](../diagrams/png/mm-platform-policies.png)

![Cadences](../diagrams/png/mm-platform-cadence.png)

![Delivery and jobs](../diagrams/png/mm-platform-delivery.png)

![Providers, VPN and GPUs](../diagrams/png/mm-platform-providers.png)

![Libraries](../diagrams/png/mm-platform-libraries.png)

## Resolved Deployment

![The root](../diagrams/png/mm-resolved.png)

![The database catalog](../diagrams/png/mm-resolved-catalog.png)

![An Application and its Release Gate](../diagrams/png/mm-resolved-application.png)

![A Process](../diagrams/png/mm-resolved-process.png)

![What a Process reaches](../diagrams/png/mm-resolved-process-reach.png)

![Probes](../diagrams/png/mm-resolved-probes.png)

![Grants, edges and environment](../diagrams/png/mm-resolved-grants.png)

![Exposure](../diagrams/png/mm-resolved-exposure.png)

![Deliverable Set: every file kind](../diagrams/png/mm-deliverables.png)

## Pinned inputs

![The node contract](../diagrams/png/mm-pinned-nodes.png)

![Images lock and ClusterState](../diagrams/png/mm-pinned-state.png)

![Proofs and assets](../diagrams/png/mm-pinned-proofs.png)

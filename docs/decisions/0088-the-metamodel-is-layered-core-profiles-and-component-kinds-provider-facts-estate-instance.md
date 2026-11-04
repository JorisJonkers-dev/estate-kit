---
status: proposed  # proposed | accepted | locked
date: 2026-11-04
rests-on: [3, 14, 50, 67, 85]
lessons: [MS-1, CS-2]
---

# The metamodel is layered: core, profiles and Component kinds, Provider facts, Estate instance

## Context

The Rust model is being written now from deploy-kit's Ecore metamodels: 86
classes and 28 enums for Project and Platform Intent, 79 classes for the
Resolved Deployment ([Models and metamodels](../design/models-and-metamodels.md)).
It is planned as one crate per model, `model-intent`, `model-effective` and
`model-resolved` ([record 14](0014-the-compiler-is-a-chain-of-typed-models-one-crate-per-step.md)),
with nothing inside them that says which concept is general and which belongs
to one target or one provider.

The architecture evaluation of 2026-11-04 (sections 3.5 and 4.1) found that
the model is specific in three ways, and that two of them are defects:

- **Target.** Tier, listener, `proxiedBy`, L4 addresses, node agents, priority
  classes and mesh enrolment are Kubernetes and k3s concepts wearing model words.
- **Provider.** Cloudflare's 100-second idle close drives `proxied: false`;
  `CF-Connecting-IP` drives `proxiedBy`; ghcr's token model shaped
  [record 9](0009-the-live-render-is-a-signed-registry-tag-per-project-and-environment.md).
  A provider change then changes what a model field means.
- **Estate.** Node names, host paths, gids, CIDRs and backup addresses are this
  estate's facts. Held as pinned, reviewed instance data, they are not a defect.

[Record 85](register.md) sets what general purpose means: no estate fact in
the core, the profiles or the compiler's code. deploy-kit's rule is that
"metamodel" names a language definition, never a layer.

The authored schema, `spec/v1` at 1.0, must not change before parity
([record 67](0067-the-compiler-is-written-to-the-1-0-contract.md)), and the
crate graph is held by `crates/layers.toml`
([record 50](0050-six-bounded-contexts-in-five-layers.md)). Splitting crates
during the port would change that file and its checks in the riskiest phase
(the evaluation, section 4.8). An architecture that a check does not read
drifts from the code (CS-2).

## Decision

The metamodel has four Model layers, and each depends only on the ones before
it. The layers cut across the three models of
[record 3](0003-three-models-intent-resolved-deployment-deliverable-set.md);
they are not a fourth model.

| Model layer | Holds | Written by |
| --- | --- | --- |
| Core | Concepts any estate has: Project, Application, Process, Surface, Exposure, Environment, Volume and its Recovery class. Nothing about a target or a provider | estate-kit |
| Profiles and Component kinds | A Profile per target (Kubernetes, NixOS) with the capabilities it offers; a Component kind per platform component (database grant, bucket, backup, Mailbox, migration) with its closed authored block | estate-kit |
| Provider facts | DNS, registry, object store, secret store, forge, measured node ceilings | The Admin, pinned |
| Estate instance | Project fragments, Platform Intent, Infrastructure Intent | Authors and the Admin |

A value belongs in the core or a Component kind if it changes what is built;
in a Profile if it describes what a target can do; in Provider facts or the
Estate instance if it changes only where, or with what credential. The core
keeps the estate's vocabulary. Mailbox is a Component kind, and the Tenant's
types stay in the tenancy context
([record 80](0080-a-tenant-is-a-custom-resource-in-a-sixth-bounded-context-tenancy.md)).
A Profile declares its capabilities, and `step-resolve` refuses an Intent that
needs one its target lacks, with a diagnostic that names the Profile and the
missing capability.

During the port the layers are modules of `model-intent`: `core`,
`profile::kubernetes`, `profile::nixos` and `kind`. `core` names no target or
provider and imports neither `profile` nor `kind`. Fields that `spec/v1` 1.0
gives provider meaning, such as `proxied` and `proxiedBy`, stay for parity and
live outside `core`. After parity the modules become the crates `model-core`
and `model-profile`, and `crates/layers.toml` holds their edges. After the
cutover, Provider facts become a pinned input by digest beside ClusterState,
which extends [record 6](0006-every-render-is-a-function-of-pinned-inputs.md)'s
input set; that lands with the split of Platform Intent in
[record 91](0091-platform-intent-is-split-by-concern-and-each-document-validates-alone.md).
A layer is published apart, with its own Contract major
([record 89](0089-every-persisted-or-externally-read-contract-has-its-own-identifier-contract-major-and-supported-range.md)),
only when a consumer outside estate-kit needs it. This extends
[record 14](0014-the-compiler-is-a-chain-of-typed-models-one-crate-per-step.md)'s
list of model crates.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Port the Ecore metamodel as one flat model | Target and provider words keep their model meaning; a provider change is a model change | The two defects the evaluation found stay |
| Split the crates now, during the port | `layers.toml` and the xtask checks change while parity is being chased | A module check gives the same seam at less risk |
| Publish each layer as its own versioned artifact now | Release and version machinery with no consumer | Publication waits for a consumer |
| Tenant and Mailbox in the core | The core presumes every estate is multi-tenant and runs mail | A core that presumes them is not neutral |
| Rename the core concepts to a neutral `Component` | Discards the terms `CONTEXT.md` makes normative; a translation layer in a shadow whose exit is parity | The estate's words stay |
| A plugin ABI, scripting language or user templates for kinds and targets | A language to design and secure; "Borg, Omega, and Kubernetes" (2016) on configuration languages that grow Turing-complete | Extensions are crates chosen at build time |
| A `Raw` deliverable as an escape hatch | Any decision can reach the Deliverable Set untyped | A field the model cannot express cannot be set by an adapter ([deploy-kit ADR 0058](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/architecture/0058-every-step-links-through-one-trace.md)) |

## Consequences

- Easier: a reviewer can tell from a type's module whether it is general; a
  new target or Component kind has a place to go; a provider move becomes data.
- Harder: every new field must choose its layer as well as its model; the
  provider-shaped fields of `spec/v1` live outside `core` until 2.0; the crate
  split after parity is a pull request of its own.
- Forbidden: a target or provider word in `core`; `core` importing a Profile or
  a Component kind; a capability used without a Profile that declares it; a
  `Raw` deliverable.

## Confirmation

The **Core neutrality check** fails when `core` (later `model-core`) names a
word from the committed list of target and provider words, or imports
`profile` or `kind`, with one failing fixture per rule. The **Profile
capability refusal fixtures** fail when an Intent needing a capability its
Profile lacks is accepted, or when the diagnostic omits the Profile or the
capability. After the split, **`cargo xtask check-layers`** holds the edges
between `model-core` and `model-profile`. Which concept goes in which layer is
a review rule, held by no check.

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

# Design

One page per concern. Decisions in [`../decisions/`](../decisions/README.md)
are normative over these pages: where a page and a record disagree, the record
wins and the page is what gets fixed. Diagrams come from
[`../diagrams/`](../diagrams/README.md).

| Page | What it covers |
| --- | --- |
| [Overview](overview.md) | What estate-kit is, its parts, the C4 context and containers, the order of work, risks |
| [Where state lives](where-state-lives.md) | Every fact and where it is kept; deployment; each stage's inputs; Platform Intent push; drift check |
| [Releasing a Project](releasing.md) | `validate` and `deploy`, the dry-run, use cases 1 to 4, sequences, rollout states, failure paths |
| [Operating the estate](operating.md) | Use cases 5 to 9: pause, roll back, admit, apply, gate; Project states |
| [Hosts](hosts.md) | Infrastructure Intent, host data, the host applier, node order, maintenance windows, use cases 10 to 12 |
| [Mail and components](mail-and-components.md) | The three components, Mailboxes, use case 13 |
| [Identity and access](identity-and-access.md) | OIDC for every caller |
| [Security](security.md) | Trust boundaries, STRIDE per boundary, the authorization matrix |
| [Errors in CI](errors-in-ci.md) | How an error reaches its YAML line |
| [Conventions](conventions.md) | API contract, errors, delivery semantics, primitives, retention, telemetry, configuration, contract evolution, bounded contexts |
| [Models and metamodels](models-and-metamodels.md) | deploy-kit's metamodels, drawn per concept, marked with what changes |
| [Inside the compiler](inside-the-compiler.md) | Crates, pipeline, types, alignment with YAML and Go, caching |
| [Inside the service](inside-the-service.md) | Packages, the rollout core, the event log |
| [Code shape and speed](code-shape-and-speed.md) | File rules, fakes, speed budgets, mutation testing |

The [plan](../plan/port.md) orders the work, and the
[lesson candidates](../lesson-candidates.md) feed the records.

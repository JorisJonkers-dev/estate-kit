---
status: accepted  # proposed | accepted | locked
date: 2026-11-04
rests-on: [43, 48, 50, 54]
amends: [43]
lessons: []
---

# Every UI action is a CLI command with the same identifier

## Context

The estate has three surfaces for people and agents: the Vue UI, the
`estate-kit` CLI and the API behind both. [Operating the estate](../design/operating.md)
says Operators act through the UI. Coding agents work in this repository and
cannot use a browser; CI has only a terminal. The architecture evaluation of
2026-11-04 (sections 10.1 and 10.2) gives the CLI "everything, scriptable",
says every mutating UI route has a CLI equivalent, and that every UI action is
also a CLI command so that an agent never needs the UI.

Delivery's API is one committed OpenAPI 3.1 document, and the Vue client is
generated from it
([record 43](0043-the-delivery-api-is-an-openapi-3-1-contract.md)). The CLI's
`--json` output has a committed schema
([record 48](0048-the-cli-s-json-output-has-a-committed-schema.md)). Every
route has a row in the authorization matrix
([record 54](0054-every-trust-boundary-has-a-threat-table-and-every-route-an-authorization-row.md)).
Observation serves the UI and its own read views and Silences from its own
binary ([record 50](0050-six-bounded-contexts-in-five-layers.md)), and no
record gives its API a committed document.

Nothing ties a button in the UI to a command in the CLI. A route can gain a UI
action with no command, and the two can drift in name and in what they send.

## Decision

Every action the UI offers, a read or a write, calls one operation of a
committed OpenAPI document, and the CLI has a command that calls the same
operation. The operation's `operationId` is the one identifier of the action:
the UI action carries it, the CLI command's words joined by hyphens spell it
(`estate-kit tenant suspend` is `tenant-suspend`), and its row in the
authorization matrix is keyed by it. An `operationId` is not an Operation id,
which names one deploy.

This extends [record 43](0043-the-delivery-api-is-an-openapi-3-1-contract.md)
to Observation: the routes the UI calls on Observation, its views and its
Silences, are described in Observation's own committed OpenAPI document, under
the same rules. That document is a contract, Locked like Delivery's: changing
it needs the maintainer's approval in the pull request. The CLI may have
commands the UI lacks, such as `validate` and
`plan`, which run offline. The UI may not have an action the CLI lacks.
[Operating the estate](../design/operating.md) now says Operators
act through the UI or the CLI.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| CLI commands named freely, with a mapping table | A second list of names to keep in step | One identifier needs no mapping |
| Only mutating actions need a CLI command | An agent cannot read what the UI shows: rollout history, Tenant state, Silences | Agents and CI read as much as they write |
| Delivery's API only; Observation's views stay UI only | Silences and the read views need a browser | Observation's routes are where the reads are |
| Observation's routes added to Delivery's document | One document for two processes, each released and versioned on its own | Each context publishes its own contract |
| The CLI drives the UI's own client code | Two clients share browser concerns and a build | The OpenAPI document already gives both the same operations |

## Consequences

- Easier: an agent or a CI job can do anything the maintainer does in the UI;
  one name finds the route, the button, the command and the authorization row.
- Harder: Observation gets a committed API document, Locked like Delivery's;
  every new UI action needs its CLI command in the same pull request; an
  `operationId` becomes a name users type, so it must read well.
- Forbidden: a UI action with no CLI command; a CLI command whose name spells
  no `operationId`; a UI action that calls a route outside a committed
  document.

## Confirmation

The **UI and CLI parity test** fails when an `operationId` the UI's generated
client calls has no CLI command that spells it, or a CLI command that calls the
API spells an `operationId` no committed document holds. The **OpenAPI route
contract test** and the **OpenAPI lint** hold Observation's document as they
hold Delivery's. The **Authorization matrix test** keeps each `operationId`
matched to its row, and the **UI stub validation** keeps the UI's calls within
the documents. That a change to either document needs the maintainer's
approval is a review rule.

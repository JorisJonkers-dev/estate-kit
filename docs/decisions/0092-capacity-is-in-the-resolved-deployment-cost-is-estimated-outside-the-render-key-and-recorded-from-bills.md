---
status: accepted  # proposed | accepted | locked
date: 2026-11-04
rests-on: [3, 6, 50, 68, 74]
lessons: [MS-10, CS-5]
---

# Capacity is in the Resolved Deployment; cost is estimated outside the Render key and recorded from bills

## Context

The maintainer wants the estate cheap, and as serverless as it can be, on owned
machines and rented VPSes across providers. No record, design page or check
prices anything; the one cost arithmetic in the repository is in a research
note (the architecture evaluation of 2026-11-04, sections 2.2 and 3.19). The
cost of estate-kit's own control plane has not been measured either (section 8).

What the platform already knows is capacity. Placement decides which node runs
each Process, and it must sum the requests per node, because a check of one
Process at a time accepts placements that overcommit a node (MS-10). Those are
decisions, so they belong in the Resolved Deployment
([record 3](0003-three-models-intent-resolved-deployment-deliverable-set.md)).

A render reads a closed set of pinned inputs, and their digest is the Render
key ([record 6](0006-every-render-is-a-function-of-pinned-inputs.md); CS-5).
A price in those inputs would make every price change re-render and re-publish
every Project, though nothing built would change. The evaluation's first
version put a projected cost in the Resolved Deployment; its critics refused
that for this reason (section 12.6).

"ABACUS: A FinOps Service for Cloud Cost Optimization" (2024) tells teams the
expected cost of a deployment before resources are created, from
infrastructure as code, and blocks new deployments when a budget is exceeded.
Whether idling saves money depends on load shape: "Analysis of
cost-efficiency of serverless approaches" (2025) reviews 34 studies and finds
17 parameters that decide it, and the estate has not measured its load.

Observation shows what runs and holds no credential that can deploy
([record 50](0050-six-bounded-contexts-in-five-layers.md)). Its writes are
named in [record 74](0074-the-release-gate-and-observation-each-have-a-named-write.md),
and nothing else in it writes.

## Decision

The Resolved Deployment carries a capacity report: for each node, the CPU,
memory and disk its placed Processes request, against the node's totals, by
Project and Environment. It holds no price. It lands as an additive release
after parity, as [record 67](0067-the-compiler-is-written-to-the-1-0-contract.md)
requires of any new field.

`estate-kit plan` prints the capacity change and a cost estimate. The estimate
is computed in the compiler context's application layer from the capacity
report and a price table the Admin keeps in the Estate instance. The price
table is never a render input and never in the Render key, so a price change
re-renders nothing. The estimate states its assumptions, gives a range, and
reports a resource with no price as unknown, never as zero. Observation keeps a
cost ledger in its own Postgres schema: the bills as recorded and the capacity
per Project, including estate-kit's own processes, whose resident memory is
measured in the shadow. This amends
[record 74](0074-the-release-gate-and-observation-each-have-a-named-write.md)
by one write: Observation appends ledger rows to its own schema, with a role
for that schema only and no Lease.

Bills reach the ledger two ways. Observation has a billing port, with one
read-only adapter per provider; each adapter reads its provider's bills with a
read-only billing credential from Vault. A provider without an adapter is
covered by a CSV of its bills that the maintainer imports each month. An
adapter is preferred wherever a provider offers a read-only billing API. The
billing port has its fake and contract suite, as
[record 68](0068-every-fake-passes-its-port-s-contract-suite.md) requires of
every port. The billing credentials are the only credentials Observation holds
outside the cluster, and they can only read.

A budget only warns until the ledger has measured the estimate's error against
the bills over 3 months. After that, the maintainer decides for each budget
whether it may refuse a deploy. A budget that may refuse does so only by more
than the measured error; one the maintainer has not allowed to refuse keeps
warning.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| A projected cost in the Resolved Deployment, prices as pinned inputs | Every price change re-renders and re-publishes every Project | Prices change nothing that is built |
| No estimate; only a ledger of bills | Cost is seen a month after the change that caused it | An estimate before deploy is ordinary practice (ABACUS, 2024) |
| An estimate with no ledger | Nothing ever measures how wrong the estimate is | A budget that refuses on an unmeasured estimate refuses at random |
| Budgets refuse from the first release | Deploys are blocked by an estimate whose error is unknown | Refusal waits for 3 months of measured error |
| Every budget refuses once its error is measured | A budget meant to inform blocks deploys | The maintainer allows refusal per budget |
| Bills only by a monthly import | A month's work by hand for every provider that has a billing API | Automation is preferred; the import covers providers without an adapter |
| Bills only through provider adapters | A provider with no read-only billing API is never recorded | The CSV import covers it |
| A Cost bounded context or a cost service | A seventh context and a deployable for one report | The estimate is a function; the ledger fits Observation |
| Prices in Platform Intent | A price edit is a Platform Intent change, pushed and composed | The price table is instance data outside every render input |

## Consequences

- Easier: every plan shows what a change asks of the nodes and roughly what it
  costs; the ledger says whether a node or a VPS could go, which is what the
  planned scale-to-zero trial on one stateless Application will be measured
  with. That trial, and which product it uses, are not decided here.
- Harder: a price table to keep current by hand; an adapter and a read-only
  billing credential per provider, and a monthly import for the rest; an
  estimate that is a range, not a number; one more write in Observation.
- Forbidden: a price in any render input or in the Render key; an unknown price
  estimated as zero; a budget that refuses before its estimate's error has
  been measured over 3 months, or that the maintainer has not allowed to
  refuse; a billing credential that can do more than read; a ledger write
  outside Observation's own schema.

## Confirmation

The **Price independence test** fails when changing only the price table
changes a render byte or the Render key, or when a step crate reads the price
table. The **Capacity report test** fails when a node's total in the report
differs from the sum of the requests placed on it. The **Cost estimate unknowns
test** fails when a resource without a price is estimated as zero or the
estimate omits its assumptions. The **Budget refusal precondition test** fails
when a budget refuses a deploy while the ledger holds less than 3 months of
measured error for that estimate, when a budget the maintainer has not allowed
to refuse refuses, or when a budget refuses by less than the measured error.
The **Port contract script** fails when the billing port lacks its fake or
its contract suite. The **RBAC fixtures** hold Observation to its named
writes, the ledger now among them. That each billing credential can only read
is a review rule.

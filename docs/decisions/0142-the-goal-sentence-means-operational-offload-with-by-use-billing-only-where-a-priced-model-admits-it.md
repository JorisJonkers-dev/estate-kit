---
status: accepted  # proposed | accepted | locked | superseded
date: 2026-11-05
rests-on: [1, 31, 92, 116]
lessons: [DR-2, TM-4]
---

# The goal sentence means operational offload, with by-use billing only where a priced model admits it

## Context

The maintainer wants the estate "cheap, and as serverless as it can be"
([record 92](0092-capacity-is-in-the-resolved-deployment-cost-is-estimated-outside-the-render-key-and-recorded-from-bills.md));
the phrase sits in that record's Context with no meaning. Nothing says whether
it promises serverless products, or names what it gives up when a provider
cannot serve the estate's needs. Owned hardware already carries the host
closures' builder, because no provider's serverless job builds a closure
([record 31](0031-host-closures-are-built-in-ci-and-cached-outside-the-cluster.md)),
and [record 116](0116-every-store-of-estate-data-runs-on-an-eu-controlled-provider-or-on-owned-hardware.md)
narrows who may hold the estate's stores. The design review of 2026-11-04 (its
goal-sentence question) asked for the sentence to be honest, and the
maintainer approved it the same day: operational offload, with by-use billing
only where a priced model admits it.

## Decision

**The goal is operational offload.** "As serverless as it can be" is a goal
about the estate's attention, not about a product category: the estate, run by
one maintainer's hours
([record 1](0001-one-maintainer-one-cluster-one-estate.md)), does not operate
a mechanism an EU-controlled provider
([record 116](0116-every-store-of-estate-data-runs-on-an-eu-controlled-provider-or-on-owned-hardware.md))
offers managed and priced by use. When a store or a platform mechanism is
chosen, a managed offering wins, and owned hardware is the exception a priced
model refuses, not a preference: the builder of
[record 31](0031-host-closures-are-built-in-ci-and-cached-outside-the-cluster.md),
whose job needs disk, a warm store and KVM no provider's serverless job gives.

**By-use billing only where a priced model admits it.** The estate pays for
what it uses where a priced model prices it that way; it does not demand a
per-request meter where the provider prices the month, nor keep a fixed
rented server as a goal in itself. The bills, whatever their shape, reach the
cost ledger of [record 92](0092-capacity-is-in-the-resolved-deployment-cost-is-estimated-outside-the-render-key-and-recorded-from-bills.md),
so the goal is measured where the money goes.

**The provider register states the reason.** Each entry of the provider
register says whether the provider manages the mechanism, and a self-managed
entry states the reason a priced model refuses it. The
**Offload preference lint** fails when an entry runs a mechanism self-managed
where its provider offers it managed and billed by use, or when a self-managed
entry names no reason.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Serverless products wherever they exist | The estate's needs (disk, KVM, EU control) sit outside many of them; the goal becomes a slogan the estate breaks | The goal is stated as offload, with its exceptions written down |
| Owned hardware as the goal, servers rented by the month | Attention spent operating what a provider will manage; a fixed bill for idle capacity | Operational offload is the goal; by-use only where priced |
| No goal sentence, each store chosen on its own | Each provider register entry re-argues the same preference | One sentence, written down and linted, answers them all |
| A goal with no register reason, review only | An entry drifts to self-managed with none the wiser | A review rule here is not enough: the register can state the reason, so a lint can read it |

## Consequences

- Easier: a new store or mechanism has one preference sentence to follow; the
  provider register entry states its reason, so no register entry re-argues
  the goal.
- Harder: each provider register entry states managed or self-managed, and
  its reason; the offload goes as far as the EU-controlled providers' offers
  do, which the maintainer must judge at each entry.
- Forbidden: an estate-operated mechanism where its provider offers it managed
  and billed by use, with no reason stated; a self-managed register entry with
  no reason a priced model refuses it; a store at a provider neither
  EU-controlled nor owned.

## Confirmation

The **Offload preference lint** fails when an entry of the provider register
runs a mechanism self-managed where its provider offers it managed and billed
by use, or when a self-managed entry names no reason a priced model refuses.
Whether a provider's offer is genuinely managed, and whether the refusal it
gives is honest, are review rules at the register entry, backed by the bills
in the cost ledger of [record 92](0092-capacity-is-in-the-resolved-deployment-cost-is-estimated-outside-the-render-key-and-recorded-from-bills.md).

---
status: accepted  # proposed | accepted | locked
date: 2026-10-30
rests-on: [1, 3]
lessons: [MS-4]
---

# Contention decides authority

## Context

The estate had no test for where a field belongs, so fields landed wherever the
change that introduced them was made. One hostname was declared authoritatively
in seven places across three repositories, and two conformance tests existed
only to notice when the seven disagreed. The guard was cheaper than the fix.

## Decision

Contention decides who arbitrates a value, not who writes it. A value that must
be unique across the estate, or that draws on a shared finite resource, is
arbitrated by the platform: the Application states a requirement, and the
platform decides whether it fits and where. Every other value is declared by the
Application and carried through untouched. The test is one question, does the
value contend, and it splits every field of
[Intent and the Resolved Deployment](0003-three-models-intent-resolved-deployment-deliverable-set.md)
with no third category.

A contention is refused, not resolved by order of arrival: the same Mailbox
local part in two Projects, or a hostname two Applications claim, is a
diagnostic that points at both authored lines
([Mail and components](../design/mail-and-components.md)). Each such value has
exactly one owner.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Whoever is paged for a value declares it | A negotiation per field, rerun when the rota changes | An implicit rule while the hostname gathered seven declarations |
| Whoever edits a value most declares it | Authority moves silently as an Application matures | The other implicit rule; declarations landed where the change was |
| A table of authority with no generating rule | Each new field is a table negotiation | The table drifts and becomes the decision |
| Authors only declare, platform never arbitrates | A contended number nobody may write is a number nobody writes | Resource requests would stay unset |

## Consequences

- Easier: a new field answers one question before it enters a schema.
- Harder: the platform must hold the pools it arbitrates, such as node capacity
  and the hostname space, and refuse what does not fit.
- Forbidden: an Application declaring a unique or pooled value on its own
  authority; a second declaration site for a contended value; a field that the
  test cannot place.

## Confirmation

Each contended value has a negative fixture in the corpus that fires its
contention diagnostic (the **Contention fixtures**), and the authority table on the Resolved Deployment page
cites, for every row, which half of the rule placed it. A row without that
citation fails the review of the schema change.

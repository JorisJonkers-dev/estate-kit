---
status: accepted  # proposed | accepted | locked | superseded
date: 2026-11-05
rests-on: [111]
lessons: []
---

# A wording fix is a dated Revised line, a change of rule is an amending record, and a Locked change needs the contract-change label

## Context

The 2026-11-04 design review found that records were fixed in two ways with
no rule between them. Some wording fixes were silent edits to an Accepted
record, so a reader could not tell a corrected typo from a changed rule. Other
changes of rule were made by editing the record, so the old decision vanished.
[Record 111](0111-decision-status-and-enforcement-status-are-separate.md) and
the [records README](README.md#how-records-are-kept) say a Locked record and a
contract are not the agent's to change, but nothing detects a pull request that
changes one: the rule rested on the agent noticing.

## Decision

A wording fix to an Accepted record (a typo, a clearer sentence, a corrected
link) is edited in place, and the record gains a line under its title,
`Revised: YYYY-MM-DD: <what changed>`. A change of rule, meaning anything
that makes a conforming implementation fail or pass differently, is never a
Revised line: it needs an amending record that declares `amends`, and the
amended record carries its back-link ([record 111](0111-decision-status-and-enforcement-status-are-separate.md)'s
rule for `amends` is held by the Records job).

A Locked change is detected, not remembered. CONTEXT.md defines two Locked
things once each: a [Locked record](../../CONTEXT.md#locked-record) and a
[Locked contract path](../../CONTEXT.md#locked-contract-path). The Contract gate
fails a pull request that changes either, found from the changed paths and the
status a record had on the base, unless the maintainer has applied the
`contract-change` label. The label is the approval, and there is no other.

A silent edit leaves no Revised line, so no script can see it: review and the
pull-request title rule catch it. The records README says so.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Edit Accepted records freely, with the history in git | A reader of the record cannot tell wording from rule without reading the diff | The decision a record states must be readable as it stands |
| Every wording fix is an amending record | A typo costs a record, a register row and a back-link | The register fills with noise and real amendments are hard to find |
| Detect a Locked change by reading the diff for rule changes | Needs a judgement a script cannot make | A script can see a path and a status; the maintainer judges the rest |
| CODEOWNERS review on contract paths | One maintainer, no required reviewers: it blocks nothing | The ruleset requires no approving review; a required check is the gate that exists |

## Consequences

- Easier: a wording fix is cheap and visible; the approval of a Locked change
  is a label the pull request shows.
- Harder: every pull request runs one more job, and the maintainer applies a
  label for each Locked change.
- Forbidden: a Revised line with no date or no sentence; a change of rule
  written as a Revised line; a Locked change merged without the label.

## Confirmation

The **Revised line check** fails on a Revised line with no date, an impossible
date or no sentence, with one failing fixture each. The **Contract gate** fails
a pull request that changes a Locked contract path or a Locked record without
the label, with a failing fixture (changed, no label) and a passing one (label
applied). Both are verified. A silent edit, and a change of rule written as a
Revised line, are held by review.

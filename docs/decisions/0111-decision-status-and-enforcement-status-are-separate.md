---
status: accepted  # proposed | accepted | locked
date: 2026-11-04
rests-on: [1, 37]
amends: [37]
lessons: [TM-4, TM-5, DR-2]
---

# Decision status and Enforcement status are separate, and each check names the mistake it catches

The maintainer added the review value on 2026-11-04 ([#177](https://github.com/JorisJonkers-dev/estate-kit/issues/177)): a record whose Confirmation names no check reads review, never verified. The table of checks also keeps a fourth status, retired, for a check that a later record replaced or removed and whose row stays as history. A retired check holds nothing: a record whose Confirmation names only retired checks reads review.

## Context

[The table of checks](../design/code-shape-and-speed.md#the-checks) names about
a hundred checks. Of those that record Confirmations name, two run today:
Records and Links. CI also runs Diagrams, Record citations, Check tests,
Actionlint, Secret scan, Hygiene, PR title and Site. So "every rule has a
check" is today mostly a plan. The architecture evaluation of 2026-11-04
(sections 3.22, 11.3 and 11.4) calls that normal for a design with no code,
and says the fix is to state it honestly: an Accepted record is a design commitment and may
describe code not yet written; only a Locked record needs its check running.
Its first version proposed that a record's status follow the checks that run,
which would have demoted every Accepted record; the second version dropped
that.

The register's status column holds one thing, the decision. A reader cannot
tell from it whether an Accepted record's checks exist. The table of checks
has a Status column ("runs today", or the issue that builds the check), but no
record or register row shows it. The table's "Fails when" column says what
trips a check, not which maintainer mistake it prevents, which is the test
[record 1](0001-one-maintainer-one-cluster-one-estate.md) sets for every
concept and check. The evaluation rates "check machinery outgrows the code" a
high risk: rules that pass silently, and gates the maintainer resents.

[Record 37](0037-every-gate-has-a-speed-budget-coverage-and-mutation-are-ratchets.md)
says an equivalent mutant is rewritten, not excluded, and holds the number of
exclusions at zero. Whether a mutant is equivalent is undecidable in general,
and some code has no clearer form that kills it. deploy-kit met such mutants
and removed one by rewriting (TM-5). A zero rule over an undecidable category
will break, and when it does it is either bent or worked around.

## Decision

Decision status and Enforcement status are separate. Decision status
(Proposed, Accepted, Locked, Merged into N, Moved to page) says what is
decided, and keeps the meanings in [the decision records](README.md#status).
Enforcement status says whether the checks a record names hold it:

| Enforcement status | Meaning |
| --- | --- |
| planned | The check is a row of the table of checks, with the issue that builds it, and no code yet |
| implemented | The check runs, but outside the required `Pipeline Complete`, or without a negative fixture shown to fail it |
| verified | The check runs inside `Pipeline Complete`, and its negative fixture fails it |
| review | The Confirmation names no check, so the rule is held by review only |

Enforcement status is derived, never written by hand. The Status column of the
table of checks takes these three values, or retired, and a record's Enforcement
status is the lowest among the live checks its Confirmation names in bold. A record that names
no check reads review; it is never verified. The register's enforcement column is derived from the table of checks, and the Records job fails when a row disagrees with its derivation.
An Accepted record may be planned. A Locked record must be verified, which is
the register's rule ("a record that is Locked without a working check is a
defect") made checkable.

Each row of the table of checks names the mistake it catches: the maintainer
mistake that, uncaught, the check would have let through. A check whose
mistake no one can name is a candidate for removal, together with the rule it
holds.

This amends [record 37](0037-every-gate-has-a-speed-budget-coverage-and-mutation-are-ratchets.md):
an equivalent mutant is still rewritten where the code can be made clearer, and
where it cannot, it may be excluded. Each exclusion names the one mutant, says
why it is equivalent, and links the pull request in which the maintainer
reviewed it. The weekly full run reports the count of exclusions; the count is
not held at zero. The rest of that record, the speed budgets and both
ratchets, stands.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| A record's status follows the checks that run (the evaluation's first version) | Every Accepted record of a design with no code is demoted | A decision is a commitment before it is code |
| Keep one status column | A reader cannot tell a running rule from a planned one | The gap is the evaluation's finding |
| Write the enforcement column by hand | It drifts from the table of checks | Derived from one source, it cannot |
| Keep "Fails when" as the only description | A check's purpose is its trigger, and a check that catches no real mistake survives | [Record 1](0001-one-maintainer-one-cluster-one-estate.md) asks every check for its mistake |
| Hold mutation exclusions at zero | The rule breaks on the first mutant with no clearer code, and is then worked around | Reviewed exclusions keep the rule honest |
| Allow exclusions without review | Survivors are hidden instead of fixed | Each exclusion is one mutant, with a reason and a reviewer |

## Consequences

- Easier: a reader sees which rules hold today; Locking a record has a
  mechanical precondition; an equivalent mutant has a legitimate, visible path.
- Harder: each of the hundred rows needs its mistake written, and the Status
  column must be moved to these values; the Records job grows.
- Forbidden: an Enforcement status written by hand; a Locked record whose
  checks are not verified; a check row with no mistake; a mutation exclusion
  without its mutant, its reason and its reviewing pull request.

## Confirmation

The **Enforcement status check** fails when a register row's enforcement
column differs from the status derived from the table of checks, when a Locked
record names a check that is not verified, or when a row of the table of checks
names no mistake. The **Mutation exclusion review** fails when an exclusion in
`.cargo/mutants.toml` lacks its mutant, its reason or the link to its reviewing
pull request. It replaces the **Mutation exclusion count**, whose row of the table of checks is retired.

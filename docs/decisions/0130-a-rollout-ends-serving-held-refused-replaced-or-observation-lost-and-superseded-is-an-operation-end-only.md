---
status: accepted  # proposed | accepted | locked
date: 2026-11-05
rests-on: [23, 96]
amends: [96]
lessons: [MS-6, DO-4]
---

# A Rollout ends Serving, Held, Refused, Replaced or Observation lost, and Superseded is an Operation end only

## Context

[Record 96](0096-a-deploy-is-an-operation-that-ends-serving-held-refused-superseded-or-observation-lost.md)
holds an Operation's five ends and its exit codes, and says what Superseded
means for an Operation. It leaves the Rollout the Operation drove with no list
of its own, so a Rollout that a newer Operation closed before it reached
Serving, Held or Refused has no legal end: the log's fold can never finish.
The design review of 2026-11-04 (the final report's section 15, question 10,
and NR-2) read the outcome types the design holds and found the Rollout and
Operation outcomes written three different ways; nothing told the two lists
apart. The maintainer settled the answer the same day: a Rollout ends Serving,
Held, Refused, Replaced or Observation lost, and Superseded is an Operation
end only. The review's own outcome list kept a boolean Superseded for the
Rollout; every wait needs a deadline, and every Rollout needs exactly one end.

A closed enumeration is one name one thing: the vocabulary holds
[Replaced](../../CONTEXT.md) and [Superseded](../../CONTEXT.md) already, and
MS-6 keeps the set finite. The ends are values a consumer reads — the exit
code, the Deployment status — so DO-4 makes the split matter: a CI author
branches on the Operation's Superseded, a log reader on the Rollout's
Replaced.

## Decision

One table holds both lists:

| Rollout ends | Operation ends |
| --- | --- |
| Serving | Serving |
| Held | Held |
| Refused | Refused |
| Replaced | Superseded |
| Observation lost | Observation lost |

A Rollout ends in exactly one of Serving, Held, Refused, Replaced or Observation lost. An Operation ends in exactly one of Serving, Held, Refused, Superseded or Observation lost
([record 96](0096-a-deploy-is-an-operation-that-ends-serving-held-refused-superseded-or-observation-lost.md)).
The two lists differ in exactly one end each way: Superseded is an Operation
end only — never a Rollout end — and Replaced is a Rollout end only — never an
Operation end. When a newer Operation for the same Project and Environment is
composed in an Operation's place or published over it before it ended, the
older Operation ends Superseded, and a Rollout it had begun and not driven to
Serving, Held or Refused ends Replaced. A Rollout that had already reached one
of those ends keeps it; the newer Operation's own Rollout ends on its own
facts.

This amends [record 96](0096-a-deploy-is-an-operation-that-ends-serving-held-refused-superseded-or-observation-lost.md):
its decision holds the ends and the exit codes of the Operation, which stand
unchanged, and gains the Rollout's own list. The vocabulary's entries
([Serving](../../CONTEXT.md), [Replaced](../../CONTEXT.md), [Superseded](../../CONTEXT.md))
already name the ends, and every page that lists the outcomes
([Releasing](../design/releasing.md) among them) names exactly these.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| [Record 96](0096-a-deploy-is-an-operation-that-ends-serving-held-refused-superseded-or-observation-lost.md) as written, the Rollout sharing the Operation's ends | A Rollout closed by a newer Operation is named Superseded, an end its exit table never offers | The two lists differ in exactly one end each way |
| Three endings for the Rollout, the rest for the Operation, kept page by page | The outcome types written three different ways again; a new end means editing every page by hand | One table here, held by one check |
| Replaced also ends Operations | Two exit codes for one outcome double the committed CLI contract | Exit 12 already names it ([record 96](0096-a-deploy-is-an-operation-that-ends-serving-held-refused-superseded-or-observation-lost.md)) |
| No ends for a closed Rollout: the log stays open | The fold of the events never finishes, and the Rollout's log has no legal end | Every Rollout ends exactly once |
| End it Observation lost | Delivery did observe the Rollout; it was simply closed | Observation lost names what is not known; Replaced names what happened |

## Consequences

- Easier: every Rollout ends exactly once; a reader tells an Operation's fate
  (Superseded, exit 12) from its Rollout's (Replaced); one check holds every
  list the records and pages hold.
- Harder: each new page or record that names the outcomes must spell exactly
  its list's ends, and the lists may grow only through an amending record.
- Forbidden: a sixth end on either list without amending this record;
  Superseded as a Rollout end; Replaced as an Operation end; an Operation end
  read as a Rollout end or the other way round.

## Confirmation

The **Rollout outcome lists check** fails when any outcome list it reads — the
vocabulary's, [record 96](0096-a-deploy-is-an-operation-that-ends-serving-held-refused-superseded-or-observation-lost.md)'s,
[record 23](0023-a-rollout-is-an-append-only-event-log-on-the-shared-postgres.md)'s,
this record's, the [Releasing](../design/releasing.md) page's or the sequence
declaration's — names an end its settled list does not hold: a stray sixth end,
a missing end, or an end read from the other list. The **Operation outcome
tests** fail when a Rollout a newer Operation closed before it reached
Serving, Held or Refused does not end Replaced while its Operation ends
Superseded.

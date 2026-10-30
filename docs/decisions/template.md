---
status: proposed  # proposed | accepted | locked
date: YYYY-MM-DD
rests-on: []      # earlier record numbers this one depends on
lessons: []       # lesson ids from lessons.md
---

# The decision, stated as a sentence

## Context

What forces this decision. Facts, with sources. No options yet.

## Decision

What is decided, in one or two paragraphs. The normative detail lives in the
contract or design page this links to, not here.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| | | |

## Consequences

What becomes easier, what becomes harder, and what is now forbidden.

## Confirmation

The check that fails when this decision is broken: a schema validation, a
contract test, an architecture rule or a lint, with its path. A record without
a Confirmation cannot be Locked.

Write each check by its name in bold, exactly as the first column of
[the table of checks](../design/code-shape-and-speed.md#the-checks) spells it,
and add a row there for a new check. The Records job fails on a bold name that
is not a row, and on an empty Confirmation. Do not claim an existing job does
what it does not: name the check that will, and the workstream issue that
builds it is in its row.

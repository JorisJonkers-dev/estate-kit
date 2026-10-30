---
status: accepted  # proposed | accepted | locked
date: 2026-10-30
rests-on: [14]
lessons: [DO-1, CS-3]
---

# A Mailbox is declared by its local part and owned by one Project

## Context

Applications send mail through the estate's mail server. An Application needs
an address and a password; the platform can derive the rest: the address on the
estate's mail domain, a generated password as a Generated key, and delivery as
env or file like any Grant ([mail and components](../design/mail-and-components.md#mailboxes)).

Two questions need an answer: who owns an address, and how the Mailbox objects
reach the mail server. An address is unique across the estate, so two Projects
cannot both own `noreply`.

## Decision

An Application declares a Mailbox by its local part only. Within one Project the
same local part names one shared Mailbox; across Projects the same local part is
refused with a contention diagnostic that points at both declarations
([record 71](0071-a-diagnostic-is-a-coded-problem-with-typed-locations.md)). Each
Mailbox has exactly one owning Project.

Each Project's render carries one Mailbox custom resource per Mailbox, in its
own unit. The mailbox component watches them by label and reconciles the mail
server, so adding a Project re-renders nothing else.

How a Mailbox is shared beyond its Project, if ever, is not decided here. It
needs its own record.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Owner plus references, or a Project-level block | More to write for every Mailbox, and a reference is a second way to name one | Least to write wins; each Mailbox has one owning Project |
| One estate-wide manifest of Mailboxes | Every Project's change edits a shared file, and ownership is a convention | Each Project controls itself (DO-1) |
| Accept the same local part in two Projects and let the last win | A silent takeover of an address | A contention is an authored error, reported with its locations (CS-3) |

## Consequences

- Authoring a Mailbox is one word.
- A contention fails at compile time, not at the mail server.
- A Project's units own their Mailboxes, so removing a Project removes them.
- Sharing across Projects is forbidden until a record allows it.

## Confirmation

- The **Mailbox fixtures**: a compiler fixture declares one local part in two Projects and expects the
  contention diagnostic with both locations; a second fixture declares it twice
  in one Project and expects one Mailbox.
- A render test pins the Mailbox custom resource whole, in the declaring
  Project's unit.

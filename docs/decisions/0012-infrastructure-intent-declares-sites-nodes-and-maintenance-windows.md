---
status: accepted  # proposed | accepted | locked
date: 2026-10-30
rests-on: [10]
lessons: [MS-4, MS-6]
---

# Infrastructure Intent declares sites, nodes and maintenance windows

## Context

The same compiler that renders Projects also renders each NixOS node's host
data ([hosts](../design/hosts.md)). A Project's author writes Project Intent;
nothing equivalent names the sites, the nodes at them, what each node has and
needs, or when it may reboot. The host applier reboots a node only inside its
**maintenance window**, and the service level for the deploy endpoint excludes
those windows ([conventions](../design/conventions.md#service-levels)), so the
window is an input to the model and not a setting on the node.

Sites differ: a Contabo VPS and a Raspberry Pi at home do not share quiet
hours. A single estate-wide window would be wrong for one of them.

## Decision

Infrastructure Intent is the one authored document that declares the estate's
sites and nodes: what each node has, what it needs, and its maintenance
window. The window is declared per site, and a node may override it. It is
authored only here; the compiler derives host data from it, and no hand-written
module or node-local file states a window.

The vocabulary is [`CONTEXT.md`](../../CONTEXT.md)'s: Infrastructure Intent,
Maintenance window, Node class. The document's fields are specified on the
host design page and in the committed schema once it is written, not here.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| One estate-wide window | A node at a site with different quiet hours reboots at a bad time, or the window shrinks to the intersection of all sites | Sites differ |
| A window per node only | Every node of a site repeats the same hours; a site's change touches every node | Little repetition is worth keeping |
| Window set on the node by a NixOS module | The compiler cannot reason about it, and the host applier and the service level read different sources | Authors state requirements and the compiler derives mechanism (MS-4) |

## Consequences

- One place to read when a node reboots, and one place to change it.
- A site's window changes in one line; an odd node says so on its own entry.
- The window is a closed, typed value, never a free string (MS-6).
- Infrastructure Intent is a second authored document type beside Project
  Intent, so the compiler and schemas cover both.

## Confirmation

- The committed JSON Schema for Infrastructure Intent requires a window on
  every site, and a corpus test shows a node override validates and a missing
  site window is refused ([record 15](0015-the-rust-types-agree-with-the-committed-schemas-on-their-corpus.md)).
- A compiler test shows no host data is rendered for a node whose site has no
  window.

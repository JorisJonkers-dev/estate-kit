# Design

The design is being worked out as a shared document, with one tab per concern:

- Overview
- Where state lives
- Releasing a Project
- Operating the estate
- Identity and access
- Errors in CI
- Inside the compiler
- Inside the service
- Code shape and speed
- Choices made
- Decision records
- Lessons

Each tab moves into this directory as a Markdown page once its decisions are
settled. The decision register in [`../decisions/`](../decisions/README.md) is
then normative over these pages.

## Settled since the document

- **Hosts.** One model and one compiler render both Kubernetes objects and
  typed host data. Hand-written NixOS modules consume the host data. A
  separate host applier runs on each node, outside Kubernetes. It pulls a
  signed generation, takes a cluster-wide Lease, drains its node and switches.
  It reboots only inside its maintenance window, which Infrastructure Intent
  declares per site and a node may override.
- **The control plane** is one node today. During its maintenance window the
  API pauses while workloads keep serving. Moving to three servers is a
  separate decision.
- **Platform Intent** is pushed by the estate repository's release workflow
  over OIDC, like any Project. The service keeps copies of every fragment and
  of Platform Intent as a rebuildable cache. The registry stays the record,
  and a nightly drift check compares git, the registry and the cache.
- **Components** (the migration runner, the secret job and the mail
  provisioner, ported to Go) are directories in this repository, in lockstep.
- **Mailboxes.** An Application lists its addresses by local part. The same
  local part within one Project names one shared Mailbox; the same local part
  in two Projects is refused. Each Project renders its own Mailbox objects, a
  custom resource, and the mail provisioner reconciles Stalwart from them.

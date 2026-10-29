---
status: proposed  # proposed | accepted | locked
date: 2026-10-29
rests-on: [1, 12]
lessons: [DR-1, DR-2]
---

# The API server's datastore is backed up off the provider, and its restore is drilled

## Context

`frankfurt-contabo-1` is the only control-plane node. Its k3s datastore is one
SQLite file, with no backup and no written restore. Losing the node loses the
cluster's state ([review](../research/review/README.md) D5).

## Decision

Keep SQLite. A NixOS timer takes a `sqlite3 .backup` of the datastore and
copies it, with the server token, to object storage outside the provider,
beside the Vault snapshots. A restore runbook builds a node with
nixos-anywhere, the binary cache, the datastore copy and the Vault restore
playbook, and is drilled once in a VM and again after every k3s minor version.
A k3s minor bump on the control plane takes a fresh snapshot first. Spike #14
proves the restore and a minor-version rollback.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Convert to one-member etcd | A one-way conversion of production; fsync-sensitive on a VPS disk | Not needed for a restore path |
| Three control-plane servers | Low-latency peers the estate does not have | High availability is a separate decision |

## Consequences

- Easier: losing the node is a restore, not a rebuild from nothing.
- Harder: the backup copies a secret off the provider; it is encrypted to a
  recipient Platform Intent names.
- Forbidden: a k3s minor bump on the control plane without a fresh snapshot.

## Confirmation

The backup timer's age is alerted on; the drill's runbook is a checked list in
the repository with the date of its last run, and a check fails when it is
older than a year.

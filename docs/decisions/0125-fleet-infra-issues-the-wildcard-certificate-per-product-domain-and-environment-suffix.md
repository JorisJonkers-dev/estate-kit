---
status: accepted  # proposed | accepted | locked | superseded
date: 2026-11-05
rests-on: [59, 76, 77]
amends: [77]
lessons: [DR-1, MS-7]
---

# Fleet-infra issues the wildcard certificate per Product domain and Environment suffix, and estate-kit names the expiry alert

## Context

[Record 77](0077-product-domains-are-admitted-by-platform-intent.md)
derives every Tenant host one level below its Product domain —
`<handle>-staging.<product domain>` in staging — so one single-level wildcard
certificate covers every Environment. It names no owner for that certificate,
no rule for its renewal, and no alert for its expiry.

The settled vocabulary changes the host's shape: the environment suffix is the
Tenant host's own DNS label
([CONTEXT.md](../../CONTEXT.md)), so a staging host is
`<handle>.staging.<product domain>`, two labels below the domain. A wildcard
certificate `*.<product domain>` matches names one label deep and no deeper, so
one certificate per Product domain now leaves staging and development Tenant
hosts uncovered — exactly the review's finding that the wildcard does not cover
every host (the architecture evaluation of 2026-11-04, A6-03). One private key
good for every Tenant host of every Environment is also more reach than any one
Environment needs.

The maintainer settled the owner and the alert: fleet-infra issues the wildcard
certificate per Product domain and Environment suffix, and estate-kit names the
expiry alert.

## Decision

The Tenant host keeps the vocabulary's shape, and each Environment has its own
wildcard certificate:

| Environment | Tenant host | Wildcard certificate |
| --- | --- | --- |
| production | `<handle>.<product domain>` | `*.<product domain>` |
| staging | `<handle>.staging.<product domain>` | `*.staging.<product domain>` |
| development | `<handle>.dev.<product domain>` | `*.dev.<product domain>` |

fleet-infra, which owns the estate's DNS and its ACME credential, issues and
renews one wildcard certificate per Product domain and Environment suffix, for
every Product domain Platform Intent admits. A per-environment override that
names another Product domain gets its certificates the same way, for the domain
it names. No certificate of one Environment ever covers another's Tenant hosts.

estate-kit names the expiry alert: each wildcard certificate carries a
`WildcardCertificateExpiry` alert that fires while there is still time to
renew. The alert reads the issuer's own metrics, so it needs no credential in
estate-kit and no active check that connects to a host.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| One wildcard certificate per Product domain, every Environment on it | With the suffix as its own DNS label, `*.<product domain>` covers only production; staging and development Tenant hosts have no certificate | Each Environment's wildcard covers exactly that Environment's Tenant hosts |
| Keep the suffix inside the handle's label, as `<handle>-staging.<product domain>` | One certificate, but one private key serves every Tenant host of every Environment, and the settled vocabulary's host shape is lost | Three certificates per domain cost nothing more to renew on a schedule |
| estate-kit issues the certificates in a component | The ACME credential sits in the cluster beside the signing keys, and renewal becomes estate-kit code | fleet-infra already owns the estate's DNS and its ACME credential ([record 59](0059-vault-unseal-and-datastore-backup-are-assumed-from-fleet-infra.md)) |
| An active check that connects to each host and reads the certificate | Remaining lifetime is learned by a probe that needs a right to reach every host | The issuer states the lifetime in metrics it already exposes |

## Consequences

- Easier: every Tenant host of every Environment is covered; a certificate leak
  reaches one Environment, not all three; the expiry alert needs no credential
  and no probe.
- Harder: three certificates per Product domain instead of one, each issued and
  renewed by fleet-infra, and one expiry alert to keep in the Observation alert
  rules.
- Forbidden: a Tenant host not covered by its Environment's wildcard
  certificate; a certificate shared across Environments; an admitted Product
  domain with no `WildcardCertificateExpiry` alert.

## Confirmation

The **Tenant host derivation test** fails when a derived Tenant host differs
from `<handle>.<product domain>` in production or from
`<handle>.<suffix>.<product domain>` elsewhere, or sits deeper than its
Environment's wildcard certificate reaches. The **Wildcard certificate expiry
alert test** fails when a Product domain Platform Intent admits has no
`WildcardCertificateExpiry` alert, or one of its wildcard certificates passes
its renewal bound and the alert raises none.

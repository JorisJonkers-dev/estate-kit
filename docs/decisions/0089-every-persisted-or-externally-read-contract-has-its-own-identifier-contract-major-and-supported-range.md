---
status: proposed  # proposed | accepted | locked
date: 2026-11-04
rests-on: [15, 34, 48]
amends: [34, 48]
lessons: [PR-2]
---

# Every persisted or externally read contract has its own identifier, Contract major and supported range

## Context

estate-kit ships every binary, image and reusable workflow under one version
([record 34](0034-every-part-of-estate-kit-lives-in-this-repository-at-one-version.md)).
Every committed schema evolves additively within a major, and CI fails when a
change disagrees with the version bump
([record 48](0048-the-cli-s-json-output-has-a-committed-schema.md)). Neither
record says which version a schema's major is. deploy-kit ties the model's
version to the package's ([deploy-kit ADR 0007](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/model/0007-schema-version-separable.md), rewritten for lockstep in
deploy-kit#373 so the maintainer reasons about one number; lesson PR-3), and
[Conventions](../design/conventions.md#contracts-and-their-evolution) already
has payloads carry their contract version, with Delivery accepting the current
major and the one before. `contracts/` is not written yet.

Several readers lag the release that writes for them:

- the reusable workflows in Projects' repositories pin a release and read the
  CLI's `--json` output; a lagging pin once broke a publish (PR-2);
- a Host applier on a node reads host data and may run an older release than
  the one that rendered it;
- Rollout events are kept 400 days
  ([record 23](0023-a-rollout-is-an-append-only-event-log-on-the-shared-postgres.md)),
  so a release reads events written by many before it;
- Observation and the UI read Delivery's API
  ([record 43](0043-the-delivery-api-is-an-openapi-3-1-contract.md)).

A release number that moves on every bug fix says nothing to these readers
about the shape of what they read. The architecture evaluation of 2026-11-04
(sections 3.3 and 4.6) adds two facts. Compatibility is directional: a new enum
value is safe for a reader of inputs and breaking for a reader of outputs. And
the one mechanical subschema checker studied, "Finding Data Compatibility Bugs
with JSON Subschema Checking" (2021), was built for JSON Schema draft-04, not
the 2020-12 dialect estate-kit emits, and may answer "unknown". "Maintaining
Robust Protocols" (RFC 9413, 2023) finds that a lenient receiver entrenches its
own bugs.

## Decision

Each of these contracts has a stable identifier, its own Contract major and a
supported range: the majors its readers accept.

- Project Intent, Platform Intent and Infrastructure Intent (`spec/v1`, major 1);
- the Resolved Deployment, which [record 3](0003-three-models-intent-resolved-deployment-deliverable-set.md) already versions;
- host data;
- the CLI's `--json` output ([record 48](0048-the-cli-s-json-output-has-a-committed-schema.md));
- Delivery's OpenAPI document and its error catalogue ([record 43](0043-the-delivery-api-is-an-openapi-3-1-contract.md));
- the Rollout event schema and the event types of the stream;
- a render's index and its provenance statement;
- each custom resource estate-kit defines, such as ProjectControl and Tenant, whose Kubernetes API version is its Contract major.

A Profile or Component kind joins the list once it is published apart
([record 88](0088-the-metamodel-is-layered-core-profiles-and-component-kinds-provider-facts-estate-instance.md)).
Delivery's own tables, read by no other program, are not on it.

This clarifies records [34](0034-every-part-of-estate-kit-lives-in-this-repository-at-one-version.md)
and [48](0048-the-cli-s-json-output-has-a-committed-schema.md). estate-kit
keeps one version; it stays in the Render key and the provenance, and decides
which releases are supported, but it is not what a reader checks. The major
that [record 48](0048-the-cli-s-json-output-has-a-committed-schema.md)'s rule
speaks of is the contract's own. A payload carries its identifier and
major, and a reader refuses a major outside its range with a coded problem.
CI classifies every schema change per reader and direction. Authored documents
refuse unknown fields; a machine reader ignores only fields the contract marks
extensible and non-essential. Deprecation is data in the schema: the
replacement and the release that removes it. A contract gets its own minor or
patch only when a reader is shown to need one. This departs from [deploy-kit ADR 0007](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/model/0007-schema-version-separable.md) and from lesson PR-3's single number.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| Lockstep: every contract's version is the release ([deploy-kit ADR 0007](https://github.com/JorisJonkers-dev/deploy-kit/blob/main/docs/adr/model/0007-schema-version-separable.md)) | A bug-fix release looks like a format change to every lagging reader | Readers lag the release, and the release says nothing about shape |
| Full semver per contract now | A minor and patch to keep per contract, with no reader that needs them | Majors and ranges are enough until a reader lags on a minor |
| A version per crate or binary | A compatibility matrix again | [Record 34](0034-every-part-of-estate-kit-lives-in-this-repository-at-one-version.md) refuses it |
| Split the repository so each contract releases alone | Release, ledger and CI machinery for one maintainer | One repository stands; identifiers give the separation |
| Readers accept any major and ignore what they do not know | A reader runs on data it misunderstands | A lenient reader entrenches its bugs (RFC 9413) |
| Trust the subschema checker's answer alone | An "unknown" or a dialect gap passes silently | It was evaluated on draft-04; "unknown" needs a person |

## Consequences

- Easier: a host applier, a workflow pin or a 400-day-old event says exactly
  which shapes it can read; a bug-fix release breaks no reader.
- Harder: each contract has an identifier, a major and a range to keep, and a
  change must be classified for each of its readers; a spike must show the
  subschema checker works on 2020-12 before CI relies on it.
- Forbidden: a payload written without its identifier and major; a reader that
  accepts a major outside its range; a contract whose major is the release
  version; a non-additive change inside a Contract major.

## Confirmation

The **Contract identity check** fails when a contract in `contracts/` has no
identifier, Contract major or supported range, or when a writer emits a payload
without them. The **Supported range fixtures** fail when a reader accepts a
payload of a major outside its range or refuses one inside it. The **Schema
evolution check** compares each change with the contract's own last major, and
the **Compatibility direction check** fails when a change is not classified for
each reader and direction, or when an "unknown" answer merges without review.
The **Workspace version check** still holds the one release version.

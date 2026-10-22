# Plan: port deploy-kit, delivery and estate-dashboard into estate-kit, then replace them

## Problem

Delivery tooling is spread over four repositories that drift apart. delivery
vendors deploy-kit's schemas at v0.6.0 while the estate runs 0.30.0. The
estate repository holds a central list of what is deployed (the pin files),
an images lock, the cluster state and a participants list, all outside the
Projects they describe. The compiler runs on a TypeScript toolchain whose dev
and CI tree is about 230 npm packages. It cannot ship as one binary, and its
types do not exist at runtime.

## Outcome

One repository, `JorisJonkers-dev/estate-kit`, contains:

- a Rust compiler, shipped as one static binary, used by every Project's
  workflow (for offline validation) and by the service (to compose);
- an in-cluster Go service, grown from estate-dashboard and delivery, that
  composes the estate, signs each render through Vault Transit, pushes it to
  ghcr, moves the Project's `render/<p>:live` tag, and reports GitHub
  Deployment status to the Project's repository;
- the Vue UI, with npm confined to building its static assets;
- the spec, the schemas, the oracle files, and a new decision register with
  `docs/lessons.md`.

Every rollout is a GitHub Actions run in the Project's repository. A Project
has two workflows: `validate` (ordinary pull requests: offline checks and a
plan) and `deploy`. A release-please pull request runs `deploy` with
`dry-run: true` as the required check `estate-kit / deploy (dry-run)`: it
builds candidate images and the service dry-runs them against the API server
with `dryRun=All`. On release, `deploy` promotes those same digests, and the
service dry-runs again before it signs anything and moves `render/<p>:prod`.
The deploy job streams the rollout live until the Release Unit settles.
Errors land on their YAML lines: as log snippets, annotations, an
`estate-kit` check run and a job summary. Every caller of the service
authenticates by OIDC: Project CI by its GitHub token (`repository_id`, the
pinned reusable workflow, the environment), people through auth-api, and
in-cluster callers by projected service-account tokens.

Flux stays the one applier. No repository holds a list of what is deployed.
An image's digest is sealed into the Intent Fragment. Pause and Rollback
state is one cluster object per Project. The estate repository keeps only
Platform Intent (including the admitted Projects) and the node contract.

The full design, with the rejected alternatives:
[`docs/design/`](../design/README.md)

## Order of work

The old repositories serve production and keep evolving until the last
switch. Changes made to them meanwhile are ported forward before the shadow
phase can close.

- [ ] Found estate-kit after the 2026-10-30 hand-in and the deletion of `emf/`.
      Import deploy-kit, delivery and estate-dashboard with history. Merge the
      founding ADRs and `docs/lessons.md`.
- [ ] Port the compiler to Rust. Gate: every oracle file renders byte-identical
      to the TypeScript compiler.
- [ ] Merge the Go services: the dashboard becomes the service, delivery's
      Release Gate and Collector join it, and Go types are generated from the
      in-repo schemas.
- [ ] Shadow: compose beside production from the same fragments, sign nothing
      live, and diff the renders. Gate: renders identical for an agreed number
      of days.
- [ ] Switch the compiler.
- [ ] Switch the pins from commits to signed registry tags.
- [ ] Switch the dashboard.
- [ ] Archive deploy-kit, delivery and estate-dashboard. Slim the estate
      repository.
- [ ] Rewrite the model (the #373 chain) in Rust, up to 1.0.

## Gates

- Lint, tests and contracts: under 2 minutes on a pull request.
- Mutation: diff-scoped, under 5 minutes on a pull request; a full sharded
  run nightly. Rust holds a 100% break score; Go starts report-only and
  ratchets.

## Not in scope

- Replacing Flux. The signed per-Project artifact keeps that possible later.
- Changing what the model means before the cutover.

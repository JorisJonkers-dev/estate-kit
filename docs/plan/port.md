# Plan: replace deploy-kit, delivery and estate-dashboard with one Rust workspace

The work is tracked as sub-issues of
[epic #9](https://github.com/JorisJonkers-dev/estate-kit/issues/9). Each issue
names the issues that block it; work the frontier, any issue whose blockers are
all closed. This plan follows the [design review](../research/review/README.md)
of 2026-10-22, as changed on 2026-10-29 by
[record 13](../decisions/0013-every-program-is-rust.md) (every program is
Rust) and [record 67](../decisions/0067-the-compiler-is-written-to-the-1-0-contract.md)
(the compiler implements the 1.0 specification). Both are accepted; the issues
they changed are listed [below](#issues-this-plan-changed).

## Problem

Delivery tooling is spread over five repositories in three languages that
drift apart. delivery vendors deploy-kit's schemas at one version while the
estate runs another. The estate repository holds a central list of what is
deployed (the pin files), an images lock, the cluster state and a participants
list, all outside the Projects they describe.

## Outcome

One repository, `JorisJonkers-dev/estate-kit`, holds one Cargo workspace
([The Rust workspace](../design/rust-workspace.md)) with:

- the compiler, implementing deploy-kit's 1.0 specification, behind the
  `estate-kit` CLI that every Project's workflow runs for offline validation;
- an in-cluster service that links the compiler, composes the estate,
  dry-runs as its own identity, signs each changed render with the render signing key
  in Vault Transit, pushes it to ghcr, moves the Project's `render/<p>:prod`
  tag, and reports GitHub Deployment status to the Project's repository;
- the Observation views the dashboard serves today, in the same binary;
- a host applier on each NixOS node that pulls its signed `host/<node>:prod`
  tag and switches one node at a time;
- six components: migration runner, secret grant, database catalog, bucket
  catalog, backup and mail provisioner;
- the Vue UI, with npm confined to building its static assets;
- the specification, the schemas and corpus, the oracle files, the decision
  records and `docs/lessons.md`.

Flux stays the one applier, locked down per Project. No repository holds a list
of what is deployed. An image's digest is sealed into the Intent Fragment and
must have been registered by the Project's own build. Pause and Rollback state
is one cluster object per Project, and a missing object reads as Paused. The
estate repository keeps only Platform Intent (including the admitted Projects)
and the node contract.

## What changed on 2026-10-29

- **Every program is Rust; the UI stays Vue.** The review chose TypeScript to
  1.0 and Go for the service (D1). The maintainer has since chosen one backend
  language, and the TypeScript compiler is not carried into estate-kit.
- **The model rewrite has shipped.** deploy-kit 1.0.0 (2026-10-27) is #373's
  contract step, so the Rust compiler implements a finished, specified model
  rather than chasing one that changed daily. Its refusal oracles (code and
  path) and expected models carry over exactly; rendered files are met in
  structure and rewritten once in the canonical format.
- **The service links the compiler** instead of running it as a subprocess
  ([record 18](../decisions/0018-the-service-links-the-compiler.md)).
- **Six components, not three**, and a fifth bounded context for the
  dashboard's read views: the inventory found delivery's catalog, bucket and
  backup jobs and the dashboard's Prometheus, Loki, Alertmanager and Gatus
  reads unplaced.

## Workstreams

The crate graph is also the division of work. Once the foundation and the
walking skeleton are in, each workstream below owns its own crates and can run
in parallel with the others, with one owner each and a list of what it must
not touch (PR-4).

| Workstream | Issues | Crates | Depends on | Characterized first |
| --- | --- | --- | --- | --- |
| W0 Foundation and gates | [#60](https://github.com/JorisJonkers-dev/estate-kit/issues/60) | `diagnostics`, `yaml-source`, `canonical`, `trace`, `reconcile`, `testkit`, `xtask` | Nothing | None |
| W1 Compiler: read and check | [#61](https://github.com/JorisJonkers-dev/estate-kit/issues/61) | `model-intent`, `step-read`, `step-check` | W0 | deploy-kit's corpus, refusal and schema-refusal oracles |
| W2 Compiler: lower, compose, resolve | [#62](https://github.com/JorisJonkers-dev/estate-kit/issues/62) | `model-effective`, `model-resolved`, `step-lower`, `step-compose`, `step-resolve` | W1 | deploy-kit's expected models |
| W3 Compiler: render and serialize | [#63](https://github.com/JorisJonkers-dev/estate-kit/issues/63) | `deliverable`, `render-*`, `serialize`, `step-outputs`, `generate` | W2 | deploy-kit's rendered oracles, in structure |
| W4 Service core | [#26](https://github.com/JorisJonkers-dev/estate-kit/issues/26) | `rollout`, `service-app` with fakes, `http-api` | W0; the compiler's application API from W1 | estate-dashboard's API responses |
| W5 Service adapters | [#64](https://github.com/JorisJonkers-dev/estate-kit/issues/64) | `adapter-postgres`, `-ghcr`, `-vault`, `-kube`, `-github`, `-github-oidc` | W4's ports | None |
| W6 Release Gate | [#25](https://github.com/JorisJonkers-dev/estate-kit/issues/25), [#37](https://github.com/JorisJonkers-dev/estate-kit/issues/37) | `release-gate` | W4 | delivery's Gate answers and Reporter statuses |
| W7 Observation | [#65](https://github.com/JorisJonkers-dev/estate-kit/issues/65) | `observation-app`, its adapters, the Vue UI's client | W4 | estate-dashboard's read responses |
| W8 Components | [#66](https://github.com/JorisJonkers-dev/estate-kit/issues/66), [#67](https://github.com/JorisJonkers-dev/estate-kit/issues/67), [#68](https://github.com/JorisJonkers-dev/estate-kit/issues/68), [#69](https://github.com/JorisJonkers-dev/estate-kit/issues/69), [#70](https://github.com/JorisJonkers-dev/estate-kit/issues/70), [#71](https://github.com/JorisJonkers-dev/estate-kit/issues/71) | `secret-grant`, `database-catalog`, `bucket-catalog`, `backup`, `mailbox`, `migration-run` and their adapters | W0 (`reconcile`) | Each Go or Python job's actions and verdicts |
| W9 Hosts | [#43](https://github.com/JorisJonkers-dev/estate-kit/issues/43) to [#49](https://github.com/JorisJonkers-dev/estate-kit/issues/49) | `host-rollout`, `host-applier-app`, its adapters, the VM tests | W0, W3 (`step-outputs`) | None: new |
| W10 rust-commons sign-in kit | identity#113 | identity#113 in rust-commons | None | identity's flow-conformance suite |
| W11 End to end | [#72](https://github.com/JorisJonkers-dev/estate-kit/issues/72) | `e2e/` | W4, W5, W3 for `minimal` | None |

## Order of work

Budgets are first estimates in maintainer hours, at a few hours a week. When a
phase overruns its budget by half, stop and choose its fallback before going
on.

| Phase | Work | Budget | Exit | Fallback |
| --- | --- | --- | --- | --- |
| 1. Spikes | #10 to #17, plus the Rust YAML reader spike in place of #18 | 25 h | Each spike's question answered in its issue | A spike that cannot answer reopens its decision as a Proposed record |
| 2. Records, lessons, founding | #19 to #22 | 25 h | Records written; the specification, oracles and old code imported with history (after 2026-10-30) | Write only the records the next phase needs |
| 3. Workspace and walking skeleton | W0, then a thin slice of W1 to W5 and W11 | 40 h | `minimal` rendered by the Rust compiler, composed by the Rust service against fakes, and written as a shadow tag on a test cluster; every gate in CI with a failing fixture (MD-5) | Narrow the slice, never skip a gate |
| 4. The compiler to 1.0 | W1 to W3 | open, measured per chapter | Every language-neutral 1.0 oracle met; every rendered oracle met in structure | Hold deploy-kit's additive releases until the Rust side catches up |
| 5. Deploy path | W4 to W6, #30 to #39 | 45 h | A test cluster deploys, rolls back and pauses through the service, with Vault scaled to zero for rollback | Ship without provenance registration, behind a claim policy only |
| 6. Recovery on the running estate | #40 to #42 | 15 h | Vault unseals itself; a datastore restore has been drilled | None: these are production risks today |
| 7. Components and Observation | W7, W8 | 40 h | Each component passes its characterization; the UI serves every page the dashboard does | Keep the old job running behind the new rendered objects |
| 8. Hosts | W9, #43 to #49 | 50 h | A host rollout switches the fleet one node at a time under the Lease | Stay on deploy-rs from generated targets (#44) |
| 9. Shadow and switch | #50 to #53 | 30 h | Every Project on signed tags with no unexplained structural difference; old repositories archived | Revert the last switched Project and keep the old stack serving |

The shadow phase's exit rule (#50) is fixed before the shadow starts: the
number of consecutive days with no unexplained difference, and which Projects
they must cover.

Phases 1 and 6 can start now. Phase 2's founding import waits for 2026-10-30,
the MDE course's Task 3 hand-in, and the deletion of deploy-kit's `emf/`.

## Sequencing deploy-kit meanwhile

deploy-kit serves production and keeps releasing additive changes for the
#373 handovers until the Rust compiler meets the oracles of its latest
release ([record 67](../decisions/0067-the-compiler-is-written-to-the-1-0-contract.md)).
Each such change lands in the specification first, with its oracles, so the
Rust side implements it from there. After that point, new concepts land in
estate-kit only.

## Gates

[Testing and speed](../design/code-shape-and-speed.md) holds them: lint and
tests under 2 minutes on a pull request; integration under 5; mutation on
every push to main, diff-scoped and sharded, with a weekly full run; 100%
unit coverage and break score on domain, application and step crates,
switched on per crate once its tests are in.

## Issues this plan changed

Rewritten on 2026-10-29 to follow records 13, 18 and 67, accepted the same day: [#18](https://github.com/JorisJonkers-dev/estate-kit/issues/18) is now the Rust YAML reader spike, [#23](https://github.com/JorisJonkers-dev/estate-kit/issues/23) the `estate-kit` CLI and its `--json` schema, [#26](https://github.com/JorisJonkers-dev/estate-kit/issues/26) the service core (W4), [#29](https://github.com/JorisJonkers-dev/estate-kit/issues/29) the walking skeleton through the Rust compiler, and [#54](https://github.com/JorisJonkers-dev/estate-kit/issues/54) the canonical format in the `canonical` crate. [#24](https://github.com/JorisJonkers-dev/estate-kit/issues/24) closed as not planned (the service links the compiler), [#55](https://github.com/JorisJonkers-dev/estate-kit/issues/55) closed by deploy-kit 1.0.0, and [#56](https://github.com/JorisJonkers-dev/estate-kit/issues/56) closed by [record 13](../decisions/0013-every-program-is-rust.md). [#22](https://github.com/JorisJonkers-dev/estate-kit/issues/22) now protects the imported specification and oracles, and [#50](https://github.com/JorisJonkers-dev/estate-kit/issues/50) compares structure against an expected-differences ledger. The workstreams have their own issues, linked in the table above, each a sub-issue of epic #9 with its blocked-by links.

## Not in scope

- Replacing Flux. The signed per-Project artifact keeps that possible later.
- Changing what the 1.0 model means during the port.
- A second control-plane server. The single control plane gets a restore path
  (#41) instead; high availability is a separate decision.
- Replacing the Vue UI.

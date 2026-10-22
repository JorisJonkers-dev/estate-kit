# Plan: bring deploy-kit, delivery and estate-dashboard into estate-kit, then replace them

The work is tracked as sub-issues of
[epic #9](https://github.com/JorisJonkers-dev/estate-kit/issues/9). Each issue
names the issues that block it; work the frontier, any issue whose blockers are
all closed. This plan follows the [design review](../research/review/README.md)
of 2026-10-22, whose decisions D1 to D12 reordered it.

## Problem

Delivery tooling is spread over four repositories that drift apart. delivery
vendors deploy-kit's schemas at v0.6.0 while the estate runs 0.31.0. The
estate repository holds a central list of what is deployed (the pin files),
an images lock, the cluster state and a participants list, all outside the
Projects they describe.

## Outcome

One repository, `JorisJonkers-dev/estate-kit`, contains:

- the TypeScript compiler, shipped as one executable behind a fixed CLI and
  `result.json` contract, used by every Project's workflow (for offline
  validation) and by the service (to compose);
- an in-cluster Go service, grown from estate-dashboard and delivery, that
  composes the estate, dry-runs as its own identity, signs each changed render
  with the render key in Vault Transit, pushes it to ghcr, moves the Project's
  `render/<p>:prod` tag, and reports GitHub Deployment status to the Project's
  repository;
- a host applier on each NixOS node that pulls its signed `host/<node>:prod`
  tag and switches one node at a time;
- the Vue UI, with npm confined to building its static assets;
- the spec, the schemas, the oracle files, the decision records and
  `docs/lessons.md`.

Flux stays the one applier, locked down per Project. No repository holds a list
of what is deployed. An image's digest is sealed into the Intent Fragment and
must have been registered by the Project's own build. Pause and Rollback state
is one cluster object per Project, and a missing object reads as Paused. The
estate repository keeps only Platform Intent (including the admitted Projects)
and the node contract.

The full design, with the rejected alternatives: [`docs/design/`](../design/README.md).

## What changed in the review

- **The compiler stays TypeScript until model 1.0** (D1). The Go service cuts
  over on today's compiler through the subprocess seam, so parity holds
  trivially and the shadow tests what actually changes: the service, signing
  and tags. The deploy-kit#373 rewrite happens in TypeScript, where its tests
  and mutation setup live. A Rust port happens only if a record written after
  1.0 justifies it, and then from the frozen 1.0 model.
- **The host applier is built alongside the service** (D2), against the
  review's recommendation to defer it. Break-glass stays on deploy-rs.
- **Mechanisms the review found could not be built as written** are replaced:
  a machine-account token for ghcr (D3), Flux lockdown and a dry-run-only
  identity (D4), the Release Gate answered from cluster state (D9).
- **Recovery work moves forward** and runs on today's estate: datastore
  backups (D5) and Vault auto-unseal (D6) do not wait for estate-kit.

## Order of work

Budgets are first estimates in maintainer hours, at a few hours a week. When a phase overruns its
budget by half, stop and choose its fallback before going on.

| Phase | Issues | Budget | Exit | Fallback |
| --- | --- | --- | --- | --- |
| 1. Spikes | #10 to #18 | 20 h | Each spike's question answered in its issue | A spike that cannot answer reopens its decision as a Proposed record |
| 2. Records, lessons, founding | #19 to #22 | 25 h | Records written; the imported trees build in estate-kit (after 2026-10-30) | Write only the records the next phase needs |
| 3. Walking skeleton | #23 to #29 | 30 h | A deploy call composes through the TypeScript binary and writes a shadow tag | Keep delivery's Go code where it is and call it from the service |
| 4. Deploy path | #30 to #39 | 45 h | A test cluster deploys, rolls back and pauses through the service, with Vault scaled to zero for rollback | Ship without provenance registration, behind a claim policy only |
| 5. Recovery on the running estate | #40 to #42 | 15 h | Vault unseals itself; a datastore restore has been drilled | None: these are production risks today |
| 6. Hosts | #43 to #49 | 50 h | A host rollout switches the fleet one node at a time under the Lease | Stay on deploy-rs from generated targets (#44) and leave the applier for later |
| 7. Shadow and switch | #50 to #53 | 30 h | Every Project on signed tags; old repositories archived | Revert the last switched Project and keep the old stack serving |
| 8. The model | #54 to #56 | open | Model 1.0 released; the Rust decision recorded | Stay on the current model |

The shadow phase's exit rule (#50) is fixed before the shadow starts: the
number of consecutive days of identical renders, and which Projects they must
cover.

Phases 1 and 5 can start now. Phase 2's founding import waits for 2026-10-30,
the MDE course's Task 3 hand-in, and the deletion of deploy-kit's `emf/`.

## Sequencing the model before the cutover

The old repositories serve production and keep evolving until the last switch.
Because the compiler is the same code on both sides, changes made to it
meanwhile need no porting. Two kinds of change still need a rule:

| Change | Before the cutover |
| --- | --- |
| Additive: a new concept, a new optional field, a new output | Allowed, in deploy-kit or estate-kit |
| A change of meaning: removing or redefining a concept, a pinned input, an oracle | Waits for the #373 rewrite (#55), except the canonical render format (#54) |

## Gates

- Lint, tests and contracts: under 2 minutes on a pull request.
- Mutation: diff-scoped, under 5 minutes on a pull request; a full sharded
  run nightly. The TypeScript compiler keeps its 100% Stryker break score; Go
  starts report-only and ratchets.

## Not in scope

- Replacing Flux. The signed per-Project artifact keeps that possible later.
- Changing what the model means before the cutover, beyond the canonical
  render format.
- A second control-plane server. The single control plane gets a restore path
  (#41) instead; high availability is a separate decision.

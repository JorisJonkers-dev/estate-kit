# Overview

estate-kit is a fresh repository that replaces deploy-kit, delivery and
estate-dashboard. A Rust compiler and an in-cluster Go service compose the
estate. Flux stays the one applier, and each Project's state stays with the
Project. The new stack is built at byte-identical parity with today's renders.
It then runs in shadow beside production, and replaces the old stack in stages.
The model rewrite (deploy-kit#373) follows the cutover.

## At a glance

![Context: Project CI, the service, ghcr and Flux](../diagrams/png/context.png)

A Project's CI asks the service to deploy. The service composes, dry-runs,
signs and moves the Project's `prod` tag. Flux pulls the tag and applies it.

## The parts of estate-kit

Three programs and three components, all in one repository at one version. The
compiler is the only part that knows the model; the others act on what it
renders.

![The parts of estate-kit and what each acts on](../diagrams/png/components.png)

## System context (C4 level 1)

Everything estate-kit talks to, and nothing else. An integration not on this
diagram does not exist.

![C4 context](../diagrams/png/c4-context.png)

## Containers (C4 level 2)

Every deployable unit and the protocol on each connection.

![C4 containers](../diagrams/png/c4-containers.png)

## Evaluation of what is replaced

The TypeScript code is healthy. Its risk is the toolchain around it, and the
EMF implementation has nothing to port.

| | TypeScript compiler (`src/`) | EMF implementation (`emf/`) |
| --- | --- | --- |
| Size | 102 files, about 15,900 lines | 536 model and Java files |
| Runtime dependencies | 2 (`yaml`, `zod`) | Eclipse, Maven and Tycho, JDK 21 |
| Quality bar | Coverage about 99.5%, mutation break score 100% | Parity with the oracle files |
| Weak points | About 230 npm packages in the dev and CI tree; types erased at runtime; Node startup; no single binary | Exists only for the course; deleted after the 2026-10-30 hand-in |
| Carried forward | Behaviour, through the oracle files | The parity contract |

## Order of work

The old repositories serve production and keep evolving until the last switch.
Each phase closes on a gate.

1. **Found estate-kit** after the 2026-10-30 hand-in and the deletion of
   `emf/`. Import deploy-kit, delivery and estate-dashboard with history. Write
   the founding records and `docs/lessons.md`. Gate: the imported trees build.
2. **Port the compiler to Rust.** Gate: every oracle file renders
   byte-identical to the TypeScript compiler.
3. **Merge the Go services**, after characterization tests pin their current
   behaviour. Gate: the service composes from real fragments in a test cluster.
4. **Shadow.** Compose beside production, write only `shadow/` tags, diff the
   renders, and port forward every change made to the old stack. Gate:
   identical renders for an agreed number of days.
5. **Staged switch:** the compiler, then registry tags replacing pin commits,
   then the dashboard. Gate: the estate runs on estate-kit alone.
6. **Archive** the old repositories and slim the estate repo.
7. **Rewrite the model** (the deploy-kit#373 chain) in Rust, up to 1.0.

## Risks and open questions

- **Catch-up drift.** Both stacks evolve during the port; the shadow diff is
  the check.
- **Two toolchains.** Rust and Go, plus npm for the UI build, held by one
  maintainer.
- **Go mutation tooling** is immature; the service may need a small runner of
  its own.
- **Vault on the deploy path.** If Vault is down, nothing new is signed; Flux
  keeps serving the last tags.
- **No PR-reviewable pin.** A tag move leaves no commit; the audit trail is the
  GitHub Deployments and the event log.
- **Open:** how many days of identical shadow renders are enough to switch.
- **Open:** the name and kind (CRD or ConfigMap) of the per-Project object for
  Pause and Rollback.
- **Open:** which Rust YAML parser keeps source positions, to be chosen by a
  spike.
- **Open:** how a Mailbox is shared beyond its own Project, if ever.

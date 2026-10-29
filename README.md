# estate-kit

estate-kit models an estate once and delivers it: the applications on its
Kubernetes cluster, and the NixOS hosts that cluster runs on. It replaces
[deploy-kit](https://github.com/JorisJonkers-dev/deploy-kit),
[delivery](https://github.com/JorisJonkers-dev/delivery) and
[estate-dashboard](https://github.com/JorisJonkers-dev/estate-dashboard).

> **Status: design.** This repository holds the design, its diagrams and the
> research behind it. No code lives here yet. The three repositories above are
> imported, with their history, after 2026-10-30. Until the cutover they keep
> serving production.

## The shape

- **One Rust workspace.** Every program is Rust, in small crates layered by
  bounded context; only the UI is Vue.
- **One model and one compiler.** A Rust binary validates authored intent
  offline and renders it: Kubernetes objects for Projects, typed host data for
  NixOS nodes. It implements deploy-kit's 1.0 specification.
- **A service in the cluster** that links the same compiler. It composes the
  estate, dry-runs every change against the API server, signs each render
  through Vault Transit, and moves the Project's `render/<p>:prod` tag. Flux
  stays the one applier.
- **A host applier on each node**, outside Kubernetes. It pulls its signed
  generation, takes a cluster-wide Lease, drains its node, switches, and
  reboots only inside its maintenance window.
- **Components** (the migration runner, the secret grant, the database and
  bucket catalogs, backups and the mail provisioner) are Rust binaries here,
  sharing one version.

Each Project keeps its own state. No repository holds a list of what is
deployed, and no lock file sits outside a Project.

## What is in here

| Path | Holds |
| --- | --- |
| [`CONTEXT.md`](CONTEXT.md) | The vocabulary that estate-kit adds to deploy-kit's |
| [`docs/design/`](docs/design/README.md) | Where the design lives and how it is organised |
| [`docs/diagrams/`](docs/diagrams/README.md) | Every diagram, as an editable draw.io source plus a PNG |
| [`docs/decisions/`](docs/decisions/README.md) | The decision register, numbered in reading order |
| [`docs/research/`](docs/research/README.md) | Prior art, and the private papers submodule |

# Inside the service (Go)

The service is a thin orchestrator around ports. The rollout package holds the
logic. Every other package adapts one outside system, and each port has exactly
one hand-written fake.

## Packages

![Go service packages](../diagrams/png/go-packages.png)

| Package | Holds | Outside system |
| --- | --- | --- |
| `api` | HTTP handlers and the SSE event stream | None |
| `auth` | GitHub OIDC, auth-api and service-account token verifiers | OIDC discovery endpoints |
| `rollout` | The rollout state machine and the composition queue | None |
| `compose` | Runs the Rust binary, reads `result.json` | The binary |
| `registry` | Fragments, renders, tags, cache lookup | ghcr, through oras-go |
| `signer` | Signs a render digest | Vault Transit |
| `cluster` | Server-side dry-run, release status | API server, through client-go |
| `github` | Deployment status, check runs, workflow dispatch | GitHub App |
| `store` | The append-only rollout event log | Postgres |
| `ui` | The embedded Vue assets | None |

## The rollout core

A rollout is a fold over its events, so its state can always be rebuilt from
the log. The queue runs one composition at a time; triggers that arrive
meanwhile merge into the next composition, and each waiting deploy job learns
which composition carries its fragment.

![Class diagram: the rollout core](../diagrams/png/go-rollout.png)

## The event log

One Postgres table of rollout events: rollout id, sequence, type, version,
time, payload. A deploy job's stream resumes from a sequence number, and the UI
reads history from the same table. Pause and held state stay in the Project's
cluster object.

## One replica

The service runs as one replica, with no leader election. If it restarts
mid-rollout, the event log says where each rollout stood, and Flux keeps
serving the last tags.

# Security

One threat table per trust boundary, and one authorization matrix that tests
enforce. Everything here is Proposed until the maintainer accepts it.

## Trust boundaries

Vault, the edge, the service and the API server sit inside the cluster.
GitHub, the browser, ghcr and the binary cache sit outside it, and every
crossing carries a verified identity.

![Trust boundaries](../diagrams/png/trust-boundaries.png)

## Threats per boundary (STRIDE)

| Boundary | Threat | Mitigation |
| --- | --- | --- |
| Runner to edge | Spoofing: a forged deploy call | GitHub OIDC JWT; `repository_id`, the pinned workflow and the environment checked against Platform Intent |
| Runner to edge | Tampering: an altered fragment | Fragments are signed and named by digest |
| Runner to edge | Repudiation: who deployed what | The event log records the token's claims; the GitHub Deployment records the run |
| Browser to edge | Elevation: an operator action by a viewer | Roles from auth-api groups; every route has a row in the matrix below |
| Browser to edge | Cross-site request forgery | Same-origin UI, SameSite cookies |
| Service to Vault | Elevation: the service signs anything | The Transit key may only sign; the service signs only after an accepted dry-run, and a test proves it |
| Service to Vault | Disclosure: the signing key leaks | The key is not exportable |
| Service to ghcr | Tampering: someone else moves a tag | Flux and the host appliers verify the signature against Vault's public key; the App token is scoped to `render/` and `host/` |
| Applier to cache | Tampering: a malicious closure | Nix signature checked against one trusted public key; the host tag is signed too |
| Applier to API | Elevation: a node evicts other nodes' pods | RBAC limits each node to its own pods and the one Lease |
| Applier to API | Denial: a Lease held forever | The Lease has a time-to-live |
| Break-glass | Elevation: a hand-made switch | Needs local root on the node and a signed generation |

## Authorization matrix

Every route is one row here, and a test fails on a route without one.

| Action | Project CI (release) | Project CI (PR) | Estate CI | Viewer | Operator | Admin | Flagger | Host applier |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Deploy a release | own Project | no | platform | no | no | no | no | no |
| Plan or dry-run | own Project | own Project | platform | no | no | no | no | no |
| Watch a rollout | own rollout | own run | own rollout | yes | yes | yes | no | no |
| Pause, resume, roll back | no | no | no | no | yes | yes | no | no |
| Change admissions | no | no | through Platform Intent | no | no | yes | no | no |
| Answer a Release Gate webhook | no | no | no | no | no | no | yes | no |
| Read its host tag | no | no | no | no | no | no | no | own node |
| Read estate status | no | no | no | yes | yes | yes | no | no |

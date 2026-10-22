# Design review: quality scenarios

The design review weighs every finding against these scenarios, not against
taste. They follow the quality-attribute scenarios of ATAM (the Architecture
Tradeoff Analysis Method): a stimulus, the state the system is in, and the
response that counts as success.

## Priorities

Set by the maintainer on 2026-10-22.

| Priority | Quality |
| --- | --- |
| High | Change safety |
| High | One-maintainer load |
| High | Recoverability |
| High | Supply-chain security |
| High | Deploy speed |
| High | Evolvability |
| Medium | Auditability |
| Medium | Learning value |

## Constraints

- **Effort.** The maintainer has a few hours a week for estate-kit. Anything
  bespoke must earn its upkeep against that budget.
- **Bounds.** Nothing is fixed. The review may propose replacing the compiler,
  the service, Rust or Go, or anything else. A settled choice reopens only on a
  new fact, and the review's job is to supply those facts.
- **Production.** deploy-kit, delivery and estate-dashboard serve production
  until the cutover. One cluster, a single control-plane node
  (`frankfurt-contabo-1`), mostly Raspberry Pi workers, seven NixOS hosts.

## Scenarios

| # | Quality | Stimulus | State | Response that counts as success |
| --- | --- | --- | --- | --- |
| S1 | Change safety | A release whose render the API server would reject | Normal operation | Refused before the `prod` tag moves; the line in the Project's YAML is named in CI |
| S2 | Change safety | A release that deploys but fails health analysis | Normal operation | Traffic stays on the old version; the Project is Held; no other Project is affected |
| S3 | Change safety | The operator rolls back a Project | Normal operation | The previous signed render serves again within 5 minutes |
| S4 | One-maintainer load | A dependency (Kubernetes, Flux, a crate, a Go module) ships a breaking release | Maintainer has a few hours that week | Upgrade lands in one sitting; no bespoke code beyond the adapter that touches it |
| S5 | One-maintainer load | The maintainer returns after two months away | Nothing changed meanwhile | Can ship a change the same day from the docs, without rediscovering the system |
| S6 | Recoverability | The estate-kit service pod dies mid-signing | Deploy in flight | No half-moved tag; the deploy resumes or fails cleanly; Flux keeps serving the last tag |
| S7 | Recoverability | Vault, ghcr or GitHub is down | Deploy wanted | Serving is unaffected; deploys fail loudly and resume when it returns |
| S8 | Recoverability | The single control-plane node is lost | Any time | Workloads keep running; a documented path restores the API server; break-glass switches a node without the cluster |
| S9 | Recoverability | A host switch leaves a node unhealthy | Host rollout | The node rolls back to its last generation; no second node switches |
| S10 | Supply-chain security | A compromised Project repository or workflow | Attacker can push and run Actions | Cannot deploy another Project, cannot change Platform Intent, cannot sign anything not built from its own sources |
| S11 | Supply-chain security | A tampered image or render in the registry | Normal operation | Flux and the host applier refuse it on signature or digest |
| S12 | Deploy speed | A one-line change merged in a Project | Normal operation | Serving within 10 minutes at p95; pull-request checks within 2 minutes |
| S13 | Evolvability | A new kind of thing to deliver (as Mailboxes were) | Model at 1.0 or before | Added in the model and one adapter, without touching the service or the applier |
| S14 | Evolvability | The model rewrite (the deploy-kit#373 chain) | After the cutover | Lands as model changes, not as a second port |
| S15 | Auditability | "Who deployed what, when, and why did the render contain X?" | Any time | Answered from the event log, GitHub Deployments and the render's trace |

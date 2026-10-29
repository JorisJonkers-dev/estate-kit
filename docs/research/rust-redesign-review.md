# Review of the all-Rust redesign

A review of the move to an all-Rust workspace, held on 2026-10-29 against
`main` at 8e5e1f1. The [design review](review/README.md) of 2026-10-22 never
saw that design: [record 13](../decisions/0013-every-program-is-rust.md)
reversed its D1 a week later, and records 13 to 18, 48, 50, 55, 63 and 65 to
71 were written and accepted the same day. This page records what the review
found, what it refuted, and what the maintainer decided. The work it causes is
tracked in [#82](https://github.com/JorisJonkers-dev/estate-kit/issues/82) and
its sub-issues.

## Method

| Pass | Who | Input | Output |
| --- | --- | --- | --- |
| Review | Six Claude Haiku reviewers, one per area, each reading the area's records and pages | Plan, workspace, compiler, service, rewrites, gates | 48 findings |
| Review | Six DeepSeek V4.1 Flash reviewers, one per area, each reading the whole corpus | Same areas | 47 findings |
| Quote check | A script | Every finding's verbatim quotes against the cited file | 95 of 95 kept |
| Skeptic | Mistral Large 4, told to refute | The findings and the corpus | 61 merged findings: 10 kept, 31 narrowed, 20 refuted |
| Decision review | A separate session, record by record | Rows 1 to 71 and every written record | A per-record verdict and a merge table |
| Synthesis | Claude Opus, in the maintainer's session | All of the above, with claims about delivery and estate-dashboard checked in their code | This page |

A finding counts as converged when both review families, or a review family
and the decision review, raised it independently and the skeptic kept it.

## What cannot be built as written

| Finding | Fix | Decided |
| --- | --- | --- |
| [Record 58](../decisions/0058-flux-is-locked-down-per-project-and-the-service-dry-runs-as-an-identity-that-cannot-write.md)'s admission policy refuses every non-dry-run request from the service's identity, yet records 17, 28 and 63 have that identity write its writer Lease and each Project's ProjectControl | Exempt the two objects by name, with a fixture each | 1 |
| [Record 61](../decisions/0061-a-rollback-moves-the-tag-back-to-the-last-serving-render-without-composing.md) promises a Rollback that works with Vault down, but [record 62](../decisions/0062-ghcr-tags-move-with-a-machine-account-token-kept-in-vault.md) reads the ghcr token from Vault at the moment of use; 61 also moves the tag without the Lease that [record 63](../decisions/0063-the-service-has-one-writer-and-reconciles-from-observed-state.md) requires | Sync the token into a Kubernetes Secret; the Rollback takes the Lease and finds the last Serving render from the registry | 2 |
| The Release Gate is said never to write, yet delivery's gate creates and updates a ConfigMap per Application and patches migration Jobs (`internal/gate/kube.go`); Observation is said to be read only, yet the dashboard writes Alertmanager silences and mirrors them in its own table | One Proposed record places each write | 3 |
| Observation runs in the service's binary and pod and shares its kube adapter, so [record 50](../decisions/0050-five-bounded-contexts.md)'s "the read side holds no write credential" is false | Observation becomes its own read-only binary | 4 |
| Record 63 calls the tag move a compare-and-swap, and ghcr has no conditional write | Read, verify, write, fenced by a freshly checked Lease; re-read after every write; state the window | No decision needed |
| [Record 18](../decisions/0018-the-service-links-the-compiler.md)'s containment does not hold: a deadline cannot stop a blocking thread, catching a panic needs unwinding and misses an abort, nothing caps memory across a Composition, and a budget breach is reported as internal although authored input caused it | A step budget, a memory cap, unwinding panics, recovery by pod restart, and a refusal code for a budget breach | 5 |
| The crate tree cannot load: component binaries and component domain crates share package names, and the `-app` crates are missing | Distinct binary names; list the `-app` crates | No decision needed |
| The crate tree cannot be layered as drawn: `reconcile` in foundation drives ports it cannot see, the `Renderer` port has no home, a constructor "private to step-check" cannot cross crates, and [record 65](../decisions/0065-the-workspace-is-layered-and-the-crate-graph-is-checked.md) omits Observation and names one context edge where the page names five | Pure decide in foundation; `Renderer` in `deliverable`; sealed proof tokens; the edges in the layer table file | No decision needed |

## The register breaks its own rules

- Eleven records rest on later numbers, and the rests-on graph has cycles:
  17 and 18, 50 and 65, and 21, 30 and 31.
- Three Accepted records rest on Proposed ones: 63 on 24, 67 on 64, 69 on 61.
- Seven records cite lesson DO-7, which curation dropped, and lesson TM-5
  still says mutation runs per pull request.
- Forty Accepted register rows have no file.
- Nothing checks any of this.

## Smaller findings that stand

- The shadow's expected-differences ledger lists "the canonical format" as a
  cause a structural diff can never produce; its causes are an open list; and
  it is not among the Locked contracts.
- [Record 15](../decisions/0015-the-rust-types-agree-with-the-committed-schemas-on-their-corpus.md)'s
  agreement should be one-directional and assert every diagnostic, not only
  the verdict; spike #18 should also settle how the schema validator's
  `required` errors map to model paths.
- [Record 71](../decisions/0071-every-diagnostic-names-its-locations-and-every-output-traces-to-its-source.md)'s
  per-field provenance is one element reference per field, while a merged
  field has several; its reorder test is wrong for ordered lists.
- "Render key" means the input digest in `CONTEXT.md` and
  [record 20](../decisions/0020-no-render-cache-an-unchanged-render-is-not-published-again.md),
  and the Transit signing key in records 17 and 21; and it leaves out the
  cross-Project Surface facts that Link reads.
- The composition queue's location is open on a page while the end-to-end page
  assumes a Postgres row and says the writer "resumes" it.
- Recreate stops the only pod on every upgrade, and nothing says a waiting
  deploy keeps its authentication.
- Events that reconcile appends after a crash are not marked as reconstructed.
- The end-to-end page signs before it takes the Lease.
- Phase 5's fallback ships without provenance registration, which the plan's
  own outcome requires; phase 4's fallback is the freeze that
  [record 67](../decisions/0067-the-compiler-is-written-to-the-1-0-contract.md)
  rejected.
- Characterization fixtures are deleted at archive, though they are the only
  witness of behaviour no specification states.
- Text gone stale: record 13 names three components where everything else
  names six; issue bodies #9, #20, #65 and #72; the overview, the design
  README and the security page; `AGENTS.md`'s Locked list.

## Scope for one maintainer

About 270 hours plus an open compiler phase, at a few hours a week, puts the
cutover 1.5 to 2 years out while deploy-kit is maintained beside it. Rewriting
six working components, the dashboard API and liquibase-runner before the
cutover is the new long pole. The decision review also named machinery that no
scenario needs yet: per-field provenance and `explain`, event upcasters with
no second event version, a service-minted rollout token, and a bespoke
check-ports tool. It proposed folding the register from 71 rows to about 36 by
merging records that always change together.

## Refuted

The skeptic refuted these, each with a quote from the corpus:

- The 100% gates do not force tests before code: a crate reports until its
  tests are in.
- Mutation on main only is deliberate (deploy-kit ADR 0063).
- `check-layers` and `check-ports` are scheduled in
  [#60](https://github.com/JorisJonkers-dev/estate-kit/issues/60).
- The end-to-end and integration time budgets are acceptance criteria in
  [#72](https://github.com/JorisJonkers-dev/estate-kit/issues/72) and
  [#64](https://github.com/JorisJonkers-dev/estate-kit/issues/64).
- [Record 69](../decisions/0069-the-deploy-path-is-tested-end-to-end.md)
  already requires a green end-to-end run before a release.
- Phase 7's fallback does not break
  [record 55](../decisions/0055-every-go-and-python-program-is-characterized-before-it-is-rewritten.md),
  which forbids archiving until the fixtures pass.
- The six components share the reconcile loop at the level the page claims.
- The Liquibase JVM staying in its image is stated, not hidden.

## Outcomes

The maintainer decided eleven questions on 2026-10-29, each as the review
recommended.

| # | Question | Chosen |
| --- | --- | --- |
| 1 | The service's identity | One service account; the admission policy exempts the coordination Lease and ProjectControl by name, a fixture each |
| 2 | Rollback with Vault down | VSO syncs the ghcr token into a Kubernetes Secret; the Rollback takes the Lease and finds the last Serving render from the registry; the end-to-end registry requires the token |
| 3 | The hidden writes | One Proposed record: the gate's Job unsuspend and per-Application record stay in the Service context under the Lease; silences are Observation's one named write, with a narrow credential |
| 4 | Observation | Its own read-only binary and Deployment, with no Vault, ghcr or signing credential |
| 5 | Containing a composition | In-process, with a step budget, a memory cap per Composition, unwinding panics, recovery by pod restart, and a refusal code for a budget breach |
| 6 | When components are ported | Lazily, after the cutover; each keeps running from delivery until its rewrite is due |
| 7 | Deferred machinery | Event upcasters, per-field provenance and `explain`, the rollout token exchange, the check-ports tool |
| 8 | The register | Folded to about 36 rows; merged numbers stay as "Merged into N" |
| 9 | The rests-on rule | Acyclic, and an Accepted record rests only on Accepted ones, held by a check |
| 10 | Phase 5's fallback | Deleted |
| 11 | Characterization fixtures | A written behaviour summary in the owning crate's docs before they are deleted |

## Cost

The external model calls cost about 1.2 US dollars: the six DeepSeek reviews
cost 0.26 and the two Mistral skeptic calls 0.91, one of them a retry. The six
Haiku reviewers ran on a subscription.

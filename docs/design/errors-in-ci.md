# Errors in CI

Every error points at a line in the Project's YAML, whether the binary found it
offline or the service found it during composition or the dry-run. An error
that is wrong *in relation to* something else points there too, even in
another Project's repository
([record 71](../decisions/0071-a-diagnostic-is-a-coded-problem-with-typed-locations.md)).

## What a diagnostic holds

| Part | What it is |
| --- | --- |
| Code | One refusal code from the catalogue; also the problem+json `type` |
| Severity | Error or warning |
| Primary location | Where to fix it |
| Related locations | Each with a label: the other claim, the declaration it contradicts, the platform rule it breaks |
| Message and help | Human text, naming elements by their names, never by position |

A location is one of three kinds:

| Kind | Holds | Example |
| --- | --- | --- |
| Authored | Project, document, model path | `notes`, `notes.project.yml`, `/applications/0/mail/0` |
| Platform Intent | Model path in the platform document | `/policies/egress/2` |
| ClusterState fact | The fact's key in the pinned snapshot | `nodes/frankfurt-contabo-1/allocatable/memory` |

## Two references, each with one job

- The **model path** is an RFC 6901 pointer by position. It exists to find a
  line: the binary in CI resolves it from the checkout at the fragment's
  source commit, and the UI through GitHub at the same commit. The fragment
  never carries source positions ([record 71](../decisions/0071-a-diagnostic-is-a-coded-problem-with-typed-locations.md)).
- The **element reference** names the element by identity (`notes` /
  `api` / `worker` / `image`). It survives reordering, and it names an
  element outside the run that found it. Within one run the compiler maps
  each to the other.

This is Xtext's split: a validation names an object and a feature, and the
node model gives the line. It also settles the review's finding that the
oracles use RFC 6901 paths while this page once showed a dotted path: both
exist, for different jobs.

## Errors the API server finds

A server-side dry-run, an admission webhook or a CRD schema refuses a field of
a rendered object. Each Deliverable keeps the model paths of the elements it
came from, so the service shows the refusal against those elements, as a
whole. Mapping the refused field to the one line that set it needs
per-field provenance, which is deferred
([record 72](../decisions/0072-per-field-provenance-and-explain-are-deferred.md)).

## Who is told

| Situation | The Project refused | Everyone else |
| --- | --- | --- |
| A Project's own input is wrong | That Project | Nothing |
| A conflict with another Project, and only one fragment changed in this composition | The Project whose fragment changed | The other Project's open rollouts and the UI show the same diagnostic as a notice |
| A conflict, and both fragments changed | Both | Nothing more |
| The cause is Platform Intent or a ClusterState fact | The Project whose element relies on it | The Platform Intent location or the fact is a related location |

## Where errors appear

| Surface | What it shows | Limit |
| --- | --- | --- |
| Job log | rustc-style snippet: each location's source line with a caret, the primary labelled, the related ones with their labels; the code; a help line | None |
| Workflow annotations | The first errors, inline on the PR's YAML; related locations in the same repository as their own annotations | GitHub drops any beyond 10 per step and 50 per job |
| Check run `estate-kit` | Every error as an annotation on its line, posted in batches | None in practice |
| Job summary | A table per Project file: code, line, message, help, and each related location as a link pinned to its commit (another repository's links go to that repository) | None |
| Sticky PR comment | The render diff, each changed object with the elements it came from, and the error count | One comment, updated in place |

The log, the check run and the job summary carry every error, so nothing is
lost to the annotation cap. SARIF and per-line review comments were rejected:
both hit the same cap and add a second shape for diagnostics.

## Following a live object back

Deferred. Annotating each live object with its Project and element reference,
so the Observation views can lead from a pod, an alert or a drifted object to
the element and its line, depends on per-field provenance
([record 72](../decisions/0072-per-field-provenance-and-explain-are-deferred.md)).

## What counts as an error code

A code exists only for authored input that would do real harm on this estate,
and each code ships with a fixture that fires it. A code that relates two
locations has a fixture asserting both. The compiler's own invariants are tests
and assertions, never user-facing codes.

## A budget breach is authored input

The service bounds a Composition by a step budget, a memory cap and an input
budget ([record 18](../decisions/0018-the-service-links-the-compiler.md)).
A breach means the document asked for more than the estate allows, so it has
its own refusal code, a primary location on the document that spent the
budget, and is reported as a 4xx problem. Its fixtures are a looping input and
an oversized input. A panic is not a refusal: it is an internal problem.

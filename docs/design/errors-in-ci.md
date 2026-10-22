# Errors in CI

Every error points at a line in the Project's YAML, whether the binary found it
offline or the service found it during composition or the dry-run.

## How an error finds its line

A diagnostic carries its code, the file and the model path, for example
`applications.api.dependencies[0]`. The binary in CI resolves that path to a
line and column from the checkout at the fragment's source commit. The UI
resolves it through GitHub at the same commit. The fragment never carries
source positions.

## Where errors appear

| Surface | What it shows | Limit |
| --- | --- | --- |
| Job log | rustc-style snippet: the source line, a caret under the span, the code, a help line | None |
| Workflow annotations | The first errors, inline on the PR's YAML | GitHub drops any beyond 10 per step and 50 per job |
| Check run `estate-kit` | Every error as an annotation on its line, posted in batches | None in practice |
| Job summary | A table per Project file: code, line, message, help; plus the render diff on a plan or dry-run | None |
| Sticky PR comment | The render diff and the error count | One comment, updated in place |

## What counts as an error code

A code exists only for authored input that would do real harm on this estate,
and each code ships with a fixture that fires it. The compiler's own invariants
are tests and assertions, never user-facing codes.

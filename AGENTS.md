# Agent contract

The estate-wide conventions live in
[`JorisJonkers-dev/workspace`'s CLAUDE.md](https://github.com/JorisJonkers-dev/workspace/blob/main/CLAUDE.md)
and are not repeated here. This file holds only what the code cannot show you.

## What this repository is

estate-kit models the estate once and delivers it: Projects onto the
Kubernetes cluster, and host configuration onto the NixOS nodes beneath it. It
is in design. No code lives here yet; deploy-kit, delivery and
estate-dashboard keep serving production until the cutover.

## Where the truth lives

| What | Where | Normative? |
| --- | --- | --- |
| Vocabulary | [`CONTEXT.md`](CONTEXT.md) | Yes: names in code use these words unchanged |
| Decisions | [`docs/decisions/`](docs/decisions/README.md) | Yes |
| Contracts (schemas, OpenAPI, error catalogue) | `contracts/` (not yet written) | Yes, once written |
| Design pages and diagrams | [`docs/design/`](docs/design/README.md), [`docs/diagrams/`](docs/diagrams/README.md) | No: they explain, decisions rule |
| Research | [`docs/research/`](docs/research/README.md) | No |

Where a design page and a record disagree, the record wins and the page is
what gets fixed.

## Stop and ask

- **A Locked record is not yours to change.** A Locked record names the check
  that enforces it. If your change needs a Locked record to bend, stop and ask
  the maintainer; never work around it, weaken its check, or delete its
  fixture.
- **Contracts are Locked by default.** That covers the committed schemas, the
  OpenAPI file, the error catalogue, the `result.json` fixtures and the
  shadow's expected-differences ledger. Changing one needs the maintainer's approval in the pull request.
- **An unanswered design question is a Proposed record**, not an improvisation.
  Write the record (see [`docs/decisions/template.md`](docs/decisions/template.md)),
  open the pull request, and stop.

## Always

- Use the words in `CONTEXT.md`. A new concept gets its term there first.
- Give every rule you add a check that fails when the rule is broken.
- Keep a design page and its diagram in step: change a diagram's declaration in
  `docs/diagrams/specs.py` and regenerate, never edit the exported XML.
- Cite a record by link, never by bare number.
- Branch off `main` and use a conventional-commit title. No agent attribution
  anywhere.

## Checks

`Pipeline Complete` in [`ci.yml`](.github/workflows/ci.yml) is the one
required check on `main`. It holds these rules:

| Rule | Job |
| --- | --- |
| Diagrams are regenerated, never hand-edited | Diagrams (`scripts/check_diagrams.py`) |
| A record is cited by link | Record citations (`scripts/check_record_citations.py`) |
| A record's status matches the register; rests-on has no cycle, and Accepted rests only on Accepted; cited lessons were kept; Accepted rows have files | Records (`scripts/check_records.py`) |
| No paper is committed | Hygiene |
| Conventional-commit title, no agent attribution | PR title |
| Every relative link and anchor resolves | Links |

Run a check locally with `python3 scripts/<check>.py`.

## Never

- Commit a paper or other third-party work here. Papers belong in the private
  `docs/research/papers` submodule.
- Edit the published site. It is built from `docs/` on every merge.
- Push to `main`.

## Nested agent files

Once code lands, each context folder under `crates/` (`compiler/`, `service/`,
`observation/`, `hosts/`, `components/`) and `ui/` gets a short `AGENTS.md`
holding only what applies inside it. The workspace's layout and layer rules are
in [`docs/design/rust-workspace.md`](docs/design/rust-workspace.md).

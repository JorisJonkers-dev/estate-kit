# Diagrams

Every diagram is generated, in draw.io's own components, and laid out by
draw.io itself. No coordinate is written by hand.

| Kind | Source | Components | Layout |
| --- | --- | --- | --- |
| Sequences | Mermaid | UML lifelines, `alt` and `opt` frames, notes, numbered messages | Mermaid |
| State machines | Mermaid | States with initial and final pseudostates | ELK, after conversion |
| Class diagrams, metamodels | Mermaid | UML classes sized to their members, stereotypes, multiplicities | Mermaid |
| Use cases | draw.io XML | Actors, a system boundary, use cases, «include» | ELK |
| C4 | draw.io XML | C4 people, systems, containers, database containers | ELK |
| Deployment | draw.io XML | Nodes as containers, cylinders for stores | ELK |
| Flows and graphs | draw.io XML | Steps, decisions, notes for artifacts, folders for packages | ELK |

Each diagram has a header that names the one use case or interaction it shows,
and colours that read in both themes. The PNGs are exported dark.

## Files

| Path | What | Written by |
| --- | --- | --- |
| [`specs.py`](specs.py) | Every declaration except the metamodels | You |
| [`metamodels.py`](metamodels.py) | deploy-kit's Ecore metamodels, one concept each, marked with what estate-kit changes | You |
| [`gen.py`](gen.py) | The vocabulary both declare in, and the colours | You |
| `raw/` | The sources: Mermaid (`.mmd`) or draw.io XML (`.drawio`) | `specs.py`, `metamodels.py` |
| `src/` | The laid-out draw.io files | `build.py` |
| `png/` | The exports, each embedding its draw.io file | `build.py` |
| `diagrams.lock` | The digest of every source and of the file built from it | `build.py` |

## Changing a diagram

Edit its declaration, never a generated file. Then regenerate the sources and
build:

```bash
cd docs/diagrams
python3 specs.py
python3 metamodels.py <path to a deploy-kit checkout>   # only for mm-*
DRAWIO=/Applications/draw.io.app/Contents/MacOS/draw.io python3 build.py [name ...]
```

`build.py` needs draw.io Desktop 32 or later: earlier releases cannot convert
Mermaid or run ELK. Look at each PNG you changed before you commit it.

CI's Diagrams job ([`check_diagrams.py`](../../scripts/check_diagrams.py)) has
no draw.io. It regenerates `raw/` from `specs.py` and compares it byte for
byte, checks `diagrams.lock` against `raw/` and `src/`, and checks that each
PNG embeds its `src/` file. A declaration changed without a rebuild, or a
generated file edited by hand, fails the job.

## Names

| Prefix | Kind |
| --- | --- |
| `uc*` | One use case each |
| `seq-*` | Sequence diagrams, one interaction each |
| `state-*` | State machines |
| `c4-*`, `context`, `context-map` | Context, containers and bounded contexts |
| `deploy-*` | Deployment |
| `inputs-*`, `flow-*` | Where each stage's inputs come from, and decisions |
| `rust-*`, `host-applier`, `mail-provisioner`, `components` | The internals |
| `alignment`, `trust-boundaries` | How the contracts stay aligned, and what crosses each trust boundary |
| `mm-*` | deploy-kit's metamodels |

# Diagrams

Each diagram has two files: a draw.io source in [`src/`](src/) and an exported
PNG in [`png/`](png/). The PNG embeds the draw.io XML, so opening it in draw.io
recovers the editable diagram.

The sources are generated. [`specs.py`](specs.py) declares every diagram on a
grid, and [`gen.py`](gen.py) turns each declaration into draw.io XML in a dark
theme. To change a diagram, edit its declaration in `specs.py`, not the XML,
and regenerate:

```bash
cd docs/diagrams
python3 specs.py
mv ./*.drawio src/
for f in src/*.drawio; do
  b=$(basename "$f" .drawio)
  /Applications/draw.io.app/Contents/MacOS/draw.io -x -f png -e -s 2 -b 24 -o "png/$b.png" "$f"
done
```

| Prefix | Kind |
| --- | --- |
| `uc*` | One use case each |
| `mm-*` | deploy-kit's metamodels, one concept each, marked with what estate-kit changes (from `metamodels.py`) |
| `seq-*` | Sequence diagrams |
| `state-*` | State machines |
| `deploy-*`, `context` | Deployment and context |
| `inputs-*` | Where each stage's inputs come from |
| `rust-*`, `go-*` | Class and package diagrams of the internals |
| `alignment` | How YAML, the schemas, Rust and Go stay aligned |

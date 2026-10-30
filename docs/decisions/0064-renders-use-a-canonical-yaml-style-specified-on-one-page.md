---
status: proposed  # proposed | accepted | locked
date: 2026-10-29
rests-on: [6, 67]
lessons: [CS-5, TM-2]
---

# Renders use a canonical YAML style specified on one page

## Context

deploy-kit renders through eemeli/yaml's YAML 1.1 output, whose quoting no Rust
crate reproduces. The Rust compiler meets deploy-kit's rendered oracles in
structure and then rewrites them once in its own format
([record 67](0067-the-compiler-is-written-to-the-1-0-contract.md)). Whatever
the format, it must be reproducible by any implementation from a written
specification ([review](../research/review/README.md) D12).

## Decision

Every YAML Deliverable is written in one canonical style, specified on one page
in `contracts/` and implemented once in the `canonical` crate:

- one document per file, after a fixed `# GENERATED` header line;
- keys in the order the narrow object model declares them;
- a string is plain only if it matches a short whitelist pattern and is not a
  YAML 1.1 or 1.2 special value; otherwise it is double-quoted with JSON
  escapes;
- a multi-line string is a `|` block literal with explicit chomping;
- integers and booleans plain; no anchors, aliases, tags or flow collections;
  two-space indent; no line folding.

JSON Deliverables are RFC 8785 canonical JSON, with keys in UTF-16 code-unit
order.

## Alternatives

| Option | Cost if taken | Why rejected |
| --- | --- | --- |
| RFC 8785 JSON for every render | Diffs that people read are harder | Renders are reviewed by people |
| Reproduce eemeli/yaml's YAML 1.1 output in Rust | A bespoke emitter kept forever | The style is a library's, not ours |
| Snapshot tests, or the YAML 1.1 output as the format | Expected outputs depend on one library's style | Oracle files at the four seams only, in the style one page specifies |

## Consequences

- Easier: any implementation can match the bytes from one page.
- Harder: every Project is reapplied by Flux once when the format lands.
- Forbidden: a second emitter; a render not produced by `canonical`.

## Confirmation

Property tests in `canonical` round-trip generated strings and objects; a
differential test checks every rendered oracle against the specification's
examples.

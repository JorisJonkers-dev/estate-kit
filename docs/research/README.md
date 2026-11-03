# Research

Prior art and papers behind the design.

## Papers

The papers live in a private repository,
`JorisJonkers-dev/estate-kit-papers`, mounted here as a submodule at
[`papers/`](papers/). Many are third-party works that may not be
redistributed, so they never land in this public repository. With access,
fetch them with:

```bash
git submodule update --init docs/research/papers
```

Without access the directory stays empty, and nothing here depends on it.

The papers are sorted into theme folders grouped by subject, such as
`papers/hosts/updates-and-upgrades/` and `papers/delivery/progressive-delivery/`.
Each PDF has a Markdown conversion beside it. Each theme folder's `INDEX.md`
gives every entry a summary written from its abstract, its DOI, why it matters
to estate-kit, and whether it is filed or still to fetch. `papers/INDEX.md`
starts from estate-kit's open questions and points to the themes that answer
them. `papers/notes/` holds prose that is not one paper: prior-art
comparisons, the survey method, and the evidence on a k3s serverless recipe.
Every index is generated from `papers/catalog.json`.

## Notes

Research notes that quote no paper at length live beside this file, one per
topic.

| Note | What it covers |
| --- | --- |
| [Multi-tenancy](multi-tenancy.md) | Data isolation, pooling, migrations, context propagation, identity, lifecycle, backups, masking and mail for many Tenants |
| [One cluster or several, and many Tenants in one](multi-cluster.md) | Scaling limits, GitOps across clusters, cells, federation, and in-cluster isolation |
| [Splitting estate-kit](decomposition.md) | Use cases, subdomains and candidate services; the deploy path without Flux; Flagger; a live view; depending less on GitHub |

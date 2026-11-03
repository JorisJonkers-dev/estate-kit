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
`papers/INDEX.md` lists every paper, with its DOI and why it matters.

## Notes

Research notes that quote no paper at length live beside this file, one per
topic.

| Note | What it covers |
| --- | --- |
| [Multi-tenancy](multi-tenancy.md) | Data isolation, pooling, migrations, context propagation, identity, lifecycle, backups, masking and mail for many Tenants |
| [One cluster or several, and many Tenants in one](multi-cluster.md) | Scaling limits, GitOps across clusters, cells, federation, and in-cluster isolation |
| [Splitting estate-kit](decomposition.md) | Use cases, subdomains and candidate services; the deploy path without Flux; Flagger; a live view; depending less on GitHub |

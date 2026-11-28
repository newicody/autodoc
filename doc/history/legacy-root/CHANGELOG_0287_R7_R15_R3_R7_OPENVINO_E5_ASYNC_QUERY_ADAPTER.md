# Changelog 0287-r7-r15-r3-r7

- Added an async adapter for the existing multilingual-e5-small pipeline.
- Locked query prefixing to `query:`.
- Locked normalized dense output to 384 dimensions.
- Reused `DenseQueryEmbedding`.
- Added serializable construction evidence without raw vectors.
- Deferred Qdrant and SQL execution to the next unit.
- r7-r1: aligned the runtime docstring with the source-level no-nested-loop rule.

# Qdrant named collection control

```text
love_installed_runtime.ini
        |
        v
canonical collection plan + digest
        |
        +---- preview/readback ----> Qdrant get_collection
        |
        +---- approved execute ----> create physical collection
                                     create canonical payload indexes
                                     exact readback
```

Canonical shape:

```text
physical collection: autodoc_context_e5_384_hybrid_v1
dense vector:        dense_e5_v1 / 384 / Cosine
sparse vector:       sparse_lexical_v1
deferred alias:      autodoc_context_hybrid_current
payload:             SQL/provenance references only
```

The alias is not created or switched in this phase. The existing
`autodoc_context_current` target is not deleted or modified.
The r10-r1 correction preserves legacy direct settings construction without changing named mode.

# Live Qdrant analysis projection

```text
SQL ContextAuthorityObject (authoritative body)
        |
        +--> passage: text --> existing async OpenVINO E5 pipeline
        |                         --> dense_e5_v1 / 384 / normalized
        |
        +--> exact build_sparse_lexical_query()
                                  --> sparse_lexical_v1
        |
        v
existing QdrantClientProjectionExecutor
        | gated upsert of one named-vector point
        v
autodoc_context_e5_384_hybrid_v1
        | payload: refs, digest, scope, validity only
        v
SQL-authoritative later rehydration
```

The async adapter does not introduce an event loop. Its caller must await it inside the Scheduler-owned execution path.
